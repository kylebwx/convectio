from pathlib import Path

import pandas as pd
import numpy as np
import geopy.distance


def rel_distance(transect, transect_dict):
    """
    Feature-relative coordinates calculated using geopy.distance
    Returns:
    Array column 0 LBF-relative distances; Array column 1 lake-relative distances
    """
    P_DIR = Path(__file__).resolve().parent
    ls_file = P_DIR.parent.parent / "data" / "gis" / "mci" / "mci_lakeshore.csv"

    #/home/kyle/PycharmProjects/convectio/src/data/gis/mci/mci_lakeshore.csv

    ls_coords = pd.read_csv(ls_file)

    infodict = transect_dict

    tr_lats = transect.lat.values
    lake_lats = ls_coords['lat'].values

    diff_matrix = np.abs(lake_lats[:, np.newaxis] - lake_lats[np.newaxis, :])
    idx = diff_matrix.argmin(axis=0)

    matched_lons = ls_coords['lon'].values[idx]
    matched_lats = ls_coords['lat'].values[idx]

    coords = np.column_stack((matched_lons, matched_lats))  # lakepoint for each coord
    tra_coords = np.column_stack((transect.lon.values, transect.lat.values))

    tr_points = zip(transect['lon'].values, transect['lat'].values)  # actual transect points

    l_dst = []
    for mm, lake in zip(tr_points, coords):
        d = geopy.distance.geodesic(mm, lake).km
        l_dst.append(d)

    dataset_date = str(pd.to_datetime(transect.time.values[0]).date())

    full_timestamp = f"{dataset_date} {infodict['lbf_time'][0]}"
    nearest_coord = transect.sel(time=full_timestamp, method='nearest')
    lbf_coord = (float(nearest_coord['lon'].values), float(nearest_coord['lat'].values))

    f_dist = []
    for mm in tra_coords:
        dst = geopy.distance.geodesic(mm, lbf_coord).km
        if mm[0] < lbf_coord[0]:
            dst = -dst
        f_dist.append(dst)

    transect['ls_distance'] = l_dst
    transect['fr_distance'] = f_dist

    return transect

