from osgeo import ogr, osr, gdal
import sys
import pyproj
import numpy as np
import re
import h5py

def getMetadata(filepath):
	
    data_dict = {}
    hdf_file = h5py.File(filepath, mode='r')
    
    # check to see if this is a EASE Grid 2.0 file
    if 'EASE2_global_projection' in hdf_file.keys():
        
        # hardcoded corner coordinates, since this is not stored in the file metadata
        x0, y0, x1, y1 = -17357881.81713629,7324184.56362408,17357881.81713629,-7324184.56362408
        
        data_dict['xmax'] = x0 
        data_dict['xmin'] = x1 
        data_dict['ymax'] = y1 
        data_dict['ymin'] = y0 

        ease = pyproj.Proj(("+proj=cea +lat_0=0 +lon_0=0 +lat_ts=30 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m"))
        wgs84 = pyproj.Proj("+init=EPSG:4326")
        lonmin, latmin = pyproj.transform(ease, wgs84, x0, y0)
        lonmax, latmax = pyproj.transform(ease, wgs84, x1, y1)
    
        data_dict['latmin'] = latmin
        data_dict['latmax'] = latmax
        data_dict['lonmin'] = lonmin
        data_dict['lonmax'] = lonmax
    return  data_dict
