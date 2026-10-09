"""Small synthetic container builders that have no Python runtime dependency."""

import bz2
import hashlib
import struct
import tempfile
import zlib
from pathlib import Path

from .oracles import command


def _align4(buffer):
    buffer.extend(b'\0' * (-len(buffer) % 4))


def cpio_newc(entries):
    """Build a deterministic `newc` CPIO stream from (name, mode, inode, nlink, data)."""
    output = bytearray()
    for name, mode, inode, nlink, data in entries:
        name_bytes = name.encode('utf-8') + b'\0'
        fields = (inode, mode, 1000, 1000, nlink, 1577934246, len(data), 0, 0, 0, 0,
                  len(name_bytes), 0)
        output.extend(b'070701')
        output.extend(b''.join(f'{value:08x}'.encode('ascii') for value in fields))
        output.extend(name_bytes)
        _align4(output)
        output.extend(data)
        _align4(output)

    name_bytes = b'TRAILER!!!\0'
    fields = (0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, len(name_bytes), 0)
    output.extend(b'070701')
    output.extend(b''.join(f'{value:08x}'.encode('ascii') for value in fields))
    output.extend(name_bytes)
    _align4(output)
    output.extend(b'\0' * (-len(output) % 512))
    return bytes(output)


def cpio_profile(payload, json_payload, xml_payload):
    """Create a newc tree with regular files, a directory, symlink and hard-link pair."""
    return cpio_newc([
        ('docs/', 0o040755, 1, 2, b''),
        ('docs/guide.txt', 0o100644, 2, 1, payload),
        ('docs/guide-hardlink.txt', 0o100644, 3, 2, b''),
        ('docs/guide-copy.txt', 0o100644, 3, 2, payload),
        ('docs/current', 0o120777, 4, 1, b'guide.txt'),
        ('docs/notes.txt', 0o100600, 5, 1,
         b'Unicode text: synthetic; repeated records preserve the compressed-stream path.\n' * 2048),
        ('docs/metadata.json', 0o100644, 6, 1, json_payload),
        ('docs/structure.xml', 0o100644, 7, 1, xml_payload),
    ])


def cpio_bz2(payload, json_payload, xml_payload, level=1):
    return bz2.compress(cpio_profile(payload, json_payload, xml_payload), compresslevel=level)


def car_profile(payload):
    """Build a small BOMStore CAR with one zlib-compressed MLEC rendition."""
    raw = payload * 8
    stream = zlib.compress(raw, level=1)
    body = b'MLEC' + struct.pack('<III', 0, 2, len(stream)) + stream
    rendition = bytearray(184)
    rendition[:4] = b'ISTC'
    struct.pack_into('<I', rendition, 4, 1)
    struct.pack_into('>4I', rendition, 168, 0, 0, 0, len(body))
    rendition.extend(body)

    catalog_header = bytearray(436)
    catalog_header[:4] = b'RATC'
    struct.pack_into('<I', catalog_header, 8, 8)
    struct.pack_into('<I', catalog_header, 16, 1)
    tree_page = bytearray(512)
    struct.pack_into('>HHII', tree_page, 0, 1, 1, 0, 0)
    struct.pack_into('>2I', tree_page, 12, 4, 5)
    rendition_tree = b'tree' + struct.pack('>4I', 1, 6, 512, 1) + b'\0'
    key_format = b'tmfk\0\0\0\0' + struct.pack('<I', 1) + b'\0' * 4
    blocks = {1: bytes(catalog_header), 2: rendition_tree, 3: key_format,
              4: bytes(rendition), 5: b'\0\0', 6: bytes(tree_page)}
    names = [(1, b'CARHEADER'), (2, b'RENDITIONS'), (3, b'KEYFORMAT')]
    variables = bytearray(struct.pack('>I', len(names)))
    for block_id, name in names:
        variables.extend(struct.pack('>IB', block_id, len(name)))
        variables.extend(name)

    output = bytearray(512)
    output[:8] = b'BOMStore'
    pointers = [(0, 0)] * 256
    # A large zero allocation gap and unused pointer slots give the compactor
    # real work while retaining the complete live block-ID set.
    output.extend(b'\0' * 4096)
    for block_id, block in blocks.items():
        output.extend(b'\0' * (-len(output) % 16))
        pointers[block_id] = (len(output), len(block))
        output.extend(block)
    output.extend(b'\0' * (-len(output) % 16))
    variables_offset = len(output)
    output.extend(variables)
    output.extend(b'\0' * (-len(output) % 16))
    index_offset = len(output)
    index = bytearray(struct.pack('>I', len(pointers)))
    for pointer in pointers:
        index.extend(struct.pack('>2I', *pointer))
    index.extend(struct.pack('>I', 0))
    output.extend(index)
    struct.pack_into('>6I', output, 8, 1, len(blocks), index_offset, len(index),
                     variables_offset, len(variables))
    return bytes(output)


def _varint(value):
    output = bytearray()
    while value > 0x7f:
        output.append((value & 0x7f) | 0x80)
        value >>= 7
    output.append(value)
    return bytes(output)


def _bytes_field(number, data):
    return _varint((number << 3) | 2) + _varint(len(data)) + data


def crx3(zip_payload):
    """Wrap ZIP bytes in a correctly signed CRX3 RSA proof using a throwaway test key."""
    with tempfile.TemporaryDirectory(prefix='frbench-crx-') as temp:
        temp = Path(temp)
        private_key = temp / 'test-private.pem'
        public_key = temp / 'test-public.der'
        signed_file = temp / 'signed.bin'
        signature_file = temp / 'signature.bin'
        command(['openssl', 'genpkey', '-algorithm', 'RSA', '-pkeyopt', 'rsa_keygen_bits:2048',
                 '-out', str(private_key)])
        command(['openssl', 'pkey', '-in', str(private_key), '-pubout', '-outform', 'DER',
                 '-out', str(public_key)])
        public_der = public_key.read_bytes()
        signed_header_data = _bytes_field(1, hashlib.sha256(public_der).digest()[:16])
        signing_input = (b'CRX3 SignedData\0' + struct.pack('<I', len(signed_header_data))
                         + signed_header_data + zip_payload)
        signed_file.write_bytes(signing_input)
        command(['openssl', 'dgst', '-sha256', '-sign', str(private_key),
                 '-sigopt', 'rsa_padding_mode:pkcs1', '-out', str(signature_file),
                 str(signed_file)])
        proof = _bytes_field(1, public_der) + _bytes_field(2, signature_file.read_bytes())
        header = _bytes_field(2, proof) + _bytes_field(10000, signed_header_data)
    return b'Cr24' + struct.pack('<II', 3, len(header)) + header + zip_payload
