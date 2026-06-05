# AGENTS.md — AVG梦工厂

> 本文档供 AI 编码助手阅读。如果你正在通过 Claude Code、Cursor、Kimi 等工具操作本项目，请优先阅读本节，再改动代码。

---

## 项目概述

**AVG梦工厂** 是一套 AI 驱动的视觉小说（AVG/Visual Novel）平台：

- **对玩家**：在浏览器或桌面客户端里选剧本、创角色，AI 实时写剧情、配音、切换表情立绘。
- **对作者**：改 `templates/` 下的 Markdown 模板即可定制世界观、角色、结局树，无需从零写引擎。
- **对 Agent**：本仓库同时是一个可安装的 Skill（`SKILL.md`），AI Agent 加载后可通过对话直接带用户开局。

核心理念：**模板 + 提示词 = 可玩的视觉小说**。剧情由 AI 实时书写，框架负责呈现与状态追踪。

---

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端引擎 | 原生 HTML/CSS/JS（无框架） | `frontend/` 目录，模块化 IIFE 挂载到 `window` |
| 开发服务器 | Node.js 原生 `http` / `https` | **零 npm 运行时依赖**，`server.js` 提供静态文件 + 代理 |
| 桌面客户端 | Electron 35 + electron-builder 25 | `electron/` 目录，内嵌本地服务器 |
| AI 后端 | OpenAI 兼容 API | 支持 DeepSeek、本地 Hermes Gateway 等 |
| TTS（可选） | Python 3.10+ + FastAPI + VoxCPM2 | `frontend/server_tts.py`，古风模板默认启用 |
| 剧本格式 | Markdown | `templates/<模板>/story/main.md` + `roles/*.md` |
| 素材管线 | ComfyUI (zImage) / RunningHub | 背景图、立绘生成与抠图 |

---

## 项目结构

