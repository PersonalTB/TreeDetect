"""
csv_post_process.py
====================================
The module for post processing the analysis results from the scale space tree detect methods.
Used to make a big csv file from smaller sub-files.
"""
import os
import glob
import numpy as np
import pandas as pd

def make_big_csv_file_from_results_folder(params, folders, settings):
    """
    Loads sub-files from a post-analysis results/mask folder, concatenates them into one big csv file, and then exports them.

    Parameters
    ----------
    params : dictionary with str as keys and dynamic values 
        dictionary with the parameters used in this analysis 
    folders : dictionary with str as keys and values
        dictionary with paths to the folders where the data and results of the analysis have been saved for easy acces for post-processing
    settings : attribute-dictionary with str as keys and dynamic values 
        dictionary with the settings used in this analysis. As an attribute dictionary, it can be accessed using dot-notation (e.g. settings.key = value)
    """
    filename = 'full'
    savepath = os.path.join(folders['results'], '{0}.csv'.format(filename))
    filepaths = glob.glob(os.path.join(folders['results'], '*_*.csv')) # get all filenames in the mask folder with the specified filetype

    frame = pd.concat([pd.read_csv(f) for f in filepaths], ignore_index=True)
    
    frame.to_csv(savepath)

    return savepath