from flask import Flask, abort, jsonify, request,send_file
from dgad.api import DGADClient  # type: ignore

app = Flask('kdga')

@app.route('/dga/<domain>')
def dga(domain):
    dgad_client = DGADClient('localhost', 4714)
    responses = dgad_client.requests(domain)
    return jsonify(responses)
