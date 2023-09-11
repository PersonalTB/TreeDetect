"""
coordinate_utils.py
====================================
The module responsible for handling generic functions dealing with coordinates.
Translates from pixels, and physical distances to coordinates and vice versa.
Also used to cut up larger bounding boxes into manageable chunks for analysis.
"""
import math
import pandas as pd
import numpy as np

def haversine(lon1, lat1, lon2, lat2):
    '''
    Returns the haversine distance, i.e. the distance between two lon/lat coordinates in meters
    See also: https://rosettacode.org/wiki/Haversine_formula#Python

    Parameters
    ----------
    lon1 : float
        the longitude of the first coordinate 
    lat1 : float
        the latitude of the first coordinate
    lon2 : float
        the longitude of the second coordinate
    lat2 : float
        the latitude of the second coordinate

    Returns
    -------
        dist: float
            the distance between the two coordinates in meters

    '''

    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))

    km_to_m = 1000
    radius_of_earth_in_km = 6371
    dist = c * radius_of_earth_in_km * km_to_m

    return dist

def haversine_inv(lon1, lat1, dx=0, dy=0):
    '''
    Returns new lon lat coordinate from beginpoint and offset in meters

    Parameters
    ----------
    lon1 : float
        longitude of the beginpoint
    lat1 : float
        latitude of the beginpoint
    dx : float
        meters in the west-east direction at which we want to find the coordinates of the endpoint
    dy : float
        meters in the north-south direction at which we want to find the coordinates of the endpoint

    Returns
    -------
    coord: tuple of 2 floats
        the longitude/latitude coordinates, which are dx,dy meters from the input coordinate 

    '''
    m_to_km = 1000
    radius_of_earth_in_km = 6371
    dy = dy/m_to_km # convert to km
    dx = dx/m_to_km
    lon2 = lon1 + (dx / radius_of_earth_in_km) * (180/math.pi) / np.cos(lat1*math.pi/180)
    lat2 = lat1 + (dy / radius_of_earth_in_km) * (180/math.pi) 
    coord = (lon2, lat2)
    return coord

def check_bbox(bbox):
    """
    Makes sure that the bbox is valid for the wms server. 
    i.e. that the lat and longitue coordinates go from low to high
    The bounding box's format for both params and return is: 

    Parameters
    ----------
    bbox : tuple of 4 floats
        coordinates of the start and end points to be checked. Format: (longitude_1, latitude_1, longitude_2, latitude_2)

    Returns
    -------
    bbox_corrected : tuple of 4 floats
        bounding box with coordinates of start and end points, from low to high. Format: (low_longitude, low_latitude, high_longitude, high_latitude)

    """
    lon1 = bbox[0]
    lat1 = bbox[1]
    lon2 = bbox[2]
    lat2 = bbox[3]
        
    if lon2 < lon1:
        lon1, lon2 = lon2, lon1
    
    if lat2 < lat1:
        lat1, lat2 = lat2, lat1
        
    bbox_corrected = (lon1, lat1, lon2, lat2)

    return bbox_corrected


def cut_up_bbox(bbox_full, im_size_out, pixel_size):

    """
    Determine how many picture requests to make for the total bounding box, i.e.:
    how many vertical and horizontal steps to take
    how big those steps must be in longitude/latitude terms

    Parameters
    ----------
    bbox_full : tuple of 4 floats
        the wanted bounding box in the format (start_longitde, start_latitude, end_longitude, end_latitude), must go from low-high
    im_size_out : int
        the wanted amount of PIXELS per cut-up output image
    pixel_size : float
        the size that each pixel represents irl, in metres

    Returns
    -------
    coord_df : pandas dataframe
        dataframe with coordinates of each 'sub-bounding box', with the format: {'filename', 'lon min', 'lat min', 'lon max', 'lat max'}
    """

    map_width_meter = haversine(
        bbox_full[0], 
        bbox_full[1],
        bbox_full[2], 
        bbox_full[1]
    ) 

    map_height_meter = haversine(
        bbox_full[0], 
        bbox_full[1],
        bbox_full[0], 
        bbox_full[3]
    ) 

    map_height_pixel = map_height_meter / pixel_size
    map_width_pixel = map_width_meter / pixel_size

    steps_vertical = int(np.ceil(map_height_pixel/im_size_out))
    steps_horizontal = int(np.ceil(map_width_pixel/im_size_out))

    lon1, lat1 = bbox_full[0], bbox_full[1]
    lon2, lat2 = haversine_inv(
        lon1, 
        lat1,
        dx=im_size_out*pixel_size, 
        dy=im_size_out*pixel_size
    )
    
    lonfinal, latfinal = haversine_inv(
        lon1, 
        lat1,
        dx=im_size_out*pixel_size*steps_horizontal, 
        dy=im_size_out*pixel_size*steps_vertical
    )

    total_bounding_box = (lon1, lat1, lonfinal, latfinal)

    stepsize_lon = lon2-lon1
    stepsize_lat = lat2-lat1

    lon_max, lat_max = bbox_full[2], bbox_full[3]

    bboxes = [] 
    coords_dict = {'filename':[], 'lon min': [], 'lat min': [], 'lon max': [], 'lat max': []}

    for i in range(steps_horizontal):
        
        lon = lon1 + i*stepsize_lon
        lon_new = lon + stepsize_lon
        
        for j in range(steps_vertical):
            
            lat = lat1 + j*stepsize_lat
            lat_new = lat + stepsize_lat
            
            bbox = (lon, lat, lon_new, lat_new)
            
            fname = '{0}_{1}'.format(i, j)
            bboxes.append(bbox)
                    
            coords_dict['filename'].append(fname)
            coords_dict['lon min'].append(lon)
            coords_dict['lat min'].append(lat)
            coords_dict['lon max'].append(lon_new)
            coords_dict['lat max'].append(lat_new)

    coord_df = pd.DataFrame(coords_dict, columns = ['filename', 'lon min', 'lat min', 'lon max', 'lat max'])
    
    return coord_df, total_bounding_box

def points_to_coords(points, pixel_size, bbox):
    '''
    Converts pixel-locations to coordinate locations.

    Parameters
    ----------
    points : numpy array of floats 
        array of pixel-coordinates, with each point in its rows, formatted as (x,y) in its columns, where x and y refer to pixel locations
    pixel_size : float 
        the size that a pixel represents in real life in meters
    bbox : tuple of 4 floats
        bounding box coordinates for the image in which these points were found, format (lon1, lat1, lon2, lat2)

    Returns
    -------
    coords: numpy array 
        array of coordinates in its rows, formatted as (lon, lat) in its columns
    '''

    lon1 = bbox[0]
    lat1 = bbox[1]

    points = np.multiply(points, pixel_size, casting = 'safe') # change each point's pixel coordinates in the image, to meters from the beginning
    coords = np.array([haversine_inv(lon1, lat1, points[b,0], points[b,1]) for b in range(points.shape[0])]) # get coords for each point

    return coords
