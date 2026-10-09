"""Passive, independently implemented profiles for newer format routes."""
import hashlib
import json
import re
import struct


def tracev3_state(data):
    import lz4.block
    if len(data) < 224 or struct.unpack_from('<IIQ', data) != (0x1000, 0x11, 208):
        raise ValueError('Unsupported tracev3 header')
    result, position, catalog_seen = [], 0, False
    while position < len(data):
        if len(data) - position < 16:
            raise ValueError('Truncated tracev3 chunk')
        tag, subtag, length = struct.unpack_from('<IIQ', data, position)
        end = position + 16 + length
        aligned = (end + 7) // 8 * 8
        if aligned > len(data):
            raise ValueError('Truncated tracev3 body/padding')
        body = data[position + 16:end]
        if tag == 0x600b:
            catalog_seen = True
        if tag != 0x600d:
            result.append(('opaque', data[position:aligned]))
        else:
            if not catalog_seen or any(data[end:aligned]):
                raise ValueError('Unsupported tracev3 chunkset ordering/padding')
            blocks, offset, dictionary, decoded_total = [], 0, b'', 0
            while offset < len(body):
                marker = body[offset:offset + 4]
                if marker == b'bv4$':
                    if offset + 4 != len(body):
                        raise ValueError('Trailing tracev3 stream bytes')
                    break
                if marker not in (b'bv4-', b'bv41') or offset + 8 > len(body):
                    raise ValueError('Invalid tracev3 block')
                decoded_size = struct.unpack_from('<I', body, offset + 4)[0]
                decoded_total += decoded_size
                if not decoded_size or decoded_total > 64 * 1024 * 1024:
                    raise ValueError('Tracev3 oracle decoded limit exceeded')
                if marker == b'bv4-':
                    next_offset = offset + 8 + decoded_size
                    raw = body[offset + 8:next_offset]
                else:
                    if offset + 12 > len(body):
                        raise ValueError('Truncated tracev3 LZ4 length')
                    encoded_size = struct.unpack_from('<I', body, offset + 8)[0]
                    next_offset = offset + 12 + encoded_size
                    if next_offset > len(body):
                        raise ValueError('Truncated tracev3 LZ4 payload')
                    raw = lz4.block.decompress(body[offset + 12:next_offset],
                                               uncompressed_size=decoded_size, dict=dictionary)
                if next_offset > len(body) or len(raw) != decoded_size:
                    raise ValueError('Tracev3 decoded length mismatch')
                blocks.append((decoded_size, hashlib.sha256(raw).hexdigest()))
                dictionary = (dictionary + raw)[-65536:]
                offset = next_offset
            else:
                raise ValueError('Missing tracev3 stream end marker')
            result.append(('chunkset', tag, subtag, blocks))
        position = aligned
    return result


def rtf_state(data, image_state):
    if len(data) > 16 * 1024 * 1024 or not data.startswith(b'{\\rtf1'):
        raise ValueError('Unsupported RTF profile')
    position, nodes = 0, 0

    def group(depth=0):
        nonlocal position, nodes
        if depth > 128:
            raise ValueError('RTF nesting limit exceeded')
        start = position
        position += 1
        tokens = []
        while position < len(data):
            nodes += 1
            if nodes > 100000:
                raise ValueError('RTF node limit exceeded')
            char = data[position]
            if char == 123:
                tokens.append(group(depth + 1))
            elif char == 125:
                position += 1
                controls = [token[1] for token in tokens if token[0] == 'control']
                if 'pict' in controls:
                    metadata, payload = [], bytearray()
                    for token in tokens:
                        if token[0] == 'text':
                            text = re.sub(rb'\s+', b'', token[1])
                            try:
                                payload.extend(bytes.fromhex(text.decode('ascii')))
                            except ValueError as exc:
                                raise ValueError('Invalid RTF picture hex') from exc
                        elif token[0] == 'binary':
                            payload.extend(token[1])
                        elif token[:2] == ('control', 'bin'):
                            continue
                        else:
                            metadata.append(token)
                    if 'pngblip' in controls or 'jpegblip' in controls:
                        content = image_state(bytes(payload))
                    else:
                        content = hashlib.sha256(payload).hexdigest()
                    return ('picture', metadata, content)
                if 'object' in controls or (tokens and tokens[0] == ('symbol', '*') and
                                            not any(c in ('shppict', 'blipuid') for c in controls)):
                    return ('opaque', data[start:position])
                return ('group', tokens)
            elif char == 92:
                position += 1
                if position >= len(data):
                    raise ValueError('Trailing RTF escape')
                if data[position] == 39:
                    encoded = data[position + 1:position + 3]
                    if len(encoded) != 2 or not re.fullmatch(rb'[0-9a-fA-F]{2}', encoded):
                        raise ValueError('Invalid RTF character escape')
                    tokens.append(('hex-character', int(encoded, 16)))
                    position += 3
                    continue
                match = re.match(rb'([a-zA-Z]+)(-?[0-9]+)?', data[position:])
                if match:
                    word = match[1].decode('ascii')
                    argument = int(match[2]) if match[2] else None
                    position += match.end()
                    if position < len(data) and data[position] in b' \t\r\n':
                        position += 1
                    tokens.append(('control', word, argument))
                    if word == 'bin':
                        if argument is None or argument < 0 or position + argument > len(data):
                            raise ValueError('Invalid RTF binary extent')
                        tokens.append(('binary', data[position:position + argument]))
                        position += argument
                else:
                    tokens.append(('symbol', chr(data[position])))
                    position += 1
            else:
                end = position
                while end < len(data) and data[end] not in b'{}\\':
                    end += 1
                text = data[position:end].replace(b'\r', b'').replace(b'\n', b'')
                if text:
                    tokens.append(('text', text))
                position = end
        raise ValueError('Unclosed RTF group')

    result = group()
    if data[position:].strip():
        raise ValueError('Trailing RTF data')
    return result


