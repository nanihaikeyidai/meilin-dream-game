"""夏日的回音（campus-summer）TTS 配置。"""

from ._builders import young_female

TEMPLATE_ID = "campus-summer"

CHARACTER_IDS = (
    "linxue",
    "suyunxi",
    "shenqingci",
    "jiangxiaoyu",
    "xiazhiyao",
    "chengnianci",
    "yexiaoman",
)

REF_SAMPLE_LINES: dict[str, str] = {
    "linxue": (
        "蝉鸣很吵，空荡的教室里只有我们两个人。"
        "陈远，高二那年的事……我想是时候告诉你真相了，你准备好了吗。"
    ),
    "suyunxi": (
        "喂，发什么呆呢！走啦走啦，天台的风那么舒服，"
        "再不去可就要被夕阳晒化啦，今天我请客喝汽水。"
    ),
    "shenqingci": (
        "图书馆角落那本书还在原处，书签夹在你离开的那一页。"
        "你若愿意听，我可以把那个夏天没说完的故事，慢慢讲给你。"
    ),
    "jiangxiaoyu": (
        "嘿！别板着脸嘛，转学第一天就被你撞见糗事，"
        "咱们算有缘对吧？走，我带你去学校后面那家超好吃的冰粉摊。"
    ),
    "xiazhiyao": (
        "学生会的事我会处理完，你不用操心。"
        "只是……当年照片里站在你身边的人，为什么从来不是我。"
    ),
    "chengnianci": (
        "母校要拆了，我连夜赶回来，怕错过最后看一眼的机会。"
        "陈远，你还记得教学楼后那棵老槐树吗，它还在。"
    ),
    "yexiaoman": (
        "毕业照洗出来了，我偷偷多留了一张。"
        "上面的笑容都好灿烂啊，要是时间能停在那一天就好了。"
    ),
}

VOICE_DESCRIPTIONS: dict[str, dict[str, str]] = {
    "linxue": young_female("温柔内敛，吐字清晰"),
    "suyunxi": young_female("明朗活泼，元气十足"),
    "shenqingci": young_female("轻柔安静，略带文艺感"),
    "jiangxiaoyu": young_female("清脆跳脱，语速略快"),
    "xiazhiyao": young_female("清冷利落，偶露柔软"),
    "chengnianci": young_female("沉静怀旧，语气克制"),
    "yexiaoman": young_female("甜美腼腆，声线偏软"),
}
