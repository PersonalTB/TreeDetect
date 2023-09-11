"""
vegetation_indices.py
====================================
The module responsible for generating vegetation indices from information gained from NIR imagery.
"""
import numpy as np

def calculate_ndvi(nir, red):
    """
    Calculates the Normalized Difference Vegetation Index (NDVI)
    Simple indicator for living vegetation in remote sensing. Chlorophill/photosynthesis sensitive.
    See also: https://en.wikipedia.org/wiki/Normalized_difference_vegetation_index

    *Background*
    - Reflected light can be split up in near-infrared and the rest (visible light).
    - Vegetation reflects near-infrared light more than visible light (as the latter is used during photosynthesis).
    - So, by looking at the difference at the reflected infrared light vs normal light, you can indicate vegetation.
    - This difference needs to be normalized by how much total light is reflected.
    - NDVI is the calculation that evaluates the above.

    Parameters
    ----------
    nir : numpy 2-d array of floats
        surface reflectance values of NIR light (channel 0 in NIR fake color images)
    red : numpy 2-d array of floats
        surface reflectance values of red light (channel 1 in NIR fake color images)

    Returns
    -------
    ndvi : numpy 2-d array of floats
        ndvi values, ranges from -1 to 1. Values of >0.2 or 0.3 typically indicates vegetation.   

    References
    ----------
    [1] Rouse, J.W, Haas, R.H., Scheel, J.A., and Deering, D.W. (1974) 'Monitoring Vegetation Systems in the Great Plains with ERTS.' Proceedings, 3rd Earth Resource Technology Satellite (ERTS) Symposium, vol. 1, p. 48-62. https://ntrs.nasa.gov/archive/nasa/casi.ntrs.nasa.gov/19740022592.pdf
    [2] Kriegler, F.J., Malila, W.A., Nalepka, R.F., and Richardson, W. (1969) 'Preprocessing transformations and their effects on multispectral recognition.' Proceedings of the Sixth International Symposium on Remote Sensing of Environment, p. 97-131. 
    """
    ndvi = (nir - red) / (nir + red)
    return ndvi


def calculate_evi(nir, red, blue, c1 = 6, c2 = 7, l = 1, g = 2.5, clip = False):
    """
    Calculates the Enhanced Vegetation Index (EVI)
    See also: https://en.wikipedia.org/wiki/Enhanced_vegetation_index
    Enhanced version of the NDVI which also detects the light reflectance/absorbsion traits of green vegetation.
    But: EVI also takes into account various canopy (boomkruin) effects, and atmospheric disturbances.

    Parameters
    ----------
    nir : numpy 2-d array of floats
        surface reflectance values of NIR light (channel 0 in NIR fake color images)
    red : numpy 2-d array of floats
        surface reflectance values of red light (channel 1 in NIR fake color images)
    l : float
        an adjustment factor accounting for tree canopy effects, default as per the MODIS-EVI algorithm: 1
    c1 : float
        coefficient accounting for atmospheric disturbances in the red-band, default as per the MODIS-EVI algorithm: 6
    c2 : float
        coefficient accounting for atmospheric disturbances in the blue-band, default as per the MODIS-EVI algorithm: 7.5
    g : float
        an over-all gain factor (an over-all 'signal boost'), default as per the MODIS-EVI algorithm: 2.5
    clip - bool
        if set to True, it will bound the evi values to be between -1 and 1 like the ndvi
    
    Returns
    -------
    evi : numpy 2-d array of floats 
        the evi values, values are not bound to a min/max unless clip is True, values of >0.2 typically indicates vegetation
    
    References
    ----------
    [1] A. Huete, K. Didan, T. Miura, E. P. Rodriguez, X. Gao, L. G. Ferreira. Overview of the radiometric and biophysical performance of the MODIS vegetation indices. Remote Sensing of Environment 83(2002) 195-213 doi:10.1016/S0034-4257(02)00096-2.
    """
    evi = g * ((nir - red) / (nir + c1 * red - c2 * blue + l))
    if clip: evi = np.clip(evi, -1, 1)
    return evi


def calculate_evi2(nir, red, c = 2.4, l = 1, g = 2.5, clip = False):
    """
    Calculates the 2-band approximation of the Enhanced Vegetation Index (EVI2)
    See also: https://en.wikipedia.org/wiki/Enhanced_vegetation_index
    Enhanced version of the NDVI which also detects the light reflectance/absorbsion traits of green vegetation.
    But: EVI also takes into account various canopy (boomkruin) effects, and atmospheric disturbances.
    This is the 2-band approximation of the EVI. Reason: because nir sensors/images usually don't have a blue-band.

    Parameters
    ----------
    nir : numpy 2-d array of floats
        surface reflectance values of NIR light (channel 0 in NIR fake color images)
    red : numpy 2-d array of floats
        surface reflectance values of red light (channel 1 in NIR fake color images)
    l : float
        an adjustment factor accounting for tree canopy effects, default as per the MODIS-EVI algorithm: 1
    c : float
        coefficient accounting for atmospheric disturbances, default as per the MODIS-EVI algorithm: 2.4
    g : float
        an over-all gain factor (an over-all 'signal boost'), default as per the MODIS-EVI algorithm: 2.5
    clip - bool
        if set to True, it will bound the evi values to be between -1 and 1 like the ndvi
    
    Returns
    -------
    evi : numpy 2-d array of floats 
        the evi values, values are not bound to a min/max unless clip is True, values of >0.2 typically indicates vegetation

    References
    ----------
    [1] Jiang, Z., Huete, A. R., Didan, K. & Miura T. (2008). Development of a two-band Enhanced Vegetation Index without a blue band, Remote Sensing of Environment, 112(10), 3833-3845, doi:10.1016/j.rse.2008.06.006.
    """
    evi2 = g * ((nir - red) / (l + nir + c * red))
    if clip: evi2 = np.clip(evi2, -1, 1)
    return evi2


def calculate_savi(nir, red, l = 0.5):
    """
    Calculates the Soil-Adjusted Vegetation Index.
    See also: https://en.wikipedia.org/wiki/Soil-adjusted_vegetation_index
    Adjusted version of the NDVI which also detects the light reflectance/absorbsion traits of green vegetation.
    Normal NDVI have been shown to be unstable, varying with soil colour, soil moisture, and saturation effects from high density vegetation.
    The SAVI accounts for the differential red and near-infrared extinction through the vegetation canopy. 

    Parameters
    ----------
    nir : numpy 2-d array of floats
        surface reflectance values of NIR light (channel 0 in NIR fake color images)
    red : numpy 2-d array of floats
        surface reflectance values of red light (channel 1 in NIR fake color images)
    l : float
        an adjustment factor accounting for tree canopy effects, default: 0.5
    
    Returns
    -------
    savi : numpy 2-d array of floats 
        the savi values, values are in the range [-1,1], values of >0.2 or 0.3 typically indicates vegetation

    References
    ----------
    [1] Huete, A.R., (1988) 'A soil-adjusted vegetation index (SAVI)' Remote Sensing of Environment, vol. 25, issue 3, pp. 259-309. DOI: 10.1016/0034-4257(88)90106-X
    """
    savi = ( (1 + l) * (nir - red) ) / (nir + red + l)
    return savi
