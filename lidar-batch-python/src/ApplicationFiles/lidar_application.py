import argparse
import pdal
import json
import numpy as np

# Construct the argument parser
ap = argparse.ArgumentParser()

# Add the arguments to the parser
ap.add_argument("-a", "--inputfile", required=True,
   help="input file, string")
ap.add_argument("-b", "--outputfile", required=False,
   help="output file, string")
args = vars(ap.parse_args())
input_file = args['inputfile']
output_file = args['outputfile']

# Print file name: not necesarry
print("Filename is {}".format(args['inputfile']))


pipeline = [
        {
            "type": "readers.las",
            "filename": input_file,
            "spatialreference":"EPSG:28992"
        },
        {
            "type":"filters.csf"
        },
       {
            "type":"filters.range",
            "limits":"Classification[2:2]"
        },
        {
            "type":"writers.las",
            "filename":output_file
        }
    ]     
   
pipeline = pdal.Pipeline(json.dumps(pipeline))
pipeline.execute()    


## Pipeline to create small sample dataset for GitHub example - to be used as input data
#pipeline = [
#        {
#            "type": "readers.las",
#            "filename": input_file,
#            "spatialreference":"EPSG:28992"
#        },
#        {
#            "type":"filters.crop",
##            "bounds":"([196000,197000],[317755,318755])" # snippet for 1km x 1km -> used for blog post example
#            "bounds":"([195150,195300],[317775,317925])" # sippet for 150m x 150m -> used for GitHub example
#        },
#        {
#            "type":"writers.las",
#            "filename":output_file
#        }
#    ]

## Pipeline snippet to write data as geotif
#
#        {
#            "type":"writers.gdal",
#            "resolution": 0.5,
#            "output_type":"idw",
#            "dimension":"Z",
#            "data_type":"float",
#            "filename":output_file
#        }
#    ]