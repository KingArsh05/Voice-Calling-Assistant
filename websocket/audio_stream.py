import json
import base64
import os
import threading

from services.stt import transcribe, mulaw_to_pcm
from services.llm import generate_response
from services.tts import synthesize


# How many mulaw bytes to buffer before sending to STT.
# At 8kHz mulaw, 1 byte = 1 sample = 0.125ms
# 8000 bytes = 1 second of audio  →  good chunk for STT accuracy
BUFFER_THRESHOLD_BYTES = int(os.getenv("AUDIO_BUFFER_BYTES", "24000"))  # ~3 seconds


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
            "payload": payload,
        },
    }
    if stream_id:
        message["streamId"] = stream_id
    ws.send(json.dumps(message))


def clear_audio(ws, stream_id=None):
    """
    Clears currently playing audio buffer in Plivo (useful when caller interrupts).
    """
    message = {"event": "clearAudio"}
    if stream_id:
        message["streamId"] = stream_id
    ws.send(json.dumps(message))


def run_pipeline(ws, stream_id, mulaw_buffer, conversation_history):
    """
    Runs the STT → LLM → TTS pipeline in a background thread so the
    WebSocket receive loop is not blocked while waiting for AI APIs.
    """
    try:
        # ── 1. Speech-to-Text ──────────────────────────────────────────────
        print(f"[STT] Transcribing {len(mulaw_buffer)} bytes of audio...", flush=True)
        transcript = transcribe(mulaw_buffer)
        print(f"[STT] Transcript: '{transcript}'", flush=True)

        if not transcript:
            print("[STT] Empty transcript, skipping response.", flush=True)
            return

        # ── 2. LLM ─────────────────────────────────────────────────────────
        conversation_history.append({"role": "user", "content": transcript})
        print(f"[LLM] Sending {len(conversation_history)} messages to LLM...", flush=True)
        ai_response = generate_response(conversation_history)
        conversation_history.append({"role": "assistant", "content": ai_response})
        print(f"[LLM] Response: '{ai_response}'", flush=True)

        # ── 3. Text-to-Speech ──────────────────────────────────────────────
        print(f"[TTS] Synthesizing response...", flush=True)
        audio_bytes = synthesize(ai_response)
        print(f"[TTS] Generated {len(audio_bytes)} bytes of audio", flush=True)

        # ── 4. Send audio back to Plivo → caller hears it ──────────────────
        play_audio(ws, audio_bytes, stream_id)
        print(f"[PLAY] Sent audio to caller via playAudio event", flush=True)

    except Exception as e:
        print(f"[PIPELINE ERROR] {e}", flush=True)


def handle_stream(ws):
    """
    Handles the live bidirectional WebSocket audio stream from Plivo.

    Flow:
      1. Receive 'start' event → note streamId / callId
      2. Buffer incoming 'media' events (mulaw 8kHz audio from caller)
      3. When buffer crosses BUFFER_THRESHOLD_BYTES, launch STT→LLM→TTS
         pipeline in a background thread and reset the buffer.
      4. Send generated audio back via 'playAudio' event.
      5. Stop on 'stop' event or disconnection.
    """
    print("[WEBSOCKET CONNECTED] Plivo client opened WebSocket connection", flush=True)
    stream_id = None
    call_id = None
    media_count = 0
    audio_buffer = bytearray()         # accumulates mulaw bytes from caller
    conversation_history = []          # tracks STT/LLM turns for context
    pipeline_running = threading.Event()  # prevents overlapping pipeline runs

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

        # ── 1. Stream started ──────────────────────────────────────────────
        if event_name == "start":
            stream_id = event.get("start", {}).get("streamId")
            call_id   = event.get("start", {}).get("callId")
            print(f"[STREAM START] streamId={stream_id}, callId={call_id}", flush=True)

        # ── 2. Caller audio arriving ───────────────────────────────────────
        elif event_name == "media":
            payload = event.get("media", {}).get("payload", "")
            chunk   = base64.b64decode(payload)
            audio_buffer.extend(chunk)
            media_count += 1

            if media_count % 50 == 1:
                print(f"[AUDIO] Received packet #{media_count}, buffer={len(audio_buffer)} bytes", flush=True)

            # When we have enough audio AND no pipeline is currently running,
            # drain the buffer and kick off the STT→LLM→TTS pipeline.
            if len(audio_buffer) >= BUFFER_THRESHOLD_BYTES and not pipeline_running.is_set():
                pipeline_running.set()
                chunk_to_process = bytes(audio_buffer)
                audio_buffer.clear()

                def _run(buf=chunk_to_process, sid=stream_id, hist=conversation_history, ev=pipeline_running):
                    try:
                        run_pipeline(ws, sid, buf, hist)
                    finally:
                        ev.clear()

                t = threading.Thread(target=_run, daemon=True)
                t.start()

        # ── 3. DTMF (keypad press) ─────────────────────────────────────────
        elif event_name == "dtmf":
            digit = event.get("dtmf", {}).get("digit")
            print(f"[DTMF] User pressed key: {digit}", flush=True)

        # ── 4. Call ended ──────────────────────────────────────────────────
        elif event_name == "stop":
            print(f"[STREAM STOP] Call ended for streamId={stream_id}", flush=True)
            break

        # ── 5. Playback confirmation ───────────────────────────────────────
        elif event_name == "playedStream":
            print(f"[PLAYED] Plivo confirmed audio playback finished", flush=True)

        elif event_name == "clearedAudio":
            print(f"[CLEARED] Plivo confirmed audio buffer cleared", flush=True)