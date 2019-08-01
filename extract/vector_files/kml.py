from osgeo import ogr

def getDataSource(filepath):
   driver = ogr.GetDriverByName('KML')
   return driver.Open(filepath)
