import os
import json
import base64
import time
from datetime import datetime
from typing import Optional, List, Dict
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import gradio as gr

# Hugging Face ZeroGPU compatibility
try:
    import spaces
    @spaces.GPU
    def zero_gpu_probe():
        return True
    # Run once at startup so ZeroGPU registers the function
    zero_gpu_probe()
except Exception:
    pass

import services

app = FastAPI(title="Piyush Mourya - AI Voice Twin")

# Conversation logging directory
LOGS_DIR = os.path.join(os.path.dirname(__file__), "conversations")
os.makedirs(LOGS_DIR, exist_ok=True)
CONVO_LOG_FILE = os.path.join(LOGS_DIR, "logs.jsonl")

def log_interaction(
    input_type: str,
    user_text: str,
    bot_response: str,
    timing_metrics: dict,
    model_used: str = "unknown",
    client_ip: str = "unknown"
):
    """
    Silently records user questions, bot responses, model used, and stage-by-stage timings in JSONL format.
    """
    try:
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "type": input_type,
            "model_used": model_used,
            "user_query": user_text,
            "bot_response": bot_response,
            "latency_ms": timing_metrics,
            "ip": client_ip
        }
        with open(CONVO_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Logging notice: {e}")

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
async def chat_text(req: TextChatRequest, request: Request):
    """
    Direct text input endpoint (e.g. when browser Web Speech API transcribes live).
    Returns text response + synthesized audio with stage timings.
    """
    start_total = time.time()
    user_text = req.message.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Empty message")

    # 1. LLM Generation
    t_llm_start = time.time()
    response_text, model_name = await services.generate_response(user_text, req.history)
    llm_ms = round((time.time() - t_llm_start) * 1000, 2)

    # 2. TTS Generation
    audio_base64 = None
    tts_ms = 0.0
    if req.use_tts:
        t_tts_start = time.time()
        try:
            audio_bytes = await services.synthesize_speech(response_text)
            audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        except Exception as e:
            print(f"TTS error during chat-text: {e}")
        tts_ms = round((time.time() - t_tts_start) * 1000, 2)

    total_ms = round((time.time() - start_total) * 1000, 2)
    timing_metrics = {
        "stt_ms": 0.0,
        "llm_ms": llm_ms,
        "tts_ms": tts_ms,
        "total_ms": total_ms
    }

    # Silently log interaction with timing metrics & model name
    client_ip = request.client.host if request.client else "unknown"
    log_interaction(
        input_type="text",
        user_text=user_text,
        bot_response=response_text,
        timing_metrics=timing_metrics,
        model_used=model_name,
        client_ip=client_ip
    )

    return {
        "user_message": user_text,
        "response_text": response_text,
        "model_used": model_name,
        "audio_base64": audio_base64,
        "timings": timing_metrics
    }

@app.post("/api/chat-voice")
async def chat_voice(
    request: Request,
    file: UploadFile = File(...),
    history_json: Optional[str] = Form("[]"),
    client_transcript: Optional[str] = Form(None)
):
    """
    Full audio voice endpoint: receives recorded audio blob.
    Uses Whisper for STT (falling back to client_transcript if provided),
    runs LLM in persona, then synthesizes speech audio with stage timings.
    """
    start_total = time.time()
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
    t_stt_start = time.time()
    user_transcript = ""
    try:
        user_transcript = await services.transcribe_audio(audio_bytes, file.filename or "speech.webm")
    except Exception as e:
        print(f"Whisper STT note: {e}")
        if client_transcript and client_transcript.strip():
            user_transcript = client_transcript.strip()
        else:
            user_transcript = "Tell me about yourself"
    stt_ms = round((time.time() - t_stt_start) * 1000, 2)

    # 2. LLM response in Piyush's persona
    t_llm_start = time.time()
    response_text, model_name = await services.generate_response(user_transcript, history)
    llm_ms = round((time.time() - t_llm_start) * 1000, 2)

    # 3. Text to Speech
    t_tts_start = time.time()
    audio_base64 = None
    try:
        audio_out = await services.synthesize_speech(response_text)
        audio_base64 = base64.b64encode(audio_out).decode("utf-8")
    except Exception as e:
        print(f"TTS synthesis error: {e}")
    tts_ms = round((time.time() - t_tts_start) * 1000, 2)

    total_ms = round((time.time() - start_total) * 1000, 2)
    timing_metrics = {
        "stt_ms": stt_ms,
        "llm_ms": llm_ms,
        "tts_ms": tts_ms,
        "total_ms": total_ms
    }

    # Silently log interaction with timing metrics & model name
    client_ip = request.client.host if request.client else "unknown"
    log_interaction(
        input_type="voice",
        user_text=user_transcript,
        bot_response=response_text,
        timing_metrics=timing_metrics,
        model_used=model_name,
        client_ip=client_ip
    )

    return {
        "user_transcript": user_transcript,
        "response_text": response_text,
        "model_used": model_name,
        "audio_base64": audio_base64,
        "timings": timing_metrics
    }

    return {
        "user_transcript": user_transcript,
        "response_text": response_text,
        "audio_base64": audio_base64
    }

# Serve the static UI directly at /app
@app.get("/app", response_class=HTMLResponse)
async def serve_direct_app():
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>App loading...</h1>")

# Mount static folder for assets
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Create Gradio demo serving an interactive iframe with full permissions (scripts, microphone, autoplay)
with gr.Blocks(title="Piyush Mourya - AI Voice Twin", head='<meta name="viewport" content="width=device-width, initial-scale=1.0">') as demo:
    gr.HTML(
        '<iframe src="/app" allow="microphone; autoplay; clipboard-write;" sandbox="allow-scripts allow-same-origin allow-forms allow-popups" style="position:fixed; top:0; left:0; width:100vw; height:100vh; border:none; z-index:999999;"></iframe>'
    )

# Mount FastAPI app onto Gradio at root
app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
