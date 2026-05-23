---
name: avg-self-test
description: >-
  自测 girlgame-skill AVG 游戏：启动服务、预检资产、浏览器进入游戏、点击交互、截图并按 PRD/UI 规范分析立绘层级与布局。
  触发词：自测、冒烟测试、游戏测试、截图验收、avg test、playwright 测试游戏、检查立绘布局。
---

# AVG 游戏自测

对 `girlgame-skill` 做**可重复**的端到端自测：预检 → 进游戏 → 交互 → 截图 → 对照规范出报告。

## 前置

| 服务 | 命令 | 必须 |
|------|------|------|
| 开发服 | `npm run dev` → `:8080` | ✅ |
| LLM | Hermes `:8656` 或设 `LLM_BASE` | 全流程必须 |
| TTS | `python frontend/server_tts.py` | 仅古风语音 |

## 工作流

复制进度清单：

```
- [ ] 1. 预检 scripts/avg-preflight.mjs
- [ ] 2. 确认/启动 npm run dev
- [ ] 3. 浏览器 MCP 打开游戏并截图
- [ ] 4. 交互：开始 → 对话 → 选项
- [ ] 5. 对照 checklist.md 写报告
```

### 1. 预检（必做）

```bash
node scripts/avg-preflight.mjs
# LLM 未开但只测布局：
node scripts/avg-preflight.mjs --allow-llm-fail
```

失败项必须在报告 **Blockers** 中说明；LLM 502 时走「布局注入自测」（见 [checklist.md](checklist.md)）。

### 2. 浏览器进游戏（cursor-ide-browser MCP）

**必须**先读 MCP 工具 schema，再操作。

推荐 URL（1280×720 或默认视口）：

```
http://localhost:8080/game.html?template=campus-summer
http://localhost:8080/game.html?template=changan-moon
```

**流程 A — 完整（需 LLM）：**

1. `browser_navigate` → 上述 URL
2. `browser_snapshot` → 确认 `#startOverlay` 或 `#gameScreen`
3. 若在开始屏：填 `#playerName`，点「开始故事 →」（`browser_click` ref）
4. 等待 `#textBody` 出现「正在落笔」或叙事文字（`browser_wait` + 多次 snapshot，勿用全页 blind sleep）
5. `browser_take_screenshot` → `01-ingame-dialog.png`
6. 点击 `#clickArea` 或「▼ 点击继续」翻页 1–2 次，再截图
7. 出现选项时截图 `03-choices.png`；数选项 ≤3
8. 点第一个 `.choice-btn`，等待新回复，再截图

**流程 B — 仅布局（LLM 502）：**

1. `browser_navigate` → `game.html?template=campus-summer`
2. `browser_snapshot` → 在控制台执行 checklist 中的**立绘注入脚本**（或通过 `browser_press_key` F12 不可行则用 evaluate 若可用）
3. 若无 evaluate：指导用户在控制台粘贴脚本后 `browser_take_screenshot`

### 3. 截图分析（必做）

对每张截图逐项判定（Pass / Fail / N/A）：

| 检查项 | 规范 |
|--------|------|
| 立绘位置 | **右侧**，非居中 |
| 层级 | 背景 < 立绘 < 对话框 |
| 立绘大小 | 半身清晰，不顶出屏幕，不太小 |
| 对话框 | 底部，文字可读 |
| 选项 | ≤3，在文本框上方，不挡正文 |
| Loading | 对话阶段无全屏「故事正在展开」 |
| 502 错误 | 不应出现（LLM 正常时） |

详细条目见 [checklist.md](checklist.md)。

### 4. 报告模板

```markdown
# AVG 自测报告 — {日期} — {模板 id}

## 环境
- BASE: http://localhost:8080
- LLM: {ok/fail} | TTS: {ok/skip}

## 预检
{粘贴 avg-preflight 输出摘要}

## 截图
| 文件 | 说明 |
|------|------|
| 01-... | ... |

## 验收结果
| 项 | 结果 | 说明 |
|----|------|------|
| 立绘右侧 | Pass/Fail | ... |
| 层级 z-index | Pass/Fail | ... |
| 选项≤3 | Pass/Fail/N/A | ... |
| 流式/省略号等待 | Pass/Fail/N/A | ... |

## Blockers
- ...

## 建议
- ...
```

## 快捷命令

```bash
npm run dev
node scripts/avg-preflight.mjs
npm run test:preflight
```

## 禁止

- 不要只 curl 页面就宣称「自测通过」——必须**截图 + 视觉分析**
- 不要在未启动 LLM 时判定「交互/流式/选项」为 Pass（标 N/A 或 Fail）
- 不要用 `HermesWorkspace` 父目录做 CodeGraph 索引（仅 `girlgame-skill`）

## 参考

- 产品规范：`docs/prd.md`
- UI 规范：`docs/ui-ux-optimization-plan.md`
- 冒烟脚本：`frontend/smoke_test.sh`（CI/无浏览器）
