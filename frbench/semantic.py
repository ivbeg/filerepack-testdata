"""Semantic metadata and graph contracts, independent of implementation validators."""
import hashlib
import json
import stat
import struct
from fractions import Fraction


def freeze(value):
    if isinstance(value, dict):
        return tuple(sorted((str(k), freeze(v)) for k, v in value.items()))
    if isinstance(value, (tuple, list)):
        return tuple(freeze(v) for v in value)
    if isinstance(value, bytearray):
        return bytes(value)
    if not isinstance(value, (int, bool)) and hasattr(value, 'numerator') and hasattr(value, 'denominator'):
        return (int(value.numerator), int(value.denominator))
    return value


def image_metadata(image, background_color=None):
    keys = {'icc_profile', 'comment', 'Comment', 'description', 'Description', 'xmp',
            'XML:com.adobe.xmp', 'dpi', 'gamma', 'srgb', 'chromaticity', 'background'}
    info = {k: freeze(v) for k, v in image.info.items() if k in keys}
    if background_color is not None:
        info['background'] = background_color
    info.update({k: freeze(v) for k, v in getattr(image, 'text', {}).items()})
    exif = image.getexif()
    if exif:
        values = {}
        for key, value in exif.items():
            if key in (0x8769, 0x8825, 0xA005):
                values[key] = freeze(exif.get_ifd(key))
            else:
                values[key] = freeze(value)
        info['exif_tags'] = freeze(values)
    return freeze(info)


def zip_metadata(info, config):
    mode = info.external_attr >> 16 if info.create_system == 3 else 0
    file_type = stat.S_IFMT(mode) or (stat.S_IFDIR if info.is_dir() else stat.S_IFREG)
    permissions = stat.S_IMODE(mode) if mode else (0o755 if info.is_dir() else 0o644)
    result = (info.date_time, file_type, permissions, info.external_attr & 0x07, info.comment)
    if config.get('compare_extra_fields'):
        result += (info.extra,)
    return result


def check_usdz(path, entries):
    with path.open('rb') as stream:
        for info in entries:
            if info.compress_type != 0 or info.flag_bits & 1:
                raise ValueError('USDZ members must be unencrypted and STORED')
            stream.seek(info.header_offset)
            header = stream.read(30)
            if len(header) != 30 or header[:4] != b'PK\x03\x04':
                raise ValueError('Invalid USDZ local header')
            name_length, extra_length = struct.unpack_from('<HH', header, 26)
            if (info.header_offset + 30 + name_length + extra_length) % 64:
                raise ValueError('USDZ member payload is not 64-byte aligned')
    if not entries or not entries[0].filename.lower().endswith(('.usd', '.usda', '.usdc')):
        raise ValueError('USDZ first member must be a USD scene')


def dtype_identity(dtype):
    return (str(dtype), freeze(dtype.metadata or {}), repr(dtype.descr) if dtype.fields else None)


def hdf5_state(path, array_bits):
    import h5py
    import numpy as np
    with h5py.File(path, 'r') as file:
        objects, links, identities = [], [], {}

        def address(obj):
            return h5py.h5o.get_info(obj.id).addr

        def visit(name, obj):
            identity = address(obj)
            if identity in identities:
                return identities[identity]
            identities[identity] = name
            objects.append((name, obj))
            if isinstance(obj, h5py.Group):
                for key in sorted(obj):
                    child_name = name.rstrip('/') + '/' + key
                    link = obj.get(key, getlink=True)
                    if isinstance(link, h5py.SoftLink):
                        links.append((child_name, 'soft', link.path))
                    elif isinstance(link, h5py.ExternalLink):
                        links.append((child_name, 'external', link.filename, link.path))
                    else:
                        target = visit(child_name, obj[key])
                        links.append((child_name, 'hard', target))
            return name

        visit('/', file)

        def value(raw):
            if isinstance(raw, h5py.Empty):
                return ('empty', dtype_identity(raw.dtype))
            if isinstance(raw, h5py.Reference):
                data = np.asarray(raw, dtype=h5py.regionref_dtype
                                  if isinstance(raw, h5py.RegionReference) else h5py.ref_dtype)
            else:
                data = np.asarray(raw)
            reference_type = h5py.check_dtype(ref=data.dtype)
            if reference_type:
                references = []
                for reference in data.flat:
                    if not reference:
                        references.append(None)
                        continue
                    target = identities.get(address(file[reference]))
                    if target is None:
                        raise ValueError('HDF5 reference points to an unqualified anonymous object')
                    region = None
                    if isinstance(reference, h5py.RegionReference):
                        selection = h5py.h5r.get_region(reference, file.id)
                        kind = selection.get_select_type()
                        if kind == h5py.h5s.SEL_HYPERSLABS:
                            region = selection.get_select_hyper_blocklist().tolist()
                        elif kind == h5py.h5s.SEL_POINTS:
                            region = selection.get_select_elem_pointlist().tolist()
                        else:
                            region = (kind, selection.get_select_npoints())
                    references.append((target, region))
                return ('references', data.shape, references)
            if data.dtype.kind == 'O' and h5py.check_dtype(vlen=data.dtype) not in (str, bytes):
                if data.shape == () and not isinstance(raw, (np.ndarray, list, tuple)):
                    raise ValueError('Unsupported HDF5 object value')
                return ('vlen', data.shape, [value(item) for item in data.flat])
            return dtype_identity(data.dtype), array_bits(data)

        states = []
        for name, obj in objects:
            attrs = [(key, value(obj.attrs[key])) for key in sorted(obj.attrs)]
            if isinstance(obj, h5py.Dataset):
                content = value(obj[()])
                descriptor = dtype_identity(obj.dtype)
            elif isinstance(obj, h5py.Datatype):
                content, descriptor = None, dtype_identity(obj.dtype)
            else:
                content = descriptor = None
            states.append((name, type(obj).__name__, descriptor, attrs, content))
        return states, sorted(links)


