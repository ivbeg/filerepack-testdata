## ADDED Requirements

### Requirement: Semantic image metadata
The harness SHALL detect removal or alteration of declared image metadata, including text, EXIF and ICC data, under a keep-meta profile.

#### Scenario: Metadata removed
- **WHEN** a candidate retains decoded pixels but removes declared metadata
- **THEN** the independent comparison differs

### Requirement: ZIP and package constraints
The harness SHALL compare semantic ZIP member metadata and enforce mandatory package ordering, storage and alignment constraints.

#### Scenario: USDZ rewritten incorrectly
- **WHEN** a USDZ candidate compresses or misaligns its members
- **THEN** verification fails

### Requirement: Rich document and media profiles
The harness SHALL compare declared PDF text, interactive structures and media timeline/stream metadata when those profiles are qualified.

#### Scenario: Semantic structure removed
- **WHEN** a candidate removes a declared document or media structure
- **THEN** verification fails
