"""
analysis_pipeline.py
====================================
The module responsible for the main loop of the function.
Analyzes the terrain in a given bounding box.
Will first check and initialize all necessary files and folders (e.g. for saving analysis results into).
Will then determine the sub-chunks to analyze to make the analysis computationally manageable.
Then fetches and analyzes the data. It can use various analysis methods, from individual tree detection, to segmentation.
Finally, it will save a log on any failed data fetches/analyses.

All of the main settings used for this and the sub-analyses can and should be set in the SETTINGS.py file.
"""
import os
import datetime
import pandas as pd
import hashlib
import traceback 
import yaml
from owslib.wms import WebMapService
from TreeDetect.input_output.coordinate_utils import check_bbox, cut_up_bbox
from TreeDetect.input_output.input_utils import (create_folders, images_already_saved, 
    get_images_from_hard_drive, get_images_from_wms_service, 
    save_images, get_todo_filenames, load_data)

def analysis_pipeline(settings, folders, coord_df, analysis_method, todo = None):
    """
    The full analysis pipeline, with data-getter and analysis.
    It will fetch (and optionally store) the aerial photography and heightmap data, and execute any analysis methods that are given as a parameter
    If any of these fail, these failed instances will be saved so they can be retried later through todo_file.
    Note that you can also use todo_file to specify only those filenames that should be analyzed (also useful for testing, e.d.)

    Parameters
    ----------
    settings : attribute-dictionary with str as keys and dynamic values 
        dictionary with the settings used in this analysis. As an attribute dictionary, it can be accessed using dot-notation (e.g. settings.key = value)
    folders : dictionary with str as keys and values
        dictionary with paths to the folders where the data and results of the analysis have been saved for easy acces for post-processing
    coord_df : pandas dataframe
        dataframe with coordinates of each 'sub-bounding box', with the format: {'filename', 'lon min', 'lat min', 'lon max', 'lat max'}
    analysis_method : function-reference
        reference to analysis function. possibilities: do_segmentation_tree_detection, do_scale_space_tree_detection, do_detectree_tree_detection
    todo : string or None
        base filename (no path or extension) of the csv file with only those filenames to-be analyzed (e.g. 'failed', 'todo'); if None, will analyze all

    Returns
    -------
    folders : dictionary with str as keys and values
        dictionary with paths to the folders where the data and results of the analysis have been saved for easy acces for post-processing
    succeeded : list of str
        list of filenames that were successfully fetched and analysis
    failed : list of str
        list of filenames of which the getting or analysis failed
    """

    ######################################
    # Setup web map services
    ######################################

    # setup web map services and data sources for according to the settings.

    data_getters = {}
    for api_key, api_settings in settings['data']['api'].items():
        if api_settings['use']:
            if api_settings['servicetype'] == 'WebMapService':
                data_getters[api_key] = WebMapService(api_settings['url'], version=api_settings['version'])
            else: 
                raise ValueError("Invalid value in setting up data api client: can currently only be WebMapService.")

    ############################################################
    # Setup which sections of the map should be fetched
    ############################################################

    # Determine which sections of the map should be fetched
    total = list(range(len(coord_df))) # all 

    if todo is not None: # if we have input a file with entries to filenames that should be retried, only do those
        todo_filepath = os.path.join(folders['base'], '{0}.csv'.format(todo))
        print('using todo file: {0}'.format(todo))
        total_try = get_todo_filenames(coord_df, todo_filepath)
        if total_try is not None and len(total_try) > 0:
            total = total_try

    # for logging purposees
    succeeded = []
    failed = []
    starttime = datetime.datetime.now()
    done = 0

    ############################################################
    # Main loop - loop over sub-bboxes, fetch, and analyze
    ############################################################

    for c in total:

        print(f'Processing bbox: {done+1}/{len(total)}')

        coord = coord_df.iloc[c]
        lon = coord['lon min']
        lat = coord['lat min']
        lon_new = coord['lon max']
        lat_new = coord['lat max']

        print(coord)
        
        bbox = (lon, lat, lon_new, lat_new)
        filename = coord['filename']
        status = 'loading'

        ######################################
        # Fetch data
        ######################################

        try:
            
            # try to fetch images from hard drive if possible, else fetch them from wms
            images, status = load_data(folders, settings, filename, bbox, data_getters)
            
            # if the images have been loaded successfully, we can go on with the analysis
            if status == 'loaded':

                ######################################
                # Analyze data
                ######################################

                if analysis_method is not None:
                    
                    result = analysis_method(
                                    images = images, 
                                    folders = folders,
                                    settings = settings, 
                                    filename = filename, 
                                    bbox = bbox
                            )

                status = 'success' # if the analysis returned properly, we have a successful analysis!
                succeeded.append(filename)

            else:
              print('Images could not be loaded.')
              status = 'fail' # if images could not be loaded, the analysis failed
              failed.append(filename)

        ######################################
        # Exception handling inside loop
        ######################################

        except Exception as e:
            status = 'fail'
            failed.append(filename)
            tb = traceback.format_exc()
            print(tb)

        done += 1

        eta = ((datetime.datetime.now() - starttime)/done) * (len(total) - done)
        print(f'Done: {done}/{len(total)} - status: {status} - eta: {eta}')

      
    ######################################
    # Logging outside loop
    ######################################  

    print(f'\nDone! - total: {len(total)} - success: {len(succeeded)} - fail: {len(failed)}')

    if len(failed) > 0:
        print(f'FAILED: {failed}')

        failure_dict = {'filename':failed}
        failed_df = pd.DataFrame(failure_dict)

        if not os.path.exists(os.path.join(folders['base'], 'failed.csv')):
            failed_df.to_csv(os.path.join(folders['base'], 'failed.csv'), index = False)

    return folders, succeeded, failed # return params, paths to the resultant folder, with all analysis results, and logs

