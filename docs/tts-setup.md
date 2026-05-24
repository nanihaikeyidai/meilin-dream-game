# TTS 语音服务配置指南

## 运行环境

| 项目 | 值 |
|------|-----|
| Python 运行路径 | `F:\ComfyUI_V6.0\ComfyUI-WorkFisher-V2\Python3.12.6\python.exe` |
| Python 环境对应 | ComfyUI WorkFisher-V2 自带环境（含 torch + CUDA + VoxCPM2） |
| 模型路径 | `F:\ComfyUI_V6.0\ComfyUI-WorkFisher-V2\ComfyUI\models\VoxCPM2` |
| 服务端口 | **7860** (FastAPI / Uvicorn) |
| 前端端口 | 5500 (可直接联调) |
| 操作系统 | Windows 10 / Windows Server |

## 启动方式

### 方式 A：直接启动（推荐）

```bash
# 进入前端目录
cd /mnt/d/HermesWorkspace/girlgame-skill/frontend

# 使用 ComfyUI Python 运行
"/mnt/f/ComfyUI_V6.0/ComfyUI-WorkFisher-V2/Python3.12.6/python.exe" -u server_tts.py
```

### 方式 B：使用启动脚本

```bash
# 一键启动（后台运行，日志写入 /tmp/tts_server.log）
bash /mnt/d/HermesWorkspace/girlgame-skill/frontend/start-tts.sh
```

### 启动日志说明

首次启动时，VoxCPM2 模型加载耗时约 **30-60 秒**（视 GPU 性能）。在此期间：

- 服务端口 7860 在 Uvicorn 启动后即可连接
- `/tts/status` 返回 `model_loaded: false` 表示模型仍在加载
- 日志会在模型就绪后打印 `[TTS] Model loaded. Voice refs: [...]`

### 指定端口

```bash
TTS_PORT=7860 python -u frontend/server_tts.py
```

## API 接口

### GET `/tts/status` — 健康检查

```bash
curl http://127.0.0.1:7860/tts/status
```

**响应示例：**
```json
{
  "status": "ok",
  "model_loaded": true,
  "uptime": 56.56,
  "clone_refs": {
    "xieyunlan": true,
    "huayingyue": true,
    "guqianfan": true,
    "shenmingyue": true,
    "lihuaijin": true,
    "gongsunlan": true
  }
}
```

**`clone_refs`** 字段表示各角色是否有参考音频文件（`.wav`），有参考音时音色更稳定。

### POST `/tts` — 生成语音

```bash
curl -X POST http://127.0.0.1:7860/tts \
  -H "Content-Type: application/json" \
  -d '{
    "charId": "xieyunlan",
    "text": "此事，与你无关。",
    "mood": "cold",
    "turnCount": 1,
    "pageIdx": 0
  }' \
  --output output.wav
```

**请求参数：**

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| charId | string | 是 | 角色 ID | `xieyunlan` |
| text | string | 是 | 台词文本 | `"此事，与你无关。"` |
| mood | string | 否 | 语气（默认 neutral） | `"cold"`, `"happy"` |
| turnCount | int | 否 | 对话轮次（用于缓存键） | `1` |
| pageIdx | int | 否 | 页码（用于缓存键） | `0` |

**支持的语气：** `neutral`, `warm`, `happy`, `sad`, `angry`, `cold`, `surprised`, `blush`
**中文别名也会自动映射：** 开心→happy, 生气→angry, 悲伤→sad, 冷漠→cold 等

**响应：** 直接返回 `audio/wav` 二进制音频流。

**缓存机制：** 相同 `charId + turnCount + pageIdx` 组合的请求自动缓存，第二次直接返回已生成的 WAV 文件。

## 音色配置

### 音色配置文件

`frontend/tts_voice_config.py` — 包含所有角色的音色描述和语气控制。

### 6 角色音色总览

| 角色 ID | 角色名 | 音色描述 |
|---------|--------|----------|
| `xieyunlan` | 谢云岚 | 冷峻青年男声，沉稳低沉 |
| `huayingyue` | 花映月 | 年轻女声，妩媚柔美 |
| `guqianfan` | 顾千帆 | 洒脱青年男声，明朗随性 |
| `shenmingyue` | 沈明月 | 英气女声，清越爽利 |
| `lihuaijin` | 李怀瑾 | 温雅青年男声，如玉温润 |
| `gongsunlan` | 公孙兰 | 沉稳中年女声，平和从容 |

### 语气控制

TTS 支持 **Clone（参考音）** 和 **Voice Design** 两种模式：

