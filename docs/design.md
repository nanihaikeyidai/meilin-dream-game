# 梅林绮梦录 — AVG 游戏设计文档

> 最后更新: 2026-05-20

## 项目信息

- **路径:** `girlgame-skill/`
- **前端入口:** `frontend/game.html`（浏览器） / Electron `index → templates → character → game`
- **开发服务器:** `npm run dev` → `server.js`（静态资源 + LLM/TTS 代理 + 剧本 markdown）
- **立绘目录:** `frontend/assets/portraits/`
- **技术栈:** HTML5 + 模块化 Vanilla JS + Electron（可选）

## 架构（2026-05 重构后）

```
frontend/js/
  template-registry.js   # 各剧本：立绘映射、场景表、开场设定
  engine.js              # 立绘回退链、场景、[EXPR]、分页
  api.js                 # LLM：Electron 直连 / 浏览器 /proxy
  tts.js                 # TTS：/proxy/tts
  save.js                # localStorage 存档
  bootstrap.js           # 游戏主循环
```

**模板加载：** `templates/{id}/story/main.md` 作为 system prompt 的故事设定（Electron `fs:read` / 浏览器 `/templates/...`）。

## 立绘系统

**加载优先级链（已实现）：**

```
SVG(表情) → PNG(表情) → SVG(default) → PNG(default) → 隐藏
```

**古风模板（changan-moon）** 6 角色 × 8 表情；校园等模板立绘映射已登记，资源就绪后自动显示。

## 标签规范

| 标签 | 用途 |
|------|------|
| `[SCENE: id]` | 切换背景，ID 见 `template-registry.js` |
| `[EXPR: smile]` | 强制表情（优先于关键词） |
| `[MOOD: warm]` | TTS 语气（月下长安） |

## 已知问题 / TODO

- [x] ~~initGame 双重调用~~（已修复）
- [x] ~~updateSprite 硬编码~~（已改为模板驱动）
- [x] Electron 选模板与 game.html 断连（已打通 sessionStorage + 动态剧本）
- [ ] 校园/都市/悬疑模板立绘资产补全
- [ ] Electron 打包与发布流程
- [ ] 与 `engine/save-manager.mjs`（Node 存档）统一格式
