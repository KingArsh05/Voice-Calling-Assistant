import json
import base64

def handle_stream(ws):
    while True:
        message = ws.receive()

        if message is None:
            break

        event = json.loads(message)

        if event["event"] == "start":
            print("STREAM STARTED")
            print(event["start"]["streamId"])

        elif event["event"] == "media":
            audio_bytes = base64.b64decode(
                event["media"]["payload"]
            )

            print("AUDIO RECEIVED:", len(audio_bytes), "bytes")

        elif event["event"] == "stop":
            print("STREAM STOPPED")
            break