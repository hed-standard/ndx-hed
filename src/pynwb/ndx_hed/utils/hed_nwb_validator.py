"""
HedValidator class for validating HED tags in NWB DynamicTable objects.
"""
import io
import json 
from typing import List, Dict, Any, Optional
from pynwb.core import DynamicTable
from ndx_events import EventsTable
from hed.errors import ErrorHandler, ErrorContext
from hed.validator import HedValidator as HedValidatorBase
from hed.models import HedString, TabularInput
from ..hed_lab_metadata import HedLabMetaData
from ..hed_tags import HedTags
from .bids2nwb import get_bids_events


class HedNWBValidator:
    """
    A validator class for HED tags in NWB DynamicTable objects.
    
    This class provides methods to validate HED tags in various NWB data structures
    using HED schema information stored in HedLabMetaData.
    """
    
    def __init__(self, hed_metadata: HedLabMetaData):
        """
        Initialize the HedNWBValidator with HED metadata.
        
        Parameters:
            hed_metadata (HedLabMetaData): The HED lab metadata containing schema information
        """
        if not isinstance(hed_metadata, HedLabMetaData):
            raise ValueError("hed_metadata must be an instance of HedLabMetaData")
        
        self.hed_metadata = hed_metadata
        self.hed_schema = hed_metadata.get_hed_schema()

    def validate_table(self, table: DynamicTable, error_handler: Optional[ErrorHandler] = None) -> List[Dict[str, Any]]:
        """
        Validates all HedTags columns in a DynamicTable using the provided HED schema metadata.
        
        Parameters:
            table (DynamicTable): The dynamic table to validate
            error_handler (ErrorHandler, optional): An ErrorHandler instance for collecting errors. 
                                                   If None, a new instance will be created.
            
        Returns:
            List[Dict[str, Any]]: A consolidated list of validation issues from all HedTags columns
        """
        
        if error_handler is None:
            error_handler = ErrorHandler(check_for_warnings=False)
        issues = []
        # TODO: Context for table needs to be added to hed-python and pushed here
        for col in table.columns:
            if isinstance(col, HedTags):
                error_handler.push_error_context(ErrorContext.COLUMN, col.name)
                col_issues = self.validate_vector(col, error_handler)
                issues += col_issues
                error_handler.pop_error_context()
        return issues

    def validate_vector(self, hed_tags: HedTags, error_handler: Optional[ErrorHandler] = None) -> List[Dict[str, Any]]:
        """
        Validates a HedTags column using the provided HED schema metadata.
        
        Parameters:
            hed_tags (HedTags): The HedTags column to validate
            error_handler (ErrorHandler, optional): An ErrorHandler instance for collecting errors. 
                                                   If None, a new instance will be created.
            
        Returns:
            List[Dict[str, Any]]: A list of validation issues found in the HedTags column
        """
        if hed_tags is None or not isinstance(hed_tags, HedTags):
            raise ValueError("The provided hed_tags is not a valid HedTags instance.")
        if error_handler is None:
            error_handler = ErrorHandler(check_for_warnings=False)
        issues = []
        
        for index, tag in enumerate(hed_tags.data):
            if tag is None or tag == '' or tag == 'n/a':
                continue

            error_handler.push_error_context(ErrorContext.ROW, index)
            hed_obj = HedString(tag, self.hed_schema)
            row_issues = hed_obj.validate(allow_placeholders=False, error_handler=error_handler)
            issues += row_issues
            error_handler.pop_error_context()

        return issues

    def validate_events(self, events: EventsTable, error_handler: Optional[ErrorHandler] = None) -> List[Dict[str, Any]]:
        """
        Validates HED tags in an EventsTable by converting it to BIDS format and validating the events.
        
        This function extracts the BIDS-formatted DataFrame and JSON sidecar from the EventsTable
        using get_bids_events(), then validates the HED tags contained within using the provided 
        HED schema metadata.
        
        Parameters:
            events (EventsTable): The EventsTable to validate containing HED tags
            error_handler (ErrorHandler, optional): An ErrorHandler instance for collecting errors. 
                                                   If None, a new instance will be created.
            
        Returns:
            List[Dict[str, Any]]: A list of validation issues found in the EventsTable HED tags
            
        Raises:
            ValueError: If the EventsTable is invalid or cannot be converted to BIDS format
            
        Notes:
            This function uses get_bids_events() to extract BIDS-formatted data from the EventsTable,
            then applies HED validation to the extracted event annotations. The validation follows
            BIDS-HED standards for event annotation validation.
        """
        if events is None or not isinstance(events, EventsTable):
            raise ValueError("The provided events is not a valid EventsTable instance.")
        
        if error_handler is None:
            error_handler = ErrorHandler(check_for_warnings=False)
        
        # Convert EventsTable to BIDS format using get_bids_events
        df, json_data = get_bids_events(events)
        if json_data:
            json_input = json.dumps(json_data)
        else:
            json_input = None

        if json_input is not None:
            sidecar = io.StringIO(json_input)
        else:
            sidecar = None

        tab_input = TabularInput(file=df, sidecar=sidecar, name=events.name)
        issues = tab_input.validate(self.hed_schema, error_handler=error_handler)
        return issues
