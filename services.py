import os
import io
import re
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


def get_offline_persona_response(user_text: str) -> str:
    """
    Intelligent offline fallback that responds strictly in Piyush's persona
    matching topics and keywords, without ever exposing technical or API key details.
    """
    text = user_text.lower()

    if any(k in text for k in ["life story", "background", "about you", "who are you", "introduce"]):
        return (
            "I graduated from IIT Bombay in Engineering Physics, where I developed a strong foundation "
            "in first-principles thinking and competitive math. That curiosity led me to AI and robotics, "
            "and today I work as an AI Engineer at Genpact building production agentic systems on Google ADK "
            "and MCP, while actively contributing upstream to open source."
        )

    if any(k in text for k in ["superpower", "strength", "best at", "greatest strength"]):
        return (
            "My number one superpower is bridging first-principles analytical thinking with practical execution. "
            "Coming from engineering physics, I don't treat complex distributed architectures or AI models as "
            "black boxes. I break them down to fundamentals, isolate bottlenecks, and ship clean, tested code."
        )

    if any(k in text for k in ["grow", "growth", "improve", "areas to grow", "weakness"]):
        return (
            "The top three areas I'm focused on growing in are: first, ultra-low latency real-time voice and multimodal "
            "agentic loops. Second, automated evaluation harnesses and statistical LLM-as-a-judge frameworks for production. "
            "And third, large-scale distributed inference infrastructure."
        )

    if any(k in text for k in ["misconception", "coworker", "peers think", "misunderstand"]):
        return (
            "A common misconception people have when they see my Engineering Physics degree and competitive math "
            "background is that I'm purely academic or theoretical. In reality, I'm a relentless builder who cares "
            "deeply about shipping production code, rock-solid tests, and reliable systems."
        )

    if any(k in text for k in ["push", "boundary", "limit", "challenge"]):
        return (
            "I push my boundaries by diving headfirst into uncharted domains until I can build them from scratch. "
            "Whether that was building an automated washbasin cleaner robot at IIT Roorkee, contributing upstream "
            "to Google's Agent Development Kit, or hacking custom hardware controllers for my room's neon posters, "
            "I thrive when exploring outside my comfort zone."
        )

    if any(k in text for k in ["adk", "genpact", "work", "project", "onesearchgo", "mcp"]):
        return (
            "At Genpact, I architected an enterprise agentic query platform handling over 30K daily queries across 7TB "
            "of multi-database data using Google ADK and MCP. I also implemented MCP sampling support for Google's ADK "
            "which was merged upstream, and on the side, I built OneSearchGo to unify personal life-logging."
        )

    if any(k in text for k in ["hobby", "free time", "outside", "lifestyle", "workout", "dance", "diet"]):
        return (
            "Outside of engineering, I hit the gym regularly to stay fit, follow a vegetarian lifestyle, and love dancing. "
            "I also love tinkering with hardware, like building my own remote control for my room's neon lights, and keeping "
            "up with everything from AI research to internet memes."
        )

    # General conversational fallback staying 100% in character
    return (
        "That's an interesting question! As an AI engineer from IIT Bombay, I love breaking down complex ideas "
        "from first principles. Feel free to ask me about my engineering work at Genpact, my open-source contributions, "
        "or what I like building in my free time."
    )



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

    # 3. Intelligent in-character persona fallback (zero leakage of system or API info)
    return get_offline_persona_response(user_text)


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
