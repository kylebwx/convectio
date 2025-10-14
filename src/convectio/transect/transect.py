import xarray as xr
import pandas as pd
import numpy as np
from typing import Optional
import os


class Transect:
    """
    A class to represent and process a single mobile mesonet transect. Designed to ingest QC'd MM data w/ optional support for non-
    QC'd data possible in the future.
    """

    def __init__(self, nc_filepath: str, temp_contamination: bool = False):
        """
        Initializes a Transect object by loading a NetCDF file.

        Args:
            nc_filepath: The file path to the NetCDF file containing
                         the transect data.
            temp_contamination: A boolean flag to indicate whether to check for
                                temperature sensor contamination flags.
        """
        self.nc_filepath = nc_filepath
        self.data: Optional[xr.Dataset] = None
        self.transect_id: str = os.path.splitext(os.path.basename(nc_filepath))[0]

        try:
            # Use xarray to open the NetCDF file.
            self.data = xr.open_dataset(self.nc_filepath)
            print(f"Transect '{self.transect_id}' loaded successfully.")

        except FileNotFoundError:
            print(f"Error: The file at '{nc_filepath}' was not found.")
            self.data = None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            self.data = None

        if self.data is not None and temp_contamination:
            print("Checking for temperature sensor contamination...")
            df = self.data.to_dataframe()
            # Use pandas string vectorization for efficiency.
            df["contam_f"] = df["error_flag"].str.contains("tf02", na=False)
            df["contam_s"] = df["error_flag"].str.contains("ts02", na=False)

            self.data = df.to_xarray()
            print("Contamination flags added.")

    def get_data_summary(self) -> Optional[pd.DataFrame]:
        """
        Returns a summary of the data variables in the transect.

        Returns:
            A pandas DataFrame with a summary of the data variables, or None
            if the data was not loaded.
        """
        if self.data is None:
            return None

        print("\nDisplaying data variables and attributes:")
        return self.data.to_dataframe().describe()

    def export_pandas(self) -> Optional[pd.DataFrame]:
        """Simple "reloading" of xarray dataset to pandas DataFrame if needed.
            Fixes nanosecond "accuracy" by rounding to nearest second.

        Returns:
            Optional[pd.DataFrame]: Pandas dataframe of original data.
        """

        if self.data is None:
            return None

        self.data = self.data.to_dataframe()
        self.data["time"] = pd.to_datetime(self.data["time"], unit="ns")
        self.data["time"] = self.data["time"].round("S")
        self.data["time"] = self.data["time"].dt.strftime("%Y-%m-%d %H:%M:%S")
        # self.data.set_index(pd.to_datetime(self.data["time"], unit="ns"), inplace=True)
        # self.data.drop(["time"], axis=1, inplace=True)

        return self.data
