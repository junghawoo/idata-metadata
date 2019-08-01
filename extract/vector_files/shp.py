from osgeo import ogr


def getDataSource(filepath):
     
    driver = ogr.GetDriverByName('ESRI Shapefile')
    datasource = driver.Open(filepath)
    return datasource