```
项目根目录/
├── server.js                    # Web 开发服：静态资源、LLM/TTS 代理、Mock 模式
├── package.json                 # npm 脚本 + electron-builder 配置
├── .env.example                 # 环境变量模板（LLM / TTS / Mock）
│
├── frontend/                    # 纯前端游戏引擎
│   ├── index.html               # 启动页跳转
│   ├── templates.html           # 选剧本页
│   ├── character.html           # 创建角色页
│   ├── game.html                # 游戏主界面（立绘 / 对话框 / 选项 / API 弹窗）
│   ├── auto_test.html           # 自动化测试入口页
│   ├── demo.html                # 演示页
│   ├── js/                      # 前端模块（IIFE）
│   │   ├── bootstrap.js         # 游戏主循环：模板加载、对话、选项、存档
│   │   ├── engine.js            # 渲染引擎：立绘回退链、场景、表情、分页
│   │   ├── api.js               # LLM 调用封装（流式 + 非流式）
│   │   ├── api-config.js        # API 配置持久化（localStorage / Electron IPC）
│   │   ├── stream.js            # 流式响应解析（SSE）
│   │   ├── mood.js              # MOOD/EXPR 标签解析、表情映射、TTS 情绪
│   │   ├── save.js              # 浏览器端存档（localStorage）
│   │   ├── tts.js               # TTS 语音播放控制
│   │   ├── bgm.js               # 背景音乐控制
│   │   └── template-registry.js # 模板元数据与角色-立绘映射
│   ├── css/style.css            # 全局样式
│   ├── assets/
│   │   ├── backgrounds/         # 场景背景图（校园 / 古风 / 都市 / 悬疑）
│   │   ├── portraits/           # 角色立绘 PNG（标准 8 表情：default/smile/happy/sad/angry/blush/cold/surprised）
│   │   ├── music/               # BGM 资源（按模板分子目录）
│   │   ├── tts/                 # TTS 语音缓存（按模板分目录）
│   │   └── voice_refs/          # TTS 角色音色参考音频
│   ├── server.js                # 遗留独立开发服（frontend/ 内，功能同根目录 server.js）
│   ├── server_tts.py            # VoxCPM2 TTS 服务（FastAPI，可选）
│   ├── tts_paths.py             # TTS 资源路径解析
│   ├── tts_voice_config.py      # TTS 音色配置与 MOOD 映射
│   ├── tts_templates/           # TTS 剧本模板生成器（__init__.py + 各模板 builder）
│   ├── start-tts.sh             # TTS 服务启动脚本
│   ├── smoke_test.sh            # Bash 冒烟测试脚本
│   └── docs/tts-voice-bank-plan.md  # TTS 语音库规划
│
├── electron/                    # 桌面客户端
│   ├── main.js                  # 主进程：启动内嵌服务器、创建窗口
│   ├── preload.js               # 预加载脚本：暴露 electronAPI 到渲染进程
│   └── ipc-handlers.js          # IPC 处理：API 配置、模板列表、文件读取、LLM 直连
│
├── templates/                   # 剧情模板（Markdown 驱动）
│   ├── campus-summer/           # 模板①：校园青春·夏日的回音（7角色，21结局）
│   ├── cafe-night/              # 模板②：都市物语·深夜咖啡店（6角色，8结局）
│   ├── changan-moon/            # 模板③：古风奇幻·月下长安（6角色，9结局）
│   ├── suspense-mansion/        # 模板④：悬疑推理·镜像之馆（6角色，13结局）
│   ├── cafe-night.md            # 都市模板概览（速查）
│   ├── changan-moon.md          # 古风模板概览（速查）
│   └── perspective-template.md  # 视角文件模板
│       # 每个模板目录内通常含：story/main.md, roles/*.md, memory/flags.md, protagonist/template.md
│
├── scripts/                     # 工具脚本
│   ├── avg-preflight.mjs        # HTTP 预检脚本：资产、页面、LLM、TTS 健康检查
│   ├── batch-generate-ancient-bg.sh
│   ├── batch-generate-backgrounds.sh
│   ├── batch_generate_defaults.py
│   ├── batch_generate_expressions.py
│   ├── batch_rembg_portraits.sh
│   ├── batch_zimage.py / .sh
│   ├── check_and_rembg.py
│   ├── download_minicpm_v46.py
│   ├── fix-motion-tags.js
│   ├── generate_portrait_test.py
│   ├── gen_huazhou.bat / .py / _tts.py
│   ├── gen_test_tts.py
│   ├── make_transparent.py
│   ├── merge_voice_refs_from_voices.py
│   ├── migrate_tts_assets.py
│   ├── patch-game-choices.js / patch-game-html.js
│   ├── prepare-wincodesign-cache.ps1
│   ├── publish-release.ps1
│   ├── rembg_portrait.py
│   ├── test-local-comfyui-bg.py
│   ├── test_minicpm_v46_video.py
│   └── verify-backgrounds.sh
│
├── engine/                      # Node.js 存档管理器（CLI）
│   ├── save-manager.mjs         # init/save/load/list
│   └── batch-save.mjs           # 快速批量存档（一次性写入 session + 视角 + 自动存档）
│
├── launcher/                    # 启动器工具
│   ├── check.py                 # 环境检查
│   ├── patch_api.py             # API 配置补丁
│   ├── start.bat                # Windows 启动脚本
│   └── start.sh                 # Linux/macOS 启动脚本
│
├── docs/                        # 设计文档
│   ├── prd.md                   # 产品需求文档（技术架构、当前状态）
│   ├── RELEASE.md               # 桌面版发布与打包说明
│   ├── TTS.md                   # TTS 配置、排错与局域网说明
│   ├── tts-plan.md              # TTS 技术方案（基于 OpenBMB/VoxCPM）
│   ├── tts-setup.md             # TTS 环境搭建指南
│   ├── design.md                # 设计文档
│   ├── ui-ux-optimization-plan.md # UI/UX 优化方案
│   ├── optimization-backlog.md  # 待优化清单
│   └── suno-bgm-prompts.md      # Suno BGM 生成提示词
│
├── references/                  # 规范与参考
│   ├── save-schema.md           # 存档格式规范
│   ├── memory-system.md         # 三级记忆架构 + 感知隔离
│   ├── character-system.md      # 角色系统 + NPC 互动动力学
│   ├── unlock-rules.md          # 解锁规则
│   └── backgrounds.md           # 背景图规范
│
├── .cursor/                     # Cursor IDE 配置
│   ├── rules/
│   │   ├── codegraph.mdc        # CodeGraph MCP 使用规则
│   │   └── git-commit-push.mdc  # Git 提交规范
│   └── skills/avg-self-test/    # Cursor 自测技能
│       ├── SKILL.md             # 自测工作流（浏览器 MCP → 进游戏 → 截图 → 报告）
│       └── checklist.md         # 验收检查清单
│
├── .github/workflows/
│   ├── release.yml              # 推送 v* 标签触发 Windows + macOS 自动构建
│   └── publish-manual.yml       # 手动触发构建
│
├── build/                       # 构建资源（应用图标等）
├── dist/                        # 构建产物（electron-builder 输出）
└── .galgame/                    # 用户存档目录（运行时生成于项目根目录或用户目录）
    └── saves/
```

---

## 构建与运行命令

### 环境要求

- Node.js ≥ 18
- LLM 服务：OpenAI 兼容接口（游戏内可配置，或通过 `.env` / 环境变量预设）
- TTS（可选）：Python 3.10+、`fastapi`、`soundfile`、`voxcpm` 包、本机 VoxCPM2 模型

### Web 开发模式（推荐）

