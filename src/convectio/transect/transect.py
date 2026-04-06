import xarray as xr
import pandas as pd
import numpy as np
from typing import Optional
import os


class Transect:
    """
    A class to represent and process a single mobile mesonet transect.
    """

    def __init__(self, nc_filepath: str, temp_contamination: bool = False):
        self.nc_filepath = nc_filepath
        self.data: Optional[xr.Dataset] = None
        self.transect_id: str = os.path.splitext(os.path.basename(nc_filepath))[0]

        try:
            self.data = xr.open_dataset(self.nc_filepath)
            print(f"Transect '{self.transect_id}' loaded successfully.")
        except Exception as e:
            print(f"Failed to load {nc_filepath}: {e}")
            self.data = None

        if self.data is not None and temp_contamination:
            # Apply QC immediately if requested
            self.apply_qc()

    def apply_qc(self):
        """
        Filters the internal xarray dataset based on error flags.
        """
        if self.data is None:
            return

        # Convert to DF temporarily to use string vectorization
        df = self.data.to_dataframe()

        flags = df["error_flag"].astype(str)
        mask = flags.str.contains('tf02|ts02|w08', na=False)

        # Keep only the rows that AREN'T flagged
        df_cleaned = df[~mask].copy()

        # Sync back to xarray
        self.data = df_cleaned.to_xarray()
        print("QC Filtering complete. Bad flags (tf02, ts02, w08) dropped.")

    def export_pandas(self) -> Optional[pd.DataFrame]:
        """
        Returns the processed data as a cleaned Pandas DataFrame.
        """
        if self.data is None:
            print("No data available to export.")
            return None

        # Convert current state to dataframe
        df = self.data.to_dataframe().reset_index()

        # Fix timestamps
        if "time" in df.columns:
            df["time"] = pd.to_datetime(df["time"], unit="ns").dt.round("s")
            # Pro tip: keep them as datetime objects if you can,
            # but if you need strings for a specific export:
            # df["time"] = df["time"].dt.strftime("%Y-%m-%d %H:%M:%S")

        return df

    def get_data_summary(self) -> Optional[pd.DataFrame]:
        if self.data is None:
            return None
        return self.data.to_dataframe().describe()