#from pyproj import Proj, transform
from osgeo import gdal
from .raster_files import hdf4
from .raster_files import hdf5
from .raster_files import nc
from .raster_files import tif
from .common import commonData
import os

extensions = ['.hdf4', '.hdf', '.hdf5', '.nc', '.tif']

LOG_PATH = '/tmp/messages.txt'

#--------------- for datasource file ------------------#
def getCoverage(datasource):
     upx, xres, xskew, upy, yskew, yres = datasource.GetGeoTransform()
     cols = datasource.RasterXSize
     rows = datasource.RasterYSize
          
     ulx = upx + 0*xres + 0*xskew
     uly = upy + 0*yskew + 0*yres
          
     llx = upx + 0*xres + rows*xskew
     lly = upy + 0*yskew + rows*yres
          
     lrx = upx + cols*xres + rows*xskew
     lry = upy + cols*yskew + rows*yres
          
     urx = upx + cols*xres + 0*xskew
     ury = upy + cols*yskew + 0*yres

     return ulx, uly, llx, lly, lrx, lry, urx, ury

def getMetadata(filepath):
    
     with open(LOG_PATH,'a+') as logfile:
         logfile.write('extract raster metadata for file %s' % filepath)
     
     data = {}
     filename, ext = os.path.splitext(filepath)
     if (ext == '.hdf4' or  ext == '.hdf'):
         data = hdf4.getMetadata(filepath)
     elif (ext == '.hdf5'):
         data = hdf4.getMetadata(filepath)
     elif (ext == '.nc'):
         data = nc.getMetadata(filepath)
     elif (ext == '.tif'):
         data = tif.getMetadata(filepath)
     
     datasource = gdal.Open(filepath)

     with open(LOG_PATH,'a+') as logfile:
         logfile.write('opened raster file successfully')

     data['xsize'] = datasource.RasterXSize
     data['ysize'] = datasource.RasterYSize
     ulx, uly, llx, lly, lrx, lry, urx, ury = getCoverage(datasource)
     latitudes = [ulx, llx, lrx, urx]
     longitudes = [uly, lly, lry, ury] 
     data['northlimit'] = uly
     data['southlimit'] = lly
     data['eastlimit'] = urx
     data['westlimit'] = ulx
     data['latmin'] = min(longitudes)
     data['latmax'] = max(longitudes)
     data['lonmin'] = min(latitudes)
     data['lonmax'] = max(latitudes)

     # file type
     data['type'] = 'geospatial'

     return commonData(data, filepath) 
