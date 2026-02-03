### Custom calculations and derivate functions for MM data
### Written by Kyle Brooks; Sep. 2025

import numpy as np
import math as m
import pandas as pd


def thetae(TC, TdC, PhPa):
    """Calculates the equivalent potential temperature (theta-e) given temperature, dew point, and pressure.
       This function requires numpy to be installed/imported.

    Args:
        TC (float): Temperature in Celsius
        TdC (float): Dew point temperature in Celsius
        PhPa (float): Pressure in hPa

    Returns:
        float: Equivalent potential temperature (theta-e) in K
    """

    # Constants
    Aliq = 2.53e11  # Pa
    Bliq = 5.42e3  # J/kg
    Rd = 287.058  # Gas constant for dry air (J/kg·K)
    Cp = 1004  # Specific heat of dry air at constant pressure (J/kg·K)
    epsilon = 0.622  # Ratio of molecular weights (Mv/Md)
    L = 2.5e6  # Latent heat of vaporization for water (J/kg)

    # Temperature conversions
    temp = TC + 273.15  # Temperature in Kelvin
    Td = TdC + 273.15  # Dew point temperature in Kelvin

    # Pressure conversion to Pascals
    pres = PhPa * 100  # Convert pressure to Pa

    # Water vapor mixing ratio
    qv = Aliq * epsilon / (pres * np.exp(Bliq / Td))

    # Potential temperature
    theta = temp * (100000 / pres) ** (Rd / Cp)

    # Moisture variables
    moist = Td
    Rw = 461.5

    # Relative humidity
    rh = 100 * np.exp((Rw / (L * temp)) * (1 - (temp / moist)))
    sat_vapor_pressure = Aliq * np.exp(-Bliq / temp)

    # Actual vapor pressure
    vapor_pressure = sat_vapor_pressure * (rh / 100)

    # Vapor mixing ratio
    vapor_mixing_ratio = qv
    sat_mixing_ratio = (sat_vapor_pressure) / (pres - sat_vapor_pressure)

    # Dewpoint
    dewpoint = moist

    # LCL Calculation
    t_lcl = (TdC - ((0.212 + (0.001571 * TdC) - (0.000436 * TC)) * (TC - TdC))) + 273.15

    # # Equivalent potential temperature (theta-e)
    thetae = theta * np.exp((L * vapor_mixing_ratio) / (Cp * t_lcl))
    # thetaes = theta * np.exp((L * sat_mixing_ratio) / (Cp * temp))

    return thetae


def stat_mslp(p_station, z_station, temp_c, dp_c, lat_deg):
    """
    Adjusts station pressure to Mean Sea Level Pressure (MSLP) using the
    Laplace Barometric Formula shown in your image. Replaced original correction
    this more robust version

    Parameters:
    -----------
    p_station : float
        Station pressure (hPa or mb).
    z_station : float
        Station elevation (meters).
    temp_c : float
        Station temperature (Celsius).
    dp_c : float
        Station dewpoint (Celsius).
    lat_deg : float
        Station latitude (Degrees).

    Returns:
    --------
    float : Mean Sea Level Pressure (hPa).
    """

    # --- Constants ---
    K = 18400.4  # Hypsometric constant for this specific log10 form
    alpha = 0.003661  # Coefficient of thermal expansion (1/273.15)
    k_lat = 0.00266  # Gravity constant for latitude correction
    R_earth = 6371000  # Radius of Earth in meters

    # --- 1. Calculate Vapor Pressure (e) ---
    # Using Bolton's approximation (1980) because it's robust
    # e in hPa
    e = 6.112 * np.exp((17.67 * dp_c) / (dp_c + 243.5))


    #### LATER VERSIONS SHOULD ADD ABILITY TO ENTER REAL LAPSE RATES
    # Calculate Mean Column Temperature (theta_m)
    # This is the biggest pain in the ass. The "standard" way is to assume
    # a lapse rate of 6.5 C/km between the station and sea level. This changes
    # between countries and even CWAs
    # theta_m = (T_station + T_sealevel) / 2
    # T_sealevel approx = T_station + (0.0065 * Elevation)
    t_lapse_adjustment = (0.0065 * z_station) / 2
    theta_m = temp_c + t_lapse_adjustment

    #  Compute the correction factors

    # Temperature Term: (1 + alpha * theta_m)
    term_temp = 1 + (alpha * theta_m)

    # Humidity Term: 1 / (1 - 0.378 * (e / p_station))
    # Note: 0.378 is roughly (1 - epsilon)/epsilon where epsilon = 0.622
    term_humidity = 1 / (1 - 0.378 * (e / p_station))

    # Latitude/Gravity Term: 1 / (1 - k * cos(2 * phi))
    lat_rad = np.radians(lat_deg)
    term_gravity = 1 / (1 - k_lat * np.cos(2 * lat_rad))

    # Vertical Gradient Term: (1 + Z / R)
    term_vertical = 1 + (z_station / R_earth)

    # Combine denominator
    denominator = K * term_temp * term_humidity * term_gravity * term_vertical

    # --- 4. Solve the Equation ---
    # log10(p0) = log10(p) + (Z / denominator)
    log_p0 = np.log10(p_station) + (z_station / denominator)

    # Convert back from log10
    p0 = 10 ** log_p0

    return p0


def wind_comps(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates the u and v wind components from speed and direction.

    Args:
        df: A pandas DataFrame containing 'wind_speed' and 'wind_dir' columns.
            Wind direction should be in degrees (0=N, 90=E, etc.).

    Returns:
        The input DataFrame with new 'u' and 'v' columns added.
    """
    # Convert wind direction from degrees to radians
    wind_direction_rad = np.deg2rad(df["wind_dir"])

    # Calculate u and v components.
    df["u"] = -df["WindSpeed"] * np.sin(wind_direction_rad)
    df["v"] = -df["WindSpeed"] * np.cos(wind_direction_rad)

    return df
