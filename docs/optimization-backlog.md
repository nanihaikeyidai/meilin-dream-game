# 待优化计划（Backlog）

> 记录日期：2026-05-24  
> 背景：API 持久化、错误 Toast、剧本选择页直达（4 默认 + 自定义）等改动后的复盘清单。  
> 用途：后续迭代时按优先级勾选实现，避免重复讨论。

**相关文档**

- [ui-ux-optimization-plan.md](./ui-ux-optimization-plan.md) — 早期 UI/UX 专项（部分已落地）
- [prd.md](./prd.md) — 产品需求
- [README.md](../README.md) — 运行与目录说明（部分流程描述可能滞后于本清单）

---

## 建议落地顺序（若只做 3 件）

1. **返回选剧本** + **API 失败重试**（用户感知最强）
2. **统一 API 配置模块** + **Electron 流式路径**（减少隐蔽 bug）
3. **对齐 dev server health / 更新 README 与自测**（团队与 CI 少踩坑）

---

## 一、体验与流程（优先）

### P0-1 菜单「返回标题」语义过时

| 项 | 内容 |
|---|---|
| **现状** | `game.html` 菜单项「返回标题」调用 `backToTitle()`，仅回到**当前剧本**的开始界面（`startOverlay`），不会回到剧本选择页。 |
| **期望** | 改名为「返回选剧本」，跳转到 `templates.html`（Electron：`electronAPI.navigate.to('templates')`）。 |
| **涉及文件** | `frontend/js/bootstrap.js`（`backToTitle`）、`frontend/game.html`（菜单文案） |
| **状态** | [ ] 待做 |

---

### P0-2 API 失败缺少「一键重试」

| 项 | 内容 |
|---|---|
| **现状** | 流式 + 非流式均失败后显示错误 Toast（`showErrorToast`），并 `restoreDialogAfterApiError()`；用户需再次点选项或操作才能重新请求。 |
| **期望** | Toast 或对话框内提供「重试本轮」按钮，直接再次调用 `requestLLM()`（保留当前 `messages` 最后一条 user）。 |
| **涉及文件** | `frontend/js/bootstrap.js`（`fallbackLLM`、`requestLLM`）、`frontend/game.html`（Toast 样式，可选操作按钮） |
| **状态** | [ ] 待做 |

---

### P0-3 API 配置 UI 重复

| 项 | 内容 |
|---|---|
| **现状** | `templates.html` 内嵌 API 表单；`game.html` 另有 `#apiConfigOverlay` + 设置菜单「API 配置」。逻辑相似（load/save/test）但未复用。 |
| **期望** | 抽取 `frontend/js/api-setup.js`（或等价模块）：`loadForm`、`saveForm`、`showOverlay`、`testConnection`；两页共用。 |
| **涉及文件** | `frontend/templates.html`、`frontend/game.html`、`frontend/js/bootstrap.js`、`frontend/js/api-config.js` |
| **状态** | [ ] 待做 |

---

### P0-4 Electron 下流式未走原生通道

| 项 | 内容 |
|---|---|
| **现状** | `api.js` 非流式在 Electron 可走 `electronAPI.llm.chat`；`stream.js` 始终 `fetch('/proxy/chat/completions')`。 |
| **风险** | 桌面端代理异常时，可能出现「非流式可用、流式失败」或反之。 |
| **期望** | Electron 增加流式 IPC，或桌面端统一走一种路径并文档说明。 |
| **涉及文件** | `frontend/js/stream.js`、`frontend/js/api.js`、`electron/preload.js`、`electron/ipc-handlers.js` |
| **状态** | [ ] 待做 |

---

## 二、开发与运维

### P1-1 双 dev server 的 health 不一致

| 项 | 内容 |
|---|---|
| **现状** | 根目录 `server.js` 的 `/proxy/health` 含 `llmAuth`、`needsClientConfig`、`mockLlm`；`frontend/server.js` 的 health 较简单。 |
| **风险** | 仅用 `node frontend/server.js` 时，`AvgApiConfig.resolveLlmSetup()` 可能误判必须配客户端 API。 |
| **期望** | health 字段对齐，或 README 明确「请用 `npm run dev` / 主 server」。 |
| **涉及文件** | `server.js`、`frontend/server.js`、`frontend/js/api-config.js` |
| **状态** | [ ] 待做 |

---

### P1-2 模板元数据双份维护

| 项 | 内容 |
|---|---|
| **现状** | `frontend/js/template-registry.js` 与 `templates/*/story/main.md` 各有一份标题/简介；`/api/templates` 又从 markdown 解析。 |
| **风险** | 长期易漂移（展示名、标签与磁盘不一致）。 |
| **期望** | 以 registry 为展示唯一源；或 build 时从 `main.md` 生成 registry；自定义剧本以磁盘为准。 |
| **涉及文件** | `frontend/js/template-registry.js`、`server.js`（`listTemplatesApi`）、`templates/` |
| **状态** | [ ] 待做 |

---

### P1-3 README / 自测与真实流程不同步

| 项 | 内容 |
|---|---|
| **现状** | README 仍写 `index → templates → character`；未写「根路径直达选剧本」「4 默认 + 自定义」「API 在选剧本页配置」。 |
| **期望** | 更新 README 流程表；`.cursor/skills/avg-self-test` 步骤从 `templates.html` 或 `/` 进入。 |
| **涉及文件** | `README.md`、`.cursor/skills/avg-self-test/SKILL.md` |
| **状态** | [ ] 待做 |

