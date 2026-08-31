import os
from flask import Flask, jsonify, Response
from flask_sock import Sock
from dotenv import load_dotenv
from routes.plivo import plivo_bp
from websocket.audio_stream import handle_stream

load_dotenv()

app = Flask(__name__)
sock = Sock(app)

# Register routes
app.register_blueprint(plivo_bp, url_prefix="/plivo")


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "voice-service"
    }), 200



@sock.route("/stream")
def stream(ws):
    handle_stream(ws)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    app.run(host="0.0.0.0", port=port, debug=True)

