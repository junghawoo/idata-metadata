from osgeo import ogr
import os


def getDataSource(filepath):
     
    driver = ogr.GetDriverByName('ESRI Shapefile')
    datasource = driver.Open(filepath)
    return datasource

def shapefileComplete(filepath):
    dirname,filename = os.path.split(filepath)
    basename,ext = os.path.splitext(filename)

    # look for other required files
    if os.path.isfile('%s/%s.dbf' % (dirname,basename)) and os.path.isfile('%s/%s.shx' % (dirname,basename)) and os.path.isfile('%s/%s.prj' % (dirname,basename)):
           return True
    else:
        return False
