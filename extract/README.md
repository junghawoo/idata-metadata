## Here is the hierarchy of GeoEDF files:
- **GeoEDF**
    - **index_metadata**
        - **extract**
            - extract_metadata.py\
                Extract_metadata reads the filepath and categories the file into different types according to its extension
            - gisfile.py\
                .gis file is a specific type of raster file. This class extracts additional metadata of .gis file
            - gmlfile.py\
                .gml file is a specific type of vector file. This class extracts additional metadata of .gml file
            - hdf4file.py\
                .hdf file is a specific type of raster file. This class extracts additional metadata of .hdf file 
            - hdf5file.py\
                .h5 file is a specific type of raster file. This class extracts additional metadata of .h5 file 
            - kmlfile.py\
                .kml file is a specific type of vector file. This class extracts additional metadata of .kml file
            - ncfile.py\
                .nc file is a specific type of raster file. This class extracts additional metadata of .kml file
            - rasterfile.py\
                Raster image file is a file category that is created with pixel-based programs or captured with a camera or scanner. This file extracts the general metadata of raster image file, such as geographic bounds and etc
            - shpfile.py\
                .shp file is a specific type of vector file. This class extracts additional metadata of .shp file
            - tiffile.py\
                .tif file is a specific type of raster file. This class extracts additional metadata of .tif file 
            - vectorfile.py\
                vector image file is a file category that is created with vector software and are common for images that will be applied onto a physical product. The file extracts the general metadata of vector image file, such as geographic bounds and etc  
        - Dockerfile\
            Docker builds the images automatically by reading the instructions from a Dockerfile. Docker creates a container that set up the executing environment for users
        - index_metadata.py\
            Index_metadata reads the filepath from user’s input and creates the metadata dictionary of file accordingly  

