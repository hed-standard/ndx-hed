# Changelog for ndx-hed

## Release 0.1.0 July 25, 2024

- Implements a `HedTags` class that extends NWB `VectorData`.
- Validates tags in the constructor and as they are added.
- The `HedTags` class can be used alone or added to any `DynamicTable`.
- The initial release only supports string HED version specifications, not tuples or lists.