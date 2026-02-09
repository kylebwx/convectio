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
        # if len(transect_nums) != len(iop_nums):
        #     raise ValueError(f'Length of iop_nums [{len(iop_nums)}] and transect_nums [{len(transect_nums)}] do not match.')

        # checks complete, begin loading logic
        # define atop class for ease-of-reference
        self.iop_nums = list(iop_nums)
        self.transect_nums = list(transect_nums)

        self.Tr_map = dict(zip(self.iop_nums, self.transect_nums))

        if print_config:
            self.show_config()

        # Load in metadata csv from src/data
        meta_df = pd.read_csv(META_PATH, sep="\s+")

        # 1. Clean up the string columns (Ensure times are strings like '16:57:00')
        meta_df['start_time'] = meta_df['start_time'].astype(str)
        meta_df['end_time'] = meta_df['end_time'].astype(str)

        # 2. Construct Full Datetime Columns
        # We create a temporary 'date_str' column to make parsing easier
        meta_df['date_str'] = pd.to_datetime(meta_df[['year', 'month', 'day']]).dt.strftime('%Y-%m-%d')

        # Combine Date + Time strings and convert to actual Pandas Timestamps
        meta_df['start_dt'] = pd.to_datetime(meta_df['date_str'] + ' ' + meta_df['start_time'])
        meta_df['end_dt'] = pd.to_datetime(meta_df['date_str'] + ' ' + meta_df['end_time'])

        # 3. Create a Unique ID for each transect
        # Format: "IOP02_T01_E" (IOP + Transect + Direction)
        meta_df['unique_id'] = (
                "IOP" + meta_df['iop'].astype(str).str.zfill(2) +
                "_T" + meta_df['transect'].astype(str).str.zfill(2) +
                "_" + meta_df['direction']
        )

        # List off all ncfiles for requested IOPs
        file_nm = meta_df[meta_df['iop'].isin(self.Tr_map)]['file_name'].unique().tolist()
        # create final pathlist by concatenation of NCDIR and the names from metadata
        f_list = [NCDIR / fname for fname in file_nm]

        # attempt to load all necessary files into mfdataset
        try:
            # xr loading
            payload = [xr.open_dataset(ncfile) for ncfile in f_list]

            # 2. Force concatenation along the time dimension
            # This allows them to have different sizes along 'time_dim'
            conc_df = xr.concat(payload, dim='time_dim')

            # 3. Now you can sort or save
            conc_df = conc_df.sortby('time_dim')

        except FileNotFoundError:

            print(f"One of the requested files does not exist in dir {NCDIR}")

        conc_df.head()
        # Slice and tag of each transect

        # t_index = conc_df.indexes['time']
        #
        # transect_mask = pd.Series(data=np.nan, index=t_index, dtype=object)
        #
        # for row in meta_df.itertuples():
        #     # .loc[] is inclusive for labels in Pandas, so this grabs the exact range
        #     # We assign the 'unique_id' to that time block
        #     try:
        #         transect_mask.loc[row.start_dt: row.end_dt] = row.unique_id
        #     except KeyError:
        #         # Optional: Print warning if a transect time isn't in your dataset
        #         pass
        # ds = conc_df.assign_coords(transect_id=('time', transect_mask))
        # ds_final = ds.dropna(dim='time', subset=['transect_id'])
        #
        # print(np.unique(ds_final.transect_id.values))


    def show_config(self):
        for iop, trans in self.Tr_map.items():
            print(f"IOP {iop} is loaded with Transects: {trans}")
