from osgeo import ogr

def getDataSource(filepath):
    driver = ogr.GetDriverByName('GML')
    datasource = driver.Open(filepath)
    return getVectorData(datasource)
