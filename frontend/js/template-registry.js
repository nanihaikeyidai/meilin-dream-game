/**
 * 剧本模板注册表：立绘映射、场景背景、开场与 UI 元数据
 */
(function (global) {
  const EXPRESSION_KEYWORDS = {
    微笑: 'smile', 浅笑: 'smile', 轻笑: 'smile', 温柔: 'smile',
    开心: 'happy', 大笑: 'happy', 笑出声: 'happy', 愉快: 'happy',
    生气: 'angry', 愤怒: 'angry', 怒: 'angry', 冷眼: 'angry', 厉声: 'angry',
    悲伤: 'sad', 伤心: 'sad', 哭: 'sad', 泪: 'sad', 哽咽: 'sad', 难过: 'sad',
    惊讶: 'surprised', 震惊: 'surprised', 愣: 'surprised', 怔: 'surprised', 难以置信: 'surprised',
    脸红: 'blush', 害羞: 'blush', 羞涩: 'blush', 心动: 'blush',
    冷漠: 'cold', 冷淡: 'cold', 面无表情: 'cold', 冰冷: 'cold', 疏离: 'cold',
  };

  const CAMPUS_SCENES = {
    default: 'assets/backgrounds/campus-summer/classroom_afternoon.png',
    classroom: 'assets/backgrounds/campus-summer/classroom_afternoon.png',
    schoolyard: 'assets/backgrounds/campus-summer/schoolyard.png',
    photo_hall: 'assets/backgrounds/campus-summer/photo_hall.png',
    rooftop: 'assets/backgrounds/campus-summer/rooftop.png',
    festival: 'assets/backgrounds/campus-summer/festival.png',
    night_sky: 'assets/backgrounds/campus-summer/night_sky.png',
    summer_farewell: 'assets/backgrounds/campus-summer/summer_farewell.png',
  };

  const ANCIENT_SCENES = {
    default: 'assets/backgrounds/ancient/moonlit_city.png',
    lantern_night: 'assets/backgrounds/ancient/lantern_night.png',
    government_hall: 'assets/backgrounds/ancient/government_hall.png',
    music_pavilion: 'assets/backgrounds/ancient/music_pavilion.png',
    changan_street: 'assets/backgrounds/ancient/changan_street.png',
    bookstore: 'assets/backgrounds/ancient/bookstore.png',
    courtyard: 'assets/backgrounds/ancient/courtyard.png',
    clinic: 'assets/backgrounds/ancient/clinic.png',
    city_wall: 'assets/backgrounds/ancient/city_wall.png',
    moonlit_city: 'assets/backgrounds/ancient/moonlit_city.png',
    lantern_river: 'assets/backgrounds/ancient/lantern_river.png',
  };

  const TEMPLATES = {
    'changan-moon': {
      id: 'changan-moon',
      title: '月下长安',
      subtitle: '古风奇幻 · AI Visual Novel',
      desc: '上元灯夜 · 长安满城花灯如昼<br>一块玉佩 · 六个各怀心事的人 · 一段横跨十年的旧案',
      tags: '古风 / 奇幻 / 权谋',
      description: '长安上元灯夜，你捡到一枚玉佩，卷入三股势力与十年旧案。',
      defaultPlayerName: '陈远',
      defaultBg: 'assets/backgrounds/ancient/moonlit_city.png',
      cardCover: 'assets/backgrounds/ancient/lantern_night.png',
      openingBeat: '上元灯夜',
      styleHint: '古风文风，诗意对话，适度的文言感',
      sceneBackgrounds: ANCIENT_SCENES,
      sceneIdsPrompt:
        'lantern_night, government_hall, music_pavilion, changan_street, bookstore, courtyard, clinic, city_wall, moonlit_city, lantern_river',
      portraits: {
        谢云岚: 'xieyunlan', 花映月: 'huayingyue', 顾千帆: 'guqianfan',
        沈明月: 'shenmingyue', 李怀瑾: 'lihuaijin', 公孙兰: 'gongsunlan',
      },
      charactersPrompt: `- 谢云岚 — 玄天司首席密探，冷峻寡言但重情义
- 花映月 — 不夜天乐坊的花魁，神秘优雅，消息灵通
- 顾千帆 — 江湖游医，洒脱不羁，似乎与血月案有旧
- 沈明月 — 将门之女，英气飒爽，在查一桩旧案
- 李怀瑾 — 当朝御史之子，温文尔雅，暗中收集证据
- 公孙兰 — 退休捕快，经营书肆，知道很多秘密（后期解锁）`,
      ttsEnabled: true,
      bgmTracks: [
        'assets/music/changan-moon/bgm_1.mp3',
        'assets/music/changan-moon/bgm_2.mp3',
      ],
    },
    'campus-summer': {
      id: 'campus-summer',
      title: '夏日的回音',
      subtitle: '校园青春 · AI Visual Novel',
      desc: '高三毕业后的暑假 · 即将拆迁的母校<br>七个身影 · 一段关于告别与重新开始的夏日',
      tags: '青春 / 治愈 / 怀旧',
      description: '回到空无一人的母校，在蝉鸣与夕阳里揭开高二那年夏天的秘密。',
      defaultPlayerName: '陈远',
      defaultBg: 'assets/backgrounds/campus-summer/classroom_afternoon.png',
      cardCover: 'assets/backgrounds/campus-summer/schoolyard.png',
      openingBeat: '回到母校',
      styleHint: '温暖怀旧的现代校园文风，注重氛围与对话',
      sceneBackgrounds: CAMPUS_SCENES,
      sceneIdsPrompt:
        'classroom, schoolyard, photo_hall, rooftop, festival, night_sky, summer_farewell',
      portraits: {
        林雪: 'linxue', 苏云溪: 'suyunxi', 沈清辞: 'shenqingci',
        江晓渔: 'jiangxiaoyu', 夏知遥: 'xiazhiyao',
        程念慈: 'chengnianci', 叶小满: 'yexiaoman',
      },
      charactersPrompt: `- 林雪 — 温柔内敛的班长
- 苏云溪 — 开朗活泼的青梅竹马
- 沈清辞 — 安静内敛的文艺少女
- 江晓渔 — 元气跳脱的转学生
- 夏知遥 — 外冷内热的学生会副会长
- 陈一鸣 — 话痨好友，气氛担当（暂无立绘）
- 程念慈 / 叶小满 — 后期可解锁角色`,
      ttsEnabled: true,
      bgmTracks: [
        'assets/music/campus-summer/bgm_1.mp3',
        'assets/music/campus-summer/bgm_2.mp3',
      ],
    },
    'cafe-night': {
      id: 'cafe-night',
      title: '深夜咖啡店',
      subtitle: '都市物语 · AI Visual Novel',
      desc: '凌晨两点 · 城市失眠者的避风港<br>咖啡、黑胶与雨夜来信',
      tags: '都市 / 文艺 / 微悬疑',
      description: '在深夜咖啡店里，每个常客都藏着未说出口的秘密。',
      defaultPlayerName: '你',
      defaultBg: 'assets/backgrounds/cafe-night/night_sky_cafe.png',
      cardCover: 'assets/backgrounds/cafe-night/cafe_interior.png',
      openingBeat: '深夜咖啡店',
      styleHint: '都市文艺文风，克制细腻，带一点悬疑',
      sceneBackgrounds: {
        default: 'assets/backgrounds/cafe-night/night_sky_cafe.png',
        night_sky: 'assets/backgrounds/cafe-night/night_sky_cafe.png',
        photo_hall: 'assets/backgrounds/campus-summer/photo_hall.png',
        cafe_interior: 'assets/backgrounds/cafe-night/cafe_interior.png',
        street_rain: 'assets/backgrounds/cafe-night/street_rain.png',
        rooftop_terrace: 'assets/backgrounds/campus-summer/rooftop.png',
      },
      sceneIdsPrompt: 'night_sky, photo_hall, cafe_interior, street_rain, rooftop_terrace',
      portraits: {
        林屿: 'linyu', 苏晚: 'suwan', 顾念: 'gunian',
        赵逐: 'zhaozhu', 周医生: 'zhoudoctor', 秦雨桐: 'qinyutong',
      },
      charactersPrompt: `- 林屿 — 咖啡店店主，温和寡言
- 苏晚 — 常客，总在雨夜出现
- 顾念 — 神秘的黑胶收藏家
- 赵逐 — 夜班记者
- 周医生 — 失眠的精神科医师
- 秦雨桐 — 钢琴教师，与黑胶唱片 #7 有关`,
      ttsEnabled: true,
      bgmTracks: [
        'assets/music/cafe-night/bgm_1.mp3',
        'assets/music/cafe-night/bgm_2.mp3',
      ],
    },
    'suspense-mansion': {
      id: 'suspense-mansion',
      title: '镜像之馆',
      subtitle: '悬疑推理 · AI Visual Novel',
      desc: '七面古镜 · 七个声音 · 二十年前的失踪案',
      tags: '悬疑 / 推理 / 心理',
      description: '庄园里的断线电话某些夜晚会响，镜子的另一边有人等你。',
      defaultPlayerName: '你',
      defaultBg: 'assets/backgrounds/campus-summer/photo_hall.png',
      cardCover: 'assets/backgrounds/campus-summer/summer_farewell.png',
      openingBeat: '镜像之馆',
      styleHint: '悬疑推理文风，氛围压迫，线索清晰',
      sceneBackgrounds: {
        default: 'assets/backgrounds/campus-summer/photo_hall.png',
        photo_hall: 'assets/backgrounds/campus-summer/photo_hall.png',
        night_sky: 'assets/backgrounds/campus-summer/night_sky.png',
        hallway: 'assets/backgrounds/ancient/government_hall.png',
        garden_dusk: 'assets/backgrounds/ancient/courtyard.png',
        mansion_attic: 'assets/backgrounds/campus-summer/rooftop.png',
      },
      sceneIdsPrompt: 'photo_hall, night_sky, hallway, garden_dusk, mansion_attic',
      portraits: {
        林映雪: 'linyingxue', 陈雾: 'chenwu', 苏晚晴: 'suwanqing',
        顾念安: 'gunianan', 赵铭深: 'zhaomingshen', '镜中人': 'jingzhongren',
      },
      charactersPrompt: `- 林映雪 — 心理学家，理性冷静
- 陈雾 — 庄园继承人
- 苏晚晴 — 古董修复师
- 顾念安 — 失踪者的妹妹
- 赵铭深 — 刑警
- 镜中人 — 神秘存在`,
      ttsEnabled: true,
      bgmTracks: ['assets/music/suspense-mansion/bgm_1.mp3'],
    },
  };

  function getTemplate(id) {
    return TEMPLATES[id] || TEMPLATES['changan-moon'];
  }

  const FEATURED_TEMPLATE_IDS = [
    'changan-moon',
    'campus-summer',
    'cafe-night',
    'suspense-mansion',
  ];

  function listTemplates() {
    return Object.values(TEMPLATES).map((t) => ({
      id: t.id,
      title: t.title,
      tags: t.tags,
      description: t.description,
    }));
  }

  function listFeaturedTemplates() {
    return FEATURED_TEMPLATE_IDS.map((id) => {
      const t = TEMPLATES[id];
      if (!t) return null;
      return {
        id: t.id,
        title: t.title,
        subtitle: t.subtitle,
        tags: t.tags,
        description: t.description,
        cardCover: t.cardCover || t.defaultBg,
      };
    }).filter(Boolean);
  }

  global.AvgTemplates = {
    EXPRESSION_KEYWORDS,
    TEMPLATES,
    FEATURED_TEMPLATE_IDS,
    getTemplate,
    listTemplates,
    listFeaturedTemplates,
  };
})(window);
