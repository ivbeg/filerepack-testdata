## ADDED Requirements

### Requirement: Oracle conformance inventory
Every qualified oracle kind SHALL have recorded equivalence and semantic-corruption regressions.

#### Scenario: Oracle added
- **WHEN** a new oracle kind is referenced by the corpus
- **THEN** conformance inventory and executable regressions include it

### Requirement: Mutation detection
Oracle conformance SHALL distinguish permissible recompression from mutations to declared payloads and metadata.

#### Scenario: Candidate corrupted
- **WHEN** a mutation violates the oracle contract
- **THEN** the comparison differs or rejects the candidate

### Requirement: Optional conformance qualification
Missing native dependencies SHALL be reported as explicit skips and strict qualified lanes SHALL reject unexpected skips.

#### Scenario: Reader unavailable
- **WHEN** a conformance dependency is unavailable
- **THEN** the result identifies the dependency and strict qualification fails
