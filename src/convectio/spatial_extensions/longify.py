from geopy.distance import geodesic
import pandas as pd
import warnings
from convectio import Transect


def get_distance(
    transect, reference_longitude: float = None, reference_latitude: float = None
):
    """Gets the geodesic distance between lat/lon pairs using geopy.

    Args:
        transect (Transect object): Transect object created my mmesopy.
        reference_longitude (float): Defaults to first point of dataset.
        reference_latitude (float): Defaults to first point of dataset.

    Returns: Pandas series for appending to a dataframe if so wished.
    """

    if not isinstance(transect, Transect):
        raise TypeError(
            "This function requires type Transect, not {}".format(transect.type)
        )

    transect_df = transect.export_pandas()

    ## Latitude and Longitude series

    if len(transect_df) == 0:
        return pd.Series([], dtype=float)

        # Check if a starting point was provided
    if reference_latitude is None and reference_longitude is None:
        warnings.warn(
            "No reference coordinates provided! Using the closest data point as the origin.",
            UserWarning,
        )
        reference_latitude = transect_df["lat"].iloc[0]
        reference_longitude = transect_df["lon"].iloc[0]

    if reference_latitude is None and reference_longitude is not None:
        print(
            "NOTICE: No latitude given; assuming straight-line longitudinal approximation."
        )
        reference_latitude = transect_df["lat"].iloc[0]

    distances = []

    current_point = (reference_latitude, reference_longitude)

    for i in range(len(transect_df)):
        next_point = (transect_df["lat"].iloc[i], transect_df["lon"].iloc[i])

        # Geodesic distance handles the curvature of the earth
        segment_distance = geodesic(current_point, next_point).m
        distances.append(segment_distance)
        current_point = list(current_point)
        current_point[0] = next_point[0]
        current_point = tuple(current_point)

    transect["distances"] = distances

    return pd.Series(distances)
