import numpy as np
import pandas as pd
import os
from .custom_math import mslp_calc
from metpy.units import units
from metpy.calc import wind_components
from mesopy import Transect


def center_difference(
    transect,
    variables: list = None,
    dt_vals_second: list = None,
    rolling_window_sec: float = None,
    transect_start_time: str = None,
    transect_end_time: str = None,
):

    # first, check for instancing on inputs; warn user if not correct

    if not isinstance(transect, pd.DataFrame):
        raise TypeError(
            "This function requires type Transect.DataFrame, not {}".format(
                transect.type
            )
        )

    # dt_vals_second can take either lists or np.ndarray; this check for either and warns user if not correct type
    if not isinstance(dt_vals_second, (list, np.ndarray)):
        raise TypeError(
            "'dt_vals_second' must be type np.array or list; got {}".format(
                dt_vals_second.type
            )
        )

    # dt_vals_second from np array to list for iterration
    if isinstance(dt_vals_second, np.ndarray):
        dt_vals_second = dt_vals_second.tolist()

    df = transect

    altimiter = df["pressure"].values / 100
    altitude = df["alt"].values
    temperature = df["fast_temp"].values - 273.15
    df["mslp"] = mslp_calc(altimiter, altitude, temperature)
    df["u_wind"], _ = wind_components(
        df["wind_speed"].values * units("m/s"), df["wind_dir"].values * units("deg")
    )

    sampling_interval_sec = df.index.to_series().diff().mean().total_seconds()

    transect_start = pd.to_datetime(transect_start_time)
    transect_end = pd.to_datetime(transect_end_time)

    df = df[(df.index >= transect_start) & (df.index <= transect_end)].copy()

    rolling_window_points = int(rolling_window_sec / sampling_interval_sec)
    df_smoothed = (
        df[variables].rolling(window=rolling_window_points, center=True).mean()
    )

    for dt_val_sec in dt_vals_second:
        dt_pts = int(np.round(dt_val_sec / sampling_interval_sec))
        dt_dir = f"dt_{dt_val_sec}"

        for var_idx, sel_var in enumerate(variables):

            derivative = (df[sel_var].shift(-dt_pts) - df[sel_var].shift(dt_pts)) / (
                2 * dt_pts * sampling_interval_sec
            )

            df["deriv_{}".format(sel_var)] = derivative

    return df
