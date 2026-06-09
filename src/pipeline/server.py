"""
EXOCORTEX — Real-time Server
=============================
FastAPI server exposing the Exocortex pipeline via:
- POST /detect — text blindspot detection
- WS   /stream — real-time audio streaming + Socratic prompt delivery
"""

import sys
import os
import json
import time
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
import subprocess

from core.exocortex_core import ExocortexPipeline, QuizGenerator, NudgeEngine

# ═══════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════

WHISPER_MODEL = "tiny"   # tiny/base/small — trade accuracy for speed
WHISPER_COMPUTE = "int8" # int8 for CPU speed
ASR_ENABLED = False       # set True after whisper model downloads

# ═══════════════════════════════════════════════════════════════════════
# INIT
# ═══════════════════════════════════════════════════════════════════════

app = FastAPI(title="EXOCORTEX — Symbiotic AI Server", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

pipeline = ExocortexPipeline()
pipeline.load_state()  # restore mastery from previous sessions
quiz_engine = QuizGenerator(pipeline)
nudge_engine = NudgeEngine(pipeline)
whisper_model = None

def load_whisper():
    global whisper_model, ASR_ENABLED
    try:
        from faster_whisper import WhisperModel
        whisper_model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type=WHISPER_COMPUTE)
        ASR_ENABLED = True
        print(f"[ASR] Loaded faster-whisper '{WHISPER_MODEL}' ({WHISPER_COMPUTE})")
    except Exception as e:
        print(f"[ASR] Failed to load whisper: {e}")

load_whisper()

# ═══════════════════════════════════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════════════════════════════════

class DetectRequest(BaseModel):
    text: str

class BlindspotResult(BaseModel):
    type: str
    severity: float
    context: str

class DetectResponse(BaseModel):
    blindspots: list[BlindspotResult]
    vector: list[float]
    prompt: str | None
    prompt_complexity: float | None
    prompt_spoil: float | None
    fade_level: str
    fatigue: float
    mastery: list[float]

