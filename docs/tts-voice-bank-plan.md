# 月下长安 TTS 语音库生成计划

> **项目**: AVG月下长安 (changan-moon)
> **状态**: VoxCPM2 参考音已就绪 (6角色 voice_refs/\*.wav)，前端 TTS 引擎已启用，零音频缓存生成中
> **目标**: 批量预生成基础语音缓存，覆盖 6 角色 × 核心语气，配合 edge-tts/VoxCPM2 实时合成

---

## 1. 项目 TTS 架构速览

```
[LLM] → [MOOD] + [EXPR] + 「台词」
         ↓
    frontend/js/mood.js → 解析 charId / mood / dialogue
         ↓
    frontend/js/tts.js → POST /proxy/tts
         ↓
    server.js → server_tts.py (VoxCPM2)
         ↓
    assets/tts/changan-moon/
         ├── voice_refs/     ← 参考音（6角色已就绪 ✅）
         └── cache/          ← 对局缓存（当前为空 ❌）
```

**已就绪**: `voice_refs/xieyunlan.wav`, `huayingyue.wav`, `guqianfan.wav`, `shenmingyue.wav`, `lihuaijin.wav`, `gongsunlan.wav` 全部存在。

**待生成**: 对局缓存 + 批量预生成基础语音（每角色 × 关键语气 × 代表性台词）。

---

## 2. 6 角色 TTS 音色分配方案

### 2.1 音色分配总表

| 角色 | 角色ID | 性格特征 | edge-tts Voice | edge-tts 风格 | VoxCPM2 Voice Description |
|:----:|--------|----------|:--------------:|:-------------:|--------------------------|
| 谢云岚 | xieyunlan | 冷峻·沉稳（玄天司少卿） | `zh-CN-YunxiNeural` | Male, Novel, Lively/Sunshine |
| 花映月 | huayingyue | 妩媚·柔美（月影阁花魁） | `zh-CN-XiaoxiaoNeural` | Female, News/Novel, Warm |
| 沈明月 | shenmingyue | 清冷·高傲（女医官） | `zh-CN-XiaoyiNeural` | Female, Cartoon/Novel, Lively |
| 李怀瑾 | lihuaijin | 温润·书生气（书生谋士） | `zh-CN-YunyangNeural` | Male, News, Professional |
| 顾千帆 | guqianfan | 磁性·低沉（隐鳞会使者） | `zh-CN-YunjianNeural` | Male, Sports/Novel, Passion |
| 公孙兰 | gongsunlan | 慵懒·淡雅（长辈） | `zh-CN-XiaoxiaoNeural` | Female, News/Novel, Warm |

### 2.2 edge-tts 角色参数（用于快速原型）

| 角色 | Voice | `--rate` | `--pitch` | 备注 |
|------|-------|----------|-----------|------|
| 谢云岚 | zh-CN-YunxiNeural | `-10%` | `-5%` | 冷峻低沉稳重感 |
| 花映月 | zh-CN-XiaoxiaoNeural | `+5%` | `+10%` | 妩媚上扬柔美感 |
| 沈明月 | zh-CN-XiaoyiNeural | `-5%` | `0%` | 清冷干脆感 |
| 李怀瑾 | zh-CN-YunyangNeural | `0%` | `+5%` | 温润书卷气 |
| 顾千帆 | zh-CN-YunjianNeural | `-15%` | `-10%` | 磁性低沉感 |
| 公孙兰 | zh-CN-XiaoxiaoNeural | `-5%` | `-10%` | 慵懒淡雅感 |

> **注意**: `zh-CN-XiaorouNeural` 在当前 edge-tts 版本中不可用，公孙兰改用 `zh-CN-XiaoxiaoNeural`（F, Warm）配合 `rate=-5%, pitch=-10%` 实现慵懒淡雅效果。

---

## 3. 语气标签参数配置

### 3.1 edge-tts 语气映射（`--rate` / `--pitch`）

基于 `frontend/js/mood.js` 定义的 8 种 mood：

