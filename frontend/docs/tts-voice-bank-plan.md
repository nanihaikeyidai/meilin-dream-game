# 月下长安 — 6角色×3语气 TTS 音色生成方案

> 迭代3 · 任务3.6 · 2026-05-24

---

## 1. 体系架构

```
前端游戏引擎 ←→ server_tts.py (FastAPI, :7860)
                    │
                    ├── tts_voice_config.py   ← 角色配置/语气风格
                    ├── assets/voice_refs/     ← 6角色参考音 (bootstrap)
                    └── assets/voices/         ← 生成输出 {charId}_{mood}.wav
```

### 核心机制：Clone 模式

TTS 使用 VoxCPM2 的 **参考音克隆模式**：
1. `reference_wav_path` 锁定音色（性别/年龄/质感）
2. `mood_style` 前缀控制语气（如 `(语气温和)`）
3. 文字内容自然传达台词情感

```
最终输入模型 = "(语气温和)你放心，有我在，不会让你受半分委屈。"
              ↑ mood_style        ↑ 自定义测试台词
```

---

## 2. 选定语气与参数映射

从 PRD 原始8种语气中选定3种：

| 语气 | MOOD_STYLES 前缀 | 语速 | 音高 | 音量 | 情感标签 |
|------|------------------|------|------|------|----------|
| warm | `(语气温和)` | 稍慢 | -2% | +5% | 温柔/体贴/慈和 |
| happy | `(语气带着笑意)` | +5% | +3% | +8% | 愉悦/轻快/爽朗 |
| sad | `(语气低落)` | -10% | -5% | -10% | 悲伤/低落/沉重 |

> **注**：当前 VoxCPM2 通过 `mood_style` 文本前缀控制语气。未来可扩展 `CLONE_GEN_KWARGS` 中的 `cfg_value` 和 `inference_timesteps` 实现更精细的韵律/速度参数调整。

---

## 3. 6角色×3语气测试文本矩阵

### 谢云岚（xieyunlan）— 冷峻青年男声，沉稳低沉

| 语气 | 测试台词 | 情境 |
|------|---------|------|
| **warm** | 「你放心，有我在，不会让你受半分委屈。」 | 温柔坚定的承诺 |
| **happy** | 「今日天色晴好，倒是个难得的舒心日子。」 | 难得展露的愉悦 |
| **sad** | 「故人旧事，终究是回不去了……你说得对。」 | 沉郁悲凉的回忆 |

### 花映月（huayingyue）— 年轻女声，妩媚柔美

| 语气 | 测试台词 | 情境 |
|------|---------|------|
| **warm** | 「夜深露重，公子披件衣裳再走罢，仔细着凉。」 | 温柔体贴的关怀 |
| **happy** | 「今儿个灯市可热闹了，快陪我逛逛去！」 | 欢快雀跃的邀约 |
| **sad** | 「这满城烟火，终究没一盏灯是等我回家的。」 | 凄楚落寞的自嘲 |

### 顾千帆（guqianfan）— 洒脱青年男声，明朗随性

| 语气 | 测试台词 | 情境 |
|------|---------|------|
| **warm** | 「别急，慢慢说，我听着呢。天塌下来也有我顶着。」 | 爽朗耐心的安抚 |
| **happy** | 「好酒！痛快！来来来，再给你满上一杯！」 | 豪爽痛快的喜悦 |
| **sad** | 「这一壶太雕，敬那些再也回不来的人罢。」 | 低沉隐忍的悼念 |

### 沈明月（shenmingyue）— 英气女声，清越爽利

| 语气 | 测试台词 | 情境 |
|------|---------|------|
| **warm** | 「你手这样凉，可是穿得太少了？我这个手炉给你。」 | 难得的柔和关切 |
| **happy** | 「查到了！果然不出我所料——走，抓人去了！」 | 爽朗明亮的破案 |
| **sad** | 「我查了三年，真相竟是如此……让我静一静。」 | 沉重不甘的打击 |

### 李怀瑾（lihuaijin）— 温雅青年男声，如玉温润

