from osgeo import gdal, ogr
import netCDF4
import numpy

def getMetadata(filepath):
   
    # ------------ NC and TIF --------------------- #
    raster = gdal.Open(filepath)
    data = {}
    
    datasource = gdal.Open(filepath)
    data['xsize'] = datasource.RasterXSize
    data['ysize'] = datasource.RasterYSize
    ulx, uly, llx, lly, lrx, lry, urx, ury = getCoverage(datasource)
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

    # ------------ NC Specific Metadata ------------ #
    ncdataset = netCDF4.Dataset(filepath)

    # globals
    global_attributes = {}
    for attr in ncdataset.ncattrs():
        global_attributes[str(attr)] = str(getattr(ncdataset, attr))
    if 'title' in global_attributes:
        data['title'] = str(global_attributes['title'])
    if 'history' in global_attributes:
        data['creator'] = global_attributes['history']
    
    subdata = {}
    # variables
    for i, (name, variable) in enumerate(ncdataset.variables.items(), start=1):
        var = {}
        for attrname in variable.ncattrs():
            var[str(attrname)] = convert_type(getattr(variable, attrname))

        var_name = 'sub{}'.format(i - 1) # start index should be 0
        for name in ['standard_name', 'long_name']:
            if name in var:
                subdata[var_name] = {'title': var[name]}
                for key in ['description', 'units', 'dimensions']:
                    if key in var:
                       subdata[var_name][key] = var[key]
                       
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

def convert_type(value):

    if isinstance(value, numpy.generic):
        return value.item()
    elif isinstance(value, tuple) or isinstance(value, list):
        ret = []
        for element in value:
            if isinstance(value, numpy.generic):
                ret.append(element.item())
            else:
                ret.append(str(element))
        return ret
    else:
        return str(value)
