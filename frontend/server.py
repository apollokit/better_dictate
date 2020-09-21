"""Frontend app for visualizing and manipulating text output from better dictate
STT engine
"""

import flask
from flask import (
    Flask, Response, jsonify, make_response, redirect, render_template, request)


# Create the Flask app.
app = Flask('Better Dictate frontend server')


# Handle initial visits to the site.
@app.route('/')
def root():
    return redirect('/yo')

# "yo"
@app.route('/yo')
def hyperquest():
    return render_template(
        'yo.html')