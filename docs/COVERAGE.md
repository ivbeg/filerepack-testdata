# Coverage snapshot

Catalog: local filerepack source; regenerate with `python scripts/update_coverage.py --filerepack ../filerepack`.

- 477 cases: 12 smoke, 440 extended, 24 rejection controls, 1 separate stress fixtures.
- 312/312 registered extension routes have non-control fixtures.
- 163 extensions have native or original fixtures.
- 102/102 handler groups have fixtures.
- 54 upstream originals; remaining fixtures are generated or routing derivatives.
- 28/28 compound/content-detected filename routes have fixtures.
- Directory Zarr v2 is an additional store fixture outside the flat extension denominator.

Handler and extension coverage means an input exists for that path. It does not guarantee that every sample is accepted for rewriting or becomes smaller.

## Fixture scopes

| Scope | Cases | Meaning |
|---|---:|---|
| alias | 28 | Existing bitstream under another supported routing suffix. |
| container-only | 130 | Generic ZIP/TAR/SQLite payload without an application-format claim. |
| native | 249 | Generated format-shaped profile checked by the listed oracle. |
| original | 54 | Unmodified, license-reviewed upstream regression sample. |
| syntax | 16 | Valid generic structure without application/render qualification. |

## Handler groups

| Handler/family | Cases | Native/original/syntax case |
|---|---:|---|
| `archive:7z` | 2 | yes |
| `archive:cab` | 1 | yes |
| `archive:cpio` | 1 | yes |
| `archive:cpio.bz2` | 1 | yes |
| `archive:rar` | 2 | yes |
| `archive:tar` | 5 | yes |
| `archive:tar.bz2` | 2 | transport/alias only |
| `archive:tar.gz` | 3 | transport/alias only |
| `archive:tar.lz` | 1 | transport/alias only |
| `archive:tar.lzo` | 1 | transport/alias only |
| `archive:tar.xz` | 1 | transport/alias only |
| `archive:tar.z` | 1 | transport/alias only |
| `archive:tar.zst` | 1 | transport/alias only |
| `archive:wim` | 1 | yes |
| `archive:zip` | 156 | yes |
| `pack_3gp` | 1 | yes |
| `pack_ai` | 1 | transport/alias only |
| `pack_ape` | 1 | yes |
| `pack_arrow` | 3 | yes |
| `pack_aseprite` | 2 | yes |
| `pack_asf` | 1 | yes |
| `pack_avi` | 1 | yes |
| `pack_avif` | 1 | yes |
| `pack_avro` | 1 | yes |
| `pack_blend` | 1 | yes |
| `pack_bmp` | 2 | yes |
| `pack_brotli` | 3 | yes |
| `pack_bz2` | 3 | yes |
| `pack_car` | 1 | yes |
| `pack_checkpoint` | 2 | yes |
| `pack_compress` | 3 | yes |
| `pack_dcm` | 3 | yes |
| `pack_dng` | 1 | yes |
| `pack_duckdb` | 1 | yes |
| `pack_exr` | 1 | yes |
| `pack_feather` | 1 | yes |
| `pack_fits` | 3 | yes |
| `pack_flac` | 2 | yes |
| `pack_gguf` | 1 | yes |
| `pack_gif` | 2 | yes |
| `pack_gzip` | 7 | yes |
| `pack_hdf5` | 4 | yes |
| `pack_heic` | 2 | yes |
| `pack_icns` | 1 | yes |
| `pack_ico` | 2 | yes |
| `pack_jp2` | 4 | yes |
| `pack_jpg` | 8 | yes |
| `pack_json` | 9 | yes |
| `pack_jsonl` | 2 | yes |
| `pack_jxl` | 1 | yes |
| `pack_lz4` | 3 | yes |
| `pack_lzip` | 3 | yes |
| `pack_lzma` | 3 | yes |
| `pack_lzo` | 3 | yes |
| `pack_m4a` | 2 | yes |
| `pack_m4v` | 1 | yes |
| `pack_mat` | 2 | yes |
| `pack_mkv` | 2 | yes |
| `pack_mov` | 1 | yes |
| `pack_mp3` | 1 | yes |
| `pack_mp4` | 1 | yes |
| `pack_netcdf` | 3 | yes |
| `pack_nib` | 1 | yes |
| `pack_nrrd` | 2 | yes |
| `pack_oga` | 1 | yes |
| `pack_ogg` | 2 | yes |
| `pack_ole` | 50 | yes |
| `pack_onnx` | 1 | yes |
| `pack_orc` | 1 | yes |
| `pack_parquet` | 3 | yes |
| `pack_pcx` | 2 | yes |
| `pack_pdf` | 3 | yes |
| `pack_png` | 7 | yes |
| `pack_pnm` | 4 | yes |
| `pack_psb` | 1 | yes |
| `pack_psd` | 1 | yes |
| `pack_qgd` | 1 | yes |
| `pack_qgs` | 1 | yes |
| `pack_r_serialization` | 18 | yes |
| `pack_rtf` | 2 | yes |
| `pack_safetensors` | 1 | yes |
| `pack_spss` | 2 | yes |
| `pack_sqlite` | 7 | yes |
| `pack_svg` | 1 | yes |
| `pack_svgz` | 1 | yes |
| `pack_swf` | 1 | yes |
| `pack_tga` | 2 | yes |
| `pack_tgs` | 1 | yes |
| `pack_tif` | 3 | yes |
| `pack_tracev3` | 1 | yes |
| `pack_ts` | 3 | yes |
| `pack_tta` | 1 | yes |
| `pack_warc` | 3 | yes |
| `pack_webm` | 1 | yes |
| `pack_webp` | 1 | yes |
| `pack_wmv` | 1 | yes |
| `pack_woff` | 1 | yes |
| `pack_woff2` | 1 | yes |
| `pack_wv` | 1 | yes |
| `pack_xml` | 13 | yes |
| `pack_xz` | 3 | yes |
| `pack_zstd` | 3 | yes |

