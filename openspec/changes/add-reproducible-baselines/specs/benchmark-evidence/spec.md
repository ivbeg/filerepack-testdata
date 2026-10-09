## ADDED Requirements

### Requirement: Complete benchmark identity
Reports SHALL identify harness revision/source hash, corpus hash and fixed implementation identity alongside versions/options/tool availability.

#### Scenario: Harness changes
- **WHEN** benchmark harness code differs between runs
- **THEN** the report identifies the difference

### Requirement: Repeated immutable baseline
Published timing evidence SHALL use an immutable implementation snapshot, at least three measured attempts and one discarded warmup.

#### Scenario: Baseline published
- **WHEN** a current-corpus baseline is produced
- **THEN** its fixed source identities and repeat policy are included

### Requirement: Comparable qualification evidence
Comparisons SHALL flag corpus/options/environment/harness incompatibility and SHALL distinguish platform configuration from executed qualification.

#### Scenario: Platform not executed
- **WHEN** a CI lane is configured but has no measured result
- **THEN** documentation does not claim it passed
