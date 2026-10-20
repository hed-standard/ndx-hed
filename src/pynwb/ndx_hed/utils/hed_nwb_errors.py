"""
Error codes that ndx-hed reports for structural problems in NWB tables.

These are registered with hedtools' ``hed_error`` decorator so that an issue produced through
``ErrorHandler.format_error_with_context`` has the same shape (``code``, ``message``, ``severity``
and the ``ec_*`` context keys) as every issue hedtools itself reports. They describe problems in
how HED is stored in a table, which hedtools cannot see because they are gone by the time the table
has been converted to a BIDS dataframe and sidecar.

The rules are documented in ``docs/source/hed_validation.md``.
"""

from hed.errors.error_reporter import hed_error

# A column named "HED" that is not a HedTags column (rule R6). The name is what marks a column as
# per-row HED in a DynamicTable and as categorical HED in a MeaningsTable, so the type must match.
HED_COLUMN_TYPE_INVALID = "HED_COLUMN_TYPE_INVALID"

# A HedValueVector column inside a MeaningsTable (rule R5). A value template has no meaning for the
# per-value annotation a MeaningsTable holds.
MEANINGS_VALUE_VECTOR_INVALID = "MEANINGS_VALUE_VECTOR_INVALID"

# A column name repeated in the BIDS view of a table (rule R9): hdmf keeps table column names unique, but
# a TimestampVectorData named "timestamp" is exported as "onset", so a table that also has a column named
# "onset" has two. Reported as the HED specification's TABULAR_INVALID (a repeated column name in a
# tabular file); the registry key is ndx-hed's own so that it cannot clash with hedtools' registration of
# that code.
BIDS_COLUMN_NAME_REPEATED = "NWB_BIDS_COLUMN_NAME_REPEATED"
TABULAR_INVALID = "TABULAR_INVALID"


@hed_error(HED_COLUMN_TYPE_INVALID)
def hed_column_type_invalid(table_name, column_type):
    return (
        f"Column 'HED' of table '{table_name}' is a {column_type}, but a column named 'HED' must be a HedTags "
        "column. Rename the column, or store its HED annotations in a HedTags column named 'HED'."
    )


@hed_error(MEANINGS_VALUE_VECTOR_INVALID)
def meanings_value_vector_invalid(table_name, column_name):
    return (
        f"Column '{column_name}' of MeaningsTable '{table_name}' is a HedValueVector, which is not allowed in a "
        "MeaningsTable. Categorical HED must be complete HED strings in a HedTags column named 'HED'."
    )


@hed_error(BIDS_COLUMN_NAME_REPEATED, actual_code=TABULAR_INVALID)
def bids_column_name_repeated(table_name, column_name):
    return (
        f"Column '{column_name}' appears more than once in table '{table_name}' as BIDS names its columns: a "
        "TimestampVectorData named 'timestamp' is exported as 'onset'. Rename the other 'onset' column."
    )
