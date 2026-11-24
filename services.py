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
        # Explicitly set api_version='v1beta' so flash models are recognized on Linux/Render
        genai_client = genai.Client(api_key=GEMINI_API_KEY, http_options={"api_version": "v1beta"})
    except Exception as e:
        print(f"Warning: Failed to initialize Gemini client: {e}")

from persona import build_system_prompt, KNOWLEDGE


def get_offline_persona_response(user_text: str) -> str:
    """
    Intelligent offline fallback that responds strictly in Piyush's persona
    matching topics and keywords, keeping answers crisp, natural, and never stiff.
    """
    text = user_text.lower()

    # Specific greetings / slang
    if any(k in text for k in ["broski", "bro", "what's going on", "wassup", "what's up", "hey", "hello", "hi"]):
        if "hobbies" not in text and "project" not in text:
            return "Hey! Doing great. What's on your mind? Feel free to ask about my projects, work, or anything you're curious about."

    if any(k in text for k in ["join", "hire", "company", "work with us", "role", "job", "offer"]):
        return "Definitely! If there are challenging AI systems or agentic infra to architect, I'd love to learn more about what you guys are building."

    if any(k in text for k in ["life story", "background", "about you", "who are you", "introduce", "tell me about yourself"]):
        return "I graduated from IIT Bombay in Engineering Physics and transitioned straight into AI. In my previous role I built production enterprise agentic systems, and I love tinkering on open-source and side projects."

    if any(k in text for k in ["superpower", "number one superpower"]):
        return "My number one superpower is my drive for knowledge. I believe knowledge is power, so once I understand the fundamentals, I have the confidence to tackle any challenge and deliver on my promises."

    if any(k in text for k in ["strength", "best at", "greatest strength"]):
        return "My biggest strength is that I'm confident, dependable, and I consistently deliver on what I promise."

    if any(k in text for k in ["weakness", "flaw"]):
        return "My biggest weakness is perfectionism. Wanting everything to be completely flawless can sometimes slow down shipping things that would be better off delivered earlier."

    if any(k in text for k in ["grow", "growth", "improve", "areas to grow", "want to learn"]):
        return "My top three growth areas are getting more hands-on with DevOps, diving deeper into low-level system design and low-latency databases, and learning more classical machine learning alongside Gen AI."

    if any(k in text for k in ["misconception", "coworker", "peers think", "misunderstand"]):
        return "People sometimes assume my physics and competitive math background makes me theoretical, but I'm actually an obsessive builder who loves shipping and writing solid tests."

    if any(k in text for k in ["push", "boundary", "limit", "challenge"]):
        return "I push my limits by diving straight into unfamiliar territory—like building hardware robots at IIT Roorkee, contributing upstream to Google ADK, or hacking together my own controllers."

    # Specific check if company name is directly asked
    if any(k in text for k in ["company name", "which company", "name of company", "where did you work", "employer"]):
        return "I previously worked as an AI Engineer at Genpact, building enterprise agent systems."

    # Day to day work & Genpact metadata platform
    if any(k in text for k in ["your work", "day to day", "genpact", "at work", "daily work", "what do you do", "metadata platform", "major project", "work project", "enterprise"]):
        return "At Genpact, I work on an enterprise metadata platform for B2B clients. Day-to-day, I work closely with business users to understand where they get stuck, debug query issues, and build an agentic natural-language query bot with custom MCP tools on our 7TB data backend so users get instant lineage and ownership answers without wading through complex dashboards."

    # Open source contribution apart from company
    if any(k in text for k in ["open source", "adk repo", "apart from work", "google adk contribution", "contributed"]):
        return "On the open-source front, I contributed MCP sampling support to Google's Agent Development Kit, enabling agent tools to request client-side LLM completions, which got merged via PR 4718."

    # Personal project: OneSearchGo with the real diary/life-logging motivation
    if any(k in text for k in ["personal project", "onesearchgo", "side project", "built for yourself", "diary", "side build"]):
        return "I built OneSearchGo because I write daily journals and notes, but found it really hard to remember and piece together everything across SMS, voice dumps, screenshots, and logs. So I built an AI agent on FastAPI and pgvector where I dump all my daily data and retrieve anything instantly through semantic search and SQL."

    # Hobbies & lifestyle (strictly non-diet)
    if any(k in text for k in ["hobby", "hobbies", "dance", "dancing", "workout", "gym", "free time", "outside", "lifestyle", "memes", "politics", "outside of coding"]):
        return "Outside coding, I hit the gym regularly, love dancing, and stay plugged into tech memes and global politics. I also love tinkering with hardware, like building custom remotes for my room."

    # College & Graduation / Major
    if any(k in text for k in ["graduate", "graduation", "college", "university", "major", "degree", "branch", "iit", "physics"]):
        return "I graduated from IIT Bombay in 2024 with a B.Tech in Engineering Physics. It gave me a super strong mathematical and first-principles foundation that I now use every day in AI engineering."

    # Location & Current City
    if any(k in text for k in ["where do you live", "where are you from", "location", "based out of", "current city"]):
        return "I'm currently based in Bengaluru, India, working as an AI Engineer."

    # Tech stack & Preferred languages
    if any(k in text for k in ["tech stack", "languages", "tools", "frameworks", "technical skills", "favourite language", "favorite language"]):
        return "Python is my primary language, and I specialize heavily in agentic AI using Google ADK, LangGraph, CrewAI, and MCP. I have a deep foundation in transformers, LLMs, and classical ML, along with strong system design, DSA, and AWS coursework."

    # Day / Small talk: "How was your day?", "How are you doing?"
    if any(k in text for k in ["how was your day", "how's your day", "how are you", "how are you doing", "how's it going"]):
        return "My day's going great! Been hacking on AI systems and tinkering with models. How's yours going?"

    # Mechatronics / Hardware / Robot / Neon controller
    if any(k in text for k in ["robot", "mechatronics", "hardware", "neon", "remote", "roorkee"]):
        return "I love hands-on hardware. During college I built an automated washbasin cleaner robot at IIT Roorkee, and recently I've been building a custom RF remote to control the neon posters in my room."

    # Food / Vegetarian
    if any(k in text for k in ["food", "diet", "vegetarian", "eat", "favorite food"]):
        return "I'm 100% vegetarian and love staying healthy and fit, though good street food or a solid paneer dish always hits the spot."

    # Safe Guardrail for queries outside your domain or overly personal
    if any(k in text for k in ["girlfriend", "relationship", "salary", "politics opinion", "who will win"]):
        return "Haha, I prefer keeping my focus on building cool tech, engineering agents, and working out. What else would you like to know about my projects?"

    # Natural, concise general conversational fallback
    return "Yeah, absolutely! Feel free to ask about my previous engineering work, open-source projects, or anything else you'd like to explore."



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


