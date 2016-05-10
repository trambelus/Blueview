#!/usr/bin/env python3
# server.py - simple Flask server for backend

from flask import Flask, request, flash, redirect, render_template, url_for, abort
import sys
import queue
import json
from datetime import timedelta
from flask import make_response, request, current_app
from functools import update_wrapper

basestring = (str,bytes)
def crossdomain(origin=None, methods=None, headers=None,
				max_age=21600, attach_to_all=True,
				automatic_options=True):
	if methods is not None:
		methods = ', '.join(sorted(x.upper() for x in methods))
	if headers is not None and not isinstance(headers, basestring):
		headers = ', '.join(x.upper() for x in headers)
	if not isinstance(origin, basestring):
		origin = ', '.join(origin)
	if isinstance(max_age, timedelta):
		max_age = max_age.total_seconds()

	def get_methods():
		if methods is not None:
			return methods

		options_resp = current_app.make_default_options_response()
		return options_resp.headers['allow']

	def decorator(f):
		def wrapped_function(*args, **kwargs):
			if automatic_options and request.method == 'OPTIONS':
				resp = current_app.make_default_options_response()
			else:
				resp = make_response(f(*args, **kwargs))
			if not attach_to_all and request.method != 'OPTIONS':
				return resp

			h = resp.headers

			h['Access-Control-Allow-Origin'] = origin
			h['Access-Control-Allow-Methods'] = get_methods()
			h['Access-Control-Max-Age'] = str(max_age)
			if headers is not None:
				h['Access-Control-Allow-Headers'] = headers
			return resp

		f.provide_automatic_options = False
		return update_wrapper(wrapped_function, f)
	return decorator


app = Flask(__name__)
q = []

@app.route('/blueview', methods=['GET'])
def index():
	return render_template('index.html')

@app.route('/blueview/data', methods=['GET','POST'])
@crossdomain(origin='*')
def data():
	if request.method == 'POST': # receiving data
		# store as dict
		d = {}
		d['uuid'] = request.form['uuid']
		d['mac'] = request.form['mac']
		d['packet'] = request.form['packet']
		d['manufacturer'] = request.form['manufacturer']
		q.append(d)
		return "OK"
		
	elif request.method == 'GET': # sending data
		# dump to json as needed, and clear list
		js = json.dumps(q)
		q.clear()
		return js

def main():
	debug = (len(sys.argv) > 1 and sys.argv[1] == 'debug')
	app.run(host='0.0.0.0', port=83, debug=debug)

if __name__ == '__main__':
	main()
