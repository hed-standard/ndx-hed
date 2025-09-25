# Changelog for ndx-hed

## Release 0.2.0 (in development)

### Features
- **HedLabMetaData**: Required metadata container for HED schema version and definitions
- **HedTags**: Row-specific HED annotations for any DynamicTable
- **HedValueVector**: Column-wide HED templates with value placeholders (`#`)
- **Comprehensive validation**: `HedNWBValidator` class for validating HED annotations
- **BIDS integration**: Bidirectional conversion utilities between BIDS events and NWB EventsTable
- **EventsTable support**: Full integration with ndx-events extension
- **HED definitions**: Support for custom HED definitions in metadata

### Examples
- 6 comprehensive runnable examples covering all functionality
- BIDS conversion workflows
- EventsTable integration patterns
- Validation workflows
- Complete end-to-end workflows

### Testing
- 116+ test cases with full coverage
- Integration tests with file I/O roundtrips
- Validation testing with both valid and invalid HED

## Release 0.1.0 July 25, 2024

- Implements a `HedTags` class that extends NWB `VectorData`.
- Validates tags in the constructor and as they are added.
- The `HedTags` class can be used alone or added to any `DynamicTable`.
- The initial release only supports string HED version specifications, not tuples or lists.