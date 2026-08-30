from flask import Blueprint, Response

plivo_bp = Blueprint("plivo", __name__)


@plivo_bp.route("/answer", methods=["GET", "POST"])
def answer():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
                <Response>
                    <Speak>Connected to AI Assistant.</Speak>

                    <Stream
                        keepCallAlive="true"
                        bidirectional="true"
                        contentType="audio/x-mulaw;rate=8000"
                        statusCallbackUrl="https://voice-calling-assistant.vercel.app/stream-status">
                        wss://YOUR-WEBSOCKET-DOMAIN/stream
                    </Stream>
                </Response>
        """

    return Response(xml, mimetype="application/xml")
