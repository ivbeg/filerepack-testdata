## ADDED Requirements

### Requirement: Strict verification
A strict benchmark SHALL fail on unexpected verifier skips or fewer than the required independently verified cases.

#### Scenario: All cases skipped
- **WHEN** strict execution skips every selected case
- **THEN** the benchmark exits nonzero

### Requirement: CI qualification lanes
CI SHALL run core smoke and rejection controls, minimum supported Python, platform harness tests and an optional-reader qualification lane.

#### Scenario: Control regression
- **WHEN** a rejection control changes bytes
- **THEN** CI fails

### Requirement: Required execution evidence
Qualification SHALL distinguish an optimizer attempt, an expected refusal, unavailable dependencies and verified size outcomes.

#### Scenario: No optimization attempted
- **WHEN** a case requiring an available backend reports no attempt
- **THEN** strict qualification fails