| Mood 标签 | 语气描述 | rate 增量 | pitch 增量 | 对应立绘表情 |
|-----------|---------|:---------:|:----------:|:-----------:|
| `neutral` | 平常/默认 | `base` | `base` | default |
| `warm` | 温和/温柔 | `base` | `+5%` | smile |
| `happy` | 开心/愉快 | `+5%` | `+10%` | happy |
| `sad` | 悲伤/低落 | `-10%` | `-5%` | sad |
| `angry` | 生气/严厉 | `+5%` | `-5%` | angry |
| `cold` | 冷漠/疏离 | `-5%` | `-10%` | cold |
| `surprised` | 惊讶 | `+5%` | `+5%` | surprised |
| `blush` | 害羞/羞涩 | `-5%` | `+5%` | blush |

**计算公式**: 最终 `--rate` = 角色基础 rate + mood rate 增量；最终 `--pitch` = 角色基础 pitch + mood pitch 增量。

**示例 — 谢云岚 + MOOD cold**:
```
--rate  = (-10%) + (-5%)  = -15%
--pitch = (-5%)  + (-10%) = -15%
```

**示例 — 花映月 + MOOD happy**:
```
--rate  = (+5%) + (+5%)   = +10%
--pitch = (+10%) + (+10%) = +20%
```

### 3.2 VoxCPM2 语气映射（Voice Description 自然语言）

参见 `frontend/tts_templates/changan_moon.py` 中 `VOICE_DESCRIPTIONS`，每角色每语气使用括号内自然语言描述控制情绪：

```python
# 示例：谢云岚
"cold": "(冷峻青年男声，沉稳低沉，语气冰冷疏离，不带感情)"
"warm": "(冷峻青年男声，沉稳低沉，语气难得温和，放软了声音)"
```

`tts_voice_config.py` 中的 `MOOD_STYLES` 作为通用语气前缀：

```python
MOOD_STYLES = {
    "neutral": "(语气平静)",
    "warm": "(语气温和)",
    "happy": "(语气带着笑意)",
    "sad": "(语气低落)",
    "angry": "(语气严厉)",
    "cold": "(语气冷淡)",
    "surprised": "(语气微讶)",
    "blush": "(语气轻柔，略带羞涩)",
}
```

---

## 4. 首批预生成语音文本清单

每角色选 2-3 句代表性台词，覆盖核心 mood。文本源自角色设定与剧情走向。

### 谢云岚（xieyunlan）— 冷峻沉稳

| # | 语气 | 台词 | 场景/用途 |
|:-:|:----:|------|-----------|
| 1 | neutral | 上元灯夜长安城中灯火万千，我奉命查访旧案路过朱雀大街，见你神色不对。 | 初次登场，表明身份 |
| 2 | cold | 此事与你无关，不必再问。再纠缠下去，我只能请你到玄天司走一趟了。 | 冷漠疏离，拒人千里 |
| 3 | warm | 罢了，你既执意要查，便跟紧我。长安城的水，比你想的要深。 | 难得温和，放软态度 |

### 花映月（huayingyue）— 妩媚柔美

| # | 语气 | 台词 | 场景/用途 |
|:-:|:----:|------|-----------|
| 1 | happy | 夜深露重，公子怎的还在街上徘徊？快进屋歇歇，仔细着凉。 | 乐坊初遇，温柔热情 |
| 2 | warm | 灯市里的人潮喧闹，我却只盼你能多留片刻。 | 情感升温，脉脉含情 |
| 3 | sad | 我这一生，从没有人问过我愿不愿意。你……是第一个。 | 真情流露，哀婉动人 |

### 沈明月（shenmingyue）— 清冷爽利

| # | 语气 | 台词 | 场景/用途 |
|:-:|:----:|------|-----------|
| 1 | neutral | 你手这样凉，可是穿得太少？我这个手炉给你。 | 医馆相遇，关切 |
| 2 | cold | 案卷上的线索我已记下，说重点，莫要绕圈子。 | 公事公办，冷硬 |
| 3 | warm | 既然信我，就把你的伤给我看看。医者仁心，不会害你。 | 放下防备，柔和 |

### 李怀瑾（lihuaijin）— 温润如玉

| # | 语气 | 台词 | 场景/用途 |
|:-:|:----:|------|-----------|
| 1 | neutral | 不妨事，慢慢来。无论多久，我都等你把话说完。 | 书肆初遇，耐心温和 |
| 2 | warm | 朝堂风云虽险，你我只管把真相查清，不负本心。 | 共谋大事，君子之约 |
| 3 | sad | 有些事，知道了反而痛苦。但我……还是想告诉你。 | 沉重真相，哀伤 |

### 顾千帆（guqianfan）— 磁性低沉（隐藏角色）

