from pyproj import Proj, transform
from osgeo import ogr
from .common import commonData
from .common import geoData
from .vector_files import gml
from .vector_files import kml
from .vector_files import shp
import os.path

extensions = ['.gml', '.kml', '.shp', '.dbf', '.prj', '.shx']
shapefile_components = ['.shp', '.dbf', '.prj', '.shx']

#------------ for vector file------------------#

def transformCoordinates(x1, y1, inProj_epsg):
     inProj = Proj(init='epsg:' + inProj_epsg)
     outProj = Proj(init='epsg:4326')
     x2,y2 = transform(inProj, outProj, x1, y1)
     return x2, y2

def shapefileComplete(filepath):
    return shp.shapefileComplete(filepath)

def getMetadata(filepath):
     
     # get datasource
     filename, ext = os.path.splitext(filepath)
     if (ext == '.gml'):
         driver = ogr.GetDriverByName('GML')
     elif (ext == '.kml'):
         driver = ogr.GetDriverByName('KML')
     elif (ext == '.shp'):
         driver = ogr.GetDriverByName('ESRI Shapefile')

     with open('/tmp/messages.txt','a+') as logfile:
         logfile.write('\n get shp metadata %s' % filepath)    
     datasource = driver.Open(filepath)
     with open('/tmp/messages.txt','a+') as logfile:
         logfile.write('\n opened shapefile')
     data = {}

     # get extent
     layer = datasource.GetLayer()
     extent = layer.GetExtent()
     if extent is not None:
         data['westlimit'] = extent[0]
         data['eastlimit'] = extent[1]
         data['southlimit'] = extent[2]
         data['northlimit'] = extent[3]
     
     # get projection
     spatialref = layer.GetSpatialRef()
     if spatialref is not None:
         inProj_epsg = spatialref.GetAttrValue('AUTHORITY', 1)
         data['lonmin'], data['latmin'] = transformCoordinates(extent[0], extent[2], str(inProj_epsg))
         data['lonmax'], data['latmax']  = transformCoordinates(extent[1], extent[3], str(inProj_epsg))
     
     # get the schema of the layers
     layerdef = layer.GetLayerDefn()
     schema = []
     for n in range(layerdef.GetFieldCount()):
         field = layerdef.GetFieldDefn(n)
         schema.append(field.name)   
     if schema is not None:
         data['schema'] = schema
         data['subject'] = schema

     # file type
     data['type'] = 'geospatial'

     #return commonData(data, filepath) 
     return geoData(data, filepath) 
