#!/usr/bin/env python3
"""
月下长安 — TTS 语音服务后端
VoxCPM2：参考音 Clone（锁定音色）+ MOOD 语气控制

启动:
  python frontend/server_tts.py

API:
  POST /tts  — 生成语音，返回 WAV 字节流
  GET  /tts/status — 健康检查
"""

import os
import time
import threading
from pathlib import Path

import numpy as np
import soundfile as sf
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from tts_voice_config import (
    CLONE_GEN_KWARGS,
    DESIGN_GEN_KWARGS,
    get_mood_style,
    get_voice_desc,
    normalize_mood,
)

MODEL_PATH = os.environ.get(
    "VOXCPM2_PATH",
    r"F:\ComfyUI_V6.0\ComfyUI-WorkFisher-V2\ComfyUI\models\VoxCPM2",
)

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
VOICE_DIR = ASSETS_DIR / "voices"
VOICE_REF_DIR = ASSETS_DIR / "voice_refs"
VOICE_DIR.mkdir(parents=True, exist_ok=True)
VOICE_REF_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="月下长安 TTS", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class TTSRequest(BaseModel):
    charId: str
    text: str
    mood: str = "neutral"
    turnCount: int = 0
    pageIdx: int = 0


class TTSStatus(BaseModel):
    status: str
    model_loaded: bool
    uptime: float
    clone_refs: dict[str, bool]


_model: object | None = None
_start_time: float = time.time()
_generate_lock = threading.Lock()


def get_ref_path(char_id: str) -> Path | None:
    path = VOICE_REF_DIR / f"{char_id}.wav"
    return path if path.is_file() else None


def load_model():
    global _model
    print(f"[TTS] Loading VoxCPM2 model from: {MODEL_PATH}", flush=True)
    from voxcpm.core import VoxCPM

    _model = VoxCPM(
        voxcpm_model_path=MODEL_PATH,
        zipenhancer_model_path=None,
        enable_denoiser=False,
        optimize=True,
    )
    refs = [p.stem for p in VOICE_REF_DIR.glob("*.wav")]
    print(f"[TTS] Model loaded. Voice refs: {refs or '(none — run scripts/generate_voice_refs.py)'}", flush=True)


@app.on_event("startup")
async def startup():
    import asyncio

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, load_model)


@app.get("/tts/status")
async def status():
    clone_refs = {
        p.stem: True for p in VOICE_REF_DIR.glob("*.wav")
    }
    return TTSStatus(
        status="ok",
        model_loaded=_model is not None,
        uptime=time.time() - _start_time,
        clone_refs=clone_refs,
    )


def _generate_sync(char_id: str, text: str, mood: str, output_path: Path) -> Path:
    if _model is None:
        raise RuntimeError("TTS model not loaded")

    mood = normalize_mood(mood)
    ref_path = get_ref_path(char_id)

    if ref_path is not None:
        mood_style = get_mood_style(mood)
        full_text = f"{mood_style}{text}"
        print(
            f"[TTS] clone {char_id} ref={ref_path.name} mood={mood} text='{text[:30]}...'",
            flush=True,
        )
        audio_array: np.ndarray = _model.generate(
            text=full_text,
            reference_wav_path=str(ref_path),
            normalize=False,
            **CLONE_GEN_KWARGS,
        )
    else:
        voice_desc = get_voice_desc(char_id, mood)
        full_text = f"{voice_desc}{text}"
        print(
            f"[TTS] design(fallback) {char_id} mood={mood} text='{text[:30]}...'",
            flush=True,
        )
        audio_array = _model.generate(
            text=full_text,
            normalize=False,
            **DESIGN_GEN_KWARGS,
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = getattr(_model.tts_model, "sample_rate", 48000)
    sf.write(str(output_path), audio_array, sample_rate)

    duration = len(audio_array) / sample_rate
    print(f"[TTS] Saved: {output_path.name} ({duration:.2f}s)", flush=True)
    return output_path


def get_cached_path(char_id: str, turn_count: int, page_idx: int) -> Path:
    return VOICE_DIR / f"{char_id}_{turn_count}_{page_idx}.wav"


@app.post("/tts")
async def tts(req: TTSRequest):
    if _model is None:
        raise HTTPException(status_code=503, detail="TTS model not yet loaded")

    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Empty text")

    cache_path = get_cached_path(req.charId, req.turnCount, req.pageIdx)

    try:
        if cache_path.exists():
            print(f"[TTS] Cache hit: {cache_path.name}", flush=True)
            return FileResponse(str(cache_path), media_type="audio/wav")

        import asyncio

        def generate_with_lock() -> Path:
            with _generate_lock:
                if cache_path.exists():
                    print(f"[TTS] Cache hit: {cache_path.name}", flush=True)
                    return cache_path
                return _generate_sync(
                    req.charId,
                    req.text,
                    req.mood,
                    cache_path,
                )

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, generate_with_lock)

        return FileResponse(str(cache_path), media_type="audio/wav")

    except Exception as e:
        print(f"[TTS] ERROR: {e}", flush=True)
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {e}")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("TTS_PORT", "7860"))
    print(f"[TTS] Starting server on 0.0.0.0:{port}", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
