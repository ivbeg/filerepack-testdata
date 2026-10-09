## ADDED Requirements

### Requirement: Boundary and protected scenarios
The corpus SHALL include bounded malformed/protected and archive nesting/path/member-boundary profiles with explicit preservation/refusal expectations.

#### Scenario: Archive hazard encountered
- **WHEN** an input violates a declared archive safety condition
- **THEN** the source remains unchanged or the declared safe handling is verified

### Requirement: Rich profiles
The corpus SHALL include text/forms/links PDF, metadata/high-depth raster, multiple media streams and scientific edge-value profiles.

#### Scenario: Rich structure altered
- **WHEN** a candidate alters a declared rich profile structure
- **THEN** independent verification fails

### Requirement: Scalable stress tier
The harness SHALL provide an explicit stress tier with configurable larger inputs and SHALL keep its results distinguishable from ordinary workload estimates.

#### Scenario: Stress selected
- **WHEN** a user selects a documented larger-input profile
- **THEN** the report records its size and resource observations separately
