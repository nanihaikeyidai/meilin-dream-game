"""
TTS 资源路径：按剧本（templateId）分目录存放参考音与对局缓存。

  assets/tts/{templateId}/voice_refs/{charId}.wav   — Clone 参考音（约 20s）
  assets/tts/{templateId}/cache/{charId}_{turn}_{page}.wav — 对局合成缓存
"""
from __future__ import annotations

import re
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
TTS_ROOT = ASSETS_DIR / "tts"
DEFAULT_TEMPLATE_ID = "changan-moon"

# 旧版扁平目录（迁移后仅作回退读取）
LEGACY_VOICE_REF_DIR = ASSETS_DIR / "voice_refs"
LEGACY_VOICE_CACHE_DIR = ASSETS_DIR / "voices"

_TEMPLATE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def sanitize_template_id(template_id: str | None) -> str:
    tid = (template_id or "").strip() or DEFAULT_TEMPLATE_ID
    if not _TEMPLATE_ID_RE.match(tid):
        return DEFAULT_TEMPLATE_ID
    return tid


def template_dir(template_id: str | None) -> Path:
    return TTS_ROOT / sanitize_template_id(template_id)


def voice_refs_dir(template_id: str | None) -> Path:
    return template_dir(template_id) / "voice_refs"


def cache_dir(template_id: str | None) -> Path:
    return template_dir(template_id) / "cache"


def voice_ref_path(template_id: str | None, char_id: str) -> Path:
    return voice_refs_dir(template_id) / f"{char_id}.wav"


def cache_path(template_id: str | None, char_id: str, turn_count: int, page_idx: int) -> Path:
    return cache_dir(template_id) / f"{char_id}_{turn_count}_{page_idx}.wav"


def resolve_voice_ref(template_id: str | None, char_id: str) -> Path | None:
    """优先新目录，其次旧版 voice_refs/。"""
    path = voice_ref_path(template_id, char_id)
    if path.is_file():
        return path
    legacy = LEGACY_VOICE_REF_DIR / f"{char_id}.wav"
    return legacy if legacy.is_file() else None


def ensure_template_dirs(template_id: str | None) -> None:
    voice_refs_dir(template_id).mkdir(parents=True, exist_ok=True)
    cache_dir(template_id).mkdir(parents=True, exist_ok=True)


def list_template_ids() -> list[str]:
    if not TTS_ROOT.is_dir():
        return []
    return sorted(
        p.name
        for p in TTS_ROOT.iterdir()
        if p.is_dir() and not p.name.startswith(".") and _TEMPLATE_ID_RE.match(p.name)
    )


def list_voice_ref_ids(template_id: str | None) -> list[str]:
    d = voice_refs_dir(template_id)
    if not d.is_dir():
        return []
    return sorted(p.stem for p in d.glob("*.wav"))
