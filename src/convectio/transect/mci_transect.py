import xarray as xr
import pandas as pd
import numpy as np
import os
from pathlib import Path
from typing import Optional, List, Union

from convectio.spatial.reldist_bckp import rel_distance


class Mitten:
    """
    A constructor based on the CoMeTalpha Meta file from the MITTEN-CI field campaign.
    """

    def __init__(self, iop_nums: Union[int, List[int]],
                 transect_nums: Union[int, List[int], List[List[int]]],
                 dirty_qc: bool = False,
                 print_config: bool = True,
                 comet_ident: str = 'alpha'):

        # --- 1. Input Normalization ---
        if isinstance(iop_nums, int):
            self.iop_nums = [iop_nums]
        else:
            self.iop_nums = list(iop_nums)

        if isinstance(transect_nums, int):
            self.transect_nums = [[transect_nums]]
        elif isinstance(transect_nums, list) and len(transect_nums) > 0 and isinstance(transect_nums[0], int):
            if len(self.iop_nums) > 1:
                self.transect_nums = [transect_nums] * len(self.iop_nums)
            else:
                self.transect_nums = [transect_nums]
        else:
            self.transect_nums = list(transect_nums)

        if len(self.iop_nums) != len(self.transect_nums):
            raise ValueError(f"Mismatch: {len(self.iop_nums)} IOPs vs {len(self.transect_nums)} transect groups.")

        self.Tr_map = dict(zip(self.iop_nums, self.transect_nums))

        if print_config:
            self.show_config()

        # --- 2. Path Setup ---
        BASE_DIR = Path(__file__).resolve().parent
        if comet_ident == 'alpha':
            NCDIR = BASE_DIR.parent.parent / "data" / "comet" / "cometalpha_MCI"
        # Add other paths if needed...
        else:
            # Fallback for now to avoid breaking if you passed something else
            NCDIR = BASE_DIR.parent.parent / "data" / "comet" / f"comet{comet_ident}_MCI"

        META_PATH = BASE_DIR.parent.parent / "data" / "comet" / "cometalpha_MCI" / "CoMetalpha_META"

        # --- 3. Load & Prep Metadata ---
        meta_df = pd.read_csv(META_PATH, sep=r"\s+")
        meta_df['start_time'] = meta_df['start_time'].astype(str)
        meta_df['end_time'] = meta_df['end_time'].astype(str)
        meta_df['date_str'] = pd.to_datetime(meta_df[['year', 'month', 'day']]).dt.strftime('%Y-%m-%d')
        meta_df['start_dt'] = pd.to_datetime(meta_df['date_str'] + ' ' + meta_df['start_time'])
        meta_df['end_dt'] = pd.to_datetime(meta_df['date_str'] + ' ' + meta_df['end_time'])

        meta_df['unique_id'] = (
                "IOP" + meta_df['iop'].astype(str).str.zfill(2) +
                "_T" + meta_df['transect'].astype(str).str.zfill(2) +
                "_" + meta_df['direction']
        )

        # --- 4. Filter Metadata ---
        mask = pd.Series(False, index=meta_df.index)
        for iop, t_list in self.Tr_map.items():
            mask |= (meta_df['iop'] == iop) & (meta_df['transect'].isin(t_list))

        self.meta_subset = meta_df[mask].copy()
        if self.meta_subset.empty:
            raise ValueError("No metadata found for the requested IOPs/Transects.")

        file_list = self.meta_subset['file_name'].unique().tolist()
        full_paths = [NCDIR / fname for fname in file_list]

        # --- 5. The Intelligent Loader ---
        cleaned_datasets = []

        for ncfile in full_paths:
            try:
                if not ncfile.exists():
                    print(f"Warning: File not found {ncfile}")
                    continue

                # Open the dataset
                ds = xr.open_dataset(ncfile, decode_timedelta=True)

                # get Filename Date/Time parts (just in case we need them)
                # Filename: UNL.CoMeTalpha.20240721.1345...
                parts = ncfile.name.split('.')
                f_date_str = parts[2]  # "20240721"
                f_time_str = parts[3]  # "1345"

                filename_date = pd.to_datetime(f_date_str, format='%Y%m%d')

                # 3. ANALYZE THE TIME DATA
                # We grab the first value and convert to seconds to see what we are dealing with.
                # (ds['time'] is likely timedelta64[ns], so we cast to float then divide by 1e9)
                first_val_seconds = ds['time'].values[0].astype('float64') / 1e9

                # --- CASE A: Unix Timestamp (The 2079 Fix) ---
                # If time > 1 year (30 million seconds), it is absolute time since 1970.
                if first_val_seconds > 3e7:
                    # print(f"DEBUG: Detected Unix Time for {ncfile.name}. Anchoring to 1970.")
                    # We add it to the Unix Epoch.
                    new_time = pd.Timestamp("1970-01-01") + ds['time'].copy()

                # --- CASE B: Time-of-Day (Seconds since Midnight) ---
                # If time is small (e.g., > 1 hour but < 1 year), it's seconds since 00:00:00 of that day.
                elif first_val_seconds > 3600:
                    # print(f"DEBUG: Detected Time-of-Day for {ncfile.name}. Anchoring to {filename_date}.")
                    # We add it to the Date from the filename.
                    new_time = filename_date + ds['time'].copy()

                # --- CASE C: Relative Start (Starts at 0 or very close to it) ---
                # The logger reset and started counting from 0 when the file was created.
                else:
                    # print(f"DEBUG: Detected Relative Start for {ncfile.name}. Using Filename Time.")
                    # We must construct the full start time from the filename (e.g. 13:45)
                    hours = int(f_time_str[:2])
                    minutes = int(f_time_str[2:])
                    file_start_offset = pd.Timedelta(hours=hours, minutes=minutes)

                    new_time = filename_date + file_start_offset + ds['time'].copy()

                # 4. Apply the Fix
                new_time.attrs = {}  # Clear attributes to stop Xarray confusion
                ds = ds.assign_coords(time=new_time)

                # 5. Swap Dims (Standardize to 'time')
                if 'time_dim' in ds.dims:
                    ds = ds.swap_dims({'time_dim': 'time'})
                    ds = ds.drop_vars(['time_dim'], errors='ignore')

                # 6. Round and Clean
                ds['time'] = ds['time'].dt.round('1s')
                _, index = np.unique(ds['time'], return_index=True)
                ds = ds.isel(time=index)

                if dirty_qc:
                    # 1. Cast to string and ensure we handle the 'time' dimension
                    flags = ds["error_flag"].astype(str)

                    # check for the specific codes directly
                    # This avoids the .split('-') dimension entirely
                    mask_tf02 = flags.str.contains('tf02')
                    mask_ts02 = flags.str.contains('ts02')
                    mask_w08 = flags.str.contains('w08')

                    drop_mask = mask_tf02 | mask_ts02 | mask_w08

                    orig_len = ds.sizes['time']
                    # Use drop=True without the 'inplace'
                    ds = ds.where(~drop_mask, drop=True)

                    if print_config:
                        print(f"QC: Dropped {orig_len - ds.sizes['time']} points from {ncfile.name}")

                cleaned_datasets.append(ds)

            except Exception as e:
                print(f"Failed to load {ncfile.name}: {e}")

        if not cleaned_datasets:
            raise ValueError("No datasets were loaded.")

        self.ds = xr.concat(cleaned_datasets, dim='time')
        self.ds = self.ds.sortby('time')

        # --- Debug Print: Show overlap ---
        d_min, d_max = self.ds.time.min().values, self.ds.time.max().values
        # print(f"\nData Range: {d_min} to {d_max}")
        # print(f"Looking for: {self.meta_subset.iloc[0].start_dt} ...")

        # --- 6. Slicing ---
        dataset_time_index = self.ds.indexes['time']
        transect_mask = pd.Series(data=np.nan, index=dataset_time_index, dtype=object)

        for row in self.meta_subset.itertuples():
            try:
                transect_mask.loc[row.start_dt: row.end_dt] = row.unique_id
            except KeyError:
                pass

        self.ds = self.ds.assign_coords(transect_id=('time', transect_mask))
        self.ds = self.ds.dropna(dim='time', subset=['transect_id'])

        if len(self.ds.time) == 0:
            print("CRITICAL WARNING: Zero data retained after filter.")
            print(f"Data covers: {d_min} <-> {d_max}")
            print(f"Requested: {self.meta_subset.iloc[0].start_dt} <-> {self.meta_subset.iloc[0].end_dt}")
        else:
            print(f"Success! Loaded {len(self.ds.time)} time steps.")
            print("Transects available:", np.unique(self.ds.transect_id.values))



    def show_config(self):
        """
        Shows configured IOPs and paired Transects.
        Returns:

        """
        for iop, trans in self.Tr_map.items():
            print(f"Configured IOP {iop} with Transects: {trans}")

    def extract_tr(self, transect_id: str = 'all') -> xr.Dataset:
        """
        Extracts a single transect as a standalone Dataset.

        Args:
            transect_id (str): The unique ID (e.g., 'IOP08_T01_E'). This defaults to
            returning all transects in a dataset.

        Returns:
            xr.Dataset: A new dataset containing only that transect's data.
        """
        # Does this ID exist?
        available_ids = np.unique(self.ds.transect_id.values)
        if transect_id != 'all':
            if transect_id not in available_ids:
                # Helpful error message so you don't lose your mind guessing IDs
                raise ValueError(f"Transect '{transect_id}' not found.\nAvailable IDs: {available_ids}")

        if transect_id == 'all':

            self.ds.attrs['description'] = "All selected transects."

            return self.ds

        # Slice (Boolean Masking)
        # We find where the coordinate equals the ID, and keep only those time steps.
        subset = self.ds.isel(time=(self.ds.transect_id == transect_id))

        # Add attributes the plot knows what it's looking at
        subset.attrs['transect_id'] = transect_id
        subset.attrs['description'] = f"Extracted slice for {transect_id}"

        return subset

    def transect_dict(self, transect_id:str = 'all') -> dict:

        """

        Args:
            transect_id (str): The unique transect ID (e.g., 'IOP08_T01_E')

        Returns:
                Dictionary containing transect UID, LBF cross time (if applicable), and the direction
                of the transect.
        """

        if transect_id != 'all' and transect_id not in self.meta_subset['unique_id'].values:
            raise ValueError(f"Transect ID '{transect_id}' not in available IDs.")

        if transect_id == 'all':
            meta_subset_tdict = self.meta_subset
        elif transect_id != 'all':
            meta_subset_tdict = self.meta_subset[(self.meta_subset['unique_id']==transect_id)]

        data_dict = {'tr_UID': meta_subset_tdict['unique_id'].values,
                    'lbf_time': meta_subset_tdict['lbf_cross_time'].values,
                    'tr_direction': meta_subset_tdict['direction'].values}

        return data_dict