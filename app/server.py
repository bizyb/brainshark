from flask import abort, Flask, request, jsonify
from flask_cors import CORS
import main
app = Flask(__name__)
CORS(app)

@app.route("/download", methods=["GET"])
def download():
    blob = main.download(request.args.get("url"))
    
