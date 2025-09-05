import pandas as pd
import numpy as np
from pynwb import NWBHDF5IO, NWBFile
from pynwb.core import DynamicTable
from datetime import datetime


def df_to_dynamic_table(df: pd.DataFrame, name: str, description: str, index_name: str = "id") -> DynamicTable:
    """
    Converts a pandas DataFrame to a pynwb.core.DynamicTable.

    Args:
        df (pd.DataFrame): The pandas DataFrame to convert.
        name (str): The name of the DynamicTable.
        description (str): The description of the DynamicTable.
        index_name (str, optional): The name for the table's index. Defaults to "id".

    Returns:
        DynamicTable: The converted pynwb DynamicTable.
    """
    dt = DynamicTable(
        name=name,
        description=description
    )

    # Add columns from the DataFrame
    for col_name, col_series in df.items():
        dt.add_column(
            name=str(col_name),
            description=f"Column for {col_name}",
            data=col_series.to_list()
        )
    
    # Add the DataFrame index as the 'id' column for the DynamicTable
    dt.add_column(
        name=index_name,
        description="The unique identifier for each row",
        data=df.index.to_list(),
        index=True
    )

    return dt


if __name__ == '__main__':
    # 1. Create a sample Pandas DataFrame
    data = {
        'event_type': ['stim_on', 'stim_off', 'response', 'stim_on', 'stim_off', 'response'],
        'latency': [1.2, 1.5, 2.1, 3.4, 3.6, 4.0],
        'correct': [True, True, False, True, True, True],
        'value': np.arange(6)
    }
    df = pd.DataFrame(data)
    print("Original Pandas DataFrame:")
    print(df)
    print("\n")

    # 2. Convert the DataFrame to a DynamicTable
    my_dynamic_table = df_to_dynamic_table(
        df=df,
        name="my_events",
        description="A sample table of experimental events."
    )
    print("Converted pynwb.core.DynamicTable:")
    print(my_dynamic_table)
    print("\n")

    # 3. (Optional) Save it to an NWB file to verify
    nwbfile = NWBFile(
        session_description='A sample session',
        identifier='sample_123',
        session_start_time=datetime.now().astimezone()
    )
    nwbfile.add_acquisition(my_dynamic_table)

    output_file = 'sample_with_dt.nwb'
    with NWBHDF5IO(output_file, 'w') as io:
        io.write(nwbfile)
    print(f"DynamicTable saved to '{output_file}'")

    # 4. (Optional) Read the file back and verify content
    with NWBHDF5IO(output_file, 'r') as io:
        read_nwbfile = io.read()
        print("\nReading table back from NWB file:")
        print(read_nwbfile.acquisition['my_events'].to_dataframe())
