# HED Definition Validation Tests Summary

## Overview
Added comprehensive tests for validating HED tags that reference definitions. This revealed and fixed an important bug in the validator where definitions were not being properly passed to the validation functions.

## Tests Added (9 new tests in `TestValidateWithDefinitions`)

### 1. **test_validator_has_definitions**
- Verifies that the validator properly stores the DefinitionDict from HedLabMetaData
- Checks that validators with definitions have populated DefinitionDict
- Checks that validators without definitions have empty DefinitionDict
- Validates definition names are stored correctly (lowercase)

### 2. **test_validate_vector_definition_references_not_supported**
- Documents that `validate_vector()` does NOT support external definitions
- Definitions must be embedded in the HED string itself for validate_vector
- Only `validate_events()` and `validate_file()` support external definitions

### 3. **test_validate_vector_with_invalid_definition_references**
- Tests that definition references in validate_vector fail validation
- Confirms DEF_INVALID error code is returned

### 4. **test_definitions_property_access**
- Tests accessing the definitions property returns correct content
- Verifies definition names appear in the extracted string (case-insensitive check)

### 5. **test_validate_events_with_definition_references**
- Tests that `validate_events()` DOES support external definitions
- Valid definition references should pass validation
- Uses EventsTable with Def/Go-stimulus, Def/Response-time/0.45, etc.

### 6. **test_validate_events_with_invalid_definition_references**
- Tests that non-existent definition references fail validation
- Confirms proper error reporting for missing definitions

### 7. **test_validate_mixed_definitions_and_regular_tags**
- Tests mixing definition references with regular HED tags
- E.g., "Def/Go-stimulus, Red, Visual-presentation"
- Validates that both are properly checked

### 8. **test_validate_definition_with_invalid_regular_tags**
- Tests that invalid regular tags are caught even when definitions are valid
- E.g., "Def/Go-stimulus, InvalidTag123"
- Ensures mixed validation works correctly

### 9. **test_validate_events_uses_definitions**
- Integration test proving definitions are actually used
- Same EventsTable passes with definitions, fails without
- Validates the end-to-end definition workflow

## Bug Fixed in `HedNWBValidator`

**Problem:** The validator was storing `hed_metadata.definitions` (a string) instead of the DefinitionDict object.

**Before:**
```python
self.definitions = hed_metadata.definitions  # Returns string or None
```

**After:**
```python
self.definitions = hed_metadata.get_definition_dict()  # Returns DefinitionDict object
```

**Impact:** 
- `validate_events()` was failing with `TypeError: Invalid type '<class 'list'>' passed to DefinitionDict`
- The TabularInput.validate() expects a DefinitionDict object, not a string
- Now definitions work correctly in validate_events()

## Key Findings

### What Works:
✅ **validate_events()** - Fully supports external definitions via `extra_def_dicts` parameter  
✅ **validate_file()** - Supports definitions (uses validate_events internally for EventsTables)

### What Doesn't Work:
❌ **validate_vector()** - Uses `HedString.validate()` which doesn't support external definitions  
❌ **validate_table()** - Uses validate_vector() internally, so inherits same limitation  
❌ **validate_value_vector()** - Same limitation as validate_vector()

### Workaround:
For validate_vector/validate_table, definitions must be included in the HED string itself as Definition tags, not referenced externally.

## Test Results

All 55 tests in test_hed_nwb_validator.py pass:
- 3 initialization tests
- 8 vector validation tests  
- 9 table validation tests
- 6 EventsTable validation tests
- 20 HedValueVector validation tests
- **9 new definition validation tests** ✨

## Examples of Valid Definition Usage

```python
# Setup
definitions = (
    "(Definition/Go-stimulus, (Sensory-event, Visual-presentation)), "
    "(Definition/Response-time/#, (Time-interval/# s))"
)
hed_metadata = HedLabMetaData(hed_schema_version="8.4.0", definitions=definitions)
validator = HedNWBValidator(hed_metadata)

# Works with validate_events
events_df = pd.DataFrame({
    "onset": [1.0, 2.0],
    "duration": [0.5, 0.5],
    "HED": ["Def/Go-stimulus", "Def/Response-time/0.45"]
})
events_table = get_events_table("events", "test", events_df, {"categorical": {}, "value": {}})
issues = validator.validate_events(events_table)  # ✅ No issues

# Doesn't work with validate_vector (external defs not supported)
hed_tags = HedTags(data=["Def/Go-stimulus"])
issues = validator.validate_vector(hed_tags)  # ❌ DEF_INVALID error
```

## Documentation Impact

The class docstring for `TestValidateWithDefinitions` now clearly states:
> "Note: Currently, definitions are only used in validate_events() method.  
> The validate_vector() and validate_table() methods use HedString.validate()  
> which does not support external definition dictionaries."

This sets proper expectations for users of the validator API.