def initialize_analysis(bbox_img, settings, root_folder = '.'):
    """
    Will check and cut-up the bounding box for the image into manageable chunks.
    Also creates folders for stored images and results, and save the parameters and the cut-up bounding boxes.

    Parameters
    ----------
    bbox_img : tuple of floats
        bounding box of the entire area to be analyzed (which is yet to be cut-up into manageable images)
    settings : attribute-dictionary with str as keys and dynamic values 
        dictionary with the settings used in this analysis. As an attribute dictionary, it can be accessed using dot-notation (e.g. settings.key = value)
    root_folder : string
        the folder to where the data folder will be located. Default: this folder ('.')

    Returns
    -------
    settings : dictionary with str as keys and dynamic values 
        dictionary with the parameters used in this analysis 
    folders : dictionary with str as keys and values
        dictionary with paths to the folders where the data and results of the analysis have been saved for easy acces for post-processing
    coord_df : pandas dataframe
        dataframe with coordinates of each 'sub-bounding box', with the format: {'filename', 'lon min', 'lat min', 'lon max', 'lat max'}
    """

    ######################################
    # Check bbox for validity
    ######################################

    bbox_img = check_bbox(bbox_img)

    ######################################
    # Determine coordinates of bboxes
    ######################################

    # determine how to fetch the map for the total bounding box, chopped up in smaller sections, and save these to a csv
    
    im_size_out = settings['data']['im_size_out']
    pixel_size = settings['data']['pixel_size']
    coord_df, total_bounding_box = cut_up_bbox(bbox_img, im_size_out, pixel_size)

    ######################################
    # Create folders and log files
    ######################################

    param_str = hashlib.sha1((str(bbox_img) + str(settings)).encode()).hexdigest()
    print("MY HASH IS: {0}".format(param_str))

    folders = create_folders(root_folder, param_str, settings)

    settings_path = os.path.join(folders['base'], 'settings.yml')
    if not os.path.exists(settings_path):
        with open(settings_path, "w", encoding = "utf-8") as yaml_file:
            dump = yaml.dump(settings, default_flow_style = False, allow_unicode = True, encoding = None)
            yaml_file.write(dump)

    coord_path = os.path.join(folders['base'], 'coord.csv')
    if not os.path.exists(coord_path):
        coord_df.to_csv(coord_path, index = False)

    return folders, coord_df
