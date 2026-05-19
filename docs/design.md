# 梅林绮梦录 — AVG 游戏设计文档

> 最后更新: 2026-05-20

## 项目信息

- **路径:** `girlgame-skill/`
- **前端入口:** `frontend/game.html`（浏览器） / Electron `index → templates → character → game`
- **开发服务器:** `npm run dev` → `server.js`（静态资源 + LLM/TTS 代理 + 剧本 markdown + SSE 流式）
- **立绘目录:** `frontend/assets/portraits/`（古风 6 角色 × 8 表情 = **48 PNG**）
- **TTS:** `frontend/server_tts.py` + VoxCPM2（`VOXCPM2_PATH` 环境变量）

## 架构

```
frontend/js/
  template-registry.js   # 各剧本：立绘映射、场景表
  mood.js                # [MOOD] / EXPR 映射、情绪推断
  engine.js              # 立绘 PNG 优先、场景、[EXPR]、分页
  api.js                 # LLM 非流式（备用）
  stream.js              # LLM SSE 流式
  tts.js                 # /proxy/tts + /proxy/tts/status
  save.js                # localStorage 存档
  bootstrap.js           # 主循环、对话框省略号等待
```

## 立绘素材库（`frontend/assets/portraits`）

| 角色 ID | 中文名 | PNG |
|---------|--------|:---:|
| xieyunlan | 谢云岚 | 8/8 |
| huayingyue | 花映月 | 8/8 |
| guqianfan | 顾千帆 | 8/8 |
| shenmingyue | 沈明月 | 8/8 |
| lihuaijin | 李怀瑾 | 8/8 |
| gongsunlan | 公孙岚 | 8/8 |

**加载规则（已实现）：仅 PNG 立绘，不使用 SVG。**

```
PNG(当前表情) → PNG(smile) → PNG(default)
```

无对应 PNG 时隐藏立绘层（不显示圆形 SVG 占位）。

## 情绪与立绘 / TTS

| 标签 | 立绘 | TTS |
|------|------|-----|
| `[MOOD: warm]` | 无 EXPR 时映射为 `smile` | VoxCPM2 括号语气描述 |
| `[EXPR: sad]` | 直接加载 `sad.png` | 不参与（语音只看 MOOD） |

解析入口：`frontend/js/mood.js` → `parsePageBeat()`，由 `engine.js` / `tts.js` / `bootstrap.js` 共用。

## 标签规范

| 标签 | 用途 |
|------|------|
| `[SCENE: id]` | 切换背景 |
| `[EXPR: smile]` | 立绘表情（优先于关键词） |
| `[MOOD: warm]` | VoxCPM2 语气；可映射到 EXPR |

**台词格式（LLM 必须）：**

```text
沈明月 [MOOD: neutral] [EXPR: default]「台词内容」
```

## 交互

- **流式叙事：** `/proxy/chat/completions` + `stream: true`，对话框内实时出字
- **等待态：** 对话框「正在落笔...」，无全屏「故事正在展开」
- **选项：** 最多 3 个预设项，位于文本框上方；自由输入独立入口
- **TTS：** 有 `「」` 台词时播放；旁白不播

## 启动

```bash
npm run dev                    # 前端 + LLM 代理
python frontend/server_tts.py  # TTS（需 VoxCPM2）
# 可选: set VOXCPM2_PATH=F:\...\VoxCPM2
```

## TODO

- [ ] 校园/都市/悬疑模板立绘 PNG 补全
- [ ] Electron 打包
- [ ] 与 `engine/save-manager.mjs` 存档格式统一
