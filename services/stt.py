import os
import io
import audioop
import wave
import requests


def transcribe_openai(pcm_bytes):
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set in .env")
    wav_buf = io.BytesIO()
    with wave.open(wav_buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(8000)
        wf.writeframes(pcm_bytes)
    wav_buf.seek(0)
    response = requests.post(
        "https://api.openai.com/v1/audio/transcriptions",
        headers={"Authorization": f"Bearer {api_key}"},
        files={"file": ("audio.wav", wav_buf, "audio/wav")},
        data={"model": "whisper-1", "language": "en"},
        timeout=15,
    )
    response.raise_for_status()
    return response.json().get("text", "").strip()


def transcribe_deepgram(pcm_bytes):
    api_key = os.getenv("DEEPGRAM_API_KEY", "")
    if not api_key:
        raise ValueError("DEEPGRAM_API_KEY is not set in .env")
    response = requests.post(
        "https://api.deepgram.com/v1/listen?model=nova-2&language=en&encoding=linear16&sample_rate=8000&channels=1",
        headers={"Authorization": f"Token {api_key}", "Content-Type": "audio/raw"},
        data=pcm_bytes,
        timeout=15,
    )
    response.raise_for_status()
    alts = (
        response.json()
        .get("results", {})
        .get("channels", [{}])[0]
        .get("alternatives", [{}])
    )
    return alts[0].get("transcript", "").strip() if alts else ""


def transcribe_google(pcm_bytes):
    import base64
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is not set in .env")
    audio_b64 = base64.b64encode(pcm_bytes).decode("utf-8")
    payload = {
        "config": {"encoding": "LINEAR16", "sampleRateHertz": 8000, "languageCode": "en-US"},
        "audio": {"content": audio_b64},
    }
    response = requests.post(
        f"https://speech.googleapis.com/v1/speech:recognize?key={api_key}",
        json=payload, timeout=15,
    )
    response.raise_for_status()
    results = response.json().get("results", [])
    if not results:
        return ""
    return results[0].get("alternatives", [{}])[0].get("transcript", "").strip()


def mulaw_to_pcm(mulaw_bytes):
    return audioop.ulaw2lin(mulaw_bytes, 2)


def transcribe(mulaw_bytes):
    provider = os.getenv("STT_PROVIDER", "openai").lower()
    pcm_bytes = mulaw_to_pcm(mulaw_bytes)
    if provider == "deepgram":
        return transcribe_deepgram(pcm_bytes)
    elif provider == "google":
        return transcribe_google(pcm_bytes)
    else:
        return transcribe_openai(pcm_bytes)
