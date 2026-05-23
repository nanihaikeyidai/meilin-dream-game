# TTS 语音配置说明

> 月下长安模板专用 · VoxCPM2 Voice Design · 经 `server.js` 代理

完整技术方案见 [`tts-plan.md`](tts-plan.md)。本文档面向**本地部署与排错**。

---

## 1. 适用范围

| 项目 | 说明 |
|------|------|
| **启用模板** | 仅 **`changan-moon`（月下长安）** 的 `ttsEnabled: true` |
| **播放内容** | 带角色名 + `「对白」` 的台词；**纯旁白不播** |
| **情绪** | LLM 输出 `[MOOD: xxx]`，映射为 VoxCPM2 括号内语气描述 |
| **缓存** | 生成结果写入 `frontend/assets/voices/{charId}_{turn}_{page}.wav` |

---

## 2. 架构

```
浏览器 tts.js
    → POST /proxy/tts
    → server.js（Node，默认 :8080）
    → frontend/server_tts.py（Python，默认 :7860）
    → VoxCPM2 模型（GPU 合成 WAV）
```

手机 / 局域网访问时，TTS 仍走游戏服的 `/proxy/tts`，**无需**单独暴露 7860 端口。

---

## 3. 环境要求

| 组件 | 要求 |
|------|------|
| **游戏服** | Node.js ≥ 18，`npm run dev` |
| **TTS 服** | Python 3.10–3.12（推荐 **3.12**） |
| **voxcpm** | `pip install voxcpm`（Python 3.13 可能安装失败） |
| **依赖** | `fastapi`、`uvicorn`、`soundfile`、`numpy` |
| **模型** | [OpenBMB/VoxCPM2](https://github.com/OpenBMB/VoxCPM) 权重目录 |
| **GPU** | 有 NVIDIA CUDA 时加载更快；CPU 亦可但极慢 |

### Windows 推荐：ComfyUI 自带 Python

若系统 Python 3.13 无法安装 `voxcpm`，可使用已集成环境的 ComfyUI Python：

```powershell
F:\ComfyUI_V6.0\ComfyUI-WorkFisher-V2\Python3.12.6\python.exe --version
```

---

## 4. 环境变量

| 变量 | 作用 | 默认值 |
|------|------|--------|
| `VOXCPM2_PATH` | VoxCPM2 模型目录 | `F:\ComfyUI_V6.0\...\models\VoxCPM2` |
| `TTS_PORT` | TTS 服务监听端口 | `7860` |
| `TTS_BASE` | 游戏服代理的上游地址 | `http://localhost:7860` |
| `PORT` | 游戏 Web 服务端口 | `8080` |

`.env` 示例（游戏服根目录）：

```env
PORT=8081
TTS_BASE=http://127.0.0.1:7860
```

> **注意**：Windows 上 **8080** 可能被系统服务（如 IP Helper）占用，可改用 `PORT=8081`。

---

## 5. 启动步骤

需要**两个终端**同时运行。

### 终端 1 — 游戏 Web 服务

```powershell
cd D:\HermesWorkspace\girlgame-skill
npm install
$env:PORT = "8081"   # 若 8080 被占用
npm run dev
```

### 终端 2 — TTS 服务

**方式 A：系统 Python（3.10–3.12）**

```powershell
$env:VOXCPM2_PATH = "F:\ComfyUI_V6.0\ComfyUI-WorkFisher-V2\ComfyUI\models\VoxCPM2"
python frontend/server_tts.py
```

**方式 B：ComfyUI Python（Windows 推荐）**

```powershell
$env:VOXCPM2_PATH = "F:\ComfyUI_V6.0\ComfyUI-WorkFisher-V2\ComfyUI\models\VoxCPM2"
& "F:\ComfyUI_V6.0\ComfyUI-WorkFisher-V2\Python3.12.6\python.exe" frontend/server_tts.py
```

**Linux / macOS**

```bash
export VOXCPM2_PATH=/path/to/VoxCPM2
bash frontend/start-tts.sh
# 或: python frontend/server_tts.py
```

首次启动会加载模型（约 10–30 秒），看到 `[TTS] Model loaded successfully` 即可。

---

## 6. 验证

| 检查项 | 地址 | 期望 |
|--------|------|------|
| TTS 直连 | `http://127.0.0.1:7860/tts/status` | `{"status":"ok","model_loaded":true,...}` |
| 游戏代理 | `http://127.0.0.1:8081/proxy/tts/status` | 同上 |
| 游戏入口 | `http://127.0.0.1:8081/game.html?template=changan-moon` | 可选剧本进入 |

游戏中右上角 **♪** 图标：

- 正常：有对白时闪动
- 异常：变暗，悬停提示「语音服务未连接」

---

## 7. 局域网 / 手机

1. 游戏服默认监听 `0.0.0.0`（`npm run dev`）
2. 手机与电脑同一 WiFi，访问 `http://<电脑IP>:8081/`
3. TTS 由电脑上的 Python 服务合成，手机只收音频流，**不必**在手机上装 Python

Windows 防火墙需放行游戏端口（如 8081）：

```powershell
New-NetFirewallRule -DisplayName "AVG梦工厂 Dev" -Direction Inbound -Protocol TCP -LocalPort 8081 -Action Allow
```

---

## 8. 播放行为（前端）

| 行为 | 说明 |
|------|------|
| 文字先显示 | 对话框渲染完成后再开始播放 / 请求 TTS |
| 翻页即停 | 文字切换、进入选项、显示「正在落笔」时立刻停止语音 |
| 预加载 | 当前页播放时，后台预下载下一页有对白的 WAV |
| 取消请求 | 快速翻页会 abort 过期的 fetch，避免播错句 |

---

## 9. LLM 输出格式

有语音的台词须包含角色名、MOOD、对白：

```text
谢云岚 [MOOD: cold] [EXPR: cold]「此事与你无关。」
```

MOOD 允许值：`neutral` `warm` `happy` `sad` `angry` `cold` `surprised` `blush`

---

## 10. 常见问题

| 现象 | 原因 / 处理 |
|------|-------------|
| 完全无声音 | TTS 服务未启动；检查 `/proxy/tts/status` |
| `ModuleNotFoundError: voxcpm` | 换 Python 3.12 或 ComfyUI Python 启动 |
| `TTS 500` / CUDA 报错 | 并发合成导致 GPU 状态异常；**重启** `server_tts.py`（服务端已加生成锁） |
| 前几句有、后面没有 | 同上，刷新页面后重试 |
| 有声音但文字未出 | 硬刷新（Ctrl+F5）加载最新 `tts.js` |
| 文字切走了还在播 | 硬刷新；确认 `bootstrap.js` 在换页时调用 `tts.stop()` |
| 校园/都市模板无语音 | 设计如此，仅月下长安启用 TTS |
| 旁白不播 | 设计如此，仅 `「」` 内对白合成 |
| `502` / 上游不可达 | `TTS_BASE` 地址错误或 7860 未监听 |
| 8080 启动失败 | 端口被占用，改用 `PORT=8081` |

---

## 11. 相关文件

| 文件 | 说明 |
|------|------|
| `frontend/server_tts.py` | FastAPI + VoxCPM2 合成服务 |
| `frontend/js/tts.js` | 浏览器播放、预加载、翻页停播 |
| `frontend/js/mood.js` | MOOD / 对白解析 |
| `frontend/js/template-registry.js` | `ttsEnabled` 开关 |
| `server.js` | `/proxy/tts` 反向代理 |
| `docs/tts-plan.md` | 需求与 API 设计详案 |

---

## 12. 一键启动参考（Windows PowerShell）

保存为 `scripts/start-with-tts.ps1` 或手动执行：

```powershell
# 游戏服（新窗口）
Start-Process powershell -ArgumentList '-NoExit','-Command','cd D:\HermesWorkspace\girlgame-skill; $env:PORT=8081; npm run dev'

# TTS 服（新窗口）
$py = 'F:\ComfyUI_V6.0\ComfyUI-WorkFisher-V2\Python3.12.6\python.exe'
Start-Process powershell -ArgumentList "-NoExit","-Command","`$env:VOXCPM2_PATH='F:\ComfyUI_V6.0\ComfyUI-WorkFisher-V2\ComfyUI\models\VoxCPM2'; & '$py' D:\HermesWorkspace\girlgame-skill\frontend\server_tts.py"
```

浏览器打开：`http://127.0.0.1:8081/game.html?template=changan-moon`
