import numpy as np

def BR_transform(latitude: np.array, longitude: np.array, frontal_crossing: list, bndry_angle: float):
    """Generates local boundary-relative transform of 2-D onto 1-D vector using WGS84 Ellipsoid correction.

    Args:
        latitude (np.array): Array of latitudes
        longitude (np.array): Array of longitudes
        frontal_crossing (list; [latitude, longitude] (degrees)): list of latitude, longitude points of boundary crossing (origin point; 0,0)
        bndry_normal (float): Angle of boundary in degrees
        
    Returns:
        dist_BR (float): Distance (meters) relative to the frontal boundary point.
    """
    lat0 = frontal_crossing[0]
    lon0 = frontal_crossing[1]
    
    phi = np.radians(lat0)
    
    ### WGS implementation
    m_per_deg_lat = (111132.92 - 559.82 * np.cos(2 * phi) + 1.175 * np.cos(4 * phi))
    m_per_deg_lon = (111412.84 * np.cos(phi) - 93.5 * np.cos(3 * phi))
    
    y = (latitude - lat0) * m_per_deg_lat
    x = (longitude - lon0) * m_per_deg_lon
    
    
    # boundary-relative normal vector
    normal_rad = np.radians(bndry_angle + 90)
    
    # unit vector comps
    nx = np.sin(normal_rad)
    ny = np.cos(normal_rad)
    
    
    # boundary relative distance (meters)
    dist_BR = (x * nx) + (y * ny)
    
    return dist_BR