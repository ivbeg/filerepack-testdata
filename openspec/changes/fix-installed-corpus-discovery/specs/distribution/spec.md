## ADDED Requirements

### Requirement: Installed corpus discovery
An installed harness SHALL locate a user-specified corpus root and SHALL give an actionable error when default corpus assets are unavailable.

#### Scenario: Wheel has no dataset
- **WHEN** a user runs a corpus command after installing the wheel without specifying a dataset
- **THEN** the error explains how to supply a corpus root

### Requirement: Distribution qualification
Distribution tests SHALL install built artifacts outside the source tree and verify CLI operation with an explicit checksummed corpus.

#### Scenario: Artifact installed
- **WHEN** a wheel or source distribution is installed in isolation
- **THEN** its CLI reads the supplied corpus without importing checkout code

### Requirement: Publication documentation
Documentation SHALL accurately describe the repository URL, supported installation modes and dataset availability.

#### Scenario: Repository published
- **WHEN** the repository has an origin remote
- **THEN** README no longer claims publication is unconfigured
