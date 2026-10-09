## ADDED Requirements

### Requirement: Append-only extension
The extension command SHALL preserve the bytes and inventories of every existing fixture.

#### Scenario: Existing CRX
- **WHEN** extension encounters an existing CRX case
- **THEN** its bytes and manifest inventory remain identical

### Requirement: Atomic generation publication
The harness SHALL validate staged additions before publishing them and SHALL leave the existing corpus intact on generation failure.

#### Scenario: Generator fails
- **WHEN** a staged generator or validation fails
- **THEN** no existing corpus or manifest changes are published