---

## 三、功能增强（中等收益）

### P2-1 剧本卡片信息增强

| 项 | 内容 |
|---|---|
| **建议** | 卡片标注：是否支持 TTS（`ttsEnabled`）、是否有本地存档（`AvgSave.hasSave`）、可选副标题已部分有 `subtitle`。 |
| **涉及文件** | `frontend/templates.html`、`frontend/js/template-registry.js`、`frontend/js/save.js` |
| **状态** | [ ] 待做 |

---

### P2-2 自定义剧本入口增强

| 项 | 内容 |
|---|---|
| **现状** | 仅输入剧本 ID + 校验 `templates/{id}/story/main.md`。 |
| **建议** | 最近用过的自定义 ID（localStorage）；失败时列出可用目录（`/api/templates` 过滤 4 个默认）；链到「如何新建剧本包」说明。 |
| **涉及文件** | `frontend/templates.html`、`docs/`（新建简短 guide 可选） |
| **状态** | [ ] 待做 |

---

### P2-3 进入游戏前预加载剧本

| 项 | 内容 |
|---|---|
| **建议** | 在 `character.html` 确认角色后或选剧本时 `fetch` `story/main.md`，写入 `sessionStorage`，`game.html` 初始化减少等待。 |
| **涉及文件** | `frontend/character.html`、`frontend/js/bootstrap.js`（`loadStoryMarkdown`） |
| **状态** | [ ] 待做 |

---

### P2-4 创角页默认名与模板一致

| 项 | 内容 |
|---|---|
| **现状** | `character.html` 未使用 `template.defaultPlayerName` 预填；`game.html` 开始界面有默认值。 |
| **期望** | 从 `sessionStorage.selectedTemplate` 或 registry 读取并预填 `#charName`。 |
| **涉及文件** | `frontend/character.html`、`frontend/js/template-registry.js` |
| **状态** | [ ] 待做 |

---

## 四、健壮性与安全

### P2-5 浏览器模式 API Key 明文存储

| 项 | 内容 |
|---|---|
| **现状** | 浏览器 `localStorage` 按 origin（含端口）隔离，换 8080→8081 会丢配置；已改为 `server.js` 写入 `.girlgame/api-config.json` 并自动从 localStorage 迁移。 |
| **建议** | 浏览器仅开发用途并文档警示；或只持久化 baseUrl/model，Key 每会话输入；Electron 保持现状。 |
| **涉及文件** | `frontend/js/api-config.js`、`docs/optimization-backlog.md`（本文件）、README |
| **状态** | [ ] 待做 |

---

### P2-6 sessionStorage 生命周期短

| 项 | 内容 |
|---|---|
| **现状** | `selectedTemplate`、`character` 存 sessionStorage，新标签/清缓存即丢。 |
| **建议** | 关键字段同步 localStorage；或 URL `?template=` 兜底（快速试玩链接可扩展）。 |
| **涉及文件** | `frontend/templates.html`、`frontend/character.html`、`frontend/js/bootstrap.js` |
| **状态** | [ ] 待做 |

---

### P2-7 存档版本迁移

| 项 | 内容 |
|---|---|
| **现状** | `frontend/js/save.js` 固定 `version: 1`。 |
| **建议** | 预留 `migrateSave(data)`，改 `messages` / `engineState` 结构时可平滑升级。 |
| **涉及文件** | `frontend/js/save.js` |
| **状态** | [ ] 待做 |

---

## 五、代码质量（长期）

| ID | 项 | 说明 | 状态 |
|---|---|---|---|
| Q-1 | `escapeHtml` 重复 | `templates.html` 内联与 `engine.js` 等可统一到 `frontend/js/util.js` | [ ] |
| Q-2 | `bootstrap.js` 过大 | 800+ 行，可拆：API 配置 / 对话循环 / 菜单存档 | [ ] |
| Q-3 | 全屏 `errorOverlay` 角色不清 | API 失败已改 Toast；overlay 仅适合初始化失败，可简化文案与按钮 | [ ] |
| Q-4 | 未提交/未推送变更 | 剧本选择页、server 默认路由等改动应独立 commit，便于回滚 | [ ] |

---

## 六、已落地（供对照，勿重复做）

| 能力 | 说明 | 大致 commit/时间 |
|---|---|---|
| API 配置持久化 | `api-config.js`：Electron `config.json` / 浏览器 `localStorage` | 较早 |
| API 失败错误 Toast | 红色 Toast + 恢复上一轮对话，替代全屏 API 错误层 | `01ed008` 等 |
| 游戏内 API 重新配置 | 设置菜单「API 配置」、`openApiConfig()` | 已有 |
| 入口直达选剧本 | `/` → `templates.html`；4 默认 + 自定义卡片 | 2026-05-24 |
| 选剧本页 API 配置 | 未配置时弹层；右上角「⚙ API」 | 2026-05-24 |
| `FEATURED_TEMPLATE_IDS` | `template-registry.js` 固定 4 本默认剧本顺序 | 2026-05-24 |

---

## 变更记录

| 日期 | 说明 |
|---|---|
| 2026-05-24 | 初版：基于入口/API/Toast 改动后的复盘清单 |
| 2026-05-24 | TTS 目录重构为 `assets/tts/{templateId}/voice_refs|cache`，参考音约 50 字 bootstrap |
| 2026-05-24 | 四默认剧本全部 `ttsEnabled: true`，25 角色参考音就绪 |
