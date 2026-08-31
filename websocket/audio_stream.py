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
    print("[WEBSOCKET CONNECTED] Plivo client opened WebSocket connection", flush=True)
    stream_id = None
    call_id = None
    media_count = 0

    while True:
        try:
            message = ws.receive()
        except Exception as e:
            print(f"[WEBSOCKET RECEIVE EXCEPTION] {e}", flush=True)
            break

        if message is None:
            print("[WEBSOCKET CLOSED] ws.receive() returned None (socket closed by remote)", flush=True)
            break

        try:
            event = json.loads(message)
        except Exception as e:
            print(f"[WEBSOCKET ERROR] Failed to parse message ({e}): {message[:100]}", flush=True)
            continue

        event_name = event.get("event")
        # Log first event details
        if media_count == 0 and event_name != "media":
            print(f"[WEBSOCKET EVENT] Received event: {event}", flush=True)


        # 1. Call connected and stream started
        if event_name == "start":
            stream_id = event.get("start", {}).get("streamId")
            call_id = event.get("start", {}).get("callId")
            print(f"[STREAM START] streamId={stream_id}, callId={call_id}", flush=True)

        # 2. Audio chunks coming in from caller (8000Hz mulaw)
        elif event_name == "media":
            payload = event.get("media", {}).get("payload")
            audio_bytes = base64.b64decode(payload)
            media_count += 1
            if media_count % 50 == 1:
                print(f"[AUDIO] Received packet #{media_count} ({len(audio_bytes)} bytes)", flush=True)

        # 3. Caller pressed a phone key
        elif event_name == "dtmf":
            digit = event.get("dtmf", {}).get("digit")
            print(f"[DTMF] User pressed key: {digit}", flush=True)

        # 4. Call ended
        elif event_name == "stop":
            print(f"[STREAM STOP] Call ended for streamId={stream_id}", flush=True)
            break