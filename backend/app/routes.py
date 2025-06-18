from flask import jsonify, request
from flask import Blueprint
import os
import uuid
from app.utils.minio import MinioDB
from app.utils.agent import AgentRecommender
from datetime import timedelta
import random
import logging
import traceback
import re

main = Blueprint('main', __name__)
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
        result = agent.recommend_from_image(image_url, user_prompt)
        pattern = r"\d+\.\s(.+?) by (.+?) - (.+?)(?=\n\d+\.|\Z)"
        matches = re.findall(pattern, result, re.DOTALL)
        recommendations = []
        for idx, (title, artist, lyrics) in enumerate(matches, start=1):
            duration = random.randint(150, 260)  # giả định độ dài bài hát
            segment_start = random.randint(10, duration - 60)
            segment_end = segment_start + 30
            relevance = random.randint(80, 95)

            recommendations.append({
                "id": str(idx),
                "title": title.strip(),
                "artist": artist.strip(),
                "segment": {
                    "start": segment_start,
                    "end": segment_end,
                    "description": lyrics.strip()[:100] + "...",  # Mô tả ngắn từ lời bài hát
                    "relevanceScore": relevance,
                },
                "duration": duration,
            })
        logger.info(f"Returning {len(recommendations)} recommendations")
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Agent error: {str(e)}\n{tb}")
        return jsonify({"error": f"Agent error: {str(e)}", "traceback": tb}), 500
    return jsonify({"recommendations": recommendations}), 200