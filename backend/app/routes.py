from flask import jsonify, request
from flask import Blueprint
import os
import uuid
from app.utils.minio import MinioDB
from datetime import timedelta

main = Blueprint('main', __name__)
minio_db = MinioDB()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file extension"}), 400

    # Get file extension
    ext = file.filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": "File extension not allowed"}), 400
    # Generate random filename
    random_name = f"{uuid.uuid4().hex}"
    # Save locally
    local_path = os.path.join("uploads", random_name)
    os.makedirs("uploads", exist_ok=True)
    file.save(local_path)

    # Upload to MinIO under 'uploads/' folder
    minio_object_path = f"uploads/{random_name}"
    try:
        minio_db.upload_image(local_path, object_name=minio_object_path, extension=ext)
        shared_url = minio_db.get_presigned_url(
            minio_object_path + f".{ext}", expiry=timedelta(days=7)
        )
        os.remove(local_path)
    except Exception as e:
        return jsonify({"error": f"MinIO upload failed: {str(e)}"}), 500

    return jsonify({
        "message": "File uploaded successfully!",
        "filename": random_name,
        "shared_url": shared_url
    }), 200