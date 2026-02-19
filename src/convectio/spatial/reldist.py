from pathlib import Path
import pandas as pd
import numpy as np
import geopy.distance
import xarray as xr


def calculate_single_transect(ds_subset, front_time, ls_coords):
    """
    Helper function to process a SINGLE transect.
    """
    # --- 1. Lake Relative Distance ---
    tr_lats = ds_subset.lat.values
    lake_lats = ls_coords['lat'].values

    # Broadcast to find nearest lake point
    diff_matrix = np.abs(tr_lats[:, np.newaxis] - lake_lats[np.newaxis, :])
    idx = diff_matrix.argmin(axis=1)

    matched_lons = ls_coords['lon'].values[idx]
    matched_lats = ls_coords['lat'].values[idx]

    tr_points_geo = np.column_stack((ds_subset.lon.values, ds_subset.lat.values))
    lake_points_geo = np.column_stack((matched_lons, matched_lats))

    l_dst = [geopy.distance.geodesic(p1, p2).km for p1, p2 in zip(tr_points_geo, lake_points_geo)]

    # --- 2. Front Relative Distance (Odometer) ---
    # Calculate cumulative distance driven from the start of the file
    dists = [0.0]
    for i in range(1, len(tr_points_geo)):
        d = geopy.distance.geodesic(tr_points_geo[i - 1], tr_points_geo[i]).km
        dists.append(d)

    cumulative_dist = np.cumsum(dists)

    # Find the odometer reading at the exact Front Crossing Time
    target_time = pd.to_datetime(front_time)
    time_diffs = np.abs(pd.to_datetime(ds_subset.time.values) - target_time)
    front_idx = time_diffs.argmin()

    dist_at_front = cumulative_dist[front_idx]

    # CASE 1: Before Crossing (Time < FrontTime)
    #   cumulative_dist is SMALL. dist_at_front is BIG.
    #   (Big - Small) = Positive.
    #
    # CASE 2: After Crossing (Time > FrontTime)
    #   cumulative_dist is BIG. dist_at_front is SMALL.
    #   (Small - Big) = Negative.

    f_dist = dist_at_front - cumulative_dist

    return l_dst, f_dist


def rel_distance(transect, transect_dict):
    """
    Calculates distances for multi-transect datasets.
    """
    P_DIR = Path(__file__).resolve().parent
    ls_file = P_DIR.parent.parent / "data" / "gis" / "mci" / "mci_lakeshore.csv"
    ls_coords = pd.read_csv(ls_file)

    processed_chunks = []

    # Loop through each transect ID in the dataset
    for t_id, group in transect.groupby("transect_id"):

        try:
            # Column-oriented lookup to find the index of the current ID
            uid_list = list(transect_dict['tr_UID'])
            idx = uid_list.index(t_id)

            t_time = transect_dict['lbf_time'][idx]

            dataset_date = str(pd.to_datetime(group.time.values[0]).date())
            full_timestamp = f"{dataset_date} {t_time}"

        except (ValueError, KeyError):
            # Fail loudly if the ID isn't in your dictionary
            raise KeyError(f"Transect ID '{t_id}' not found in transect_dict['tr_UID']")

        # Calculate with the new sign logic
        l_d, f_d = calculate_single_transect(group, full_timestamp, ls_coords)

        # Assign coordinates
        group = group.assign_coords({
            "ls_distance": ("time", l_d),
            "fr_distance": ("time", f_d)
        })

        processed_chunks.append(group)

    # Recombine
    ds_final = xr.concat(processed_chunks, dim="time")

    ds_final.coords['ls_distance'].attrs = {'long_name': 'Distance to Lakeshore', 'units': 'km'}
    ds_final.coords['fr_distance'].attrs = {'long_name': 'Distance to Front (Along Track)', 'units': 'km'}

    return ds_final