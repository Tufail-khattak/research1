from flask import Flask, request, jsonify
from flask_cors import CORS
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import base64
import json
import time
import hashlib
import threading
import os
from cryptography.hazmat.backends import default_backend

app = Flask(__name__)
CORS(app)

sessions = {}

with open("keys/sms_priv.pem", "rb") as f:
    sms_priv = serialization.load_pem_private_key(f.read(), password=None)
with open("keys/ws_pub.pem", "rb") as f:
    ws_pub = serialization.load_pem_public_key(f.read())
with open("keys/client_pub.pem", "rb") as f:
    client_pub = serialization.load_pem_public_key(f.read())

def encrypt_payload(payload, public_key):
    return base64.b64encode(public_key.encrypt(
        json.dumps(payload).encode(),
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )).decode()

def decrypt_payload(ciphertext, private_key):
    return json.loads(private_key.decrypt(
        base64.b64decode(ciphertext),
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    ).decode())

def generate_th(data):
    return hashlib.sha224(json.dumps({"PuKc": data["PuKc"], "Nc": data["Nc"], "Ns": data["Ns"]}).encode()).hexdigest()

def encrypt_esid(esid, sk):
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(sk), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    padding_length = 16 - len(esid) % 16
    padded_esid = esid + chr(padding_length) * padding_length
    encrypted_esid = encryptor.update(padded_esid.encode()) + encryptor.finalize()
    return base64.b64encode(iv + encrypted_esid).decode()

def update_esid():
    while True:
        for id in list(sessions.keys()):
            session_id = str(int(time.time()))[:50]
            sk = sessions[id]["SK"]
            sessions[id]["ESID"] = encrypt_esid(session_id, sk)
            print(f"Updated ESID for {id}: {sessions[id]['ESID']}")
        time.sleep(53)

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = decrypt_payload(request.json['data'], sms_priv)
        th = generate_th(data)
        session_id = str(int(time.time()))[:50]
        sk = base64.b64decode("4H7n8J9kPqRt2vWxYzAbCdEfGhIjKlMn")
        esid = encrypt_esid(session_id, sk)
        sessions[data["PuKc"]] = {"TH": th, "ESID": esid, "SK": sk, "Ns": data["Ns"]}
        payload = {"TH": th, "ESID": esid, "Ns": data["Ns"], "SK": base64.b64encode(sk).decode()}
        encrypted_payload = encrypt_payload(payload, ws_pub)
        return jsonify({"data": encrypted_payload})
    except Exception as e:
        print(f"Generate error: {str(e)}")
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500

if __name__ == "__main__":
    threading.Thread(target=update_esid, daemon=True).start()
    app.run(port=5003)