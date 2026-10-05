# Coverage snapshot

Catalog: current local filerepack source, 2026-10-05. Regenerate this snapshot with `python -m frbench coverage --json`.

- 403 cases: 12 smoke, 377 extended, 14 rejection controls.
- 302/303 registered extension routes have non-control fixtures (99.67%).
- 139 extensions have native or original fixtures; the rest are syntax, routing or transport tests.
- 94/94 distinct file-handler/archive-family groups have fixtures.
- 48 upstream originals; remaining fixtures are generated or explicit routing derivatives.
- Directory Zarr v2 and compound compressed-tar/WARC names are additional cases, outside the flat extension denominator.

The missing `.crx` route requires a proper signed Chrome extension envelope. A renamed ZIP would not supply meaningful CRX evidence, so it is an explicit gap.

Handler coverage means an input exists for the code path. It does not mean the environment has every encoder, that every variant is supported, or that every case produced a smaller candidate.

## Fixture scopes

| Scope | Cases | Meaning |
|---|---:|---|
| alias | 27 | An existing bitstream under another supported routing suffix. |
| container-only | 128 | Generic ZIP/TAR/SQLite payload; no application-format claim. |
| native | 184 | Generated readable profile for that format; see oracle limits. |
| original | 48 | Unmodified commit-pinned upstream regression sample. |
| syntax | 16 | Valid generic text/binary structure, without application/render qualification. |

## Handler groups

