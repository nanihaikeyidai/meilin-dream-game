"""
月下长安 TTS 音色配置
- REF_SAMPLE_LINES：各角色参考音 bootstrap 台词（Voice Design 一次性生成）
- MOOD_STYLES：Clone 模式下仅控制语气，音色由 reference_wav 锁定
"""

from __future__ import annotations

VALID_MOODS = frozenset({
    "neutral", "warm", "happy", "sad", "angry", "cold", "surprised", "blush",
})

CHARACTER_IDS = (
    "xieyunlan",
    "huayingyue",
    "guqianfan",
    "shenmingyue",
    "lihuaijin",
    "gongsunlan",
)

# Clone 合成参数（更贴参考音、波动更小）
CLONE_GEN_KWARGS = {
    "cfg_value": 2.5,
    "inference_timesteps": 15,
}

# 无参考音时的 Voice Design 兜底
DESIGN_GEN_KWARGS = {
    "cfg_value": 2.0,
    "inference_timesteps": 10,
}

# 参考音 bootstrap：每角色一句代表性 neutral 台词
REF_SAMPLE_LINES: dict[str, str] = {
    "xieyunlan": "此事，与你无关。",
    "huayingyue": "你来啦。",
    "guqianfan": "走，别处说话去。",
    "shenmingyue": "说重点。",
    "lihuaijin": "请坐吧。",
    "gongsunlan": "且慢。",
}

# Clone 模式：括号内只写语气，不写「男声/女声/年龄」
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

# Voice Design 全描述（仅 bootstrap 参考音 / 无 ref 文件时兜底）
VOICE_DESCRIPTIONS: dict[str, dict[str, str]] = {
    "xieyunlan": {
        "neutral": "(冷峻青年男声，沉稳低沉，语气平静)",
        "happy": "(冷峻青年男声，沉稳低沉，语气微微上扬，带着难得的笑意)",
        "sad": "(冷峻青年男声，沉稳低沉，语气压抑，带着沉重的悲伤)",
        "angry": "(冷峻青年男声，沉稳低沉，语气冰冷，隐含怒意)",
        "warm": "(冷峻青年男声，沉稳低沉，语气难得温和，放软了声音)",
        "cold": "(冷峻青年男声，沉稳低沉，语气冰冷疏离，不带感情)",
        "surprised": "(冷峻青年男声，沉稳低沉，语气略有波动，带着意外)",
        "blush": "(冷峻青年男声，沉稳低沉，语气微顿，略带不自在)",
    },
    "huayingyue": {
        "neutral": "(年轻女声，妩媚柔美，语气温柔含笑)",
        "happy": "(年轻女声，妩媚柔美，语气轻快愉悦，带着笑意)",
        "sad": "(年轻女声，妩媚柔美，语气低落哀婉，带着愁绪)",
        "angry": "(年轻女声，妩媚柔美，语气冷了下来，话中带刺)",
        "warm": "(年轻女声，妩媚柔美，语气格外温柔亲切)",
        "cold": "(年轻女声，妩媚柔美，语气冷淡疏远，笑里藏刀)",
        "surprised": "(年轻女声，妩媚柔美，语气微微上扬，带着惊讶)",
        "blush": "(年轻女声，妩媚柔美，语气轻柔，带着羞涩笑意)",
    },
    "guqianfan": {
        "neutral": "(洒脱青年男声，明朗随性，语气轻松)",
        "happy": "(洒脱青年男声，明朗随性，语气爽朗带笑)",
        "sad": "(洒脱青年男声，明朗随性，语气低沉，带着隐忍的悲伤)",
        "angry": "(洒脱青年男声，明朗随性，语气冷峻，压抑着怒火)",
        "warm": "(洒脱青年男声，明朗随性，语气温柔耐心)",
        "cold": "(洒脱青年男声，明朗随性，语气淡漠疏离)",
        "surprised": "(洒脱青年男声，明朗随性，语气上扬，带着意外)",
        "blush": "(洒脱青年男声，明朗随性，语气略慌，带着打趣般的害羞)",
    },
    "shenmingyue": {
        "neutral": "(英气女声，清越爽利，语气干脆)",
        "happy": "(英气女声，清越爽利，语气轻快明亮)",
        "sad": "(英气女声，清越爽利，语气沉重，带着不甘)",
        "angry": "(英气女声，清越爽利，语气严厉，带着愤然)",
        "warm": "(英气女声，清越爽利，语气柔和了几分)",
        "cold": "(英气女声，清越爽利，语气冷硬如铁)",
        "surprised": "(英气女声，清越爽利，语气微顿，带着惊讶)",
        "blush": "(英气女声，清越爽利，语气发紧，带着少见的羞赧)",
    },
    "lihuaijin": {
        "neutral": "(温雅青年男声，如玉温润，语气和煦)",
        "happy": "(温雅青年男声，如玉温润，语气含笑，如春风拂面)",
        "sad": "(温雅青年男声，如玉温润，语气低沉哀伤)",
        "angry": "(温雅青年男声，如玉温润，语气虽平但隐有冷意)",
        "warm": "(温雅青年男声，如玉温润，语气格外温柔)",
        "cold": "(温雅青年男声，如玉温润，语气冷淡疏远)",
        "surprised": "(温雅青年男声，如玉温润，语气微讶)",
        "blush": "(温雅青年男声，如玉温润，语气轻柔，略带局促)",
    },
    "gongsunlan": {
        "neutral": "(沉稳中年女声，平和从容，语气淡定)",
        "happy": "(沉稳中年女声，平和从容，语气带着慈和的笑意)",
        "sad": "(沉稳中年女声，平和从容，语气沉重叹息)",
        "angry": "(沉稳中年女声，平和从容，语气严厉，不怒自威)",
        "warm": "(沉稳中年女声，平和从容，语气格外温厚)",
        "cold": "(沉稳中年女声，平和从容，语气冷淡疏离)",
        "surprised": "(沉稳中年女声，平和从容，语气微有波澜)",
        "blush": "(沉稳中年女声，平和从容，语气慈和，带着温和的笑意)",
    },
}


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


def get_voice_desc(char_id: str, mood: str) -> str:
    mood = normalize_mood(mood)
    char_map = VOICE_DESCRIPTIONS.get(char_id, VOICE_DESCRIPTIONS["xieyunlan"])
    return char_map.get(mood, char_map["neutral"])


def get_mood_style(mood: str) -> str:
    mood = normalize_mood(mood)
    return MOOD_STYLES.get(mood, MOOD_STYLES["neutral"])


def get_ref_sample_line(char_id: str) -> str:
    return REF_SAMPLE_LINES.get(char_id, REF_SAMPLE_LINES["xieyunlan"])
