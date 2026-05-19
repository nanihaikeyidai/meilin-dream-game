#!/usr/bin/env python3
"""
月下长安 — TTS 语音服务后端
Phase 1 MVP: FastAPI + VoxCPM2 实时生成

启动:
  python -u server-tts.py

API:
  POST /tts  — 生成语音，返回 WAV 字节流
  GET  /tts/status — 健康检查
"""

import io
import json
import os
import sys
import hashlib
import time
import functools
from pathlib import Path

import numpy as np
import soundfile as sf
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
from pydantic import BaseModel

# voxcpm 已作为 pip 包安装，不需要 custom_nodes 路径
MODEL_PATH = os.environ.get(
    "VOXCPM2_PATH",
    r"F:\ComfyUI_V6.0\ComfyUI-WorkFisher-V2\ComfyUI\models\VoxCPM2",
)

# ── 资产路径 ───────────────────────────────────────────────
ASSETS_DIR = Path(__file__).resolve().parent / "assets"
VOICE_DIR = ASSETS_DIR / "voices"
VOICE_DIR.mkdir(parents=True, exist_ok=True)

# VoxCPM2 Voice Design：括号内自然语言描述 + 正文
# https://github.com/OpenBMB/VoxCPM — model.generate(text="(描述)对白")

VALID_MOODS = frozenset({
    "neutral", "warm", "happy", "sad", "angry", "cold", "surprised", "blush",
})


def normalize_mood(mood: str) -> str:
    m = (mood or "neutral").lower()
    aliases = {
        "平静": "neutral",
        "温和": "warm",
        "温柔": "warm",
        "开心": "happy",
        "愉快": "happy",
        "悲伤": "sad",
        "难过": "sad",
        "生气": "angry",
        "愤怒": "angry",
        "冷漠": "cold",
        "冰冷": "cold",
        "惊讶": "surprised",
        "震惊": "surprised",
        "害羞": "blush",
        "脸红": "blush",
    }
    if m in aliases:
        m = aliases[m]
    return m if m in VALID_MOODS else "neutral"


# ── 音色映射表：6 角色 × 8 情绪 ─────────────────────────
VOICE_DESCRIPTIONS = {
    "xieyunlan": {
        "neutral": "(冷峻青年男声，沉稳低沉，语气平静)",
        "happy":   "(冷峻青年男声，沉稳低沉，语气微微上扬，带着难得的笑意)",
        "sad":     "(冷峻青年男声，沉稳低沉，语气压抑，带着沉重的悲伤)",
        "angry":   "(冷峻青年男声，沉稳低沉，语气冰冷，隐含怒意)",
        "warm":    "(冷峻青年男声，沉稳低沉，语气难得温和，放软了声音)",
        "cold":    "(冷峻青年男声，沉稳低沉，语气冰冷疏离，不带感情)",
        "surprised": "(冷峻青年男声，沉稳低沉，语气略有波动，带着意外)",
        "blush":   "(冷峻青年男声，沉稳低沉，语气微顿，略带不自在)",
    },
    "huayingyue": {
        "neutral": "(年轻女声，妩媚柔美，语气温柔含笑)",
        "happy":   "(年轻女声，妩媚柔美，语气轻快愉悦，带着笑意)",
        "sad":     "(年轻女声，妩媚柔美，语气低落哀婉，带着愁绪)",
        "angry":   "(年轻女声，妩媚柔美，语气冷了下来，话中带刺)",
        "warm":    "(年轻女声，妩媚柔美，语气格外温柔亲切)",
        "cold":    "(年轻女声，妩媚柔美，语气冷淡疏远，笑里藏刀)",
        "surprised": "(年轻女声，妩媚柔美，语气微微上扬，带着惊讶)",
        "blush":   "(年轻女声，妩媚柔美，语气轻柔，带着羞涩笑意)",
    },
    "guqianfan": {
        "neutral": "(洒脱青年男声，明朗随性，语气轻松)",
        "happy":   "(洒脱青年男声，明朗随性，语气爽朗带笑)",
        "sad":     "(洒脱青年男声，明朗随性，语气低沉，带着隐忍的悲伤)",
        "angry":   "(洒脱青年男声，明朗随性，语气冷峻，压抑着怒火)",
        "warm":    "(洒脱青年男声，明朗随性，语气温柔耐心)",
        "cold":    "(洒脱青年男声，明朗随性，语气淡漠疏离)",
        "surprised": "(洒脱青年男声，明朗随性，语气上扬，带着意外)",
        "blush":   "(洒脱青年男声，明朗随性，语气略慌，带着打趣般的害羞)",
    },
    "shenmingyue": {
        "neutral": "(英气女声，清越爽利，语气干脆)",
        "happy":   "(英气女声，清越爽利，语气轻快明亮)",
        "sad":     "(英气女声，清越爽利，语气沉重，带着不甘)",
        "angry":   "(英气女声，清越爽利，语气严厉，带着愤然)",
        "warm":    "(英气女声，清越爽利，语气柔和了几分)",
        "cold":    "(英气女声，清越爽利，语气冷硬如铁)",
        "surprised": "(英气女声，清越爽利，语气微顿，带着惊讶)",
        "blush":   "(英气女声，清越爽利，语气发紧，带着少见的羞赧)",
    },
    "lihuaijin": {
        "neutral": "(温雅青年男声，如玉温润，语气和煦)",
        "happy":   "(温雅青年男声，如玉温润，语气含笑，如春风拂面)",
        "sad":     "(温雅青年男声，如玉温润，语气低沉哀伤)",
        "angry":   "(温雅青年男声，如玉温润，语气虽平但隐有冷意)",
        "warm":    "(温雅青年男声，如玉温润，语气格外温柔)",
        "cold":    "(温雅青年男声，如玉温润，语气冷淡疏远)",
        "surprised": "(温雅青年男声，如玉温润，语气微讶)",
        "blush":   "(温雅青年男声，如玉温润，语气轻柔，略带局促)",
    },
    "gongsunlan": {
        "neutral": "(沉稳中年女声，平和从容，语气淡定)",
        "happy":   "(沉稳中年女声，平和从容，语气带着慈和的笑意)",
        "sad":     "(沉稳中年女声，平和从容，语气沉重叹息)",
        "angry":   "(沉稳中年女声，平和从容，语气严厉，不怒自威)",
        "warm":    "(沉稳中年女声，平和从容，语气格外温厚)",
        "cold":    "(沉稳中年女声，平和从容，语气冷淡疏离)",
        "surprised": "(沉稳中年女声，平和从容，语气微有波澜)",
        "blush":   "(沉稳中年女声，平和从容，语气慈和，带着温和的笑意)",
    },
}


