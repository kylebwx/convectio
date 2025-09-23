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


def mslp_calc(pressure, height, temp):
    """Calculates MSLP from station pressure using NWS's simple calculation.

    Args:
        pressure (int or float): station pressure (hPa or mb)
        height (int or float): height of station ASL(meters)
        temp (int or float): temperature at station (degC)

    Returns:
        pressure_msl (int or float): Corrected MSLP (not accounting for moisture)
    """

    press_msl = pressure * (
        1 - (0.0065 * height) / (temp + 0.0065 * height + 273.15)
    ) ** (-5.257)

    return press_msl


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

    # Calculate u and v components. The negative sign is crucial because
    # wind direction is "from where" and the components point "to where".
    df["u"] = -df["WindSpeed"] * np.sin(wind_direction_rad)
    df["v"] = -df["WindSpeed"] * np.cos(wind_direction_rad)

    return df
