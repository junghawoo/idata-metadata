import sys, os
from extract import raster, vector
from index import index

if __name__ == "__main__": 

    if len(sys.argv) < 2: 
        filepath = input("Enter a filename: ")
    else:
        filepath = sys.argv[1]
        
    filename, fileext = os.path.splitext(filepath)
    if fileext in raster.extensions:
        metadata = raster.getMetadata(filepath) 
        print(metadata)
        index.newFile(metadata)
    elif fileext in VECTOR_EXT:
        metadata = vector.getMetadata(filepath)
        print(metadata)
        index.newFile(metadata)
