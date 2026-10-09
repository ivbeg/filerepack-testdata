## ADDED Requirements

### Requirement: Live registry discovery
The harness SHALL discover extension, alias, handler and compound-route metadata from current and supported legacy filerepack checkouts.

#### Scenario: Derived registry views
- **WHEN** a checkout derives constant lists from a registry module
- **THEN** catalog extraction succeeds

### Requirement: Live handler coverage
The harness SHALL derive handler coverage from the same implementation identity as extension coverage.

#### Scenario: New handler added
- **WHEN** a new implementation handler has no qualified fixture
- **THEN** coverage reports the missing handler

### Requirement: Coverage gate
The coverage command SHALL support a strict gate for missing routes, handlers and unexplained registry drift.

#### Scenario: Missing route
- **WHEN** strict coverage finds an uncovered required route
- **THEN** the command exits nonzero
