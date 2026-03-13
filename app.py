from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
from similarity import find_similar

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/compare", methods=["POST"])
def compare():

    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]

    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    filename = str(uuid.uuid4()) + "_" + file.filename
    image_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(image_path)

    try:
        results = find_similar(image_path)

        formatted_results = [
            {"image_path": path, "similarity_score": float(score)}
            for path, score in results
        ]

        return jsonify({
            "query_image": image_path,
            "top_matches": formatted_results
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)