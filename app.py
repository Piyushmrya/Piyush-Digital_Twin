import os
import json
import base64
from typing import Optional, List, Dict
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import services

app = FastAPI(title="Piyush Mourya - AI Voice Twin")

# CORS middleware for open web access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request schemas
class TextChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []
    use_tts: bool = True

@app.get("/api/health")
async def health_check():
    has_openai = bool(services.OPENAI_API_KEY)
    has_gemini = bool(services.GEMINI_API_KEY)
    return {
        "status": "healthy",
        "openai_available": has_openai,
        "gemini_available": has_gemini,
        "edge_tts_available": True,
        "mode": "openai" if has_openai else ("gemini" if has_gemini else "keyless-edge-tts")
    }

@app.post("/api/chat-text")
async def chat_text(req: TextChatRequest):
    """
    Direct text input endpoint (e.g. when browser Web Speech API transcribes live).
    Returns text response + synthesized audio.
    """
    user_text = req.message.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Empty message")

    response_text = await services.generate_response(user_text, req.history)

    audio_base64 = None
    if req.use_tts:
        try:
            audio_bytes = await services.synthesize_speech(response_text)
            audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        except Exception as e:
            print(f"TTS error during chat-text: {e}")

    return {
        "user_message": user_text,
        "response_text": response_text,
        "audio_base64": audio_base64
    }

@app.post("/api/chat-voice")
async def chat_voice(
    file: UploadFile = File(...),
    history_json: Optional[str] = Form("[]"),
    client_transcript: Optional[str] = Form(None)
):
    """
    Full audio voice endpoint: receives recorded audio blob.
    Uses Whisper for STT (falling back to client_transcript if provided),
    runs LLM in persona, then synthesizes speech audio.
    """
    history = []
    if history_json:
        try:
            history = json.loads(history_json)
        except Exception:
            pass

    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="No audio data received")

    # 1. Speech to Text: Try Whisper, fallback to client_transcript if Whisper fails/unconfigured
    user_transcript = ""
    try:
        user_transcript = await services.transcribe_audio(audio_bytes, file.filename or "speech.webm")
    except Exception as e:
        print(f"Whisper STT note: {e}")
        if client_transcript and client_transcript.strip():
            user_transcript = client_transcript.strip()
        else:
            # If both whisper and client transcript are empty, provide friendly fallback
            user_transcript = "Tell me about yourself"

    # 2. LLM response in Piyush's persona
    response_text = await services.generate_response(user_transcript, history)

    # 3. Text to Speech
    audio_base64 = None
    try:
        audio_out = await services.synthesize_speech(response_text)
        audio_base64 = base64.b64encode(audio_out).decode("utf-8")
    except Exception as e:
        print(f"TTS synthesis error: {e}")

    return {
        "user_transcript": user_transcript,
        "response_text": response_text,
        "audio_base64": audio_base64
    }

# Serve the web UI at root
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Piyush Voice Bot is running. Static UI not found.</h1>")

# Mount static folder if it exists
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=7860, reload=True)
