# 🎮 AVG梦工厂 — AI 视觉小说创作与游玩

> **ADV**enture Game · 用 AI 写故事、做立绘、听语音，一站式玩转视觉小说

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📖 这是什么

**AVG梦工厂** 是一套 AI 驱动的视觉小说平台：既能**在浏览器 / 桌面客户端里直接玩**（立绘、流式叙事、选项、语音），也支持在 Claude Code、Cursor、[Hermes Agent](https://hermes-agent.nousresearch.com) 等 Agent 里通过 Skill 模式对话开局。

你可以把它理解为：

- **玩家的梦工厂** — 选剧本、创角色，AI 当场写剧情、配音、换表情
- **作者的梦工厂** — 改 markdown 模板即可定制世界，无需从零写引擎

### 核心理念

```
剧情由 AI 实时书写，框架负责呈现与状态追踪。
模板 + 提示词 = 可玩的视觉小说。
```

这意味着：

- **开箱即玩** — Web / 桌面客户端，`npm run dev` 即可本地运行
- **修改剧情 = 改 markdown** — 模板在 `templates/` 目录
- **完全开源** — MIT 许可，故事与素材归你所有

---

## 🚀 快速开始

### 方式一：Web 客户端游玩（推荐体验立绘 / 流式 / TTS）

#### 环境要求

| 组件 | 说明 |
|------|------|
| Node.js | ≥ 18，用于 `node server.js` |
| LLM 服务 | OpenAI 兼容接口；可在 **游戏内配置**（Base URL / API Key / 模型），或通过 `.env` / 环境变量预设 |
| TTS（可选） | Python 3.10+、`voxcpm` 包、本机 VoxCPM2 模型，仅 **月下长安** 模板启用语音 |

#### 1. 启动游戏服务

```bash
# 安装依赖（Electron 桌面版可选）
npm install

# 启动开发服务器（默认 http://localhost:8080）
npm run dev
```

按需设置环境变量（推荐复制 `.env.example` → `.env`，`npm run dev` 会自动加载）：

```bash
# Windows PowerShell 示例
$env:PORT = "8080"
# 方案 A：DeepSeek / 任意 OpenAI 兼容 HTTPS API
$env:LLM_BASE = "https://api.deepseek.com/v1"
$env:LLM_API_KEY = "sk-..."              # 与 Hermes 配置中的 Key 相同即可
$env:LLM_MODEL = "deepseek-chat"
# 方案 B：本地 Hermes Gateway
# $env:LLM_BASE = "http://localhost:8656"
# 方案 C：无 LLM 仅测布局/UI
# $env:AVG_MOCK_LLM = "1"
$env:TTS_BASE = "http://localhost:7860"   # TTS 服务地址（见下方）
npm run dev
```

浏览器打开：**http://localhost:8080/**

**配置 LLM（三选一，任选其一即可）：**

| 方式 | 说明 |
|------|------|
| **游戏内弹窗**（推荐） | 未配置时，启动页或点击「开始故事」会自动弹出；游戏中 ⚙ → **API 配置** 可随时修改 |
| **`.env` 文件** | 复制 `.env.example` → `.env`，填写 `LLM_BASE` / `LLM_API_KEY` / `LLM_MODEL` |
| **Mock 模式** | 设置 `AVG_MOCK_LLM=1`，无需真实 API，仅测布局/UI |

DeepSeek 示例：`LLM_BASE=https://api.deepseek.com/v1`，`LLM_MODEL=deepseek-chat`

**自测（Agent / CLI）：**

```bash
npm run test:preflight          # HTTP 预检（资产、页面、LLM）
npm run test:preflight:layout   # LLM 未开时仅测布局相关项
```

在 Cursor 中说「AVG 自测」或引用技能 `avg-self-test`，按 `.cursor/skills/avg-self-test/SKILL.md` 进游戏、交互、截图并对照规范。

#### 2. 游戏流程

```
首页 index.html → 选择剧本 templates.html → 创建角色 character.html → 开始游戏 game.html
```

| 步骤 | 页面 | 操作 |
|------|------|------|
| 选剧本 | `/templates.html` | 校园 / 都市 / **月下长安** / 悬疑 等模板 |
| 创角 | `/character.html` | 填写姓名、性格等 |
| 游玩 | `/game.html?template=changan-moon` | 点击继续翻页，底部 **最多 3 个**选项推进剧情 |

**快捷入口（已创角可直进）：**

```
http://localhost:8080/game.html?template=changan-moon
http://localhost:8080/game.html?template=campus-summer
```

#### 3. 操作说明

- **点击屏幕 /「▼ 点击继续」**：翻页阅读叙事
- **选项**：出现在文本框上方，选 1～3 或点 **✎** 自由输入
- **菜单**：存档 / 读档 / 返回（`game.html` 内菜单按钮）
- **立绘**：LLM 输出 `[MOOD]` / `[EXPR]` 后自动切换 PNG 表情（**月下长安** 6 角色、**校园** 7 角色已齐；无 PNG 时不显示占位图）
- **语音**：需启动 TTS；有 `「对白」` 的台词会按 `[MOOD:]` 情绪合成（旁白不播）
- **对话框**：底部留白、紧凑行距；选项在文本框上方，最多 3 个

#### 4. 启动 TTS（可选，月下长安）

```bash
# 指定 VoxCPM2 模型目录（按本机路径修改）
# Windows
set VOXCPM2_PATH=F:\ComfyUI_V6.0\ComfyUI-WorkFisher-V2\ComfyUI\models\VoxCPM2
python frontend/server_tts.py

# 或使用脚本（Linux/macOS）
bash frontend/start-tts.sh
```

另开终端保持 `npm run dev` 运行。健康检查：`http://localhost:8080/proxy/tts/status`（端口以 `PORT` 为准）。

**完整配置、排错与局域网说明见 [`docs/TTS.md`](docs/TTS.md)。** 技术方案见 [`docs/tts-plan.md`](docs/tts-plan.md)（基于 [OpenBMB/VoxCPM](https://github.com/OpenBMB/VoxCPM) Voice Design）。

#### 5. Electron 桌面版（v1.0）

```bash
npm install
npm start          # 开发运行
npm run build:win  # Windows 安装包 + 便携版 → dist/
npm run build:mac  # macOS dmg/zip（须在 Mac 上执行）
```

打包说明见 [`docs/RELEASE.md`](docs/RELEASE.md)。桌面版内嵌本地服务器，与浏览器版功能一致；API 可在应用内配置，或写入用户目录 `.env`（见 `.env.example`）。

**v1.0 发布：** 推送 git 标签 `v1.0.0` 可触发 GitHub Actions 在 Windows / macOS 上自动构建安装包。

#### 6. 常见问题

| 现象 | 处理 |
|------|------|
| 502 / 上游服务不可达 | 点击 **「配置 API」** 填写 Base URL 与 Key；或在 `.env` 配 `LLM_BASE`+`LLM_API_KEY`；或 `AVG_MOCK_LLM=1` 后**重启** `npm run dev` |
| 弹出 API 配置 | 服务端未检测到 LLM Key 且本地无保存配置时正常行为；保存后会自动测试连接 |
| 一直「正在落笔」无内容 | 确认 `LLM_BASE` 可访问，且上游支持 `POST /v1/chat/completions` |
| 无立绘 | 月下长安等模板需 `frontend/assets/portraits/{角色Id}/*.png`；无 PNG 时不显示占位图 |
| 无语音 | 见 [`docs/TTS.md`](docs/TTS.md)：启动 `server_tts.py`，检查 `/proxy/tts/status` 是否为 200 |
| 流式不生效 | 上游需支持 `stream: true`；失败时会自动降级为非流式整包请求 |

---

### 方式二：Agent Skill 模式游玩

在支持 Skill 的 Agent 中加载本仓库的 `SKILL.md`，然后对话开局即可：

```bash
# 示例：在 Agent 中加载 skill 后说
「我要开一局校园青春模板」
```

AI 引导你创建角色 → 故事开始。

### 自建模板

```bash
# 告诉 AI：
「我要自定义模板」

# AI 抛 8 个问题引导你完成创作
# 15 分钟后你就有自己的故事了
```

详见 [`references/template-authoring.md`](references/template-authoring.md)

---

## 🎯 适用场景

| 类型 | 适合吗 |
|------|--------|
| 视觉小说 / 电子小说 | ✅ 完美 |
| Galgame / 乙女游戏 | ✅ 完美 |
| 交互式故事 / CYOA | ✅ 完美 |
| 文字冒险游戏 | ✅ 完美 |
| 悬疑推理 / 剧情驱动 | ✅ 完美 |
| 代码引擎渲染的游戏 | ❌ 不适合（请看其他方案） |

---

## 📁 项目结构

```
项目根目录/
├── server.js                         # Web 开发服（静态资源 + LLM/TTS 代理，支持客户端 API 头透传）
├── .env.example                      # LLM / TTS 环境变量示例
├── package.json                      # npm run dev / test:preflight / npm start
├── scripts/avg-preflight.mjs         # HTTP 预检（资产、页面、LLM）
├── frontend/
│   ├── index.html                    # 启动页（浏览器/API 配置）
│   ├── templates.html                # 选剧本
│   ├── character.html                # 创角
│   ├── game.html                     # 游戏主界面（立绘 / 对话框 / API 弹窗）
│   ├── js/                           # engine / bootstrap / api-config / stream / mood / tts
│   ├── assets/portraits/             # 立绘 PNG（月下长安 6×8 + 校园 7×8）
│   └── server_tts.py                 # VoxCPM2 TTS 服务
├── .cursor/skills/avg-self-test/     # Cursor 自测技能与清单
├── electron/                         # 桌面客户端（可选）
├── SKILL.md                          # 框架核心引擎（系统提示词）
├── AVG.md                            # 工程说明
├── docs/                             # 设计 / PRD / TTS / UI 方案
├── references/
│   ├── save-schema.md                # 存档格式规范
│   ├── memory-system.md              # 三级记忆架构 + 感知隔离
│   ├── character-system.md           # 角色系统 + NPC互动动力学
│   ├── ending-design.md              # 结局设计规范
│   ├── unlock-rules.md               # 解锁规则
│   ├── template-authoring.md         # 自定义模板创作指南
│   └── auto-progression.md           # 自动推进机制设计模式
├── templates/
│   ├── campus-summer/                # 模板①：校园青春·夏日的回音
│   │   ├── story/main.md             #   故事框架（3幕·21结局）
│   │   ├── roles/                    #   7个完整角色卡
│   │   │   ├── linxue.md
│   │   │   ├── suyunxi.md
│   │   │   ├── shenqingci.md
│   │   │   ├── jiangxiaoyu.md
│   │   │   ├── xiazhiyao.md
│   │   │   ├── chengnianci.md
│   │   │   └── yexiaoman.md
│   │   ├── memory/flags.md           #   Flag清单·信物·存档点
│   │   └── protagonist/template.md   #   主角创建模板
│   ├── cafe-night/                   # 模板②：都市物语·深夜咖啡店
│   ├── changan-moon/                 # 模板③：古风奇幻·月下长安
│   └── perspective-template.md       # 视角文件模板
├── launcher/                         # Web端角色创建向导
│   └── index.html                    #   7步引导，一键生成初始化指令
└── .galgame/                         # 用户存档目录（位于 ~/ 下）
    └── saves/
```

---

## 🎭 核心功能

### 三级记忆系统

```
┌─ ① 工作记忆（State Card） ─┐  ←  每轮对话末尾的状态摘要
│  Scene / Route / Affection   │
└─────────────────────────────┘
              ↕
┌─ ② 会话缓存（session.json）─┐  ←  每回合自动写入
│  完整状态 + 近期历史         │
└─────────────────────────────┘
              ↕
┌─ ③ 持久化存档（save_N.json）┐  ←  关键节点保存
│  完整状态 + 全部历史         │
└─────────────────────────────┘
```

### 感知隔离

每个角色拥有独立视角文件。AI 生成对话时，角色 A 只能引用自己视角文件里的信息——不知道的事不能暗示、不能影射。这解决了多角色对话中「信息泄露」的常见问题。

### 角色冲突网络

角色之间不是只围着主角转。每张角色卡预定义了：
- 与其他角色的隐藏张力
- 好感度增减事件表（精确到数值）
- 路线中的关系动态变化
- 侧写事件和 AI 扮演指南

### 校园模板亮点

> 🌸 **夏日的回音** — 毕业那年夏天，回到空无一人的母校。
> 每个人都藏着同一个关于高二的秘密……

- **7个可攻略角色**，每个有独立深层秘密
- **21个结局**（7HE + 7NE + 6BE + 1隐藏）
- **8个校园活动**推进剧情（返校日→大扫除→旧照片展→夏夜会→文化祭→星空坦白→夏日祭告别）
- **核心悬念**贯穿全剧，逐层揭示
- **5条 BE 路线**让选择具有真实重量

### 都市模板亮点

> ☕ **深夜咖啡店** — 凌晨两点，城市失眠者的避风港。
> 咖啡杯沿上的口红印、黑胶唱片的第四分三十三秒、雨夜里的第十三封信……

- **6个可攻略角色**，每个都有未说出口的秘密
- **8个结局**（5HE + 1NE + 1隐藏 + 1BE）
- **贯穿全剧的暗线系统**：夜航船日志、黑胶唱片 #7、雨夜来信
- **时间推进机制**：每次选择后时间向前走，凌晨的城市在灯光中渐次睡去
- **隐藏结局「凌晨四点的答案」** 需要整合所有暗线碎片

### 古风模板亮点

> 🌙 **月下长安** — 上元灯夜，你捡到一枚刻着「归」字的玉佩。
> 三股势力在你身后交织，而你身上藏着连你自己都不知道的秘密……

- **6个可攻略角色**（4初期 + 2解锁），三大势力都有各自的立场
- **9个结局**（6HE + 1NE + 1隐藏 + 1BE）
- **梦境系统**：每幕后的梦境逐渐揭示二十年前那夜的真相
- **谶言破解**：四句童谣对应四条关键线索，全部破解解锁隐藏结局
- **势力声望系统**：选择影响角色好感也影响势力声望

### 悬疑模板亮点

> 🔍 **镜像之馆** — 七面古镜，七个声音，二十年前的失踪案。
> 庄园里有一部断线电话——某些夜晚，它会响。

- **6个角色**（4初期 + 2解锁），每人站在不同专业视角面对同一个谜
- **13个结局**（6HE + 4NE + 1隐藏 + 2BE）
- **推理进度条**：线索收集驱动真相解锁
- **证物收集 + 红鲱鱼误导**：真假线索交织
- **倒影世界**：镜子的另一边有人等你
- **心理防御系统**：每个角色有信任值和防御值双重状态

---

## 🛠 自定义模板

### 三阶段创作流程

```
【阶段一】AI 引导（5分钟）
  回答 8 个问题，AI 生成模板骨架

【阶段二】AI 填充（5分钟）
  AI 自动生成角色卡、场景、Flags、结局表

【阶段三】手动精调（无限时）
  - 入门：改文本（描写、台词、结局文案）
  - 进阶：改数值（好感度节点、Flag 条件）
  - 高级：改规则（新增系统、自定义机制）
```

### 支持的游戏风格

| 模板 | 风格 | 可攻略 | 结局 | 状态 |
|------|------|--------|------|------|
| 🏫 校园·夏日的回音 | 青春/治愈/悬疑 | 7人 | 21 | ✅ 完整 |
| ☕ 都市·深夜咖啡店 | 都市/文艺/微悬疑 | 6人 | 8 | ✅ 完整 + 暗线系统 |
| 🌙 古风·月下长安 | 古风/权谋/轻玄幻 | 6人 | 9 | ✅ 完整 + 谶言梦境 |
| 🔍 悬疑·镜像之馆 | 悬疑/推理/心理 | 6人 | 13 | ✅ 完整 |

---

## 📜 许可

MIT License — 随便用，随便改，随便分享。

---

## 🙏 致谢

- [Hermes Agent](https://hermes-agent.nousresearch.com) — 提供了 agent 框架
- 灵感来自 SillyTavern、Ren'Py 等优秀的文字游戏工具

---

> *"没有冲突，就没有故事。"*