| # | 语气 | 台词 | 场景/用途 |
|:-:|:----:|------|-----------|
| 1 | cold | 别急，慢慢说，我听着呢。天塌下来也有我顶着。 | 首次现身，亦敌亦友 |
| 2 | neutral | 你且把今夜所见一五一十讲来，莫要遗漏半分。 | 盘问线索，沉着 |
| 3 | warm | 这么多年了……你是第一个让我想停下来的人。 | 破防时刻，真情 |

### 公孙兰（gongsunlan）— 慵懒淡雅

| # | 语气 | 台词 | 场景/用途 |
|:-:|:----:|------|-----------|
| 1 | warm | 孩子，这些年你受苦了。回来了就好，回来了就好。 | 长辈关怀，慈和温厚 |
| 2 | neutral | 当年的事我一直没敢告诉你，今日既已至此，便不再隐瞒。 | 揭开往事，平和从容 |
| 3 | sad | 那丫头若还在，也该有你这么大了……罢了，不提了。 | 往事唏嘘，沉重叹息 |

---

## 5. 生成命令模板

### 5.1 edge-tts 单条生成（快速原型用）

```bash
# 基本格式: edge-tts --voice <VOICE> --rate <RATE> --pitch <PITCH> --text "<台词>" --write-media <输出路径>.mp3

# 示例：谢云岚 cold（冷漠）
edge-tts \
  --voice zh-CN-YunxiNeural \
  --rate -15% \
  --pitch -15% \
  --text "此事与你无关，不必再问。再纠缠下去，我只能请你到玄天司走一趟了。" \
  --write-media /d/HermesWorkspace/girlgame-skill/frontend/assets/tts/changan-moon/cache/xieyunlan_cold_01.mp3

# 示例：花映月 happy（开心）
edge-tts \
  --voice zh-CN-XiaoxiaoNeural \
  --rate +10% \
  --pitch +20% \
  --text "夜深露重，公子怎的还在街上徘徊？快进屋歇歇，仔细着凉。" \
  --write-media /d/HermesWorkspace/girlgame-skill/frontend/assets/tts/changan-moon/cache/huayingyue_happy_01.mp3
```

### 5.2 edge-tts 批量生成脚本模板

