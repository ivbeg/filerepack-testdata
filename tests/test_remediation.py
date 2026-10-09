import argparse
import json
import shutil
import zipfile

import pytest

from frbench.catalog import discover_catalog
from frbench.common import check_manifest, file_inventory, write_json
from frbench.generate import Builder, extend, zip_bytes
from frbench.oracles import fingerprint
from frbench import runner
from frbench.worker import outcome_issues


def case_manifest(root, *, oracle=None, tier='extended'):
    path = root / 'corpus/generated/reference.bin'
    path.parent.mkdir(parents=True)
    path.write_bytes(b'pinned reference')
    case = {'id': 'reference', 'path': str(path.relative_to(root)), 'extension': 'bin',
            'family': 'native', 'scope': 'native', 'tier': tier, 'expectation': 'observe',
            'oracle': oracle or {'kind': 'bytes'}, 'license': 'BSD-3-Clause',
            'provenance': {'type': 'generated'}, 'inventory': file_inventory(path)}
    manifest = {'schema_version': 1, 'supported_extensions': ['bin'], 'cases': [case],
                'generation_gaps': []}
    catalog = {'supported_extensions': ['bin'], 'handler_by_extension': {'bin': 'pack_bin'},
               'filename_suffixes': []}
    write_json(root / 'corpus/manifest.json', manifest)
    write_json(root / 'corpus/catalog.json', catalog)
    return case, catalog


def test_png_metadata_removal_and_high_depth_value_corruption_are_detected(tmp_path):
    Image = pytest.importorskip('PIL.Image')
    PngImagePlugin = pytest.importorskip('PIL.PngImagePlugin')
    source, stripped = tmp_path / 'source.png', tmp_path / 'stripped.png'
    info = PngImagePlugin.PngInfo()
    info.add_text('Comment', 'must survive')
    Image.new('RGB', (8, 8), 'red').save(source, pnginfo=info, compress_level=1)
    with Image.open(source) as image:
        image.save(stripped)
    assert fingerprint(source, {'kind': 'raster'}) != fingerprint(stripped, {'kind': 'raster'})
    candidate = tmp_path / 'candidate.png'
    Image.new('RGB', (8, 8), 'red').save(candidate, pnginfo=info, compress_level=9)
    assert fingerprint(source, {'kind': 'raster'}) == fingerprint(candidate, {'kind': 'raster'})
    for path, value in [(source, 1024), (candidate, 1025)]:
        image = Image.new('I;16', (8, 8), value)
        image.save(path)
    assert fingerprint(source, {'kind': 'raster'}) != fingerprint(candidate, {'kind': 'raster'})


def test_gif_palette_reordering_and_equivalent_disposal_are_accepted(tmp_path):
    Image = pytest.importorskip('PIL.Image')
    source, candidate = tmp_path / 'source.gif', tmp_path / 'candidate.gif'
    for path, colors, index, disposal in [
            (source, [255, 0, 0, 0, 255, 0], 0, 0),
            (candidate, [0, 255, 0, 255, 0, 0], 1, 1)]:
        image = Image.new('P', (8, 8), index)
        image.putpalette(colors + [0] * (768 - len(colors)))
        image.save(path, background=index, duration=100, loop=2,
                   disposal=disposal, optimize=False)
    config = {'kind': 'raster'}
    assert fingerprint(source, config) == fingerprint(candidate, config)
    strict = {'kind': 'raster', 'preserve_frame_controls': True}
    assert fingerprint(source, strict) != fingerprint(candidate, strict)
    with Image.open(candidate) as image:
        image.save(candidate, background=0, duration=100, loop=2, optimize=False)
    assert fingerprint(source, config) != fingerprint(candidate, config)


