import os
from flask import Blueprint, Response

plivo_bp = Blueprint("plivo", __name__)


@plivo_bp.route("/answer", methods=["GET", "POST"])
def answer():
    # WebSocket stream endpoint (e.g., wss://voice-service.onrender.com/stream)
    websocket_url = os.getenv("WEBSOCKET_URL", "wss://YOUR-WEBSOCKET-DOMAIN/stream")
    # Base URL for status callbacks
    base_url = os.getenv("BASE_URL", "https://voice-calling-assistant.vercel.app")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Speak>Connected to AI Assistant.</Speak>
    <Stream
        keepCallAlive="true"
        bidirectional="true"
        contentType="audio/x-mulaw;rate=8000"
        statusCallbackUrl="{base_url}/stream-status">
        {websocket_url}
    </Stream>
</Response>"""

    return Response(xml.strip(), mimetype="application/xml")
