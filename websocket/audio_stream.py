import json
import base64


def play_audio(ws, audio_bytes, stream_id=None):
    """
    Sends audio bytes back to Plivo to play to the caller.
    Audio format: audio/x-mulaw;rate=8000
    """
    payload = base64.b64encode(audio_bytes).decode("utf-8")
    message = {
        "event": "playAudio",
        "media": {
            "contentType": "audio/x-mulaw;rate=8000",
            "sampleRate": 8000,
            "payload": payload
        }
    }
    if stream_id:
        message["streamId"] = stream_id

    ws.send(json.dumps(message))


def clear_audio(ws, stream_id=None):
    """
    Clears currently playing audio buffer in Plivo (useful when caller interrupts the bot).
    """
    message = {"event": "clearAudio"}
    if stream_id:
        message["streamId"] = stream_id
    ws.send(json.dumps(message))


def handle_stream(ws):
    """
    Handles the live bidirectional WebSocket audio stream from Plivo.
    """
    stream_id = None
    call_id = None

    while True:
        message = ws.receive()

        if message is None:
            print("WebSocket closed by client.")
            break

        event = json.loads(message)
        event_name = event.get("event")

        # 1. Call connected and stream started
        if event_name == "start":
            stream_id = event.get("start", {}).get("streamId")
            call_id = event.get("start", {}).get("callId")
            print(f"[STREAM START] streamId={stream_id}, callId={call_id}")

        # 2. Audio chunks coming in from caller (8000Hz mulaw)
        elif event_name == "media":
            payload = event.get("media", {}).get("payload")
            audio_bytes = base64.b64decode(payload)
            # print(f"[AUDIO] Received {len(audio_bytes)} bytes from caller")

            # AI PIPELINE STEP:
            # - Send audio_bytes to STT (Speech-to-Text)
            # - Send transcribed text to LLM
            # - Generate TTS audio response (in mulaw 8000Hz format)
            # - Send back to caller: play_audio(ws, tts_audio_bytes, stream_id)

        # 3. Caller pressed a phone key
        elif event_name == "dtmf":
            digit = event.get("dtmf", {}).get("digit")
            print(f"[DTMF] User pressed key: {digit}")

        # 4. Call ended
        elif event_name == "stop":
            print(f"[STREAM STOP] Call ended for streamId={stream_id}")
            break