```bash
npm install
npm run dev          # 仅开发服 http://localhost:8080
npm run dev:all      # 开发服 + TTS（推荐本地游玩）
```

环境变量（也可写入 `.env`，`server.js` 会自动加载）：

```bash
# Windows PowerShell
$env:PORT = "8080"
$env:LLM_BASE = "https://api.deepseek.com/v1"
$env:LLM_API_KEY = "sk-..."
$env:LLM_MODEL = "deepseek-chat"
$env:TTS_BASE = "http://localhost:7860"   # 可选
# $env:AVG_MOCK_LLM = "1"                  # 无 LLM 时仅测布局/UI
```

### Electron 桌面版

```bash
npm start              # 开发运行
npm run pack           # 仅解压目录（快速验证）
npm run build:win      # Windows 安装包 + 便携版 → dist/
npm run build:mac      # macOS dmg/zip（须在 Mac 上执行）
npm run build:all      # 全平台
```

### 测试命令

```bash
npm run test:preflight          # HTTP 预检（资产、页面、LLM）
npm run test:preflight:layout   # 允许 LLM 失败，仅测布局相关项
npm run test                    # 同 test:preflight:layout
npm run smoke                   # bash 冒烟脚本（frontend/smoke_test.sh）
```

### TTS 服务（可选，古风模板默认启用）

```bash
# 指定 VoxCPM2 模型目录后启动
set VOXCPM2_PATH=F:\ComfyUI_V6.0\...\VoxCPM2
python frontend/server_tts.py
# 或使用 bash frontend/start-tts.sh
```

---

## 代码风格与模块约定

### 前端模块模式

所有前端 JS 使用 **IIFE（立即执行函数）**，将公共 API 挂载到 `window` 全局对象，模块间通过全局对象引用：

```javascript
(function (global) {
  // 私有实现...
  global.AvgEngine = { createEngine, escapeHtml, splitIntoPages, renderPageText };
})(window);
```

主要全局命名空间：

| 命名空间 | 文件 | 职责 |
|----------|------|------|
| `AvgEngine` | `engine.js` | 渲染引擎（立绘、场景、分页） |
| `AvgBootstrap` | `bootstrap.js` | 游戏主循环（内部使用） |
| `AvgApi` | `api.js` | LLM 调用封装 |
| `AvgApiConfig` | `api-config.js` | API 配置管理 |
| `AvgStream` | `stream.js` | 流式响应处理（SSE） |
| `AvgMood` | `mood.js` | 情绪/表情标签解析 |
| `AvgSave` | `save.js` | 浏览器存档（localStorage） |
| `AvgTemplates` | `template-registry.js` | 模板注册表（含场景背景、立绘映射） |

### LLM 输出标签规范

AI 生成的叙事文本中，引擎通过以下标签控制呈现：

| 标签 | 示例 | 作用 |
|------|------|------|
| `[MOOD:xxx]` | `[MOOD: warm]` | 情绪标签，映射到立绘表情和 TTS 语气 |
| `[EXPR:xxx]` | `[EXPR: smile]` | 显式指定表情（优先级高于 MOOD） |
| `[SCENE:xxx]` | `[SCENE: classroom]` | 切换场景背景图 |

有效表情（`EXPR`）：`default`, `smile`, `happy`, `sad`, `angry`, `blush`, `cold`, `surprised`

### 路径与文件组织

- 立绘资源路径固定为 `assets/portraits/{剧本Id}/{角色Id}/{表情}.png`
- 模板路径固定为 `templates/{模板Id}/story/main.md`
- 任何服务端文件路径解析都必须做目录遍历防护（参考 `server.js` 中 `path.normalize` + `startsWith` 检查）

---

## 测试策略

### 预检脚本 `scripts/avg-preflight.mjs`

自测入口，检查项包括：

1. 开发服务器 `/proxy/health` 是否可达
2. LLM 代理 `/proxy/chat/completions` 是否正常（可 `--allow-llm-fail` 跳过）
3. TTS 代理 `/proxy/tts/status` 是否可达（optional）
4. `game.html` 关键布局标记是否存在（`character-layer`、`choices-panel` 等）
5. 立绘 PNG HTTP 可达性（月下长安 6角色 + 校园 7角色 + 都市 6角色 + 悬疑 6角色，各 8 表情）
6. `/api/templates` 接口是否返回预期模板列表

### Bash 冒烟测试 `frontend/smoke_test.sh`

CI/无浏览器环境下的基础验证：
- 代理服务器健康检查
- Hermes Gateway 可达性
- `game.html` 关键内容完整性
- API 代理响应
- 本地立绘资产存在性
- JS 模块与模板 API 就绪

### Cursor 端到端自测

`.cursor/skills/avg-self-test/SKILL.md` 定义了基于浏览器 MCP 的可重复验收流程：

