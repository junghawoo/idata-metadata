import raster
import vector
import os.path

def extract_metadata(filepath):
    root, ext = os.path.splitext(filepath)
    if (ext in vector.extensions):
        return vector.getMetadata(filepath)
    elif (ext in raster.extensions):
        return raster.getMetadata(filepath)

if __name__ == "__main__":
        
    import json, sys

    if (len(sys.argv) == 2):
       filepath= sys.argv[1]
    else:
       #filepath = "sample_files/Riv2.shp"
       #filepath = "sample_files/acre.kml"
       #filepath = "sample_files/raing1.shp"
       #filepath = "sample_files/openflights-sample.kml"
       filepath = "sample_files/canaryislands_tmo_2013166_geo.tif"
       #filepath = "sample_files/TerraClimate_aet_1961.nc"
       #filepath = "sample_files/mypolygon_px6.gml"
       #filepath = "sample_files/aet.nc"
       #filepath = "sample_files/sresa1b_ncar_ccsm3-example.nc"
       #filepath = "sample_files/county83.shp"
       
    print(json.dumps(extract_metadata(filepath), indent=3))
