"""
scale_space_tree_detect.py
====================================
The module for tree detection using a scale space method.
Uses Near-Infrared aerial photography, to calculate vegetation indices.
These are then used to scan the image for Gaussian features at different scales, with various properties.
From these, Gaussian blobs are detected.
These Gaussian blobs in NDVI can then be assumed to be trees.

TODO: Keep blobs where terrein > x m 
"""
import os
import numpy as np
import pandas as pd
import matplotlib
from math import sqrt, pi
from matplotlib import pyplot as plt
from skimage.feature import blob_dog, blob_log, blob_doh
from TreeDetect.data_preparation.preprocess import split_channels, clamp_values
from TreeDetect.data_preparation.geo_indices import calculate_ndvi, calculate_savi, calculate_evi2
from TreeDetect.input_output.coordinate_utils import points_to_coords

def log_blob_detect(img, **kwargs):
    '''
    Applies the scale-space method for detecting blobs in an image that have tree-like intensity profiles. That is:

    1. Blob-detect the original image using the laplacian of the gaussian method in scale-space.
    2. Filter the found blobs: must be >= ndvi threshold, must not overlap, and must have gaussian blob-like intensity profile in scale-dimension
    
    Parameters
    ----------
    img : numpy array of floats between 0-1
        1-channel image to detect features in (probably should be the ndvi)
    min_sigma: scalar or sequence of scalars, optional
        The minimum standard deviation for Gaussian kernel. Keep this low to detect smaller blobs. 
        Can be given for each axis as a sequence, or as a single number, in which case it is equal for all axes.
    max_sigma: scalar or sequence of scalars, optional
        The maximum standard deviation for Gaussian kernel. Keep this high to detect larger blobs. 
        Can be given for each axis as a sequence, or as a single number, in which case it is equal for all axes.
    num_sigma: int 
        The number of intermediate values of standard deviations to consider between min_sigma and max_sigma.
    overlap: float between 0 and 1, optional
        If the area of two blobs overlaps by a fraction greater than threshold, the smaller blob is eliminated.
    threshold_rel: float or None, optional
        Lower bound for scale space maxima, under which they are ignored. Reduce to detect blobs with lower intensity. 
        
    
    Returns
    -------
    blobs : list of (x,y,scale) tuples
        the found blobs
    '''
    blobs = blob_log(img, **kwargs)
    blobs[:, 2] *= sqrt(2)
    return blobs

def scale_space_tree_detect(images, folders, settings, filename, bbox):
    '''
    Does a scale space tree detection analysis.
    i.e. it will detect individual trees using the ndvi and a gaussian scale-space analysis with tree intensity profile modeling.
    Then it will cluster these points based on their distance.
    Then it will make hulls / polygons from the points in each clusters.
    
    Parameters
    ----------
    images : dictionary with str as keys, and numpy arrays as values
        contains the rgb, nir, dsm and dtm images. Keys are the, e.g. 'rgb', 'nir', 'dsm', 'dtm'
    folders : dictionary with str as keys, and str as values
        contains the paths to the folders where files should be saved. Keys: 'rgb', 'nir', 'mask', 'base', etc.
    settings : attribute-dictionary with str as keys and dynamic values 
        dictionary with the settings used in this analysis. As an attribute dictionary, it can be accessed using dot-notation (e.g. settings.key = value)
    filename : str 
        the basename (no extention or full path) of the image we're currently looking at
    bbox : tuple of 4 floats
        the bounding box of coordinates of the area we're currently looking at, format: (lat1, lon1, lat2, lon2)

    Returns
    -------
    result : tuple 
        the analysis-result (currently: a list of tree-blobs as [lat,lon,size], their clustering, and the hulls/polygons thereof)
    '''
    print('doing scale space tree detection')

    if not settings['general']['redo_if_already_processed']:
        filepath = os.path.join(folders['results'], '{0}.csv'.format(filename))
        if os.path.exists(filepath):
            return None

    ######################################
    # Get settings
    ######################################

    # pre-processing and feature settings
    data_settings = settings['data']
    pixel_size = data_settings['pixel_size'] # how many real-life meters does one pixel in the image represent?
    nir_max_value = data_settings['api']['nir']['max_value']

    # scales and blob detection settings
    scalespace_settings = settings['scale_space']
    minrad = scalespace_settings['minrad'] # minimum diameter of tree crown in meters
    maxrad = scalespace_settings['maxrad'] # max diameter of tree crown in meters
    steprad = scalespace_settings['steprad'] # step size for the scale range (between min and max diameter) in meters
    threshold_rel_blob_peaks = scalespace_settings['threshold_rel_blob_peaks'] # relative threshold, when a peak is deemed a local maximum rather than randomness
    blob_overlap_threshold = scalespace_settings['blob_overlap_threshold'] # the ratio/amount of overlap two blobs can have before being pruned.
    
    # output settings
    save_results = settings['general']['save_results']
    save_fileformat = scalespace_settings['output_file_format']

    ######################################
    # Preprocess and get features
    ###################################### 

    # preprocess nir image
    nir_img = images['nir']
    nir_img = clamp_values(nir_img, nir_max_value)
    nir, red, green = split_channels(nir_img)
    ndvi = calculate_ndvi(nir, red)

    # which features to use for blob detect
    img_for_blob_detect = ndvi

    # generate scales used for generating the scale space
    minradpix = minrad / pixel_size # minimum radius of tree crowns in pixels
    maxradpix = maxrad / pixel_size # max radius of tree crown in pixels
    difrad = maxrad - minrad # difference in gaussian blob radius in meters
    difradpix = difrad / pixel_size # difference in radius in pixels
    stepradpix = steprad / pixel_size # step size for the scale range (between min and max radius) in pixels
    nscales = int(difradpix / stepradpix) # how many scales we must create between min and max radius

    ######################################
    # Do the scale-space analysis
    ######################################

    # do scale-space tree-like-feature detection
    blobs = []

    blobs = log_blob_detect(img = img_for_blob_detect, 
        min_sigma = minradpix,
        max_sigma = maxradpix,
        num_sigma = nscales,
        overlap = blob_overlap_threshold,
        threshold_rel = threshold_rel_blob_peaks
    )

    ######################################
    # Save, and return results
    ######################################

    blobs = blobs.astype(np.float32)
    blobs[:,0:2] = np.flip(blobs[:,0:2], axis=1) # flip x and y coordinates
    blobs[:,1] = ndvi.shape[0] - blobs[:,1] # flip vertical pixels coordinates
    
    blobs[:,0:2] = points_to_coords(blobs[:,0:2], pixel_size, bbox) # substitute the pixel coordinates with their longitude/latitude coordinates
    blobs[:,2] = np.multiply(blobs[:,2], pixel_size) # substitute the radius of the blobs in pixels, to their radius in meters
    blobs = np.c_[blobs, blobs[:,2] * 2] # add column for diameter
    blobs = np.c_[blobs, blobs[:,2] * 2 * pi] # add column for circumference
    blobs = np.c_[blobs, blobs[:,2]**2 * pi] # add column for area of blobs

    result = blobs # result of analysis: detected blobs as [lat,lon,radius], their clusterings into areas, and the hulls thereof

    # save results
    if save_results:
        print('saving results')
        filepath = os.path.join(folders['results'], f'{filename}.{save_fileformat}')
        np.savetxt(filepath, blobs, delimiter=",", header = "longitude,latitude,radius,diameter,circumference,area", comments='')

    return result