- 预检 → 浏览器进入游戏 → 交互（点击翻页、选项）→ 截图 → 对照 `checklist.md` 出报告
- **禁止**仅 curl 页面就宣称通过；必须截图 + 视觉分析
- LLM 未开启时，交互/流式/选项项应标 N/A 或 Fail，不得标 Pass

### Mock 模式

设置 `AVG_MOCK_LLM=1` 后，`server.js` 会返回固定 Mock 叙事，用于无 API 时的 UI/布局自测。

---

## 部署与发布

### Web 端

直接运行 `npm run dev` 即可，无额外构建步骤。`server.js` 是纯 Node.js 原生实现，零 npm 运行时依赖（开发依赖仅 Electron 相关）。

### 桌面端

- 使用 `electron-builder` 打包
- 产物输出到 `dist/`
- Windows：`.exe` 安装程序 + 便携版
- macOS：`.dmg` + `.zip`（x64 / arm64）
- 应用图标可放入 `build/icon.ico`（Windows）和 `build/icon.icns`（macOS）

### CI/CD

`.github/workflows/release.yml`：

- 触发条件：推送 `v*` 标签（如 `v1.0.0`），或手动 `workflow_dispatch`
- `build-win`：Windows runner 打 portable + nsis 包
- `build-mac`：macOS runner 打 dmg + zip 包（`continue-on-error: true`）
- `publish`：收集产物并创建 GitHub Release

---

## 关键配置说明

### `.env` 变量

复制 `.env.example` 为 `.env` 后填写：

| 变量 | 必填 | 说明 |
|------|------|------|
| `LLM_BASE` | 是 | OpenAI 兼容 API 地址，如 `https://api.deepseek.com/v1` |
| `LLM_API_KEY` | 远程必填 | API Key；本地 localhost 可免填 |
| `LLM_MODEL` | 否 | 默认 `deepseek-v4-flash` |
| `TTS_BASE` | 否 | TTS 服务地址，默认 `http://localhost:7860` |
| `AVG_MOCK_LLM` | 否 | 设为 `1` 启用 Mock 模式（无真实 LLM） |
| `PORT` | 否 | 开发服务器端口，默认 `8080` |

### Electron 桌面版配置

- 首次启动可在界面内弹窗配置 API
- 或在用户数据目录放 `.env`（Windows: `%APPDATA%\avg-menggongchang\.env`）
- API 配置通过 IPC 持久化到 `config.json`（`electron/ipc-handlers.js`）

---

## 安全与注意事项

1. **API Key 不落地服务端**：`server.js` 仅从环境变量或客户端请求头读取 Key，不做持久化。浏览器端存 `localStorage`，Electron 端存 `config.json`。
2. **路径遍历防护**：所有文件读取（模板、静态资源）都做了 `path.normalize` + 前缀校验，禁止访问规定目录之外的路径。
3. **CORS**：开发服务器全局设置 `Access-Control-Allow-Origin: *`，仅用于本地开发。
4. **代码签名**：当前未启用（`forceCodeSigning: false`）。CI 中通过环境变量禁用签名自动发现。
5. **不要在生产环境暴露 `AVG_MOCK_LLM=1`**：Mock 返回固定假数据，仅用于测试。
6. **存档隔离**：浏览器端存档 key 为 `girlgame_save_{templateId}_{slot}`；Node.js CLI 存档在 `.galgame/saves/{存档名}/`，含 `session.json` 和 `perspectives/*.md`。

---

## 给 Agent 的常用操作速查

| 目的 | 命令 |
|------|------|
| 启动开发服 | `npm run dev` |
| 开发服 + TTS | `npm run dev:all` |
| 运行预检 | `node scripts/avg-preflight.mjs` |
| 允许 LLM 失败的预检 | `node scripts/avg-preflight.mjs --allow-llm-fail` |
| 启动桌面版 | `npm start` |
| 打 Windows 包 | `npm run build:win` |
| 查看模板列表 | 读 `templates/` 下的子目录，或请求 `http://localhost:8080/api/templates` |
| 添加新模板 | 在 `templates/` 下新建目录，含 `story/main.md`、`roles/`、`memory/flags.md` 等 |
| 添加新角色立绘 | 在 `frontend/assets/portraits/{剧本Id}/{角色Id}/` 下放 `{表情}.png`（8 种标准表情） |
| 启动 TTS | `python frontend/server_tts.py`（需设 `VOXCPM2_PATH`） |
| CLI 存档管理 | `node engine/save-manager.mjs init <存档名>` |
| 批量存档 | `node engine/batch-save.mjs '<json>'` |

---

> 更多详情见 `README.md`（快速开始与功能介绍）、`SKILL.md`（Agent 游玩模式系统提示词）、`docs/prd.md`（产品需求与架构）。