- **Clone 模式**（默认）：有参考音频时，语气用 `(语气XX)` 前缀控制，音色由参考音锁定
- **Voice Design 模式**（兜底）：无参考音频时，用完整音色描述 + 语气合成

每个角色 × 8 种语气 = **48 种组合**，在 `VOICE_DESCRIPTIONS` 字典中配置。

### 合成参数

| 模式 | 参数 | 值 | 说明 |
|------|------|:---:|------|
| Clone | cfg_value | 2.5 | 更贴参考音，波动更小 |
| Clone | inference_timesteps | 15 | 推理步数（越高越精细） |
| Voice Design | cfg_value | 2.0 | 设计模式 cfg |
| Voice Design | inference_timesteps | 10 | 设计模式步数 |

## 参考音频

参考音频文件存放在 `frontend/assets/voice_refs/` 目录下，格式为 WAV 16kHz mono：

```
frontend/assets/voice_refs/
├── xieyunlan.wav    — "此事，与你无关。"
├── huayingyue.wav   — "你来啦。"
├── guqianfan.wav    — "走，别处说话去。"
├── shenmingyue.wav  — "说重点。"
├── lihuaijin.wav    — "请坐吧。"
└── gongsunlan.wav   — "且慢。"
```

生成脚本：`scripts/generate_voice_refs.py`

## 前端联调

前端通过 `dev-server.sh`（端口 5500）提供服务：
```html
<!-- 前端自动检测后端端口 -->
const API_BASE = `http://${window.location.hostname}:7860`;
```

前端调用示例（JavaScript）：
```javascript
async function playTTS(charId, text, mood) {
  const resp = await fetch(`http://localhost:7860/tts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ charId, text, mood, turnCount: 0, pageIdx: 0 })
  });
  const blob = await resp.blob();
  const url = URL.createObjectURL(blob);
  const audio = new Audio(url);
  audio.play();
}
```

## 常见问题排查

### Q1：服务无法启动 / 端口被占用

```bash
# 检查端口占用
netstat -ano | findstr :7860

# 用 taskkill 结束占用进程
taskkill /PID <PID> /F
```

### Q2：模型加载失败

检查 ComfyUI Python 环境是否已安装 VoxCPM2：
```bash
F:\ComfyUI_V6.0\ComfyUI-WorkFisher-V2\Python3.12.6\python.exe -c "import voxcpm; print('OK')"
```

如未安装，需要安装 VoxCPM2（参考 ComfyUI 自定义节点文档）。

### Q3：语音生成超时或报错

常见原因及解决方法：

| 症状 | 可能原因 | 解决方案 |
|------|----------|----------|
| 返回 503 | 模型未加载完 | 稍等 30-60 秒后重试 |
| 返回 500，GPU OOM | 显存不足 | 检查 GPU 是否被其他进程占用，关闭 ComfyUI 等 |
| 音频空白/噪音 | 参考音频格式不对 | 确保参考音为 16kHz mono WAV |
| 语气不生效 | 语气别名不识别 | 使用标准英文语气名：neutral/warm/happy/sad/angry/cold/surprised/blush |

### Q4：启动后 curl 连接失败

```bash
# 确认服务进程存在
tasklist | findstr python

# 确认端口 LISTENING
netstat -ano | findstr :7860

# 确认 Windows 防火墙未拦截 7860 端口
# 临时禁用防火墙测试
```

### Q5：日志中无输出

Windows Python stdout 缓冲可能导致日志延迟：
- 确保 Python 使用 `-u` 参数（无缓冲）
- 或改用 `print("msg", flush=True)`
- 或重定向到日志文件查看

### Q6：WSL 调用 Windows Python 时 stdout 不可见

从 WSL 启动的 Windows Python 进程的 stdout 不会出现在 WSL 终端缓冲区中。
建议重定向到日志文件：
```bash
"/mnt/f/ComfyUI_V6.0/..." -u server_tts.py > /tmp/tts_server.log 2>&1
```

## 文件结构

```
girlgame-skill/frontend/
├── server_tts.py          # TTS 服务主程序（FastAPI）
├── tts_voice_config.py    # 音色配置（48种情绪组合）
├── start-tts.sh           # 启动脚本
├── assets/
│   ├── voice_refs/        # 参考音频（每角色一段）
│   └── voices/            # 生成的语音缓存
```

## 更新日志

| 日期 | 变更 |
|:----:|------|
| 2026-05-24 | 初始版本，路径映射到 HermesWorkspace |