| 语气 | 测试台词 | 情境 |
|------|---------|------|
| **warm** | 「不妨事，慢慢来。无论多久，我都等你。」 | 如玉温润的包容 |
| **happy** | 「这曲子我练了些时日，你听听可好？」 | 含笑谦和的分享 |
| **sad** | 「原来这世间最苦，不是求不得，而是已失去。」 | 低沉哀伤的顿悟 |

### 公孙兰（gongsunlan）— 沉稳中年女声，平和从容

| 语气 | 测试台词 | 情境 |
|------|---------|------|
| **warm** | 「孩子，这些年你受苦了。回来了就好，回来了就好。」 | 慈和温厚的重逢 |
| **happy** | 「哟，今日这是吹了什么风，你竟也学会哄人开心了。」 | 含笑欣慰的调侃 |
| **sad** | 「当年的事，我一直没敢告诉你……是我不对。」 | 沉重叹息的忏悔 |

---

## 4. 批生成脚本说明

**文件**: `frontend/generate_voice_bank.py`

### 用法

```bash
# 生成全部 18 个组合
python frontend/generate_voice_bank.py

# Dry-run 查看参数
python frontend/generate_voice_bank.py --dry-run

# 单个组合测试
python frontend/generate_voice_bank.py --single xieyunlan warm
```

### 调用示例（HTTP API）

```python
POST /tts
Content-Type: application/json

{
  "charId": "xieyunlan",
  "text": "你放心，有我在，不会让你受半分委屈。",
  "mood": "warm",
  "turnCount": 1,      # 避免缓存命中同名旧文件
  "pageIdx": 0
}
```

### 输出文件

```
assets/voices/
├── xieyunlan_warm.wav
├── xieyunlan_happy.wav
├── xieyunlan_sad.wav
├── huayingyue_warm.wav
├── huayingyue_happy.wav
├── huayingyue_sad.wav
├── guqianfan_warm.wav
├── guqianfan_happy.wav
├── guqianfan_sad.wav
├── shenmingyue_warm.wav
├── shenmingyue_happy.wav
├── shenmingyue_sad.wav
├── lihuaijin_warm.wav
├── lihuaijin_happy.wav
├── lihuaijin_sad.wav
├── gongsunlan_warm.wav
├── gongsunlan_happy.wav
└── gongsunlan_sad.wav
```

---

## 5. 生成结果验证

| 指标 | 值 |
|------|----|
| 角色数 | 6 / 6 ✅ |
| 每种语气的角色数 | 6 / 6 ✅ |
| 总生成数 | 18 / 18 ✅ |
| 失败数 | 0 ❌ |
| 文件大小范围 | ~315 KB ~ 630 KB |
| 服务端 | 127.0.0.1:7860, 模型已加载 ✅ |
| 参考音 | 6个全部就绪 ✅ |

---

## 6. 前端集成指南

在游戏引擎中调用音色文件：

```javascript
// 预加载所有音色
const voiceBank = {};
for (const charId of ['xieyunlan','huayingyue','guqianfan','shenmingyue','lihuaijin','gongsunlan']) {
  for (const mood of ['warm','happy','sad']) {
    const key = `${charId}_${mood}`;
    voiceBank[key] = new Audio(`assets/voices/${key}.wav`);
  }
}

// 播放
function playVoice(charId, mood) {
  voiceBank[`${charId}_${mood}`]?.play();
}
```

---

## 7. 注意事项

1. **文件命名**：使用 `{charId}_{mood}.wav` 格式，与 game skill 中 `mood` 参数字段值一致
2. **缓存冲突**：批生成脚本中 `turnCount` 设为递增序号避免命中缓存旧文件
3. **服务器地址**：生产环境替换为实际内网 IP（当前为 `127.0.0.1:7860`）
4. **扩展性**：3种语气可随时扩展为 5-8 种，只需在 `SELECTED_MOODS` 列表和 `TEST_LINES` 字典中新增条目
5. **质量检查**：建议逐个人耳听一遍，确认语气区分度。如 warm 与 neutral 差异不够明显，可调整台词文本的情感浓度
