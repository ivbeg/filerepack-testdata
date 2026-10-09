## ADDED Requirements

### Requirement: HDF5 graph identity
The HDF5 oracle SHALL compare reachable object identity and declared hard/soft/external links without traversing external sources.

#### Scenario: Link removed
- **WHEN** a candidate removes or retargets a declared HDF5 link
- **THEN** verification differs

### Requirement: NetCDF nested groups
The NetCDF oracle SHALL recursively compare groups, dimension ownership, variable types/data and semantic metadata.

#### Scenario: Nested value changed
- **WHEN** a value in a nested NetCDF group changes
- **THEN** verification differs

### Requirement: Exact scientific values
Qualified scientific profiles SHALL retain signed zero, NaN payloads and exact declared numeric and attribute representations.

#### Scenario: Numeric edge value changes
- **WHEN** a candidate changes an exact scientific value bit pattern
- **THEN** verification differs
