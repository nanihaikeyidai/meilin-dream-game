"""镜像之馆（suspense-mansion）TTS 配置。"""

from ._builders import ethereal_voice, young_female, young_male

TEMPLATE_ID = "suspense-mansion"

CHARACTER_IDS = (
    "linyingxue",
    "chenwu",
    "suwanqing",
    "gunianan",
    "zhaomingshen",
    "jingzhongren",
)

REF_SAMPLE_LINES: dict[str, str] = {
    "linyingxue": (
        "庄园里的空气很沉，镜子照出的不只是脸。"
        "我作为心理学家应邀前来，请先告诉我，你昨夜究竟看见了什么。"
    ),
    "chenwu": (
        "这座馆子是陈家祖产，如今只剩我和满屋古镜。"
        "客人若不怕夜里的声响，便请进，茶已备好，真相……未必今日揭晓。"
    ),
    "suwanqing": (
        "古镜背面的铭文磨损了，我花了三个月才拼出一半。"
        "别碰那面裂镜，有些历史一旦被唤醒，就再也封不回去了。"
    ),
    "gunianan": (
        "我姐姐失踪二十年了，官方档案早已结案。"
        "可电话会在午夜响起，空房间里只有她的呼吸声，你信吗。"
    ),
    "zhaomingshen": (
        "刑警赵铭深，奉命复查旧案。"
        "现场证据被篡改过，但镜子不会说谎，请把你知道的全部告诉我。"
    ),
    "jingzhongren": (
        "你在镜中看见了我，我便在此处。"
        "别回头，别眨眼，二十年前的那个雨夜，我们其实见过面。"
    ),
}

VOICE_DESCRIPTIONS: dict[str, dict[str, str]] = {
    "linyingxue": young_female("理性冷静，吐字精准"),
    "chenwu": young_male("压抑低沉，继承人气质"),
    "suwanqing": young_female("轻柔专注，修复师般的耐心"),
    "gunianan": young_female("略带颤抖，隐忍悲伤"),
    "zhaomingshen": young_male("硬朗干脆，刑警口吻"),
    "jingzhongren": ethereal_voice("回响感，似近似远"),
}
