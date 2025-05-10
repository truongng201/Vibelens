from flask import jsonify, request
from flask import Blueprint

main = Blueprint('main', __name__)

@main.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Hello, Flask API!"})

@main.route("/upload-image", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    
    # filter file name to allow only alphanumeric characters and underscores
    


    return jsonify({"message": "File uploaded successfully!"}), 200