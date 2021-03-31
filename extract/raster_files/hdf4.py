from pyhdf.SD import SD, SDC
from osgeo import ogr, osr, gdal
import sys
from pyproj import Proj, transform
import pyproj
import numpy as np
import re

def getMetadata(filepath):
    metadata = {}
    hdf_file = SD(filepath, SDC.READ)
    dataset= gdal.Open(filepath, gdal.GA_ReadOnly)
   
    # Construct the grid.  The needed information is in a global attribute
    # called 'StructMetadata.0'.  Use regular expressions to tease out the
    # extents of the grid.  
    fattrs = hdf_file.attributes(full=1)
    ga = fattrs["StructMetadata.0"]
    gridmeta = ga[0]

    ul_regex = re.compile(r'''UpperLeftPointMtrs=\(
                          (?P<upper_left_x>[+-]?\d+\.\d+)
                          ,
                          (?P<upper_left_y>[+-]?\d+\.\d+)
                          \)''', re.VERBOSE)
    match = ul_regex.search(gridmeta)
    x0 = np.float(match.group('upper_left_x'))
    y0 = np.float(match.group('upper_left_y'))
    
    lr_regex = re.compile(r'''LowerRightMtrs=\(
                          (?P<lower_right_x>[+-]?\d+\.\d+)
                          ,
                          (?P<lower_right_y>[+-]?\d+\.\d+)
                          \)''', re.VERBOSE)
    match = lr_regex.search(gridmeta)
    x1 = np.float(match.group('lower_right_x'))
    y1 = np.float(match.group('lower_right_y'))

    metadata['xmax'] = x0 
    metadata['xmin'] = x1 
    metadata['ymax'] = y1 
    metadata['ymin'] = y0 

    # determine the projection GCTP code from the grid metadata
    proj_regex = re.compile(r'''Projection=(?P<projection>\w+)''',re.VERBOSE)
    match = proj_regex.search(gridmeta)
    proj = match.group('projection')

    # support MODIS sinusoidal projection for now, add others later
    if proj == 'GCTP_SNSOID':
        sinu = pyproj.Proj("+proj=sinu +R=6371007.181 +nadgrids=@null +wktext")
        wgs84 = pyproj.Proj("+init=EPSG:4326")
        metadata['lonmin'], metadata['latmin'] = pyproj.transform(sinu, wgs84, x0, y0)
        metadata['lonmax'], metadata['latmax'] = pyproj.transform(sinu, wgs84, x1, y1)

    return  metadata
