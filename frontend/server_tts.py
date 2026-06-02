#!/usr/bin/env python3
"""
AVG TTS 语音服务 — VoxCPM2 Clone + MOOD 语气控制
资源按剧本分目录：assets/tts/{templateId}/voice_refs|cache/

启动:
  python frontend/server_tts.py
"""

import os
import json
import time
import threading
import gc
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

DEFAULT_MODEL_PATH = r"F:\ComfyUI_V6.0\ComfyUI-WorkFisher-V2\ComfyUI\models\VoxCPM2"
CONFIG_PATH = Path(__file__).resolve().parents[1] / ".girlgame" / "tts-config.json"

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
    model_error: str | None = None
    model_path: str
    uptime: float
    templates: dict[str, dict[str, bool]]


class TTSConfig(BaseModel):
    modelPath: str


_model: object | None = None
_model_error: str | None = None
_model_path: str = ""
_start_time: float = time.time()
_generate_lock = threading.Lock()


def read_config_file() -> dict[str, str]:
    try:
        if not CONFIG_PATH.is_file():
            return {}
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return {"modelPath": str(raw.get("modelPath") or "").strip()}
    except Exception:
        return {}


def get_configured_model_path() -> str:
    saved = read_config_file().get("modelPath")
    if saved:
        return saved
    return os.environ.get("VOXCPM2_PATH", DEFAULT_MODEL_PATH).strip() or DEFAULT_MODEL_PATH


def write_config_file(model_path: str) -> dict[str, str]:
    path = model_path.strip()
    if not path:
        raise ValueError("modelPath is required")
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {"modelPath": path}
    CONFIG_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def load_model(model_path: str | None = None):
    global _model, _model_error, _model_path
    _model_path = model_path or get_configured_model_path()
    print(f"[TTS] Loading VoxCPM2 from: {_model_path}", flush=True)
    try:
        from voxcpm.core import VoxCPM

        _model = VoxCPM(
            voxcpm_model_path=_model_path,
            zipenhancer_model_path=None,
            enable_denoiser=False,
            optimize=True,
        )
        _model_error = None
        templates = list_template_ids()
        print(
            f"[TTS] Model loaded. Templates: {templates or '(none — run scripts/generate_voice_refs.py)'}",
            flush=True,
        )
    except Exception as exc:
        _model = None
        _model_error = f"{type(exc).__name__}: {exc}"
        print(f"[TTS] Model unavailable: {_model_error}", flush=True)


def reset_model_after_generation_error(exc: Exception) -> None:
    global _model, _model_error
    message = f"{type(exc).__name__}: {exc}"
    _model_error = message
    print(f"[TTS] Resetting model after generation error: {message}", flush=True)
    _model = None
    gc.collect()
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
    except Exception as cleanup_exc:
        print(f"[TTS] CUDA cleanup skipped: {cleanup_exc}", flush=True)
    load_model(_model_path or get_configured_model_path())


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
        status="ok" if _model is not None else "model_unavailable",
        model_loaded=_model is not None,
        model_error=_model_error,
        model_path=_model_path or get_configured_model_path(),
        uptime=time.time() - _start_time,
        templates=templates,
    )


@app.get("/tts/config")
async def get_config():
    return TTSConfig(modelPath=_model_path or get_configured_model_path())


@app.post("/tts/config")
async def set_config(req: TTSConfig):
    try:
        payload = write_config_file(req.modelPath)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    import asyncio

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, load_model, payload["modelPath"])
    return {
        "success": True,
        "config": payload,
        "model_loaded": _model is not None,
        "model_error": _model_error,
    }


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
        detail = "TTS model not yet loaded"
        if _model_error:
            detail += f": {_model_error}"
        raise HTTPException(status_code=503, detail=detail)

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
        print(f"[TTS] ERROR: {type(e).__name__}: {e!r}", flush=True)
        try:
            import asyncio

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, reset_model_after_generation_error, e)
        except Exception as reload_exc:
            print(f"[TTS] Reload after error failed: {type(reload_exc).__name__}: {reload_exc!r}", flush=True)
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {e}")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("TTS_PORT", "7860"))
    print(f"[TTS] Starting server on 0.0.0.0:{port}", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
