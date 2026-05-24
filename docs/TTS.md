# TTS 语音配置说明

> 按剧本分目录 · VoxCPM2 Clone · 经 `server.js` 代理

完整技术方案见 [`tts-plan.md`](tts-plan.md)。资源目录说明见 [`frontend/assets/tts/README.md`](../frontend/assets/tts/README.md)。

---

## 1. 资源目录（按剧本）

```
frontend/assets/tts/
  {templateId}/              # 与 template-registry.js 中 id 一致
    voice_refs/              # 参考音（约 50 字生成，目标 ~18–22s）
      {charId}.wav
    cache/                   # 对局对白缓存（自动生成，可 gitignore）
      {charId}_{turn}_{page}.wav
```

| templateId | 剧本 | 角色数 | 前端 `ttsEnabled` |
|------------|------|--------|-------------------|
| `changan-moon` | 月下长安 | 6 | ✅ |
| `campus-summer` | 夏日的回音 | 7 | ✅ |
| `cafe-night` | 深夜咖啡店 | 6 | ✅ |
| `suspense-mansion` | 镜像之馆 | 6 | ✅ |

| 项目 | 说明 |
|------|------|
| **参考音** | `assets/tts/{templateId}/voice_refs/{charId}.wav` |
| **对局缓存** | `assets/tts/{templateId}/cache/{charId}_{turn}_{page}.wav` |
| **文案与音色** | `frontend/tts_templates/{模块}.py` → `REF_SAMPLE_LINES`、`VOICE_DESCRIPTIONS` |
| **请求参数** | `tts.js` 自动附带当前剧本 `templateId` |

旧版扁平目录 `assets/voice_refs/`、`assets/voices/` 已废弃。

---

## 2. 生成参考音

每角色使用 **约 50 字** neutral 台词，Voice Design 一次性生成参考 WAV：

```powershell
$env:VOXCPM2_PATH = "你的\VoxCPM2模型路径"

# 单剧本
python scripts/generate_voice_refs.py --template campus-summer

# 四剧本一键（已有文件默认跳过）
python scripts/generate_voice_refs.py --all

# 强制覆盖
python scripts/generate_voice_refs.py --all --force
```

生成后 **重启 `server_tts.py`**。

`GET /proxy/tts/status` 返回 `templates.{templateId}.{charId}` 表示该角色参考音是否在磁盘上。

---

## 3. 运行时行为

1. LLM 输出带 `[MOOD: …]` 与 `「台词」` 的页 → `mood.js` 解析 `charId` / `mood`
2. `tts.js` → `POST /proxy/tts`，body 含 `templateId`、`charId`、`text`、`mood`、`turnCount`、`pageIdx`
3. `server_tts.py` 读取对应 `voice_refs/{charId}.wav`，Clone 合成；命中 cache 则直接返回
4. 纯旁白（无 `「」`）不触发 TTS

**MOOD 标准集**（与立绘/LLM 一致）：  
`neutral | warm | happy | sad | angry | cold | surprised | blush`

---

## 4. 新剧本接入 TTS

1. 在 `frontend/tts_templates/` 新增模块（`TEMPLATE_ID`、`CHARACTER_IDS`、`REF_SAMPLE_LINES`、`VOICE_DESCRIPTIONS`）
2. 在 `tts_templates/__init__.py` 的 `_REGISTRY` 注册
3. `template-registry.js`：`portraits` 中文名 → `charId`，`ttsEnabled: true`
4. `python scripts/generate_voice_refs.py --template 新剧本id`
5. 重启 TTS 服务并验证 `/proxy/tts/status`

---

## 5. 架构

```
浏览器 tts.js（templateId + charId + mood）
    → POST /proxy/tts
    → server.js → server_tts.py
    → 读 assets/tts/{templateId}/voice_refs/{charId}.wav（Clone）
    → 写 assets/tts/{templateId}/cache/…
```

排错与环境变量见 [`tts-setup.md`](tts-setup.md)（若存在）或 `tts-plan.md` 环境变量章节。
