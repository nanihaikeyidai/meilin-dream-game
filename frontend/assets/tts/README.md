# TTS 资源目录（按剧本）

```
assets/tts/
  {templateId}/          # 与 template-registry.js 中剧本 id 一致，如 changan-moon
    voice_refs/          # Clone 参考音，每角色一个 {charId}.wav（约 50 字 → ~20s）
      xieyunlan.wav
    cache/               # 对局合成缓存（自动生成，可删）
      xieyunlan_3_0.wav
```

## 生成参考音

```powershell
$env:VOXCPM2_PATH = "你的\VoxCPM2模型路径"
python scripts/generate_voice_refs.py --template changan-moon
python scripts/generate_voice_refs.py --template changan-moon --force
```

文案在 `frontend/tts_templates/{剧本模块}.py` 的 `REF_SAMPLE_LINES`（约 50 字）。

## 已配置剧本

| templateId | 目录 | 角色数 |
|------------|------|--------|
| `changan-moon` | 月下长安 | 6 |
| `campus-summer` | 夏日的回音 | 7 |
| `cafe-night` | 深夜咖啡店 | 6 |
| `suspense-mansion` | 镜像之馆 | 6 |

一键生成全部参考音：

```powershell
python scripts/generate_voice_refs.py --all --force
```

## 新剧本

1. 在 `frontend/tts_templates/` 增加配置模块并注册到 `__init__.py`
2. `template-registry.js` 中设置 `ttsEnabled: true` 与 `portraits` 映射
3. 运行 `generate_voice_refs.py --template 你的剧本id`

## 迁移旧目录

若仍有 `assets/voice_refs/*.wav`：

```powershell
python scripts/migrate_tts_assets.py --template changan-moon
```