@pytest.mark.parametrize('removed_marker', [0xE1, 0xE2], ids=['exif', 'icc'])
def test_jpeg_metadata_removal_without_pixel_changes_is_detected(tmp_path, removed_marker):
    Image = pytest.importorskip('PIL.Image')
    from frbench.common import ROOT
    source = ROOT / 'corpus/generated/images/metadata.jpg'
    data = source.read_bytes()
    result = bytearray(data[:2])
    offset = 2
    removed = False
    while offset < len(data):
        assert data[offset] == 0xFF
        marker = data[offset + 1]
        if marker == 0xDA:
            result.extend(data[offset:])
            break
        length = int.from_bytes(data[offset + 2:offset + 4], 'big')
        end = offset + 2 + length
        if marker == removed_marker:
            removed = True
        else:
            result.extend(data[offset:end])
        offset = end
    assert removed
    candidate = tmp_path / 'stripped.jpg'
    candidate.write_bytes(result)
    with Image.open(source) as original, Image.open(candidate) as stripped:
        assert original.convert('RGB').tobytes() == stripped.convert('RGB').tobytes()
    assert fingerprint(source, {'kind': 'raster'}) != fingerprint(candidate, {'kind': 'raster'})


@pytest.mark.parametrize('field', ['permissions', 'timestamp', 'comment'])
def test_zip_metadata_mutations_are_detected(tmp_path, field):
    paths = [tmp_path / name for name in ('source.zip', 'changed.zip')]
    for index, path in enumerate(paths):
        with zipfile.ZipFile(path, 'w') as archive:
            info = zipfile.ZipInfo('script.sh', (2020 + (index if field == 'timestamp' else 0), 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (0o100755 if not index or field != 'permissions' else 0o100644) << 16
            info.comment = b'retain' if not index or field != 'comment' else b''
            archive.writestr(info, b'echo synthetic\n')
    assert fingerprint(paths[0], {'kind': 'zip'}) != fingerprint(paths[1], {'kind': 'zip'})


def test_usdz_rejects_compressed_and_unaligned_members(tmp_path):
    path = tmp_path / 'scene.usdz'
    path.write_bytes(zip_bytes({'scene.usda': b'#usda 1.0\n'}, level=9))
    with pytest.raises(ValueError, match='STORED'):
        fingerprint(path, {'kind': 'zip', 'package': 'usdz'})
    path.write_bytes(zip_bytes({'scene.usda': b'#usda 1.0\n'}))
    with pytest.raises(ValueError, match='aligned'):
        fingerprint(path, {'kind': 'zip', 'package': 'usdz'})


def test_hdf5_links_cycles_and_reference_targets_are_verified(tmp_path):
    h5py = pytest.importorskip('h5py')
    np = pytest.importorskip('numpy')
    source, candidate = tmp_path / 'source.h5', tmp_path / 'candidate.h5'
    with h5py.File(source, 'w') as file:
        data = file.create_dataset('data', data=[0.0, -0.0])
        group = file.create_group('group')
        group['cycle'] = file
        file['alias'] = data
        file['soft'] = h5py.SoftLink('/data')
        file['external'] = h5py.ExternalLink('absent.h5', '/untouched')
        file.attrs['target'] = data.ref
        file.attrs['nan'] = np.array([np.nan])
    shutil.copyfile(source, candidate)
    config = {'kind': 'hdf5'}
    expected = fingerprint(source, config)
    assert expected == fingerprint(candidate, config)
    with h5py.File(candidate, 'r+') as file:
        del file['soft']
    assert expected != fingerprint(candidate, config)
    shutil.copyfile(source, candidate)
    with h5py.File(candidate, 'r+') as file:
        file.attrs['target'] = file['group'].ref
    assert expected != fingerprint(candidate, config)


def test_netcdf_nested_data_dimension_ownership_and_metadata_are_verified(tmp_path):
    netCDF4 = pytest.importorskip('netCDF4')
    source, candidate = tmp_path / 'source.nc', tmp_path / 'candidate.nc'
    with netCDF4.Dataset(source, 'w') as file:
        file.createDimension('x', 1)
        group = file.createGroup('measurements')
        variable = group.createVariable('value', 'i4', ('x',))
        variable[:] = [123]
        variable.units = 'synthetic'
    shutil.copyfile(source, candidate)
    expected = fingerprint(source, {'kind': 'netcdf'})
    assert expected == fingerprint(candidate, {'kind': 'netcdf'})
    with netCDF4.Dataset(candidate, 'r+') as file:
        file.groups['measurements'].variables['value'][:] = [999]
    assert expected != fingerprint(candidate, {'kind': 'netcdf'})


@pytest.mark.parametrize('modern', [False, True])
def test_catalog_accepts_literal_and_derived_registry_views(tmp_path, modern):
    package = tmp_path / 'filerepack'
    package.mkdir()
    (package / '__init__.py').write_text('')
    tables = "ARCHIVE_EXTS=['zip']; STANDALONE_EXTS=['gz','gzip']; STANDALONE_ALIASES={'gzip':'gz'}; SPECIAL_FAMILY={}; COMPOUND_FAMILY={'tar.gzip':'tar.gz'}\n"
    if modern:
        (package / 'format_registry.py').write_text(tables)
        (package / 'consts.py').write_text('from .format_registry import *\n')
        (package / 'formats.py').write_text('from .format_registry import *\n')
    else:
        (package / 'consts.py').write_text(tables)
        (package / 'formats.py').write_text(tables)
    (package / 'dispatch.py').write_text("_PACKERS = {'gz': PackerSpec(pack_gzip, 'data')}\n")
    catalog = discover_catalog(tmp_path)
    assert catalog['handler_by_extension']['gzip'] == 'pack_gzip'
    assert 'tar.gzip' in catalog['filename_suffixes']
    assert catalog['implementation']['registry_sha256']


def test_live_handler_coverage_does_not_reuse_cached_mapping(tmp_path, monkeypatch):
    case_manifest(tmp_path)
    live = {'supported_extensions': ['bin', 'new'],
            'handler_by_extension': {'bin': 'pack_bin', 'new': 'pack_new'},
            'filename_suffixes': []}
    monkeypatch.setattr('frbench.catalog.discover_catalog', lambda source: live)
    result = runner.coverage(tmp_path, 'trusted-checkout')
    assert result['handler_count'] == 2
    assert result['missing_handlers'] == ['pack_new']
    assert result['missing'] == ['new']


def test_extension_retains_existing_bytes_and_is_idempotent(tmp_path, monkeypatch):
    case, catalog = case_manifest(tmp_path)
    def additions(builder):
        builder.add('reference.bin', b'volatile replacement', 'bin', 'native', {'kind': 'bytes'})
        builder.cases[-1]['id'] = 'reference'
        builder.add('new.bin', b'new pinned specimen', 'bin', 'native', {'kind': 'bytes'})
    monkeypatch.setattr(Builder, 'additional_formats', additions)
    args = argparse.Namespace(scale=1, strict=True)
    assert extend(tmp_path, catalog, args) == 0
    assert file_inventory(tmp_path / case['path']) == case['inventory']
    first = (tmp_path / 'corpus/manifest.json').read_bytes()
    assert extend(tmp_path, catalog, args) == 0
    assert (tmp_path / 'corpus/manifest.json').read_bytes() == first
    assert not check_manifest(tmp_path)


def test_failed_extension_does_not_publish_partial_cases(tmp_path, monkeypatch):
    _, catalog = case_manifest(tmp_path)
    before = (tmp_path / 'corpus/manifest.json').read_bytes()
    def additions(builder):
        builder.add('new.bin', b'new', 'bin', 'native', {'kind': 'bytes'})
        builder.gaps.append({'generator': 'required', 'reason': 'simulated failure'})
    monkeypatch.setattr(Builder, 'additional_formats', additions)
    assert extend(tmp_path, catalog, argparse.Namespace(scale=1, strict=True)) == 1
    assert (tmp_path / 'corpus/manifest.json').read_bytes() == before
    assert not (tmp_path / 'corpus/generated/new.bin').exists()


def test_extension_rejects_existing_path_with_a_new_id(tmp_path, monkeypatch):
    case, catalog = case_manifest(tmp_path)
    original = (tmp_path / case['path']).read_bytes()
    def additions(builder):
        builder.add('reference.bin', b'collision', 'bin', 'native', {'kind': 'bytes'})
        builder.cases[-1]['id'] = 'new-identity'
    monkeypatch.setattr(Builder, 'additional_formats', additions)
    with pytest.raises(ValueError, match='collides'):
        extend(tmp_path, catalog, argparse.Namespace(scale=1, strict=True))
    assert (tmp_path / case['path']).read_bytes() == original
    assert not check_manifest(tmp_path)


def test_extension_publication_failure_rolls_back_moved_files_and_inventory(tmp_path, monkeypatch):
    import frbench.generate as generation
    _, catalog = case_manifest(tmp_path)
    originals = {name: (tmp_path / 'corpus' / name).read_bytes()
                 for name in ('manifest.json', 'catalog.json')}
    def additions(builder):
        builder.add('new.bin', b'new specimen', 'bin', 'native', {'kind': 'bytes'})
    original_writer = generation.write_json
    def fail_publication(path, value):
        if path == tmp_path / 'corpus/manifest.json':
            raise OSError('Simulated publication failure')
        return original_writer(path, value)
    monkeypatch.setattr(Builder, 'additional_formats', additions)
    monkeypatch.setattr(generation, 'write_json', fail_publication)
    with pytest.raises(OSError, match='publication failure'):
        extend(tmp_path, catalog, argparse.Namespace(scale=1, strict=True))
    assert not (tmp_path / 'corpus/generated/new.bin').exists()
    assert all((tmp_path / 'corpus' / name).read_bytes() == data for name, data in originals.items())
    assert not check_manifest(tmp_path)


def test_zero_verification_and_strict_missing_reader_runs_fail(tmp_path, monkeypatch):
    case_manifest(tmp_path)
    monkeypatch.setattr(runner, 'environment', lambda: {})
    monkeypatch.setattr(runner, 'measure', lambda *a, **k: {
        'status': 'skipped-verifier', 'reason': 'Missing test reader',
        'seconds': None, 'input_bytes': 16, 'output_bytes': 16})
    args = argparse.Namespace(root=str(tmp_path), filerepack=None, family=None, ext=None,
                              case=None, tier='all', native_only=False, output=str(tmp_path / 'out'),
                              profile='lossless', options='{}', repeat=1, warmup=0,
                              timeout=10, keep_work=False, strict_verifiers=True, min_verified=1)
    assert runner.run(args) == 1
    report = json.loads((tmp_path / 'out/report.json').read_text())
    assert report['qualification']['verified_cases'] == 0
    assert len(report['qualification']['issues']) == 2


def test_outcome_contract_checks_routing_refusal_and_attempts():
    case = {'qualification': {'statuses': ['unchanged'], 'routing': {'packer': 'model'},
                              'reason_pattern': 'inspection only', 'require_attempt': True}}
    result = {'status': 'unchanged', 'reason': 'inspection only',
              'detected': {'packer': 'model'}, 'packer_results': [{'replaced': False}]}
    assert not outcome_issues(case, result)
    result['detected'] = {'packer': 'wrong'}
    assert outcome_issues(case, result)


def test_corpus_root_configuration_and_missing_diagnostic(tmp_path, monkeypatch):
    from frbench import common
    case_manifest(tmp_path)
    monkeypatch.setenv('FILEREPACK_TESTDATA_ROOT', str(tmp_path))
    assert common.corpus_root() == tmp_path
    monkeypatch.delenv('FILEREPACK_TESTDATA_ROOT')
    empty = tmp_path / 'empty'
    empty.mkdir()
    monkeypatch.chdir(empty)
    monkeypatch.setattr(common, 'ROOT', empty)
    with pytest.raises(ValueError, match='--root'):
        common.corpus_root()


def test_original_index_and_legal_notices_are_checked(tmp_path):
    case, _ = case_manifest(tmp_path)
    case['scope'] = 'original'
    case['provenance']['license_files'] = ['licenses/original-LICENSE']
    manifest = json.loads((tmp_path / 'corpus/manifest.json').read_text())
    manifest['cases'] = [case]
    write_json(tmp_path / 'corpus/manifest.json', manifest)
    write_json(tmp_path / 'corpus/originals/index.json', {'cases': [case]})
    assert any('legal notice' in failure for failure in check_manifest(tmp_path))
    (tmp_path / 'licenses').mkdir()
    (tmp_path / 'licenses/original-LICENSE').write_text('synthetic legal notice')
    assert not check_manifest(tmp_path)
    write_json(tmp_path / 'corpus/originals/index.json', {'cases': []})
    assert any('index IDs' in failure for failure in check_manifest(tmp_path))


def test_arrow_signed_zero_nan_payload_and_metadata_are_preserved(tmp_path):
    np = pytest.importorskip('numpy')
    pa = pytest.importorskip('pyarrow')
    pq = pytest.importorskip('pyarrow.parquet')
    source, candidate = tmp_path / 'source.parquet', tmp_path / 'candidate.parquet'
    values = np.array([0, 0x80000000, 0x7FC01234], dtype='<u4').view('<f4')
    table = pa.table({'values': pa.array(values)})
    pq.write_table(table, source, compression='NONE')
    pq.write_table(table, candidate, compression='zstd')
    config = {'kind': 'arrow', 'format': 'parquet'}
    expected = fingerprint(source, config)
    assert expected == fingerprint(candidate, config)
    for index, bits in [(1, 0), (2, 0x7FC01235)]:
        changed = values.view('<u4').copy()
        changed[index] = bits
        pq.write_table(pa.table({'values': pa.array(changed.view('<f4'))}), candidate)
        assert expected != fingerprint(candidate, config)


def test_pdf_form_value_link_and_text_mutations_are_detected(tmp_path):
    pikepdf = pytest.importorskip('pikepdf')
    from frbench.common import ROOT
    from frbench.oracles import require
    config = {'kind': 'pdf'}
    if require(config):
        pytest.skip('PDF readers/rendering unavailable')
    source = ROOT / 'corpus/generated/documents/text-form-link.pdf'
    expected = fingerprint(source, config)
    candidate = tmp_path / 'candidate.pdf'
    with pikepdf.open(source) as pdf:
        pdf.save(candidate, compress_streams=True)
    assert expected == fingerprint(candidate, config)
    for mutation in ('link', 'form', 'text'):
        with pikepdf.open(source) as pdf:
            if mutation == 'link':
                pdf.pages[0].obj['/Annots'][0]['/A']['/URI'] = 'https://example.org/changed'
            elif mutation == 'form':
                pdf.Root['/AcroForm']['/Fields'][0]['/V'] = 'Changed form value'
            else:
                contents = pdf.pages[0].obj['/Contents']
                contents.write(contents.read_bytes().replace(b'Synthetic', b'Corrupted'))
            pdf.save(candidate)
        assert expected != fingerprint(candidate, config)


def test_media_tracks_tags_and_presentation_times_are_verified(tmp_path):
    from frbench.common import ROOT
    from frbench.oracles import command, require
    config = {'kind': 'video'}
    if require(config):
        pytest.skip('FFmpeg unavailable')
    source = ROOT / 'corpus/generated/video/multiple-streams.mkv'
    expected = fingerprint(source, config)
    candidate = tmp_path / 'candidate.mkv'
    command(['ffmpeg', '-v', 'error', '-y', '-i', str(source), '-map', '0', '-c', 'copy', str(candidate)])
    assert expected == fingerprint(candidate, config)
    for options in (['-map', '0:0', '-map', '0:1'],
                    ['-map', '0', '-metadata:s:a:1', 'language=deu']):
        command(['ffmpeg', '-v', 'error', '-y', '-i', str(source), *options, '-c', 'copy', str(candidate)])
        assert expected != fingerprint(candidate, config)
    command(['ffmpeg', '-v', 'error', '-y', '-itsoffset', '0.2', '-i', str(source),
             '-map', '0', '-c', 'copy', str(candidate)])
    assert expected != fingerprint(candidate, config)


def test_comparison_flags_harness_environment_and_selection_differences(tmp_path):
    report = {'corpus_manifest_sha256': 'a', 'options': {}, 'environment': {'python': '3.13'},
              'harness': {'python_source_sha256': 'first'}, 'profile': 'lossless',
              'repeat': 3, 'warmup': 1, 'timeout': 90, 'summary': {'cases': []}}
    write_json(tmp_path / 'before.json', report)
    report['harness']['python_source_sha256'] = 'second'
    report['environment']['python'] = '3.10'
    write_json(tmp_path / 'after.json', report)
    result = runner.compare(tmp_path / 'before.json', tmp_path / 'after.json')
    assert not result['comparable']
    assert 'harness: differs' in result['incompatibilities']
    assert 'environment: differs' in result['incompatibilities']
