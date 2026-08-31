import os
import io
import audioop
import requests


def synthesize_openai(text):
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set in .env")
    response = requests.post(
        "https://api.openai.com/v1/audio/speech",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "tts-1", "voice": os.getenv("OPENAI_TTS_VOICE", "alloy"), "input": text, "response_format": "pcm"},
        timeout=20,
    )
    response.raise_for_status()
    pcm_24k = response.content
    pcm_8k = audioop.ratecv(pcm_24k, 2, 1, 24000, 8000, None)[0]
    return audioop.lin2ulaw(pcm_8k, 2)


def synthesize_elevenlabs(text):
    api_key = os.getenv("ELEVENLABS_API_KEY", "")
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY is not set in .env")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
    response = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream",
        headers={"xi-api-key": api_key, "Content-Type": "application/json"},
        json={"text": text, "model_id": "eleven_turbo_v2", "output_format": "ulaw_8000"},
        timeout=20,
    )
    response.raise_for_status()
    return response.content


def synthesize_google(text):
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is not set in .env")
    payload = {
        "input": {"text": text},
        "voice": {"languageCode": "en-US", "name": "en-US-Neural2-F"},
        "audioConfig": {"audioEncoding": "MULAW", "sampleRateHertz": 8000},
    }
    response = requests.post(
        f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}",
        json=payload, timeout=20,
    )
    response.raise_for_status()
    import base64
    return base64.b64decode(response.json()["audioContent"])


def synthesize(text):
    provider = os.getenv("TTS_PROVIDER", "openai").lower()
    if provider == "elevenlabs":
        return synthesize_elevenlabs(text)
    elif provider == "google":
        return synthesize_google(text)
    else:
        return synthesize_openai(text)
