## ADDED Requirements

### Requirement: Model inspection cases
The corpus SHALL contain valid and malformed bounded Safetensors, GGUF and ONNX profiles without executing models or loading arbitrary objects.

#### Scenario: Inspection-only model
- **WHEN** a valid model inspection fixture is processed
- **THEN** its bytes remain unchanged and its inspection outcome is recorded

### Requirement: Current data/document routes
The corpus SHALL provide independently verifiable tracev3, gzip and RTF profiles with explicit capability expectations.

#### Scenario: Format routed
- **WHEN** the implementation supports a new route
- **THEN** its fixture and expected behavior are present

### Requirement: Detected filename routes
The corpus SHALL cover registered compound aliases and representative content detection without relying only on an expected suffix.

#### Scenario: WARC named gzip
- **WHEN** a WARC gzip stream has only a generic compression suffix
- **THEN** routing evidence identifies the WARC profile
