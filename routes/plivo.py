import os
from flask import Blueprint, Response

plivo_bp = Blueprint("plivo", __name__)


@plivo_bp.route("/answer", methods=["GET", "POST"])
def answer():
    print("[PLIVO WEBHOOK] Received /plivo/answer webhook from Plivo")
    websocket_url = os.getenv(
        "WEBSOCKET_URL", "wss://voice-calling-assistant-sl9u.onrender.com/stream"
    ).strip()

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
                <Response>
                    <Speak>Connected to AI Assistant.</Speak>
                    <Stream bidirectional="true" keepCallAlive="true" contentType="audio/x-mulaw;rate=8000">{websocket_url}</Stream>
                </Response>
            """

    return Response(xml.strip(), mimetype="application/xml")
    