def get_voice_desc(char_id: str, mood: str) -> str:
    """VoxCPM2 Voice Design 描述（括号前缀），mood 归一化后查表"""
    mood = normalize_mood(mood)
    char_map = VOICE_DESCRIPTIONS.get(char_id, VOICE_DESCRIPTIONS["xieyunlan"])
    return char_map.get(mood, char_map["neutral"])


# ── FastAPI app ────────────────────────────────────────────
app = FastAPI(title="月下长安 TTS", version="0.1.0")
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


# ── 模型全局变量 ──────────────────────────────────────────
_model: object | None = None
_start_time: float = time.time()


def load_model():
    """同步预加载 VoxCPM2 模型（阻塞直到加载完成）"""
    global _model
    print(f"[TTS] Loading VoxCPM2 model from: {MODEL_PATH}", flush=True)
    from voxcpm.core import VoxCPM

    _model = VoxCPM(
        voxcpm_model_path=MODEL_PATH,
        zipenhancer_model_path=None,
        enable_denoiser=False,
        optimize=True,
    )
    print(f"[TTS] Model loaded successfully", flush=True)


@app.on_event("startup")
async def startup():
    """启动时在后台线程预加载模型"""
    import asyncio

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, load_model)


@app.get("/tts/status")
async def status():
    """健康检查"""
    return TTSStatus(
        status="ok",
        model_loaded=_model is not None,
        uptime=time.time() - _start_time,
    )


def _generate_sync(text: str, voice_desc: str, output_path: Path) -> Path:
    """同步生成语音文件（在 executor 中调用）"""
    if _model is None:
        raise RuntimeError("TTS model not loaded")

    full_text = f"{voice_desc}{text}"
    print(f"[TTS] Generating: charId=..., text='{text[:30]}...'", flush=True)

    audio_array: np.ndarray = _model.generate(
        text=full_text,
        cfg_value=2.0,
        inference_timesteps=10,
        normalize=False,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = getattr(_model.tts_model, "sample_rate", 48000)
    sf.write(str(output_path), audio_array, sample_rate)

    duration = len(audio_array) / sample_rate
    print(f"[TTS] Saved: {output_path.name} ({duration:.2f}s)", flush=True)
    return output_path


def get_cached_path(char_id: str, turn_count: int, page_idx: int) -> Path:
    """获取语音缓存文件路径"""
    return VOICE_DIR / f"{char_id}_{turn_count}_{page_idx}.wav"


@app.post("/tts")
async def tts(req: TTSRequest):
    """
    生成角色对话语音。
    请求: {charId, text, mood, turnCount, pageIdx}
    返回: WAV 音频字节流（同时写入缓存文件）
    """
    if _model is None:
        raise HTTPException(status_code=503, detail="TTS model not yet loaded")

    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Empty text")

    voice_desc = get_voice_desc(req.charId, normalize_mood(req.mood))
    cache_path = get_cached_path(req.charId, req.turnCount, req.pageIdx)

    try:
        # 如果缓存已存在，直接返回
        if cache_path.exists():
            print(f"[TTS] Cache hit: {cache_path.name}", flush=True)
            return FileResponse(str(cache_path), media_type="audio/wav")

        # 生成语音（在 executor 中避免阻塞事件循环）
        import asyncio

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            functools.partial(_generate_sync, req.text, voice_desc, cache_path),
        )

        return FileResponse(str(cache_path), media_type="audio/wav")

    except Exception as e:
        print(f"[TTS] ERROR: {e}", flush=True)
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {e}")


# ── 主入口 ─────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("TTS_PORT", "7860"))
    print(f"[TTS] Starting server on 0.0.0.0:{port}", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