def netcdf_state(path, array_bits):
    import netCDF4
    import numpy as np
    with netCDF4.Dataset(path) as file:
        file.set_auto_maskandscale(False)

        def attrs(obj):
            return [(key, array_bits(np.asarray(obj.getncattr(key))))
                    for key in sorted(obj.ncattrs())]

        def datatype(value):
            dtype = getattr(value, 'dtype', value)
            return (type(value).__name__, getattr(value, 'name', None),
                    str(dtype), freeze(getattr(value, 'enum_dict', {})))

        def visit(group):
            dimensions = [(key, len(dim), dim.isunlimited())
                          for key, dim in sorted(group.dimensions.items())]
            variables = []
            for key, variable in sorted(group.variables.items()):
                ownership = [(d.group().path, d.name) for d in variable.get_dims()]
                variables.append((key, ownership, datatype(variable.datatype),
                                  attrs(variable), array_bits(variable[:])))
            types = [(kind, key, datatype(value))
                     for kind in ('enumtypes', 'vltypes', 'cmptypes')
                     for key, value in sorted(getattr(group, kind).items())]
            return (group.path, attrs(group), dimensions, types, variables,
                    [visit(child) for _, child in sorted(group.groups.items())])
        return visit(file)


def pdf_semantics(pdf):
    """Passive document/interactive graph projection; never execute actions."""
    import pikepdf
    page_ids = {page.obj.objgen: i for i, page in enumerate(pdf.pages)}
    active = set()
    budget = [100000]

    def value(obj):
        budget[0] -= 1
        if budget[0] < 0:
            raise ValueError('PDF semantic graph exceeds oracle node budget')
        if isinstance(obj, pikepdf.Object) and obj.is_indirect:
            identity = obj.objgen
            if identity in page_ids:
                return ('page', page_ids[identity])
            if identity in active:
                return ('cycle',)
            active.add(identity)
        else:
            identity = None
        try:
            if isinstance(obj, (pikepdf.Dictionary, pikepdf.Stream)):
                result = [(str(k), value(v)) for k, v in sorted(obj.items())
                          if str(k) not in ('/Parent', '/Length', '/Filter', '/DecodeParms')]
                if isinstance(obj, pikepdf.Stream):
                    result.append(('decoded-stream', hashlib.sha256(obj.read_bytes()).hexdigest()))
                return result
            if isinstance(obj, pikepdf.Array):
                return [value(v) for v in obj]
            if isinstance(obj, pikepdf.String):
                return ('string', str(obj))
            return str(obj) if isinstance(obj, pikepdf.Object) else obj
        finally:
            if identity is not None:
                active.remove(identity)

    root_keys = ('/AcroForm', '/Outlines', '/OpenAction', '/AA', '/PageLabels',
                 '/StructTreeRoot', '/Lang', '/ViewerPreferences', '/Metadata')
    roots = [(key, value(pdf.Root.get(key))) for key in root_keys]
    annotations = [value(page.obj.get('/Annots')) for page in pdf.pages]
    return roots, annotations


def media_metadata(info, command, path):
    """Semantic tags, dispositions, colors and decoded presentation timelines."""
    incidental = {'encoder', 'vendor_id', 'DURATION', 'NUMBER_OF_BYTES', 'NUMBER_OF_FRAMES',
                  'BPS', '_STATISTICS_WRITING_APP', '_STATISTICS_WRITING_DATE_UTC',
                  '_STATISTICS_TAGS'}

    def tags(obj):
        return sorted((key, val) for key, val in obj.get('tags', {}).items()
                      if key not in incidental)

    def ratio(value):
        if value in (None, 'N/A', '0/0'):
            return None
        number = Fraction(str(value))
        return number.numerator, number.denominator

    states = []
    for stream in info['streams']:
        timing = None
        if stream['codec_type'] == 'video' and not stream.get('disposition', {}).get('attached_pic'):
            decoded = json.loads(command(['ffprobe', '-v', 'error', '-select_streams',
                                          str(stream['index']), '-show_frames',
                                          '-show_entries', 'frame=best_effort_timestamp,duration,pkt_duration',
                                          '-of', 'json', str(path)]))
            base = Fraction(stream['time_base'])
            timing = [(ratio(int(frame['best_effort_timestamp']) * base)
                       if 'best_effort_timestamp' in frame else None,
                       ratio(int(frame.get('duration', frame.get('pkt_duration'))) * base)
                       if frame.get('duration', frame.get('pkt_duration')) is not None else None)
                      for frame in decoded.get('frames', [])]
        colors = tuple(stream.get(key) for key in
                       ('color_range', 'color_space', 'color_transfer', 'color_primaries'))
        states.append((stream['codec_type'], tags(stream), freeze(stream.get('disposition', {})),
                       ratio(int(stream['start_pts']) * Fraction(stream['time_base']))
                       if 'start_pts' in stream else ratio(stream.get('start_time')),
                       stream.get('channel_layout'), colors, timing))
    return tags(info.get('format', {})), states
