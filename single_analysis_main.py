"""
single_analysis_main.py
====================================
The core module of the project.
Starts the analysis pipeline.
"""
from TreeDetect.input_output.input_utils import load_conf
from TreeDetect.input_output.output_utils import make_big_csv_file_from_results_folder
from TreeDetect.analyses.analysis_pipeline import initialize_analysis, analysis_pipeline
from TreeDetect.analyses.scale_space_tree_detection import scale_space_tree_detect

'''
Example usage of the analysis pipeline.
To check other areas, set the BBOX field in this script. See for example: https://boundingbox.klokantech.com/
To alter the analysis methods, set the ANALYSIS_METHOD in this script.
In order to show and save progress, and the results of the analyses, alter these fields accordingly as well.
'''

settings = load_conf('confs/conf.yml')
root_folder = '.'

# You can use https://boundingbox.klokantech.com/ (format: CSV RAW) to find bounding boxes for areas.
bbox = [5.9184681997,52.5527079202,5.9195896983,52.553360466] # Boomstraat, Posterholt, NL

folders, coord_df = initialize_analysis(bbox, settings, root_folder)

folders, succeeded, failed = analysis_pipeline(
                                settings = settings,
                                folders = folders, 
                                coord_df = coord_df, 
                                analysis_method = scale_space_tree_detect,
                                todo = None # set this to 'failed' if you only want to retry the failed tiles of a previous run
                                )

csv_filepath = make_big_csv_file_from_results_folder(folders, settings)
