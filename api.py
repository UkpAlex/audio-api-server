from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS  # นำเข้า CORS
import base64
import os
import json
import sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)  # เปิดใช้งาน CORS สำหรับทุก endpoint

API_KEY = "TNIAPIKey"
latest_audio_file = None

if not os.path.exists("uploads"):
    os.makedirs("uploads")

def authenticate(request):
    api_key = request.headers.get("X-API-KEY")
    if api_key != API_KEY:
        return False
    return True

def log_to_sqlite(outcome):
    conn = sqlite3.connect('log.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            outcome TEXT
        )
    ''')

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO logs (timestamp, outcome) VALUES (?, ?)", (timestamp, outcome))
    conn.commit()
    conn.close()

@app.route('/api/upload', methods=['POST'])
def upload_audio():
    global latest_audio_file
    if not authenticate(request):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    if "audio" not in data or "features" not in data:
        log_to_sqlite("Missing audio or features in request")
        return jsonify({"error": "Missing audio or features"}), 400

    # แปลงข้อมูลเสียงจาก base64 และบันทึกเป็นไฟล์ .wav
    encoded_audio = data["audio"]
    audio_data = base64.b64decode(encoded_audio)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    audio_file_path = os.path.join("uploads", f"{timestamp}_audio.wav")
    
    with open(audio_file_path, "wb") as audio_file:
        audio_file.write(audio_data)

    # อัปเดตชื่อไฟล์เสียงล่าสุด
    latest_audio_file = f"{timestamp}_audio.wav"

    # บันทึกข้อมูล features ลงในไฟล์ features.json เดียว
    features = data["features"]
    features_file_path = os.path.join("uploads", "features.json")
    
    # ถ้าไฟล์ features.json มีอยู่แล้ว ให้โหลดข้อมูลเดิมและเพิ่มเข้าไป
    if os.path.exists(features_file_path):
        with open(features_file_path, "r") as f:
            existing_features = json.load(f)
    else:
        existing_features = []

    # เพิ่มฟีเจอร์ใหม่เข้าไปในรายการเดิม
    existing_features.append({
        "timestamp": timestamp,
        "features": features
    })

    # บันทึกฟีเจอร์ทั้งหมดลงไฟล์ features.json
    with open(features_file_path, "w") as f:
        json.dump(existing_features, f)

    log_to_sqlite("Audio and features received and saved successfully")
    return jsonify({"status": "success", "message": "Audio and features received and saved"}), 200

@app.route('/api/latest_audio', methods=['GET'])
def get_latest_audio():
    if latest_audio_file:
        return jsonify({"latest_audio_file": latest_audio_file}), 200
    else:
        return jsonify({"error": "No audio file available"}), 404

@app.route('/api/list_audio', methods=['GET'])
def list_audio_files():
    if not authenticate(request):
        return jsonify({"error": "Unauthorized"}), 401

    files = [f for f in os.listdir("uploads") if f.endswith(".wav")]
    return jsonify({"audio_files": files}), 200

@app.route('/api/get_model',methods=['GET'])
def download_m():
  try:
    return send_from_directory(directory='models',filename='sound_detection_model.mat',as_attachment=True)
  except:
    return jsonify({"error": "Model file not found"}), 404

@app.route('/api/download_audio/<filename>', methods=['GET'])
def download_audio_file(filename):
    if not authenticate(request):
        return jsonify({"error": "Unauthorized"}), 401

    try:
        return send_from_directory("uploads", filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404

if __name__ == '__main__':
    app.run(host='192.168.1.105', port=5000)
