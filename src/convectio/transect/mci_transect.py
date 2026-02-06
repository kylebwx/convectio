import xarray as xr
import pandas as pd
import numpy as np
from typing import Optional
import os

class Mitten:
    """
     A constructor based on the CoMeTalpha Meta file from the MITTEN-CI field campaign
     """
    def __init__(self, iop_nums, transect_nums):
        """Lists of desired IOPs and tuple of transect sets for each desire IOP."""

        # we check for consistency
        if len(transect_nums) != len(iop_nums):
            raise ValueError(f'Length of iop_nums [{len(iop_nums)}] and transect_nums [{len(transect_nums)}] do not match.')

        # define atop class for ease-of-reference
        self.iop_nums = list(iop_nums)
        self.transect_nums = list(transect_nums)

        self.Tr_map = dict(zip(self.iop_nums, self.transect_nums))

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

    def show_config(self):
        for iop, trans in self.Tr_map.items():
            print(f"IOP {iop} is loaded with Transects: {trans}")

    def