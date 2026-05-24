"""深夜咖啡店（cafe-night）TTS 配置。"""

from ._builders import mature_female, young_female, young_male

TEMPLATE_ID = "cafe-night"

CHARACTER_IDS = (
    "linyu",
    "suwan",
    "gunian",
    "zhaozhu",
    "zhoudoctor",
    "qinyutong",
)

REF_SAMPLE_LINES: dict[str, str] = {
    "linyu": (
        "凌晨两点，城里只剩这家咖啡店还亮着灯。"
        "想喝点什么就说，不必拘束，雨夜漫长，我们有的是时间。"
    ),
    "suwan": (
        "又是你。外面雨下得真大，伞骨都弯了。"
        "坐下吧，热咖啡给你留着，今晚……也许我会多说几句。"
    ),
    "gunian": (
        "这张黑胶是绝版，封面上的划痕都是岁月。"
        "你若真心想听故事，就先学会安静，音乐最怕急躁的人。"
    ),
    "zhaozhu": (
        "夜班刚结束，路过闻见咖啡香就进来了。"
        "老板，老规矩。顺便问一句，昨晚巷口那阵动静，你听见了吗。"
    ),
    "zhoudoctor": (
        "失眠又来了，别紧张，我不是来问诊的。"
        "只是夜里走得累了，借你这里一盏灯，让我把思绪理清楚。"
    ),
    "qinyutong": (
        "七号黑胶放的是肖邦，夜曲第三首。"
        "你若是听得懂沉默里的人声，便知道有些秘密只能放在琴键里。"
    ),
}

VOICE_DESCRIPTIONS: dict[str, dict[str, str]] = {
    "linyu": young_male("低沉稳重，温和寡言"),
    "suwan": young_female("略带沙哑，神秘克制"),
    "gunian": young_male("斯文低沉，语速不紧不慢"),
    "zhaozhu": young_male("干练略疲惫，都市记者感"),
    "zhoudoctor": mature_female("平和理性，医生般的镇定"),
    "qinyutong": young_female("清亮细腻，钢琴教师气质"),
}
