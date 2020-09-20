#!/bin/bash
#
# This runs the flask server. Note that if you want better debugging support, run it like:
#
#    FLASK_ENV=development ./run.sh
#    
# If you want to listen on a custom port:
# 
# 	./run.sh -p 5001
set -e

DIR=$(dirname $0)

# Make sure we're in the right virtualenv.
source $DIR/../source_virtualenv

# Include the rest of the stockbot libraries so the site can use all that good stuff.
export PYTHONPATH=$PYTHONPATH:$DIR/..:$DIR/../../lib

# Run the server.
cd $DIR
export FLASK_APP=server.py
flask run --host=0.0.0.0 $@


