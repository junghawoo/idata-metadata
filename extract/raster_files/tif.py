from osgeo import gdal

#--------------- for datasource file ------------------#

 # "enum GDALColorInterp" from https://www.gdal.org/gdal_8h.html#ace76452d94514561fffa8ea1d2a5968c
GDALColorInterp = { 0: 'Undefined', 1: 'Gray', 2: 'Paletted (see color table)', 3: 'Red', 4: 'Green', 5: 'Blue', 6: 'Alpha', 7: 'Hue', 8: 'Saturation', 9: 'Lightness', 10: 'Cyan', 11: 'Magenta', 12: 'Yellow', 13: 'Black', 14: 'Y Luminance', 15: 'Cb Chroma', 16: 'Cr Chroma', 17: 'Max'}

LOG_PATH = '/tmp/messages.txt'

def getMetadata(filepath):
  
   data = {}

   datasource = gdal.Open(filepath)

   try:
       if datasource.RasterXSize is not None:
           data['xsize'] = datasource.RasterXSize
       if datasource.RasterYSize is not None:
           data['ysize'] = datasource.RasterYSize
       ulx, uly, llx, lly, lrx, lry, urx, ury = getCoverage(datasource)
   except:
       with open(LOG_PATH,'a+') as logfile:
           logfile.write('exception occurred getting metadata for tif file')
   longitudes = [ulx, llx, lrx, urx]
   latitudes = [uly, lly, lry, ury] 
   data['northlimit'] = uly
   data['southlimit'] = lly
   data['eastlimit'] = urx
   data['westlimit'] = ulx
   data['latmin'] = min(longitudes)
   data['latmax'] = max(longitudes)
   data['lonmin'] = min(latitudes)
   data['lonmax'] = max(latitudes)

   # geotif-related metadata
   metadata = datasource.GetMetadata()
   if metadata is not None:
       if 'TIFFTAG_DOCUMENTNAME' in metadata:
          data['title'] = metadata.pop('TIFFTAG_DOCUMENTNAME')
       if 'TIFFTAG_IMAGEDESCRIPTION' in metadata:
          data['description'] = metadata.pop('TIFFTAG_IMAGEDESCRIPTION')
       if 'TIFFTAG_DATETIME' in metadata:
          data['date'] = metadata.pop('TIFFTAG_DATETIME')
       if 'TIFFTAG_SOFTWARE' in metadata:
          data['source'] = metadata.pop('TIFFTAG_SOFTWARE')
       if 'TIFFTAG_ARTIST' in metadata:
          data['creator'] = metadata.pop('TIFFTAG_ARTIST')

   # get subdata, which in the case of a GeoTiff file could be the color interpretation of each band
   subdata = {}
   for band_num in range(datasource.RasterCount, 1):
      band = datasource.GetRasterBand(band_num)
      band_description = band.GetDescription()
      band_color_interp = band.GetColorInterpretation()
      key = 'sub{}'.format(band_num - 1) # index should start at 0
      title = 'Band {}'.format(band_num)
     
      subdata[key] = {}
      # if there is a user defined description
      if band_description is not None and band_description != '':
          subdata[key]['title'] = title
          subdata[key]['description'] = band_description

      # if there is a valid color interpretation
      if band_color_interp is not None and band_color_interp in range(18):
          subdata[key]['title'] = title
          subdata[key]['type'] =  GDALColorInterp.get(band_color_interp)

   # if there was nonempty subdata, add it to the data dictionary
   if len(subdata) > 0:
      data['subdata'] = subdata 

   return data

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