| Handler/family | Cases | Native/original/syntax case |
|---|---:|---|
| `archive:7z` | 2 | yes |
| `archive:cab` | 1 | yes |
| `archive:rar` | 2 | yes |
| `archive:tar` | 3 | yes |
| `archive:tar.bz2` | 2 | transport/alias only |
| `archive:tar.gz` | 3 | transport/alias only |
| `archive:tar.lz` | 1 | transport/alias only |
| `archive:tar.lzo` | 1 | transport/alias only |
| `archive:tar.xz` | 1 | transport/alias only |
| `archive:tar.z` | 1 | transport/alias only |
| `archive:tar.zst` | 1 | transport/alias only |
| `archive:wim` | 1 | yes |
| `archive:zip` | 137 | yes |
| `pack_3gp` | 1 | yes |
| `pack_ai` | 1 | transport/alias only |
| `pack_ape` | 1 | yes |
| `pack_arrow` | 2 | yes |
| `pack_aseprite` | 2 | yes |
| `pack_asf` | 1 | yes |
| `pack_avi` | 1 | yes |
| `pack_avif` | 1 | yes |
| `pack_avro` | 1 | yes |
| `pack_blend` | 1 | yes |
| `pack_bmp` | 2 | yes |
| `pack_brotli` | 3 | yes |
| `pack_bz2` | 3 | yes |
| `pack_checkpoint` | 2 | yes |
| `pack_compress` | 3 | yes |
| `pack_dcm` | 3 | yes |
| `pack_dng` | 1 | yes |
| `pack_duckdb` | 1 | yes |
| `pack_exr` | 1 | yes |
| `pack_feather` | 1 | yes |
| `pack_fits` | 3 | yes |
| `pack_flac` | 1 | yes |
| `pack_gif` | 2 | yes |
| `pack_gzip` | 3 | yes |
| `pack_hdf5` | 3 | yes |
| `pack_heic` | 2 | yes |
| `pack_icns` | 1 | yes |
| `pack_ico` | 2 | yes |
| `pack_jp2` | 4 | yes |
| `pack_jpg` | 7 | yes |
| `pack_json` | 9 | yes |
| `pack_jsonl` | 2 | yes |
| `pack_jxl` | 1 | yes |
| `pack_lz4` | 3 | yes |
| `pack_lzip` | 3 | yes |
| `pack_lzma` | 3 | yes |
| `pack_lzo` | 3 | yes |
| `pack_m4a` | 2 | yes |
| `pack_m4v` | 1 | yes |
| `pack_mat` | 1 | yes |
| `pack_mkv` | 1 | yes |
| `pack_mov` | 1 | yes |
| `pack_mp3` | 1 | yes |
| `pack_mp4` | 1 | yes |
| `pack_netcdf` | 2 | yes |
| `pack_nib` | 1 | yes |
| `pack_nrrd` | 2 | yes |
| `pack_oga` | 1 | yes |
| `pack_ogg` | 2 | yes |
| `pack_ole` | 50 | yes |
| `pack_orc` | 1 | yes |
| `pack_parquet` | 2 | yes |
| `pack_pcx` | 2 | yes |
| `pack_pdf` | 1 | yes |
| `pack_png` | 4 | yes |
| `pack_pnm` | 4 | yes |
| `pack_psb` | 1 | yes |
| `pack_psd` | 1 | yes |
| `pack_qgd` | 1 | yes |
| `pack_qgs` | 1 | yes |
| `pack_r_serialization` | 6 | yes |
| `pack_spss` | 2 | yes |
| `pack_sqlite` | 7 | yes |
| `pack_svg` | 1 | yes |
| `pack_svgz` | 1 | yes |
| `pack_swf` | 1 | yes |
| `pack_tga` | 2 | yes |
| `pack_tgs` | 1 | yes |
| `pack_tif` | 2 | yes |
| `pack_ts` | 3 | yes |
| `pack_tta` | 1 | yes |
| `pack_warc` | 2 | yes |
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
| .arrow | 1 | native |
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
| .cb7 | 1 | alias |
| .cbr | 1 | alias |
| .cbt | 1 | container-only |
| .cbz | 1 | container-only |
| .crate | 1 | alias |
| .crtx | 1 | container-only |
| .crx | 0 | missing |
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
| .docx | 2 | container-only, native |
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
| .flac | 1 | native |
| .fts | 1 | native |
| .gcsx | 1 | container-only |
| .gem | 1 | container-only |
| .geojson | 1 | native |
| .gif | 2 | native |
| .glox | 1 | container-only |
| .gltf | 1 | native |
| .gpkg | 1 | container-only |
| .gpx | 1 | syntax |
| .gqsx | 1 | container-only |
| .gz | 3 | native |
| .h5 | 1 | native |
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
| .jpg | 1 | native |
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
| .mat | 1 | native |
| .mbtiles | 1 | container-only |
| .mcaddon | 1 | container-only |
| .mcpack | 1 | container-only |
| .mcworld | 1 | container-only |
| .mellel | 1 | syntax |
| .mkv | 1 | native |
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
| .nc4 | 1 | native |
| .ndjson | 1 | native |
| .nib | 1 | syntax |
| .nmbtemplate | 1 | container-only |
| .notebook | 1 | container-only |
| .npz | 2 | container-only, native |
| .nrrd | 2 | native |
| .numbers | 1 | container-only |
| .nupkg | 1 | container-only |
| .odb | 1 | container-only |
| .odc | 1 | container-only |
| .odf | 1 | container-only |
| .odg | 1 | container-only |
| .odi | 1 | container-only |
| .odm | 1 | container-only |
| .odp | 2 | container-only, native |
| .ods | 2 | container-only, native |
| .odt | 2 | container-only, native |
| .oex | 1 | container-only |
| .oga | 1 | native |
| .ogg | 1 | native |
| .onepkg | 1 | container-only |
| .opus | 1 | native |
| .ora | 1 | container-only |
| .orc | 1 | native |
| .osk | 1 | container-only |
| .otc | 1 | container-only |
| .otg | 1 | container-only |
| .oth | 1 | container-only |
| .oti | 1 | container-only |
| .otm | 1 | container-only |
| .otp | 1 | container-only |
| .ots | 1 | container-only |
| .ott | 1 | container-only |
| .oxps | 1 | container-only |
| .oxt | 1 | container-only |
| .pages | 1 | container-only |
| .parquet | 2 | native |
| .pbm | 1 | native |
| .pcx | 1 | native |
| .pdf | 1 | native |
| .pgm | 1 | native |
| .pk3 | 1 | container-only |
| .png | 3 | native |
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
| .rda | 2 | native |
| .rdata | 2 | native |
| .rds | 2 | native |
| .rels | 1 | syntax |
| .rmskin | 1 | container-only |
| .rss | 1 | syntax |
| .rtb | 1 | container-only |
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
| .tar | 1 | native |
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
| .tiff | 1 | native |
| .tlz | 1 | alias |
| .topojson | 1 | native |
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
| .warc | 2 | native |
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
| .zip | 2 | native |
| .zipx | 1 | container-only |
| .zsav | 1 | native |
| .zst | 3 | native |

## Remaining depth gaps

Additional real-world modern Office/ODF/media/scientific workloads, application rendering, nested archive-within-archive permutations, complex HDF5 link graphs, wide bit-depth/image metadata coverage and opt-in OLE content transforms would strengthen representativeness. The existing corpus is a compact format and preservation matrix, with deliberately favorable synthetic compression opportunities.

Generic ODF-style ZIP aliases may be rejected by package policy; the separate native ODT/ODS/ODP/EPUB fixtures exercise proper controls and mimetype layout. Original licensed samples and synthetic files must be analyzed separately for empirical claims.