# ═══════════════════════════════════════════════════════════════════════
# REST ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html><head>
      <meta http-equiv="refresh" content="0;url=/client">
      <title>EXOCORTEX</title>
    </head><body>
      <p>Chuyển hướng đến <a href="/client">EXOCORTEX Client</a>...</p>
    </body></html>
    """

@app.get("/health")
async def health():
    return {"status": "ok", "asr_enabled": ASR_ENABLED, "pipeline": "ready"}

@app.post("/detect", response_model=DetectResponse)
async def detect(req: DetectRequest):
    """Detect blindspots in text and generate Socratic prompt."""
    text = req.text.strip()
    if not text:
        raise HTTPException(400, "Text is empty")

    signals = pipeline.detector.detect(text)
    vec = pipeline.detector.blindspot_vector(text)
    prompt = pipeline.generator.generate(signals, pipeline.user_model.state)

    pipeline.fading.update(pipeline.user_model)
    fade_level = pipeline.fading.get_fade_level(
        float(np.mean(pipeline.user_model.state.fading))
    )
    pipeline.save_state()  # persist mastery changes

    return DetectResponse(
        blindspots=[BlindspotResult(
            type=s.blindspot_type.name,
            severity=round(s.severity, 3),
            context=s.context
        ) for s in signals],
        vector=[round(v, 3) for v in vec.tolist()],
        prompt=prompt.text if prompt else None,
        prompt_complexity=round(prompt.complexity, 3) if prompt else None,
        prompt_spoil=round(prompt.spoil_level, 3) if prompt else None,
        fade_level=fade_level.name,
        fatigue=round(pipeline.user_model.state.fatigue, 3),
        mastery=[round(m, 3) for m in pipeline.user_model.state.mastery.tolist()]
    )

@app.post("/asr-detect")
async def asr_detect(req: DetectRequest):
    """
    Combined ASR + Detect endpoint.
    If text starts with [AUDIO], treat as transcribed audio segment
    for natural conversation flow.
    """
    text = req.text.strip()
    if text.startswith("[AUDIO]"):
        text = text[8:]  # strip marker
        pipeline.user_model.tick_second()

    return await detect(DetectRequest(text=text))

@app.post("/process-voice")
async def process_voice(file: UploadFile = File(...)):
    """
    Accept audio upload (OGG from Telegram, WAV, MP3) from Telegram bot.
    Runs ASR + blindspot detection + Socratic generation.
    Returns full pipeline result.
    """
    audio_bytes = await file.read()
    if len(audio_bytes) < 500:
        raise HTTPException(400, "Audio too short")

    text = await transcribe_audio_bytes(audio_bytes, file.filename or "audio.ogg")

    if not text:
        return {"transcript": "", "blindspots": [], "prompt": None,
                "message": "Không nghe rõ, thử lại nhé?"}

    pipeline.user_model.tick_second()
    signals = pipeline.detector.detect(text)
    prompt = pipeline.generator.generate(signals, pipeline.user_model.state)
    pipeline.fading.update(pipeline.user_model)

    fade_level = pipeline.fading.get_fade_level(
        float(np.mean(pipeline.user_model.state.fading))
    )

    return DetectResponse(
        blindspots=[BlindspotResult(
            type=s.blindspot_type.name,
            severity=round(s.severity, 3),
            context=s.context
        ) for s in signals],
        vector=[round(v, 3) for v in pipeline.detector.blindspot_vector(text).tolist()],
        prompt=prompt.text if prompt else None,
        prompt_complexity=round(prompt.complexity, 3) if prompt else None,
        prompt_spoil=round(prompt.spoil_level, 3) if prompt else None,
        fade_level=fade_level.name,
        fatigue=round(pipeline.user_model.state.fatigue, 3),
        mastery=[round(m, 3) for m in pipeline.user_model.state.mastery.tolist()]
    )


async def transcribe_audio_bytes(audio_bytes: bytes, filename: str) -> str:
    """Transcribe audio bytes (any format ffmpeg can decode) to text."""
    if not whisper_model:
        return ""

    try:
        # Convert to 16kHz mono PCM using ffmpeg
        proc = subprocess.run(
            ["ffmpeg", "-i", "pipe:0", "-ar", "16000", "-ac", "1",
             "-f", "s16le", "-acodec", "pcm_s16le", "pipe:1"],
            input=audio_bytes, capture_output=True, timeout=15
        )
        if proc.returncode != 0:
            return ""

        pcm = proc.stdout
        audio_np = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0

        if len(audio_np) < 1600:
            return ""

        segments, _ = whisper_model.transcribe(audio_np, language="vi",
                                                beam_size=1, vad_filter=True)
        text = " ".join(s.text.strip() for s in segments if s.text.strip())
        return text
    except Exception:
        return ""


# ═══════════════════════════════════════════════════════════════════════
# WEBSOCKET — Real-time Audio Streaming
# ═══════════════════════════════════════════════════════════════════════

@app.websocket("/stream")
async def stream(ws: WebSocket):
    """
    Real-time audio streaming endpoint.
    
    Client sends:
      - Binary: audio chunk (PCM 16kHz mono int16)
      - Text: {"type":"turn_end"} to signal turn boundary
      - Text: {"type":"voice_features", ...} for fatigue estimation
    
    Server replies:
      - {"type":"prompt","text":"...","complexity":0.4,...}
      - {"type":"partial_transcript","text":"..."}
      - {"type":"silence"}
    """
    await ws.accept()
    print("[WS] Client connected")

    audio_buffer = b""
    last_detect_time = 0
    detect_interval = 1.5  # run detection every 1.5s

    try:
        while True:
            msg = await ws.receive()

            if msg["type"] == "websocket.disconnect":
                break

            elif "bytes" in msg:
                audio_buffer += msg["bytes"]

                if (ASR_ENABLED and whisper_model and
                    time.time() - last_detect_time > detect_interval and
                    len(audio_buffer) > 8000):

                    text = await transcribe_audio(audio_buffer[-160000:])
                    last_detect_time = time.time()

                    if text:
                        await ws.send_json({"type": "partial_transcript", "text": text})

            elif "text" in msg:
                data = json.loads(msg["text"])
                msg_type = data.get("type")

                if msg_type == "turn_end":
                    text = ""
                    if ASR_ENABLED and whisper_model and len(audio_buffer) > 1000:
                        text = await transcribe_audio(audio_buffer[-320000:])

                    if not text:
                        await ws.send_json({"type": "silence", "reason": "empty_transcript"})
                        continue

                    signals = pipeline.detector.detect(text)

                    voice = data.get("voice_features", {})
                    if voice:
                        pipeline.user_model.update_fatigue(voice)

                    pipeline.fading.update(pipeline.user_model)

                    prompt = pipeline.generator.generate(signals, pipeline.user_model.state)

                    if prompt:
                        pipeline.user_model.record_prompt(prompt)
                        await ws.send_json({
                            "type": "prompt",
                            "text": prompt.text,
                            "target": prompt.blindspot_target.name,
                            "complexity": round(prompt.complexity, 3),
                            "spoil": round(prompt.spoil_level, 3),
                            "blindspots": [
                                {"type": s.blindspot_type.name, "severity": round(s.severity, 3)}
                                for s in signals[:3]
                            ]
                        })
                    else:
                        fade_level = pipeline.fading.get_fade_level(
                            float(np.mean(pipeline.user_model.state.fading))
                        )
                        await ws.send_json({
                            "type": "silence",
                            "reason": "no_suitable_prompt",
                            "fade_level": fade_level.name
                        })

                    audio_buffer = b""

                elif msg_type == "voice_features":
                    pipeline.user_model.update_fatigue(data.get("features", {}))
                    pipeline.fading.update(pipeline.user_model)

    except WebSocketDisconnect:
        print("[WS] Client disconnected")
    except Exception as e:
        print(f"[WS] Error: {e}")
        try:
            await ws.close()
        except Exception:
            pass


async def transcribe_audio(audio_bytes: bytes) -> str:
    """Transcribe audio bytes to text using faster-whisper."""
    if not whisper_model:
        return ""

    try:
        audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        if len(audio_np) < 1600:  # <0.1s at 16kHz
            return ""

        segments, _ = whisper_model.transcribe(audio_np, language="vi",
                                                beam_size=1, vad_filter=True)

        text = " ".join(s.text.strip() for s in segments if s.text.strip())
        return text
    except Exception as e:
        print(f"[ASR] Transcription error: {e}")
        return ""


# ═══════════════════════════════════════════════════════════════════════
# STATIC — PWA Client
# ═══════════════════════════════════════════════════════════════════════

CLIENT_DIR = Path(__file__).parent.parent / "client"
CLIENT_DIR.mkdir(exist_ok=True)

@app.get("/client")
@app.get("/client/")
async def client_html():
    client_file = CLIENT_DIR / "index.html"
    if client_file.exists():
        return HTMLResponse(client_file.read_text())
    return HTMLResponse("<h1>Client not built yet</h1>")


# ═══════════════════════════════════════════════════════════════════════
# PROACTIVE — Quiz, Nudge, Reflection, Status
# ═══════════════════════════════════════════════════════════════════════

class QuizSubmitRequest(BaseModel):
    quiz_id: str
    domain_idx: int
    score: float

@app.get("/status")
async def status():
    return {
        "status": "ok",
        "asr_enabled": ASR_ENABLED,
        "cognitive": pipeline.get_status(),
    }

@app.get("/quiz")
async def get_quiz(n: int = 3):
    questions = quiz_engine.generate_quiz(n)
    return {"quiz": questions, "generated_at": time.time()}

@app.post("/quiz/submit")
async def submit_quiz(req: QuizSubmitRequest):
    quiz_engine.submit_answer(req.quiz_id, req.domain_idx, req.score)
    pipeline.save_state()
    return {
        "accepted": True,
        "new_mastery": round(float(pipeline.user_model.state.mastery[req.domain_idx]), 3),
        "status": pipeline.get_status(),
    }

@app.get("/nudge")
async def get_nudge():
    nudge = nudge_engine.get_nudge()
    if nudge:
        return {"nudge": nudge, "has_nudge": True}
    return {"has_nudge": False, "next_available_in": round(nudge_engine.nudge_interval - (time.time() - nudge_engine.last_nudge_time), 0)}

@app.get("/reflect")
async def get_reflection():
    return nudge_engine.daily_reflection()


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8083))
    print(f"🧠 EXOCORTEX Server starting on :{port}")
    print(f"   ASR: {'enabled' if ASR_ENABLED else 'disabled'}")
    print("   REST: POST /detect  |  WS: /stream")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