## Extension routes

| Extension | Cases | Scopes |
|---|---:|---|
| .3gp | 1 | native |
| .3mf | 1 | container-only |
| .7z | 1 | native |
| .aab | 1 | container-only |
| .aar | 1 | container-only |
| .accdt | 1 | container-only |
| .afdesign | 1 | container-only |
| .afphoto | 1 | container-only |
| .afpub | 1 | container-only |
| .ai | 1 | alias |
| .air | 1 | container-only |
| .ape | 1 | native |
| .apk | 1 | container-only |
| .apks | 1 | container-only |
| .apng | 1 | native |
| .appx | 1 | container-only |
| .appxbundle | 1 | container-only |
| .arrow | 2 | native |
| .ase | 1 | native |
| .aseprite | 1 | native |
| .asf | 1 | native |
| .atom | 1 | syntax |
| .avi | 1 | native |
| .avif | 1 | native |
| .avro | 1 | native |
| .blend | 1 | syntax |
| .bmp | 1 | native |
| .br | 3 | native |
| .bz2 | 3 | native |
| .cab | 1 | native |
| .car | 1 | native |
| .cb7 | 1 | alias |
| .cbr | 1 | alias |
| .cbt | 1 | container-only |
| .cbz | 1 | container-only |
| .cpbz2 | 1 | native |
| .cpio | 1 | native |
| .crate | 1 | alias |
| .crtx | 1 | container-only |
| .crx | 1 | native |
| .cur | 1 | native |
| .dae | 1 | syntax |
| .db | 1 | native |
| .dcm | 1 | native |
| .dcx | 1 | native |
| .dib | 1 | native |
| .dic | 1 | native |
| .dicom | 1 | native |
| .dng | 1 | native |
| .doc | 16 | original |
| .docm | 1 | container-only |
| .docx | 3 | container-only, native, original |
| .dot | 1 | alias |
| .dotm | 1 | container-only |
| .dotx | 1 | container-only |
| .duckdb | 1 | native |
| .dwfx | 1 | container-only |
| .ear | 1 | container-only |
| .egg | 1 | container-only |
| .epub | 2 | container-only, native |
| .exr | 1 | native |
| .fb2 | 1 | syntax |
| .fcstd | 1 | container-only |
| .feather | 1 | native |
| .fit | 1 | native |
| .fits | 1 | native |
| .flac | 2 | native, original |
| .fts | 1 | native |
| .gcsx | 1 | container-only |
| .gem | 1 | container-only |
| .geojson | 1 | native |
| .gguf | 1 | native |
| .gif | 2 | native |
| .glox | 1 | container-only |
| .gltf | 1 | native |
| .gpkg | 1 | container-only |
| .gpx | 1 | syntax |
| .gqsx | 1 | container-only |
| .gz | 4 | native |
| .gzip | 3 | native |
| .h5 | 2 | native |
| .har | 1 | native |
| .hdf | 1 | native |
| .hdf5 | 1 | native |
| .heic | 1 | native |
| .heif | 1 | native |
| .hwp | 4 | original |
| .ibooks | 1 | container-only |
| .icns | 1 | native |
| .ico | 1 | native |
| .idml | 1 | container-only |
| .ifczip | 1 | container-only |
| .ipa | 1 | container-only |
| .ipc | 1 | native |
| .ipsw | 1 | container-only |
| .ipynb | 1 | native |
| .j2k | 1 | native |
| .jar | 1 | container-only |
| .jfi | 1 | alias |
| .jfif | 1 | alias |
| .jif | 1 | alias |
| .jp2 | 1 | native |
| .jpe | 1 | alias |
| .jpeg | 1 | alias |
| .jpf | 1 | alias |
| .jpg | 2 | native |
| .jpx | 1 | alias |
| .json | 3 | native |
| .jsonl | 1 | native |
| .jxl | 1 | native |
| .key | 1 | container-only |
| .kml | 1 | syntax |
| .kmz | 1 | container-only |
| .kra | 1 | container-only |
| .kth | 1 | container-only |
| .lpf | 1 | container-only |
| .lz | 3 | native |
| .lz4 | 3 | native |
| .lzma | 3 | native |
| .lzo | 3 | native |
| .m2ts | 1 | native |
| .m4a | 1 | native |
| .m4b | 1 | native |
| .m4v | 1 | native |
| .map | 1 | native |
| .mat | 2 | native, original |
| .mbtiles | 1 | container-only |
| .mcaddon | 1 | container-only |
| .mcpack | 1 | container-only |
| .mcworld | 1 | container-only |
| .mellel | 1 | syntax |
| .mkv | 2 | native |
| .mov | 1 | native |
| .mp3 | 1 | native |
| .mp4 | 1 | native |
| .mpp | 1 | original |
| .msg | 2 | original |
| .msi | 1 | original |
| .msix | 1 | container-only |
| .mts | 1 | native |
| .mxl | 1 | container-only |
| .nbk | 1 | container-only |
| .nc | 1 | native |
| .nc4 | 2 | native |
| .ndjson | 1 | native |
| .nib | 1 | syntax |
| .nmbtemplate | 1 | container-only |
| .notebook | 1 | container-only |
| .npz | 2 | container-only, native |
| .nrrd | 2 | native |
| .numbers | 1 | container-only |
| .nupkg | 1 | container-only |
| .odb | 2 | container-only, native |
| .odc | 2 | container-only, native |
| .odf | 2 | container-only, native |
| .odg | 2 | container-only, native |
| .odi | 2 | container-only, native |
| .odm | 2 | container-only, native |
| .odp | 2 | container-only, native |
| .ods | 2 | container-only, native |
| .odt | 2 | container-only, native |
| .oex | 1 | container-only |
| .oga | 1 | native |
| .ogg | 1 | native |
| .onepkg | 1 | container-only |
| .onnx | 1 | native |
| .opus | 1 | native |
| .ora | 1 | container-only |
| .orc | 1 | native |
| .osk | 1 | container-only |
| .otc | 2 | container-only, native |
| .otg | 2 | container-only, native |
| .oth | 2 | container-only, native |
| .oti | 2 | container-only, native |
| .otm | 2 | container-only, native |
| .otp | 2 | container-only, native |
| .ots | 2 | container-only, native |
| .ott | 2 | container-only, native |
| .oxps | 1 | container-only |
| .oxt | 1 | container-only |
| .pages | 1 | container-only |
| .parquet | 3 | native |
| .pbm | 1 | native |
| .pcx | 1 | native |
| .pdf | 3 | native, original |
| .pgm | 1 | native |
| .pk3 | 1 | container-only |
| .png | 6 | native, original |
| .pnm | 1 | native |
| .pot | 1 | alias |
| .potm | 1 | container-only |
| .potx | 1 | container-only |
| .ppam | 1 | container-only |
| .ppm | 1 | native |
| .pps | 1 | alias |
| .ppsm | 1 | container-only |
| .ppsx | 1 | container-only |
| .ppt | 6 | original |
| .pptm | 1 | container-only |
| .pptx | 2 | container-only, native |
| .psb | 1 | native |
| .psd | 1 | native |
| .pt | 1 | native |
| .pth | 1 | native |
| .pub | 1 | original |
| .puz | 1 | container-only |
| .qgd | 1 | native |
| .qgs | 1 | native |
| .qgz | 1 | native |
| .rar | 1 | native |
| .rda | 6 | native |
| .rdata | 6 | native |
| .rds | 6 | native |
| .rels | 1 | syntax |
| .rmskin | 1 | container-only |
| .rss | 1 | syntax |
| .rtb | 1 | container-only |
| .rtf | 2 | native |
| .safetensors | 1 | native |
| .sav | 1 | native |
| .scrivx | 1 | container-only |
| .sketch | 1 | container-only |
| .sldm | 1 | container-only |
| .sldx | 1 | container-only |
| .snupkg | 1 | container-only |
| .sqlite | 1 | native |
| .sqlite3 | 1 | native |
| .sqlitedb | 1 | native |
| .stc | 1 | container-only |
| .std | 1 | container-only |
| .sti | 1 | container-only |
| .stw | 1 | container-only |
| .svg | 1 | native |
| .svgz | 1 | native |
| .swf | 1 | native |
| .sxc | 1 | container-only |
| .sxd | 1 | container-only |
| .sxg | 1 | container-only |
| .sxi | 1 | container-only |
| .sxm | 1 | container-only |
| .sxw | 1 | container-only |
| .tar | 3 | native |
| .targa | 1 | alias |
| .taz | 1 | alias |
| .tbz | 1 | alias |
| .tbz2 | 1 | alias |
| .template | 1 | container-only |
| .tga | 1 | native |
| .tgs | 1 | native |
| .tgz | 1 | alias |
| .thm | 1 | alias |
| .thmx | 1 | container-only |
| .tif | 1 | native |
| .tiff | 2 | native |
| .tlz | 1 | alias |
| .topojson | 1 | native |
| .tracev3 | 1 | native |
| .ts | 1 | native |
| .tta | 1 | native |
| .txz | 1 | alias |
| .tzo | 1 | alias |
| .tzst | 1 | alias |
| .ui | 1 | syntax |
| .unitypackage | 1 | alias |
| .usdz | 1 | native |
| .vdw | 1 | container-only |
| .vscdb | 1 | native |
| .vsd | 1 | original |
| .vsdm | 1 | container-only |
| .vsdx | 1 | container-only |
| .vsix | 1 | container-only |
| .vssm | 1 | container-only |
| .vssx | 1 | container-only |
| .vstm | 1 | container-only |
| .vstx | 1 | container-only |
| .war | 1 | container-only |
| .warc | 3 | native |
| .webm | 1 | native |
| .webp | 1 | native |
| .wgt | 1 | container-only |
| .whl | 1 | container-only |
| .wim | 1 | native |
| .wmv | 1 | native |
| .woff | 1 | native |
| .woff2 | 1 | native |
| .wv | 1 | native |
| .xap | 1 | container-only |
| .xapk | 1 | container-only |
| .xd | 1 | container-only |
| .xhtml | 1 | syntax |
| .xla | 1 | alias |
| .xlam | 1 | container-only |
| .xls | 13 | original |
| .xlsb | 1 | container-only |
| .xlsm | 1 | container-only |
| .xlsx | 2 | container-only, native |
| .xlt | 1 | alias |
| .xltm | 1 | container-only |
| .xltx | 1 | container-only |
| .xmind | 1 | container-only |
| .xml | 1 | syntax |
| .xmp | 1 | syntax |
| .xpi | 1 | container-only |
| .xps | 1 | container-only |
| .xsl | 1 | syntax |
| .xslt | 1 | syntax |
| .xz | 3 | native |
| .z | 3 | native |
| .zip | 5 | native |
| .zipx | 1 | container-only |
| .zsav | 1 | native |
| .zst | 3 | native |

