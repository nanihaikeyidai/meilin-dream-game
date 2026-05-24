"""生成各角色 VOICE_DESCRIPTIONS 的辅助函数。"""

from __future__ import annotations


def _moods(neutral: str, happy: str, sad: str, angry: str, warm: str, cold: str, surprised: str, blush: str) -> dict[str, str]:
    return {
        "neutral": neutral,
        "happy": happy,
        "sad": sad,
        "angry": angry,
        "warm": warm,
        "cold": cold,
        "surprised": surprised,
        "blush": blush,
    }


def young_female(tone: str) -> dict[str, str]:
    return _moods(
        f"(年轻女声，{tone}，语气平静)",
        f"(年轻女声，{tone}，语气轻快愉悦，带着笑意)",
        f"(年轻女声，{tone}，语气低落哀婉)",
        f"(年轻女声，{tone}，语气冷了下来)",
        f"(年轻女声，{tone}，语气格外温柔亲切)",
        f"(年轻女声，{tone}，语气冷淡疏远)",
        f"(年轻女声，{tone}，语气微微上扬，带着惊讶)",
        f"(年轻女声，{tone}，语气轻柔，带着羞涩)",
    )


def young_male(tone: str) -> dict[str, str]:
    return _moods(
        f"(青年男声，{tone}，语气平静)",
        f"(青年男声，{tone}，语气爽朗带笑)",
        f"(青年男声，{tone}，语气低沉压抑)",
        f"(青年男声，{tone}，语气严厉)",
        f"(青年男声，{tone}，语气温和耐心)",
        f"(青年男声，{tone}，语气淡漠疏离)",
        f"(青年男声，{tone}，语气上扬，带着意外)",
        f"(青年男声，{tone}，语气略慌，带着不自在)",
    )


def mature_female(tone: str) -> dict[str, str]:
    return _moods(
        f"(成熟女声，{tone}，语气淡定)",
        f"(成熟女声，{tone}，语气带着笑意)",
        f"(成熟女声，{tone}，语气沉重叹息)",
        f"(成熟女声，{tone}，语气严厉)",
        f"(成熟女声，{tone}，语气温厚)",
        f"(成熟女声，{tone}，语气冷淡)",
        f"(成熟女声，{tone}，语气微有波澜)",
        f"(成熟女声，{tone}，语气慈和)",
    )


def ethereal_voice(tone: str) -> dict[str, str]:
    return _moods(
        f"(空灵中性声线，{tone}，语气平静)",
        f"(空灵中性声线，{tone}，语气飘忽含笑)",
        f"(空灵中性声线，{tone}，语气低沉回响)",
        f"(空灵中性声线，{tone}，语气骤然转冷)",
        f"(空灵中性声线，{tone}，语气轻柔)",
        f"(空灵中性声线，{tone}，语气疏离)",
        f"(空灵中性声线，{tone}，语气微顿)",
        f"(空灵中性声线，{tone}，语气若有若无)",
    )
