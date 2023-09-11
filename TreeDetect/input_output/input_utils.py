"""
io_utils.py
====================================
The module used for input/output. 
Used for loading pre-fetched data from the hard drive, or to fetch them from WMS services.
Also used for saving and exporting images and analysis results.
"""
import os
import numpy as np
import pandas as pd
import skimage
from skimage import io
import rasterio
import yaml

def load_data(folders, settings, filename, bbox, wmses):
    """
    Try to fetch images from hard drive if possible, else fetch them from wms

    Parameters
    ----------
    folders : dictionary with str as keys and values
        dictionary with the quick-keys and the filepath to the data and output saving folders. E.g. {'rgb' : path_to_rgb_img_folder, 'mask' : ...}
    settings : dictionary with str as keys, and dynamic values 
        dictionary with the settings used in this session
    filename : str
        base filename (no extension and path), format: x_y, the indices of the current horizontal and vertical step/slice-picture
    bbox : tuple of 4 floats
        bounding box of the sub-area to-be-fetched from the wms services in this method, format: (longitude_min, latitude_min, longitude_max, latitude_max)
    wmses : dictionary with str as keys, and OWSLib.WMS and OWSLib.WCS services as values
        dictionary with the WMS/WCS clients to fetch the data with, one for each data to be fetched (e.g. rgb, nir, dsm, dtm)

    Returns
    -------
    images : dictionary with str as keys and numpy n-d arrays as values
        dictionary with 'rgb' and 'nir' (3-channel 2-d arr of floats), 'dsm' and 'dtm' (1-channel 2-d arr of floats) images
    status : str
        the return status of the loading ('loaded' when images have successfully loaded; or 'load_fail' if the loading failed)
    """

    images = {}
    status = 'loading'
    save_wms_data_to_hard_drive = settings['general']['save_wms_data_to_hard_drive']

    if save_wms_data_to_hard_drive and images_already_saved(folders, filename, settings):
        try:
            images = get_images_from_hard_drive(folders, settings, filename)
            status = 'loaded' # if successfully loaded from hard drive, set status to loaded
        except Exception as e:
            print(e)
            status = 'retry' # if image load from hard drive failed, retry from wms source
    elif status == 'loading' or status == 'retry':
        try:
            images = get_images_from_wms_service(wmses, settings, bbox)
            if save_wms_data_to_hard_drive:
              save_images(images, folders, filename, settings)
            status = 'loaded' # if successfully loaded from wms service, set status to loaded
        except Exception as e:
            print(e)
            status = 'load_fail'

    return images, status

def images_already_saved(folders, filename, settings):
    """
    Determine if a sub-bounding box (corresponding to the filename) has already been fetched and saved.

    Parameters
    ----------
    folders : dictionary with str as key and values
        dictionary containing paths to folders. E.g. {'rgb' : path_to_rgb_img_folder, 'mask' : path_to_mask_img_folder}
    filename : str
        base filename (no extension and path), format: x_y, the indices of the current horizontal and vertical step of the cut-up bounding box
    settings : dict
        dictionary with the settings of this session

    Returns
    -------
    already_saved : bool
        whether or not the rgb, nir, dsm and dtm data has been saved on the hard-drive in the respective folders
    """

    # iterate over all apis, see if their data has already been fetched for this bbox
    for api_key, api_settings in settings['data']['api'].items():
        if api_settings['use']:
            folder_path = folders[api_key]
            save_format = api_settings['save_format']
            img_path = os.path.join(folder_path, f'{filename}.{save_format}')
            already_saved = os.path.exists(img_path)
            if not already_saved: 
                return False
    
    # True if all the images that we need to use for the analyses are downloaded
    return True

def get_todo_filenames(coord_df, todo_filepath):
    """
    From the file with entries to filenames that should be retried, find out which indices in the coord_dataframe should then be retried.

    Parameters
    ----------
    - coord_df : pandas dataframe
        dataframe with coordinates of each 'sub-bounding box' in its rows, format of columms: {'filename', 'lat min', 'lon min', 'lat max', 'lon max'}
    - todo_filepath : string
        path to the file with filenames that should be analyzed

    Returns
    -------
    indices : list of int
        list of indices of the coord_df rows that have to be retried
    """

    indices = []

    try:

        if os.path.exists(todo_filepath):

            try_df = pd.read_csv(todo_filepath)

            if 'filename' not in try_df.columns.values or len(try_df['filename']) == 0:
                print('There is no filename column in todo csv file, or there are no entries in the column. Using the full set.')
                return None

            for try_el in try_df['filename']:
                if try_el in coord_df['filename'].values:
                    ind = coord_df.index[coord_df['filename'] == try_el]
                    indices.append(ind.tolist()[0])
                else:
                    print('{0} not in coords.'.format(try_el))

            return indices

    except Exception as e:
        print(e)
        print('Something went wrong in the todo file loader. Using the full set instead.')
        return None

