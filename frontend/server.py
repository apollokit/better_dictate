"""The main flask app."""
import boto3
import flask
from flask import (
    Flask, redirect, render_template)

# from vinci.db import connection


# Create the Flask app.
app = Flask('Better Dictate Frontend Server')
    
# The main UI page
@app.route('/')
def main_ui():

    return render_template('ui.html')