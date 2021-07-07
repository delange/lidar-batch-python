import argparse
import pdal
import json
import numpy as np

# Construct the argument parser
ap = argparse.ArgumentParser()

# Add the arguments to the parser
ap.add_argument("-a", "--inputfile", required=True,
   help="first operand")
ap.add_argument("-b", "--outputfile", required=False,
   help="second operand")
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
#        {
#            "type":"writers.gdal",
#            "resolution": 15,
#            "output_type":"mean",
#            "dimension":"Z",
#            "data_type":"float",
#            "filename":output_file
#    }
#    ]


#pipeline = [
#        {
#            "type": "readers.las",
#            "filename": input_file,
#            "spatialreference":"EPSG:28992"
#        },
#        {
#            "type":"filters.crop",
#            "bounds":"([196000,197000],[316755,317755])"
#        },
#        {
#            "type":"writers.las",
#            "filename":output_file
#        }
#    ]


pipeline = pdal.Pipeline(json.dumps(pipeline))
pipeline.execute()
# read & print the data schema from the pipeline object
schema = pipeline.schema
print("Schema is {}".format(schema))