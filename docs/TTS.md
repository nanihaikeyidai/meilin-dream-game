# TTS 语音配置说明

> 按剧本分目录 · VoxCPM2 Clone · 经 `server.js` 代理

完整技术方案见 [`tts-plan.md`](tts-plan.md)。

---

## 1. 资源目录（按剧本）

```
frontend/assets/tts/
  changan-moon/              # templateId，与 template-registry.js 一致
    voice_refs/              # 参考音（约 50 字生成，目标 ~20s）
      xieyunlan.wav
      …
    cache/                   # 对局对白缓存（自动生成，可 gitignore）
      xieyunlan_3_0.wav
```

| 项目 | 说明 |
|------|------|
| **当前启用 TTS 的剧本** | 仅 `changan-moon`（`ttsEnabled: true`） |
| **参考音** | `assets/tts/{templateId}/voice_refs/{charId}.wav` |
| **对局缓存** | `assets/tts/{templateId}/cache/{charId}_{turn}_{page}.wav` |
| **文案配置** | `frontend/tts_templates/changan_moon.py` → `REF_SAMPLE_LINES` |

旧版扁平目录 `assets/voice_refs/`、`assets/voices/` 已废弃，可用 `scripts/migrate_tts_assets.py` 迁移。

---

## 2. 生成参考音（推荐流程）

每角色使用 **约 50 字** neutral 台词，Voice Design 一次性生成 **约 18～22 秒** 参考 WAV：

```powershell
$env:VOXCPM2_PATH = "F:\ComfyUI_V6.0\ComfyUI-WorkFisher-V2\ComfyUI\models\VoxCPM2"
python scripts/generate_voice_refs.py --template changan-moon
python scripts/generate_voice_refs.py --template changan-moon --force
```

生成后 **重启 `server_tts.py`**。前端请求需带 `templateId`（`tts.js` 已自动传入当前剧本 id）。

`GET /tts/status` 返回 `templates.{templateId}.{charId}` 表示参考音是否就绪。

---

## 3. 新剧本接入 TTS

1. 在 `frontend/tts_templates/` 新增模块（`REF_SAMPLE_LINES` 约 50 字/角色、`VOICE_DESCRIPTIONS`）
2. 在 `tts_templates/__init__.py` 注册
3. `template-registry.js`：`ttsEnabled: true`，`portraits` 中文名 → charId
4. `python scripts/generate_voice_refs.py --template 新剧本id`

---

## 4. 架构

```
浏览器 tts.js（templateId + charId + mood）
    → POST /proxy/tts
    → server.js → server_tts.py
    → 读 assets/tts/{templateId}/voice_refs/{charId}.wav（Clone）
    → 写 assets/tts/{templateId}/cache/…
```

更多排错见 [`tts-setup.md`](tts-setup.md)。