```bash
#!/bin/bash
# 文件: scripts/batch_gen_changan_tts.sh
# 月下长安 TTS 批量预生成

TTS_DIR="/d/HermesWorkspace/girlgame-skill/frontend/assets/tts/changan-moon/cache"
mkdir -p "$TTS_DIR"

# === 谢云岚 (xieyunlan) ===
# Base: --voice zh-CN-YunxiNeural --rate -10% --pitch -5%

edge-tts --voice zh-CN-YunxiNeural --rate -10% --pitch -5% \
  --text "上元灯夜长安城中灯火万千，我奉命查访旧案路过朱雀大街，见你神色不对。" \
  --write-media "$TTS_DIR/xieyunlan_neutral_01.mp3"

edge-tts --voice zh-CN-YunxiNeural --rate -15% --pitch -15% \
  --text "此事与你无关，不必再问。再纠缠下去，我只能请你到玄天司走一趟了。" \
  --write-media "$TTS_DIR/xieyunlan_cold_01.mp3"

edge-tts --voice zh-CN-YunxiNeural --rate -10% --pitch 0% \
  --text "罢了，你既执意要查，便跟紧我。长安城的水，比你想的要深。" \
  --write-media "$TTS_DIR/xieyunlan_warm_01.mp3"

# === 花映月 (huayingyue) ===
# Base: --voice zh-CN-XiaoxiaoNeural --rate +5% --pitch +10%

edge-tts --voice zh-CN-XiaoxiaoNeural --rate +10% --pitch +20% \
  --text "夜深露重，公子怎的还在街上徘徊？快进屋歇歇，仔细着凉。" \
  --write-media "$TTS_DIR/huayingyue_happy_01.mp3"

edge-tts --voice zh-CN-XiaoxiaoNeural --rate +5% --pitch +15% \
  --text "灯市里的人潮喧闹，我却只盼你能多留片刻。" \
  --write-media "$TTS_DIR/huayingyue_warm_01.mp3"

edge-tts --voice zh-CN-XiaoxiaoNeural --rate -5% --pitch +5% \
  --text "我这一生，从没有人问过我愿不愿意。你……是第一个。" \
  --write-media "$TTS_DIR/huayingyue_sad_01.mp3"

# === 沈明月 (shenmingyue) ===
# Base: --voice zh-CN-XiaoyiNeural --rate -5% --pitch 0%

edge-tts --voice zh-CN-XiaoyiNeural --rate -5% --pitch 0% \
  --text "你手这样凉，可是穿得太少？我这个手炉给你。" \
  --write-media "$TTS_DIR/shenmingyue_neutral_01.mp3"

edge-tts --voice zh-CN-XiaoyiNeural --rate -10% --pitch -10% \
  --text "案卷上的线索我已记下，说重点，莫要绕圈子。" \
  --write-media "$TTS_DIR/shenmingyue_cold_01.mp3"

edge-tts --voice zh-CN-XiaoyiNeural --rate -5% --pitch +5% \
  --text "既然信我，就把你的伤给我看看。医者仁心，不会害你。" \
  --write-media "$TTS_DIR/shenmingyue_warm_01.mp3"

# === 李怀瑾 (lihuaijin) ===
# Base: --voice zh-CN-YunyangNeural --rate 0% --pitch +5%

edge-tts --voice zh-CN-YunyangNeural --rate 0% --pitch +5% \
  --text "不妨事，慢慢来。无论多久，我都等你把话说完。" \
  --write-media "$TTS_DIR/lihuaijin_neutral_01.mp3"

edge-tts --voice zh-CN-YunyangNeural --rate 0% --pitch +10% \
  --text "朝堂风云虽险，你我只管把真相查清，不负本心。" \
  --write-media "$TTS_DIR/lihuaijin_warm_01.mp3"

edge-tts --voice zh-CN-YunyangNeural --rate -10% --pitch 0% \
  --text "有些事，知道了反而痛苦。但我……还是想告诉你。" \
  --write-media "$TTS_DIR/lihuaijin_sad_01.mp3"

# === 顾千帆 (guqianfan) ===
# Base: --voice zh-CN-YunjianNeural --rate -15% --pitch -10%

edge-tts --voice zh-CN-YunjianNeural --rate -15% --pitch -10% \
  --text "别急，慢慢说，我听着呢。天塌下来也有我顶着。" \
  --write-media "$TTS_DIR/guqianfan_cold_01.mp3"

edge-tts --voice zh-CN-YunjianNeural --rate -15% --pitch -10% \
  --text "你且把今夜所见一五一十讲来，莫要遗漏半分。" \
  --write-media "$TTS_DIR/guqianfan_neutral_01.mp3"

edge-tts --voice zh-CN-YunjianNeural --rate -15% --pitch -5% \
  --text "这么多年了……你是第一个让我想停下来的人。" \
  --write-media "$TTS_DIR/guqianfan_warm_01.mp3"

# === 公孙兰 (gongsunlan) ===
# Base: --voice zh-CN-XiaoxiaoNeural --rate -5% --pitch -10%

edge-tts --voice zh-CN-XiaoxiaoNeural --rate -5% --pitch -5% \
  --text "孩子，这些年你受苦了。回来了就好，回来了就好。" \
  --write-media "$TTS_DIR/gongsunlan_warm_01.mp3"

edge-tts --voice zh-CN-XiaoxiaoNeural --rate -5% --pitch -10% \
  --text "当年的事我一直没敢告诉你，今日既已至此，便不再隐瞒。" \
  --write-media "$TTS_DIR/gongsunlan_neutral_01.mp3"

edge-tts --voice zh-CN-XiaoxiaoNeural --rate -15% --pitch -15% \
  --text "那丫头若还在，也该有你这么大了……罢了，不提了。" \
  --write-media "$TTS_DIR/gongsunlan_sad_01.mp3"

echo "=== 月下长安 TTS 批量预生成完成 ==="
echo "共 18 条音频 → $TTS_DIR"
ls -la "$TTS_DIR"/*.mp3 2>/dev/null | wc -l
```

### 5.3 VoxCPM2 单条生成（高质量用）

通过 TTS API 生成（需先启动 `server_tts.py`）：

```python
import requests

TTS_URL = "http://localhost:7860/tts"

payload = {
    "templateId": "changan-moon",
    "charId": "xieyunlan",
    "text": "此事与你无关，不必再问。再纠缠下去，我只能请你到玄天司走一趟了。",
    "mood": "cold",
    "turnCount": 0,
    "pageIdx": 0,
}

resp = requests.post(TTS_URL, json=payload, timeout=120)
if resp.status_code == 200:
    with open("output.wav", "wb") as f:
        f.write(resp.content)
    print(f"✅ 生成成功 ({len(resp.content)/1024:.1f}KB)")
```

