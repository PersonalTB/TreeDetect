"""
preprocess.py
====================================
The module for preprocessing steps for images to create features useful for later processing.
Includes a preprocessing of the images to split, normalize, and replace null values in the images.
And a further preprocessing method to generate vegetation indices and a height difference map.
"""
import numpy as np

def clamp_values(img, max_value=255):
  """
  Preprocesses the image into representations useful for further processing.
  i.e.: clamps the values in the image between 0 and 1 based on the max_value

  Parameters
  ----------
  img : numpy matrix of floats 
      matrix containing values.
  max_value: int
      int value specifying the max value that a value in the matrix can take. e.g. for 8-bit channels, 256 possible values per pixel, so max_value is 255

  Returns
  -------
  result : numpy matrix of floats
      tuple with n split channels
  """
    
  img = img / max_value    
  return img
  
def split_channels(img):
  """
  Preprocesses the image into representations useful for further processing.
  i.e.: clamps the values in the image between 0 and 1 based on the max_value

  Parameters
  ----------
  img : numpy matrix of floats with 3 dimensions.
      matrix containing values.

  Returns
  -------
  result : list of numpy matrix of floats
      list with n split channel matrices
  """
  
  assert len(img.shape) == 3
  return [img[:,:,i] for i in range(img.shape[2])]
  