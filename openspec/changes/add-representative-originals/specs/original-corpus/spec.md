## ADDED Requirements

### Requirement: Diversified licensed originals
The corpus SHALL include immutable licensed originals in document, image, media and scientific families in addition to OLE/CFB.

#### Scenario: New original included
- **WHEN** an upstream original is admitted
- **THEN** its pinned URL, exact inventory, redistribution evidence and notices are recorded

### Requirement: Original inventory consistency
Corpus checks SHALL validate original-index, manifest and license-reference consistency.

#### Scenario: Provenance diverges
- **WHEN** the original index disagrees with a manifest record
- **THEN** integrity checking fails

### Requirement: Separate evidence aggregates
Reports SHALL provide separate original and generated qualified aggregates.

#### Scenario: Mixed corpus
- **WHEN** a report includes synthetic and original inputs
- **THEN** their empirical savings remain separately identifiable