### 5.4 VoxCPM2 批量生成脚本

参考 `scripts/gen_test_tts.py` 模板，扩展为全角色全语气：

```bash
python scripts/gen_changan_tts_batch.py
```

---

## 6. 文件命名规范

```
assets/tts/changan-moon/cache/
  {charId}_{mood}_{seq}.mp3     ← edge-tts 批量预生成
  {charId}_{turn}_{page}.wav    ← VoxCPM2 运行时缓存（自动）

assets/tts/changan-moon/voice_refs/
  {charId}.wav                  ← VoxCPM2 参考音（已就绪）
```

**命名规则**:
- `charId`: 小写，与 `frontend/tts_templates/changan_moon.py` 定义一致
- `mood`: 小写，与 `mood.js` VALID_MOODS 一致
- `seq`: 两位数字序号（01/02/03...）
- 扩展名: edge-tts 用 `.mp3`，VoxCPM2 用 `.wav`

---

## 7. 生成优先级与批次

### 第1批（P0 · 立即执行）
6 角色 × 2~3 核心语气 = **18 条语音**
- 参考上面第4节清单
- 目标：验证语气效果，提交冒烟测试

### 第2批（P1 · 剧情覆盖）
6 角色 × 8 语气 = **48 条语音**
- 每角色每语气 1 句代表性台词
- 目标：覆盖 MOOD 体系全色彩

### 第3批（P2 · 关键场景）
根据剧情对话实际使用频率，增量补充高频台词
- 目标：提升缓存命中率，减少运行时合成

---

## 8. 验收清单

| # | 检查项 | 方法 |
|:-:|--------|------|
| 1 | 每个角色可听到 distinct 音色 | 听取 6 角色 neutral 语音 |
| 2 | 同一角色不同语气可区分 | 听同一角色 cold vs warm |
| 3 | 音频时长 3-10 秒 | `ffprobe` 或手动播放 |
| 4 | 音频无杂音/爆音 | 实际试听 |
| 5 | edge-tts 参数生效 | 对比默认值与调参后的差异 |
| 6 | 文件命名符合规范 | 检查 `${charId}_${mood}_${seq}.mp3` 格式 |

---

## 9. 已有配置对照

| 配置文件 | 路径 | 说明 |
|---------|------|------|
| TTS 角色配置 | `frontend/tts_templates/changan_moon.py` | 6角色VOICE_DESCRIPTIONS + REF_SAMPLE_LINES |
| 语气标签 | `frontend/js/mood.js` | 8种MOOD + 检测/映射逻辑 |
| TTS 播放 | `frontend/js/tts.js` | 调用 /proxy/tts，缓存命中逻辑 |
| 路径解析 | `frontend/tts_paths.py` | 模板分目录资源定位 |
| 音色配置 | `frontend/tts_voice_config.py` | MOOD_STYLES + 通用参数 |
| TTS 服务 | `frontend/server_tts.py` | VoxCPM2 FastAPI 服务 |
| 语音库 | `frontend/assets/tts/changan-moon/voice_refs/` | 6角色参考音 WAV 已就绪 ✅ |
| 缓存目录 | `frontend/assets/tts/changan-moon/cache/` | 空目录，待生成 |

---

## 10. 快速启动指南

```bash
# 1. 确认 edge-tts 可用
edge-tts --list-voices | grep zh-CN

# 2. 生成第1批 18 条语音（使用上面批量脚本）
bash scripts/batch_gen_changan_tts.sh

# 3. 或使用 VoxCPM2（需先启动 TTS 服务）
cd frontend
python server_tts.py
# 另开终端
python scripts/gen_changan_tts_batch.py

# 4. 验证
ls -la frontend/assets/tts/changan-moon/cache/
# 应看到 18+ 个 .mp3 或 .wav 文件
```

---

> **更新日志**
> - 2026-05-27 初版：基于 PRD 5.4 节 + 现有 `changan_moon.py` 配置 + 边缘检测到 `zh-CN-XiaorouNeural` 不可用，公孙兰调整为 zh-CN-XiaoxiaoNeural
