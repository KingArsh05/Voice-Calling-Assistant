import os
from flask import Flask, jsonify, Response
from flask_sock import Sock
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
sock = Sock(app)


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "voice-service"}), 200


@app.route("/plivo/answer", methods=["GET", "POST"])
def answer():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Speak>Hello, your Plivo connection is working.</Speak>
</Response>
"""
    return Response(xml, mimetype="application/xml")


@sock.route("/stream")
def stream(ws):
    while True:
        message = ws.receive()

        if message is None:
            break

        print("RECEIVED:", message)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    app.run(host="0.0.0.0", port=port, debug=True)
