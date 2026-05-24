"""按剧本注册的 TTS 配置。"""
from __future__ import annotations

from . import cafe_night, campus_summer, changan_moon, suspense_mansion

_REGISTRY: dict[str, object] = {
    changan_moon.TEMPLATE_ID: changan_moon,
    campus_summer.TEMPLATE_ID: campus_summer,
    cafe_night.TEMPLATE_ID: cafe_night,
    suspense_mansion.TEMPLATE_ID: suspense_mansion,
}

ALL_TEMPLATE_IDS: tuple[str, ...] = tuple(_REGISTRY.keys())


def get_template_config(template_id: str):
    from tts_paths import DEFAULT_TEMPLATE_ID, sanitize_template_id

    tid = sanitize_template_id(template_id)
    return _REGISTRY.get(tid) or _REGISTRY[DEFAULT_TEMPLATE_ID]
