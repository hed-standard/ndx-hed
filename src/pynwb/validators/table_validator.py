"""
Table validation functions for HED tags in NWB DynamicTable objects.
"""

from typing import List, Dict, Any
from pynwb.core import DynamicTable
from ndx_hed.hed_lab_metadata import HedLabMetaData
from ndx_hed.hed_tags import HedTags


def validate_table(hed_metadata: HedLabMetaData, dynamic_table: DynamicTable) -> List[Dict[str, Any]]:
    """
    Validates all HedTags columns in a DynamicTable using the provided HED schema metadata.
    
    Args:
        hed_metadata (HedLabMetaData): The HED lab metadata containing schema information
        dynamic_table (DynamicTable): The dynamic table to validate
        
    Returns:
        List[Dict[str, Any]]: A consolidated list of validation issues from all HedTags columns
    """
    
    df = dynamic_table.to_dataframe()
    issues = []
    
    # Iterate through all columns in the dynamic table
    for column_name in dynamic_table.colnames:
        column = dynamic_table[column_name]
        
        # Check if the column is a HedTags instance
        if isinstance(column, HedTags):
            # Validate this HedTags column
            column_issues = validate_tags(column, hed_metadata)
            
            # Add column name context to each issue
            for issue in column_issues:
                issue['column'] = column_name
                issues.append(issue)
    
    return issues


def validate_tags(hed_tags: HedTags, hed_metadata: HedLabMetaData) -> List[Dict[str, Any]]:
    """
    Validates a HedTags column using the provided HED schema metadata.
    
    Args:
        hed_tags (HedTags): The HedTags column to validate
        hed_metadata (HedLabMetaData): The HED lab metadata containing schema information
        
    Returns:
        List[Dict[str, Any]]: A list of validation issues found in the HedTags column
    """
    issues = []
    
    # TODO: Implement HedValidator validation logic
    # This is a placeholder that will be filled in later
    # The function should:
    # 1. Get the HED schema from hed_metadata
    # 2. Create a HedValidator instance
    # 3. Validate each HED string in the hed_tags data
    # 4. Return formatted validation issues
    
    # Placeholder return - replace with actual validation logic
    return issues