## Filename routes

| Filename suffix or detected type | Cases |
|---|---:|
| `.cpio` | archives-cpio-tree-cpio |
| `.cpio.bz2` | streams-cpio-tree-cpio-bz2 |
| `.otf (ODF package detected by ZIP content)` | packages-native-otf |
| `.rda.bz2` | scientific-arrays-rda-bz2 |
| `.rda.gz` | scientific-arrays-rda-gz |
| `.rda.gzip` | scientific-arrays-rda-gzip |
| `.rda.xz` | scientific-arrays-rda-xz |
| `.rdata.bz2` | scientific-arrays-rdata-bz2 |
| `.rdata.gz` | scientific-arrays-rdata-gz |
| `.rdata.gzip` | scientific-arrays-rdata-gzip |
| `.rdata.xz` | scientific-arrays-rdata-xz |
| `.rds.bz2` | scientific-arrays-rds-bz2 |
| `.rds.gz` | scientific-arrays-rds-gz |
| `.rds.gzip` | scientific-arrays-rds-gzip |
| `.rds.xz` | scientific-arrays-rds-xz |
| `.tar.br` | archives-container-tar-br |
| `.tar.bz2` | archives-container-tar-bz2 |
| `.tar.gz` | archives-container-tar-gz |
| `.tar.gzip` | archives-container-tar-gzip |
| `.tar.lz` | archives-container-tar-lz |
| `.tar.lz4` | archives-container-tar-lz4 |
| `.tar.lzma` | archives-container-tar-lzma |
| `.tar.lzo` | archives-container-tar-lzo |
| `.tar.xz` | archives-container-tar-xz |
| `.tar.z` | archives-container-tar-z |
| `.tar.zst` | archives-container-tar-zst |
| `.warc.gz` | native-weak-warc-gz |
| `.warc.gzip` | native-alias-warc-gzip |

