from osgeo import ogr
import os
import functools


def getDataSource(filepath):
     
    driver = ogr.GetDriverByName('ESRI Shapefile')
    datasource = driver.Open(filepath)
    return datasource

def shapefileComplete(filepath):
    shapefile_components = ['.shp', '.shx', '.prj', '.dbf']
    dirname,filename = os.path.split(filepath)
    basename,ext = os.path.splitext(filename)

    return functools.reduce((lambda x,y: x and y),list(map((lambda ext: os.path.isfile('%s/%s%s' % (dirname,basename,ext))),shapefile_components)))
