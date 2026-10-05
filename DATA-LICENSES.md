# Code and data licenses

Code and synthetic fixtures authored in this repository use BSD-3-Clause (see `LICENSE`).
Generated DOCX/PPTX files also contain bundled python-docx/python-pptx template parts under MIT;
their manifest license is `BSD-3-Clause AND MIT` and the MIT notices are included as
`licenses/template-python-docx-LICENSE` and `licenses/template-python-pptx-LICENSE`.
Third-party originals retain separate upstream license labels; they are not relicensed as BSD.
`corpus/originals/index.json` records each original's exact URL, SHA-256, size and license.

| Directory/source | Declared upstream terms | Included legal files |
|---|---|---|
| `corpus/originals/ole` · Apache POI | Apache-2.0 | `licenses/ole-LICENSE.apache-poi`, `licenses/ole-NOTICE.apache-poi` |
| Apache POI files in `corpus/originals/ole_extended` | Apache-2.0 | `licenses/ole_extended-LICENSE.apache-poi`, `licenses/ole_extended-NOTICE.apache-poi` |
| pyhwp HWP fixtures in `corpus/originals/ole_extended` | AGPL-3.0 (upstream label) | `licenses/ole_extended-COPYING.pyhwp` |
| LibreOffice DOC/XLS regression fixtures | MPL-2.0 | `licenses/ole_extended-LICENSE.libreoffice` |
| WiX v3 MSI fixture | Microsoft Reciprocal License (MS-RL) | `licenses/ole_extended-LICENSE.wix3` |

Any additional upstream license/notice copied with this corpus is retained under `licenses/`.
Source commit IDs are embedded in every original URL. Derivative routing aliases record the parent
case and retain its license. Original binary bytes, including macro-containing regression samples,
are retained exactly and are parsed without executing their application content.

The test harness uses libraries/tools as installed dependencies, not vendored implementation code.
No private user documents or credentials are included. Benchmark results are ignored by Git;
review logs and reproduction directories before voluntarily publishing them because those may
include local paths. Checked-in baseline evidence contains summaries/environment, not raw logs.
