import xarray as xr
import pandas as pd
import numpy as np


from typing import Optional
import os
from pathlib import Path

class Mitten:
    """
     A constructor based on the CoMeTalpha Meta file from the MITTEN-CI field campaign.
     """
    def __init__(self, iop_nums: list = None, transect_nums: list = None, print_config: bool = True, comet_ident:str = 'alpha'):
        """Lists of desired IOPs and tuple of transect sets for each desire IOP."""
        BASE_DIR = Path(__file__).resolve().parent

        # First, we have to figure out what CoMeT is desired and set our NCDIR accordingly
        if comet_ident == 'unl_2':
            NCDIR = BASE_DIR.parent.parent / "data" / "comet" / "comet2_MCI"
        elif comet_ident == 'unl_3':
            NCDIR = BASE_DIR.parent.parent / "data" / "comet" / "comet3_MCI"
        elif comet_ident == 'alpha':
            NCDIR = BASE_DIR.parent.parent / "data" / "comet" / "cometalpha_MCI"
        else:
            raise ValueError(f"Unrecognized instrumentation '{comet_ident}'")

        META_PATH = BASE_DIR.parent.parent / "data" / "comet" / "cometalpha_MCI" / "CoMetalpha_META"

        # we check for consistency
        if len(transect_nums) != len(iop_nums):
            raise ValueError(f'Length of iop_nums [{len(iop_nums)}] and transect_nums [{len(transect_nums)}] do not match.')

        # checks complete, begin loading logic
        # define atop class for ease-of-reference
        self.iop_nums = list(iop_nums)
        self.transect_nums = list(transect_nums)

        self.Tr_map = dict(zip(self.iop_nums, self.transect_nums))

        if print_config:
            self.show_config()

        # Load in metadata csv from src/data
        meta_df = pd.read_csv(META_PATH, sep="\s+")

        for iop, transect in self.Tr_map:


        # use the metadata to generate the filtdict for selected IOP/Transect pairs (ITs)
        # appendee = meta_df[(meta_df['iop'].isin(iop_nums)) & (meta_df['transect'].isin(transect_nums))]
        #
        # if appendee.empty:
        #     raise IndexError("There is no metadata for defined IOP/Transect pair.")
        #     return None
        #
        # for iop in iop_nums:
        # row = appendee.iloc[0]
        # # full_path = NCDIR + str(row['file_name'])
        # # date_str = f"{row['year']}-{str(row['month']).zfill(2)}-{str(row['day']).zfill(2)}"




        # try:
        #     # Use xarray to open the NetCDF file.
        #     self.data = xr.open_dataset(self.nc_filepath)
        #     print(f"Transect '{self.transect_id}' loaded successfully.")
        #
        # except FileNotFoundError:
        #     print(f"Error: The file at '{nc_filepath}' was not found.")
        #     self.data = None
        # except Exception as e:
        #     print(f"An unexpected error occurred: {e}")
        #     self.data = None

    def show_config(self):
        for iop, trans in self.Tr_map.items():
            print(f"IOP {iop} is loaded with Transects: {trans}")
