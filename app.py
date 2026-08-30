import os
from flask import Flask, jsonify
from flask_sock import Sock
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
sock = Sock(app)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "voice-service"}), 200


@sock.route("/stream")
def stream(ws):
    while True:
        message = ws.receive()
        if message is None:
            break
        print("Received message:", message)


if __name__ == "__main__":
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port, debug=True)