def get_images_from_hard_drive(folders, settings, filename, use_wms):

    """
    Reads images from the hard drive, based on their PATHS.

    Parameters
    ----------
    folders : dictionary with str as key and values
        dictionary containing paths to folders. E.g. {'rgb' : path_to_rgb_img_folder, 'mask' : path_to_mask_img_folder}
    settings : dictionary with str as keys, and dynamic values 
        dictionary with the parameters used in this session
    filename : str
        base filename (no extension and path), format: x_y, the indices of the current horizontal and vertical step/slice-picture
    use_wms : dictionary with str as key and bool as values
        dictionary specifying whether to use a certain wms data or not by their quick-key. E.g. {'rgb':False, 'nir':True, 'height':False} will ONLY use NIR

    Returns
    -------
    images : dictionary with str as keys and numpy n-d arrays as values
        dictionary with 'rgb' and 'nir' (3-channel 2-d arr of floats), 'dsm' and 'dtm' (1-channel 2-d arr of floats) images

    """
    print('Fetching images from hard drive')

    # put all images into a container for easy lookup
    images = {}

    # the full filepaths for the images for the current sub-box to look at

    for api_key, folder_path in folders.item():
        api_settings = settings['data']['api'][api_key]
        filetype = api_settings['save_format']
        img_path = os.path.join(folders[api_key], f'{filename}.{filetype}')
        img_read_kwargs = ['pilmode', 'as_gray'] 
        api_kwargs = {arg: api_settings[arg] for arg in img_read_kwargs if arg in api_settings}
        img = io.imread(rgb_img_name, **api_kwargs)
        images[api_key] = img

    return images

def create_folders(root_folder, param_str, settings):
    """
    Creates folders for saving the data and the output of the methods.

    Parameters
    ----------
    root_folder : str
        path in which the data folder should be stored. Default: the main working directory.
    param_str : str
        a hash-string representation for the current parameter settings (so that the method doesn't have to fetch the same area twice)
    settings : dict
        a dictionary containing the settings of this analysis

    Returns
    -------
    folders : dict with str as keys and values
        dictionary with quick-keys and the filepath to data and output saving folders. E.g. {'nir' : path_to_nir_img_folder, 'results' : ...}
    """

    # determine the paths to the folders to store the data and results of the analyses to
    data_folder = os.path.join(root_folder, 'data')
    base_folder = os.path.join(data_folder, param_str)
    result_folder = os.path.join(base_folder, 'results')

    # put the paths inside a container dictionary for easy-lookup later
    folders = {
        'root':root_folder,
        'data':data_folder,
        'base':base_folder,
        'results':result_folder,
    }

    # folders to save intermediate data to
    if settings['general']['save_wms_data_to_hard_drive']:
        for api_key, api_values in settings['data']['api'].items():    
            if api_values['use']: 
                api_folder = os.path.join(base_folder, api_key)
                folders[api_key] = api_folder

    for folder_key, folder_path in folders.items():
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)

    return folders

def save_images(images, folders, filename, settings):
    """
    Saves images to their corresponding folders.

    Parameters
    ----------
    images : dictionary with str as keys and numpy n-d arrays as values
        dictionary with 'rgb' and 'nir' (3-channel 2-d arr of floats), 'dsm' and 'dtm' (1-channel 2-d arr of floats) images
    folders : dictionary with str as keys and values
        dictionary with the quick-keys and the filepath to the data and output saving folders. E.g. {'rgb' : path_to_rgb_img_folder, 'mask' : ...}
    filename : str
        base filename (no extension and path), format: x_y, the indices of the current horizontal and vertical step/slice-picture
    settings : dict
        dictionary with the settings used for the current session
    """
    
    # save the images we fetched from the wms (if we fetched them)
    for key, image in images.items():
        folder = folders[key]
        save_format = settings['data'][key]['save_format']
        filepath = os.path.join(folder, f'{filename}.{save_format}')
        skimage.io.imsave(filepath, image)

def get_images_from_wms_service(wmses, settings, bbox):
    """
    Fetches the images from wms and wcs services.

    Parameters
    ----------
    wmses : dictionary with str as keys, and OWSLib.WMS and OWSLib.WCS services as values
        dictionary with the WMS/WCS clients to fetch the data with, one for each data to be fetched (e.g. rgb, nir, dsm, dtm)
    settings : dictionary with str as keys, and dynamic values 
        dictionary with the parameters used in this session
    bbox : tuple of 4 floats
        bounding box of the area to-be-fetched from the wms services in this method, format: (longitude_min, latitude_min, longitude_max, latitude_max)
    
    Returns
    -------
    images : dictionary with str as keys and numpy n-d arrays as values
        dictionary with 'rgb' and 'nir' (3-channel 2-d arr of floats), 'dsm' and 'dtm' (1-channel 2-d arr of floats) images
    """
    print('Fetching images from wms services')

    # get relevant settings
    coord_crs = settings['data']['coord_crs'] # coordinate reference frame of the images to fetch
    im_size_out = settings['data']['im_size_out'] # size of the image in pixels per axis

    # initialize container dictionary for easy lookup of the data later
    images = {}

    # if we want to get a certain kind of image (rgb, nir, dsm, dtm) for our analysis, 
    # request the image for the current sub-box we're looking at
    # else, just return an empty numpy array

    for api_key, api_service in wmses.items():

        if settings['data']['api'][api_key]['use']:
            
            img = None
            api_settings = settings['data']['api'][api_key]

            if api_settings['servicetype'] == 'WebMapService': 
                img_f = api_service.getmap(
                            layers=[api_settings['layer']],                
                            srs=coord_crs,
                            bbox=bbox,
                            size=(im_size_out,im_size_out),
                            format=api_settings['format']
                            )
                img = io.imread(img_f.read(), plugin='imageio')

            else:
                raise ValueError('Loading data from services other than WebMapService is not implemented.')

            images[api_key] = img

    return images

def load_conf(path):
    conf_dict = {}
    with open(path, "r", encoding = "utf-8") as yaml_file:
        conf_dict = yaml.safe_load(yaml_file)
    return conf_dict