def model_state(data, form):
    """Validate bounded structural profiles; inspection-only byte identity is mandatory."""
    if len(data) > 32 * 1024 * 1024:
        raise ValueError('Model oracle profile exceeds 32 MiB')
    if form == 'safetensors':
        if len(data) < 10:
            raise ValueError('Truncated Safetensors file')
        size = struct.unpack_from('<Q', data)[0]
        if size < 2 or size > len(data) - 8:
            raise ValueError('Invalid Safetensors header extent')
        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError('Duplicate Safetensors header key')
                result[key] = value
            return result
        header = json.loads(data[8:8 + size], object_pairs_hook=unique)
        widths = {'F32': 4, 'F64': 8, 'F16': 2, 'I32': 4, 'I64': 8, 'U8': 1, 'BOOL': 1}
        intervals = []
        for key, entry in header.items():
            if key == '__metadata__':
                if not isinstance(entry, dict) or any(not isinstance(v, str) for v in entry.values()):
                    raise ValueError('Invalid Safetensors metadata')
                continue
            width = widths.get(entry.get('dtype'))
            if width is None:
                raise ValueError('Unqualified Safetensors dtype')
            count = 1
            for dim in entry['shape']:
                if type(dim) is not int or dim < 0:
                    raise ValueError('Invalid Safetensors shape')
                count *= dim
            start, end = entry['data_offsets']
            if type(start) is not int or type(end) is not int or start < 0 or end - start != count * width:
                raise ValueError('Invalid Safetensors range')
            intervals.append((start, end))
        cursor = 0
        for start, end in sorted(intervals):
            if start != cursor:
                raise ValueError('Safetensors ranges overlap or leave gaps')
            cursor = end
        if cursor != len(data) - 8 - size:
            raise ValueError('Safetensors payload extent mismatch')
    elif form == 'gguf':
        if len(data) < 24 or data[:4] != b'GGUF':
            raise ValueError('Invalid GGUF header')
        version, tensors, metadata_count = struct.unpack_from('<IQQ', data, 4)
        if version not in (2, 3) or tensors > 10000 or metadata_count > 10000:
            raise ValueError('Unqualified GGUF profile')
        position = 24
        def take(fmt):
            nonlocal position
            size = struct.calcsize(fmt)
            if position + size > len(data):
                raise ValueError('Truncated GGUF descriptor')
            result = struct.unpack_from(fmt, data, position)[0]
            position += size
            return result
        def string():
            nonlocal position
            size = take('<Q')
            if size > 1024 * 1024 or position + size > len(data):
                raise ValueError('Invalid GGUF string extent')
            text = data[position:position + size].decode('utf-8')
            position += size
            return text
        alignment, seen = 32, set()
        for _ in range(metadata_count):
            key, kind = string(), take('<I')
            if key in seen:
                raise ValueError('Duplicate GGUF metadata')
            seen.add(key)
            if kind == 4:
                value = take('<I')
            elif kind == 8:
                value = string()
            else:
                raise ValueError('Unqualified GGUF metadata type')
            if key == 'general.alignment':
                alignment = value
        if type(alignment) is not int or not 8 <= alignment <= 1048576 or alignment % 8:
            raise ValueError('Invalid GGUF alignment')
        intervals, names = [], set()
        for _ in range(tensors):
            name, ndim = string(), take('<I')
            if name in names or not 1 <= ndim <= 8:
                raise ValueError('Invalid GGUF tensor name/dimensions')
            names.add(name)
            count = 1
            for _ in range(ndim):
                count *= take('<Q')
            kind, offset = take('<I'), take('<Q')
            width = {0: 4, 1: 2, 26: 4, 27: 8}.get(kind)
            if width is None or offset % alignment:
                raise ValueError('Unqualified GGUF tensor type/alignment')
            intervals.append((offset, offset + count * width))
        data_start = (position + alignment - 1) // alignment * alignment
        if any(data[position:data_start]) or data_start > len(data):
            raise ValueError('Invalid GGUF header padding')
        cursor = 0
        for start, end in sorted(intervals):
            if start < cursor or data_start + end > len(data):
                raise ValueError('GGUF tensor extent mismatch')
            cursor = end
    elif form == 'onnx':
        import onnx
        model = onnx.load_model_from_string(data)
        if any(tensor.external_data for tensor in model.graph.initializer):
            raise ValueError('External ONNX data is not qualified by this single-file profile')
        onnx.checker.check_model(model)
    else:
        raise ValueError('Unknown model oracle profile')
    return form, hashlib.sha256(data).hexdigest()
