import time
import requests
import base64
import json
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import traceback

app = Flask(__name__, static_folder='client', static_url_path='')
CORS(app, resources={r"/*": {"origins": "http://127.0.0.1:8000"}})

users = {"user1": {"password": "pass123", "primary_key": "client_pk"}}
sessions = {}

with open("keys/ws_priv.pem", "rb") as f:
    ws_priv = serialization.load_pem_private_key(f.read(), password=None)
with open("keys/sms_pub.pem", "rb") as f:
    sms_pub = serialization.load_pem_public_key(f.read())

def encrypt_payload(payload, public_key):
    try:
        return base64.b64encode(public_key.encrypt(
            json.dumps(payload).encode(),
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        )).decode()
    except Exception as e:
        print(f"Encryption failed: {str(e)}")
        raise ValueError("Encryption failed")

def decrypt_payload(ciphertext, private_key):
    try:
        return json.loads(private_key.decrypt(
            base64.b64decode(ciphertext),
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        ).decode())
    except Exception as e:
        print(f"Decryption failed: {str(e)}")
        raise ValueError("Decryption failed")

@app.route('/login', methods=['POST'])
def login():
    start_time = time.time()
    try:
        data = request.json
        id, password, primary_key, nonce, user_agent = data['id'], data['password'], data['primaryKey'], data['nonce'], data['userAgent']
        print(f"Received Data: ID = {id}, Nonce = {nonce}, PuKc = {primary_key}, User Agent = {user_agent}")
        if users.get(id, {}).get("password") == password and users[id]["primary_key"] == primary_key:
            payload = {"PuKc": primary_key, "Nc": nonce, "Ns": str(int(time.time()))}
            encrypted_payload = encrypt_payload(payload, sms_pub)
            sms_start_time = time.time()
            response = requests.post("http://127.0.0.1:5003/generate", json={"data": encrypted_payload})
            sms_end_time = time.time()
            print(f"Time to call SMS and get response: {sms_end_time - sms_start_time:.4f} seconds")
            if response.status_code == 200:
                sms_data = decrypt_payload(response.json()['data'], ws_priv)
                sessions[id] = {"TH": sms_data["TH"], "ESID": sms_data["ESID"], "Ns": sms_data["Ns"], "SK": base64.b64decode(sms_data["SK"])}
                return jsonify({"status": "success", "message": "Login successful", "TH": sms_data["TH"], "ESID": sms_data["ESID"]})
            return jsonify({"status": "error", "message": f"SMS failure: {response.text}"}), 500
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401
    except Exception as e:
        print(f"Login error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500

@app.route('/validate', methods=['POST'])
def validate():
    try:
        data = request.json
        id, th, esid, nonce = data['id'], data['TH'], data['ESID'], data['nonce']
        session = sessions.get(id)
        if session and session["TH"] == th and session["ESID"] == esid:
            return jsonify({"status": "success", "message": "Session valid"})
        return jsonify({"status": "error", "message": "Invalid session"}), 401
    except Exception as e:
        print(f"Validate error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(port=5002)