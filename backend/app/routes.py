from flask import jsonify, request
from flask import Blueprint, Response
import os
import uuid
from app.utils.minio import MinioDB
from app.utils.agent import AgentRecommender
from app.utils.database import Database
from datetime import timedelta
import json
import logging
import traceback
from flask_cors import CORS
from app.utils.ytbdownloader import download_ytb_mp3

main = Blueprint('main', __name__)
CORS(main)
minio_db = MinioDB()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

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

    ext = file.filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": "File extension not allowed"}), 400
    random_name = f"{uuid.uuid4().hex}"
    local_path = os.path.join("uploads", random_name)
    os.makedirs("uploads", exist_ok=True)
    file.save(local_path)

    minio_object_path = f"uploads/{random_name}"
    try:
        minio_db.upload_image(local_path, object_name=minio_object_path, extension=ext)
        shared_url = minio_db.get_presigned_url(
            minio_object_path + f".{ext}", expiry=timedelta(days=7)
        )
        os.remove(local_path)
        logger.info(f"Uploaded file to MinIO at {minio_object_path}.{ext}")
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"MinIO upload failed: {str(e)}\n{tb}")
        return jsonify({"error": f"MinIO upload failed: {str(e)}", "traceback": tb}), 500

    return jsonify({
        "message": "File uploaded successfully!",
        "filename": random_name,
        "shared_url": shared_url
    }), 200

@main.route("/recommend-music", methods=["POST"])
def recommend_music():
    logger.info("Received recommend-music request")
    data = request.get_json()
    image_url = data.get("image_url")
    user_prompt = data.get("prompt", "")
    if not image_url:
        return jsonify({"error": "Missing image_url"}), 400
    agent = AgentRecommender()
    try:
        recommendations = agent.recommend_from_image(image_url, user_prompt)
        json_str = json.dumps(recommendations, ensure_ascii=False, indent=2)
        print(json_str)
        response_json = json.dumps({"recommendations": recommendations}, ensure_ascii=False, indent=2)

    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Agent error: {str(e)}\n{tb}")
        return jsonify({"error": f"Agent error: {str(e)}", "traceback": tb}), 500
    
    return Response(
        response_json,
        content_type="application/json; charset=utf-8"
    )
    
@main.route("/play-music", methods=["POST"])
def play_music():
    data = request.get_json()
    music_title = data.get("music_title", "").strip()
    if not music_title:
        return jsonify({"error": "Missing title"}), 400
    
    database = Database()
    res = database.execute_query(
        "SELECT id, artist FROM songs WHERE title LIKE %s",
        (f"%{music_title}%", )
    )
    
    if not res or len(res) == 0:
        return jsonify({"error": "Music not found"}), 404
    
    music_id = res[0][0]  # Assuming the first column is the ID
    music_artist = res[0][1]  # Assuming the second column is the artist
    logger.info(f"Music ID found: {music_id}")
    
    # check if the music is already in the minio database
    if minio_db.check_exists(music_id + ".mp3"):
        logger.info(f"Music {music_id} already exists in MinIO")
        # return presigned URL to play the music
        presigned_url = minio_db.get_presigned_url(music_id + ".mp3", expiry=timedelta(minutes=60))
        return jsonify({"message": "Music already exists", "url": presigned_url})
    logger.info(f"Music {music_id} not found in MinIO, downloading from YouTube")

    # Download the music from YouTube
    try:
        downloaded_file = download_ytb_mp3(music_title, music_artist, music_id)
        minio_db.upload_mp3(downloaded_file, object_name=music_id)
        os.remove(downloaded_file)  # Clean up the downloaded file
        presigned_url = minio_db.get_presigned_url(music_id + ".mp3", expiry=timedelta(minutes=60))
        logger.info(f"Music {music_id} downloaded and uploaded to MinIO successfully")
        return jsonify({"message": "Music downloaded and uploaded successfully", "url": presigned_url}), 200
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Error downloading or uploading music: {str(e)}\n{tb}")
        return jsonify({"error": f"Error downloading or uploading music: {str(e)}", "traceback": tb}), 500
    