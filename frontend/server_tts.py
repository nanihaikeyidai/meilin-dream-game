#!/usr/bin/env python3
"""
AVG TTS 语音服务 — VoxCPM2 Clone + MOOD 语气控制
资源按剧本分目录：assets/tts/{templateId}/voice_refs|cache/

启动:
  python frontend/server_tts.py
"""

import os
import time
import threading
from pathlib import Path

import soundfile as sf
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from tts_paths import (
    DEFAULT_TEMPLATE_ID,
    cache_path,
    ensure_template_dirs,
    list_template_ids,
    list_voice_ref_ids,
    resolve_voice_ref,
    sanitize_template_id,
)
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

app = FastAPI(title="AVG TTS", version="0.3.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class TTSRequest(BaseModel):
    templateId: str = DEFAULT_TEMPLATE_ID
    charId: str
    text: str
    mood: str = "neutral"
    turnCount: int = 0
    pageIdx: int = 0


class TTSStatus(BaseModel):
    status: str
    model_loaded: bool
    uptime: float
    templates: dict[str, dict[str, bool]]


_model: object | None = None
_start_time: float = time.time()
_generate_lock = threading.Lock()


def load_model():
    global _model
    print(f"[TTS] Loading VoxCPM2 from: {MODEL_PATH}", flush=True)
    from voxcpm.core import VoxCPM

    _model = VoxCPM(
        voxcpm_model_path=MODEL_PATH,
        zipenhancer_model_path=None,
        enable_denoiser=False,
        optimize=True,
    )
    templates = list_template_ids()
    print(
        f"[TTS] Model loaded. Templates: {templates or '(none — run scripts/generate_voice_refs.py)'}",
        flush=True,
    )


@app.on_event("startup")
async def startup():
    import asyncio

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, load_model)


@app.get("/tts/status")
async def status():
    templates: dict[str, dict[str, bool]] = {}
    for tid in list_template_ids() or [DEFAULT_TEMPLATE_ID]:
        templates[tid] = {cid: True for cid in list_voice_ref_ids(tid)}
    return TTSStatus(
        status="ok",
        model_loaded=_model is not None,
        uptime=time.time() - _start_time,
        templates=templates,
    )


def _generate_sync(
    template_id: str,
    char_id: str,
    text: str,
    mood: str,
    output_path: Path,
) -> Path:
    if _model is None:
        raise RuntimeError("TTS model not loaded")

    mood = normalize_mood(mood)
    ref_path = resolve_voice_ref(template_id, char_id)

    if ref_path is not None:
        mood_style = get_mood_style(mood)
        full_text = f"{mood_style}{text}"
        print(
            f"[TTS] clone [{template_id}] {char_id} ref={ref_path.name} mood={mood} "
            f"text='{text[:30]}...'",
            flush=True,
        )
        audio_array = _model.generate(
            text=full_text,
            reference_wav_path=str(ref_path),
            normalize=False,
            **CLONE_GEN_KWARGS,
        )
    else:
        voice_desc = get_voice_desc(char_id, mood, template_id)
        full_text = f"{voice_desc}{text}"
        print(
            f"[TTS] design(fallback) [{template_id}] {char_id} mood={mood} "
            f"text='{text[:30]}...'",
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
    print(f"[TTS] Saved: {output_path} ({duration:.2f}s)", flush=True)
    return output_path


@app.post("/tts")
async def tts(req: TTSRequest):
    if _model is None:
        raise HTTPException(status_code=503, detail="TTS model not yet loaded")

    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Empty text")

    template_id = sanitize_template_id(req.templateId)
    ensure_template_dirs(template_id)
    out = cache_path(template_id, req.charId, req.turnCount, req.pageIdx)

    try:
        if out.exists():
            print(f"[TTS] Cache hit: {out}", flush=True)
            return FileResponse(str(out), media_type="audio/wav")

        import asyncio

        def generate_with_lock() -> Path:
            with _generate_lock:
                if out.exists():
                    print(f"[TTS] Cache hit: {out}", flush=True)
                    return out
                return _generate_sync(
                    template_id,
                    req.charId,
                    req.text,
                    req.mood,
                    out,
                )

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, generate_with_lock)

        return FileResponse(str(out), media_type="audio/wav")

    except Exception as e:
        print(f"[TTS] ERROR: {e}", flush=True)
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {e}")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("TTS_PORT", "7860"))
    print(f"[TTS] Starting server on 0.0.0.0:{port}", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