async def generate_response(
    user_text: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    session_groundings: Optional[List[str]] = None
) -> tuple[str, str]:
    """
    Generates persona response using OpenAI (default) or Gemini fallback.
    Takes user_text, conversation_history, and optional session_groundings.
    Returns (response_text, model_name).
    """
    if conversation_history is None:
        conversation_history = []
    if session_groundings is None:
        session_groundings = []

    # Detect repeated consecutive queries to prevent repetitive agreement loops (e.g. "Yeah, exactly that")
    repetition_hint = ""
    if conversation_history:
        user_msgs = [m for m in conversation_history if m.get("role") == "user"]
        if user_msgs and user_msgs[-1].get("content", "").strip().lower() == user_text.strip().lower():
            repetition_hint = "\n[CRITICAL NOTE: The interviewer asked this exact question again. Rephrase naturally from a fresh angle or give a different concrete example. DO NOT say 'Yeah, exactly that' and DO NOT repeat your previous response.]\n"

    # 1. Try OpenAI if key is present
    system_prompt = build_system_prompt(user_text, session_groundings)
    if repetition_hint:
        system_prompt += repetition_hint

    if openai_client:
        try:
            model_name = "gpt-4o-mini"
            messages = [{"role": "system", "content": system_prompt}]
            for msg in conversation_history[-6:]:  # Keep recent context
                messages.append({"role": msg["role"], "content": msg["content"]})
            messages.append({"role": "user", "content": user_text})

            response = openai_client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.5,
                max_tokens=150
            )
            return response.choices[0].message.content.strip(), model_name
        except Exception as e:
            print(f"OpenAI completion error: {e}. Checking fallbacks...")

    # 2. Try Gemini fallback if present
    if genai_client:
        for gemini_model in ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-flash-lite-latest", "gemini-flash-latest"]:
            try:
                full_prompt = f"{system_prompt}\nRecent Conversation Context:\n"
                for msg in conversation_history[-6:]:
                    speaker = "Interviewer" if msg["role"] == "user" else "Piyush"
                    full_prompt += f"{speaker}: {msg['content']}\n"
                if repetition_hint:
                    full_prompt += f"{repetition_hint}\n"
                full_prompt += f"Interviewer: {user_text}\nPiyush (1 to 2 spoken sentences, zero fluff):"

                response = genai_client.models.generate_content(
                    model=gemini_model,
                    contents=full_prompt,
                    config={
                        "temperature": 0.5,
                        "max_output_tokens": 150
                    }
                )
                if response.text and response.text.strip():
                    return response.text.strip(), gemini_model
            except Exception as e:
                print(f"Gemini {gemini_model} error: {e}")

    # 3. Intelligent in-character persona fallback (zero leakage of system or API info)
    return get_offline_persona_response(user_text), "offline-rule-matcher"


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
