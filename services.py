import os
import io
import asyncio
import tempfile
from typing import Optional, List, Dict
from dotenv import load_dotenv

load_dotenv()

# Check for API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

# Initialize OpenAI client if key present
openai_client = None
if OPENAI_API_KEY:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        print(f"Warning: Failed to initialize OpenAI client: {e}")

# Initialize Google GenAI client if key present
genai_client = None
if GEMINI_API_KEY:
    try:
        from google import genai
        genai_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Warning: Failed to initialize Gemini client: {e}")

from persona import PIYUSH_PERSONA_PROMPT


async def transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """
    Transcribes audio using OpenAI Whisper if OPENAI_API_KEY is available.
    """
    if openai_client:
        try:
            # Create in-memory file for OpenAI Whisper
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = filename
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
            return transcript.strip()
        except Exception as e:
            print(f"OpenAI Whisper error: {e}")
            raise e
    raise ValueError("No server-side STT API key configured.")


async def generate_response(user_text: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
    """
    Generates persona response using OpenAI (default) or Gemini fallback.
    """
    if conversation_history is None:
        conversation_history = []

    # 1. Try OpenAI if key is present
    if openai_client:
        try:
            messages = [{"role": "system", "content": PIYUSH_PERSONA_PROMPT}]
            for msg in conversation_history[-6:]:  # Keep recent context
                messages.append({"role": msg["role"], "content": msg["content"]})
            messages.append({"role": "user", "content": user_text})

            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                max_tokens=250
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI completion error: {e}. Checking fallbacks...")

    # 2. Try Gemini fallback if present
    if genai_client:
        try:
            full_prompt = f"{PIYUSH_PERSONA_PROMPT}\n\nRecent Conversation:\n"
            for msg in conversation_history[-4:]:
                full_prompt += f"{msg['role']}: {msg['content']}\n"
            full_prompt += f"user: {user_text}\nPiyush:"

            response = genai_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=full_prompt
            )
            return response.text.strip()
        except Exception as e:
            print(f"Gemini fallback error: {e}")

    # 3. Graceful offline/mock response if no keys exist
    return (
        "Hey! I'm Piyush. It looks like no API keys are currently configured on the server, "
        "but my system is ready to connect to OpenAI or Gemini as soon as the key is added in Hugging Face secrets!"
    )


async def synthesize_speech(text: str, voice: str = "en-US-GuyNeural") -> bytes:
    """
    Converts text to speech audio bytes.
    First tries OpenAI TTS if key available, otherwise falls back to free high-fidelity edge-tts.
    """
    # 1. Try OpenAI TTS if configured
    if openai_client:
        try:
            # Map default or custom voice to OpenAI voice (alloy, echo, fable, onyx, nova, shimmer)
            openai_voice = "onyx"  # Solid confident male tone suitable for Piyush
            response = openai_client.audio.speech.create(
                model="tts-1",
                voice=openai_voice,
                input=text
            )
            return response.content
        except Exception as e:
            print(f"OpenAI TTS error: {e}. Falling back to edge-tts...")

    # 2. Free high-quality Microsoft Edge TTS (Zero API key needed)
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        audio_stream = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_stream.write(chunk["data"])
        return audio_stream.getvalue()
    except Exception as e:
        print(f"edge-tts error: {e}")
        raise e
