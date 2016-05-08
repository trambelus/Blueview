#!/usr/bin/env python3
# server.py - simple Flask server for backend

from flask import Flask, request, flash, redirect, render_template, url_for, abort
import sys
import queue
import json

app = Flask(__name__)
q = []

@app.route('/blueview', methods=['GET'])
def index():
	return open('/templates/index.html','r').read()

@app.route('/blueview/data', methods=['GET','POST'])
def data():
	if request.method == 'POST': # receiving data
		# store as dict
		d = {}
		d['uuid'] = request.form['uuid']
		d['mac'] = request.form['mac']
		d['packet'] = request.form['packet']
		q.append(d)
		return "OK"
		
	elif request.method == 'GET': # sending data
		# dump to json as needed, and clear list
		js = json.dumps(list(d))
		d.clear()
		return js

def main():
	debug = (len(sys.argv) > 1 and sys.argv[1] == 'debug')
	app.run(host='0.0.0.0', port=83, debug=debug)

if __name__ == '__main__':
	main()
