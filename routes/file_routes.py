from flask import Blueprint, request, jsonify, send_from_directory
import os
from werkzeug.utils import secure_filename

file_bp = Blueprint('file', __name__)

UPLOAD_DIR = "uploaded_files"
BASE_PUBLIC_URL = "http://147.93.103.168:5632/files"
API_KEY = "SUPER_SECRET_KEY"

os.makedirs(UPLOAD_DIR, exist_ok=True)


@file_bp.route('/upload-public', methods=['POST'])
def upload_file():
    if request.headers.get("X-API-KEY") != API_KEY:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    if 'file' not in request.files:
        return jsonify({"ok": False, "error": "No file"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"ok": False, "error": "Empty filename"}), 400

    filename = secure_filename(file.filename)
    save_path = os.path.join(UPLOAD_DIR, filename)

    try:
        file.save(save_path)
        return jsonify({"ok": True, "url": f"{BASE_PUBLIC_URL}/{filename}"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@file_bp.route('/files/<path:filename>', methods=['GET'])
def serve_file(filename):
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=False)
