import os
import requests


def ask_openai(conversation_history):
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set in .env")
    system_prompt = os.getenv("AI_SYSTEM_PROMPT", "You are a helpful voice assistant. Keep responses short and conversational, under 2 sentences.")
    messages = [{"role": "system", "content": system_prompt}] + conversation_history
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": os.getenv("OPENAI_LLM_MODEL", "gpt-4o-mini"), "messages": messages, "max_tokens": 150},
        timeout=20,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def ask_anthropic(conversation_history):
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is not set in .env")
    system_prompt = os.getenv("AI_SYSTEM_PROMPT", "You are a helpful voice assistant. Keep responses short and conversational, under 2 sentences.")
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
        json={"model": os.getenv("ANTHROPIC_LLM_MODEL", "claude-3-haiku-20240307"), "system": system_prompt, "messages": conversation_history, "max_tokens": 150},
        timeout=20,
    )
    response.raise_for_status()
    return response.json()["content"][0]["text"].strip()


def ask_gemini(conversation_history):
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is not set in .env")
    system_prompt = os.getenv("AI_SYSTEM_PROMPT", "You are a helpful voice assistant. Keep responses short and conversational, under 2 sentences.")
    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    contents = []
    for msg in conversation_history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": contents,
        "generationConfig": {"maxOutputTokens": 150},
    }
    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
        json=payload, timeout=20,
    )
    response.raise_for_status()
    return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


def generate_response(conversation_history):
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    if provider == "anthropic":
        return ask_anthropic(conversation_history)
    elif provider == "gemini":
        return ask_gemini(conversation_history)
    else:
        return ask_openai(conversation_history)