The ODF packages use the registered media-type/extension pairs from the [OASIS OpenDocument 1.3 MIME type table](https://docs.oasis-open.org/office/OpenDocument/v1.3/os/part3-schema/OpenDocument-v1.3-os-part3-schema.pdf). The `.otf` sample is an ODF formula template selected by ZIP content, because `.otf` is not a flat registry extension.

## Remaining depth gaps

More real user-created office, video and scientific files, application rendering, larger heterogeneous archives and opt-in OLE content transforms would improve representativeness. Bounded nesting, archive links/controls, HDF5 graphs/references, nested NetCDF groups, high-bit-depth pixels, image metadata, rich PDF and multi-stream media are included. The current synthetic corpus deliberately includes favorable compression opportunities.

CRX3 is included as a correctly signed ZIP package and the independent oracle checks the signature. The current local filerepack run safely leaves it unchanged because the archive reader rejects the CRX prefix. This fixture records input coverage, not a claim of successful CRX recompression.

Original licensed samples and generated files must be analyzed separately for empirical claims.
The catalog is a snapshot of the local registry, including optional RTF. The committed 95827f3 implementation has 311 flat extensions and 101 handlers. Extra corpus routes are reported as removed registry entries when comparing an older implementation; strict coverage gates uncovered live routes, unresolved handler mappings and filename paths.
