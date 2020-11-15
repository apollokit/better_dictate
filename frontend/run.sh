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
source $DIR/../env/source_virtualenv

# Run the server.
cd $DIR
export FLASK_APP=server.py
export FLASK_DEBUG=1
flask run --host=0.0.0.0 -p 5050