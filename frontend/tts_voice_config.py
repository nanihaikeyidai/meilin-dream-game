"""
TTS 音色配置入口：全局 MOOD + 按剧本（tts_templates/*）角色描述与参考音文案。
"""

from __future__ import annotations

from tts_templates import get_template_config

VALID_MOODS = frozenset({
    "neutral", "warm", "happy", "sad", "angry", "cold", "surprised", "blush",
})

# Clone 合成（对局对白）
CLONE_GEN_KWARGS = {
    "cfg_value": 2.5,
    "inference_timesteps": 15,
}

# 参考音 bootstrap（约 50 字 → 目标 ~20s）
REF_GEN_KWARGS = {
    "cfg_value": 2.0,
    "inference_timesteps": 18,
}

# 无参考音时的 Voice Design 兜底
DESIGN_GEN_KWARGS = {
    "cfg_value": 2.0,
    "inference_timesteps": 10,
}

MOOD_STYLES: dict[str, str] = {
    "neutral": "(语气平静)",
    "warm": "(语气温和)",
    "happy": "(语气带着笑意)",
    "sad": "(语气低落)",
    "angry": "(语气严厉)",
    "cold": "(语气冷淡)",
    "surprised": "(语气微讶)",
    "blush": "(语气轻柔，略带羞涩)",
}

# 兼容旧脚本：默认剧本角色列表
from tts_templates.changan_moon import CHARACTER_IDS, REF_SAMPLE_LINES, VOICE_DESCRIPTIONS  # noqa: E402


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


def get_character_ids(template_id: str | None = None) -> tuple[str, ...]:
    cfg = get_template_config(template_id)
    return tuple(cfg.CHARACTER_IDS)


def get_voice_desc(char_id: str, mood: str, template_id: str | None = None) -> str:
    mood = normalize_mood(mood)
    cfg = get_template_config(template_id)
    desc_map = cfg.VOICE_DESCRIPTIONS
    fallback_id = cfg.CHARACTER_IDS[0]
    char_map = desc_map.get(char_id, desc_map[fallback_id])
    return char_map.get(mood, char_map["neutral"])


def get_mood_style(mood: str) -> str:
    mood = normalize_mood(mood)
    return MOOD_STYLES.get(mood, MOOD_STYLES["neutral"])


def get_ref_sample_line(char_id: str, template_id: str | None = None) -> str:
    cfg = get_template_config(template_id)
    lines = cfg.REF_SAMPLE_LINES
    fallback_id = cfg.CHARACTER_IDS[0]
    return lines.get(char_id, lines[fallback_id])
