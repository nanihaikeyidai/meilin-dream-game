# AVG 自测验收清单

## 层级（PRD §二）

| 层 | z-index | 验收 |
|----|---------|------|
| 背景 `#bgImage` | 0 | 全屏 cover，场景可切换 |
| 立绘 `#spriteImage` | 2 | **右侧**半身，在背景上 |
| 点击区 `.click-area` | 3 | 可翻页 |
| 对话框 `.text-layer` | 5 | 底部，盖住立绘下半 |
| 选项 `.choices-in-window` | 6 | 文本框上方，≤3 项 |
| 菜单 `#menuBtn` | 15 | 左上角可见 |

## 立绘（P0）

- [ ] PNG 显示（非 SVG 圆形占位）
- [ ] 位置：**屏幕右侧**，`object-position: bottom right`
- [ ] 高度：`max-height` 约 48–74vh，**不超出视口**
- [ ] 宽度：约 38–44vw，**不太小**（半身可辨）
- [ ] 底部留出对话框空间，立绘不被裁到屏幕外
- [ ] 旁白页可保留上一张立绘
- [ ] 新角色从右侧滑入（`slide-in-right`）

## 交互（P0）

- [ ] 开始画面 → 填名/性格 → 进入 `#gameScreen`
- [ ] LLM 可用时：对话框「正在落笔...」，**无全屏**「故事正在展开」遮罩
- [ ] 流式文字出现在 `#textBody`
- [ ] 点击继续翻页；最后一页出现选项
- [ ] 选项 **最多 3 条**，位于文本框上方，不遮挡正文
- [ ] 选选项后推进剧情（无 502）

## 模板资源

| 模板 | query | 立绘 charId 示例 |
|------|-------|------------------|
| 古风 | `changan-moon` | shenmingyue, xieyunlan |
| 校园 | `campus-summer` | linxue, suyunxi |

## LLM 不可用时的布局自测

在 `game.html` 已打开且 `#gameScreen` 可见时，浏览器控制台：

```javascript
document.getElementById('startOverlay').style.display = 'none';
document.getElementById('gameScreen').style.display = 'block';
const img = document.getElementById('spriteImage');
img.src = 'assets/portraits/linxue/smile.png';
img.classList.add('visible', 'slide-in-right');
document.getElementById('textName').textContent = '林雪 · 温和';
document.getElementById('textName').classList.add('visible');
document.getElementById('textBody').innerHTML = '<p>自测：立绘应在右侧，对话框在底部。</p>';
```

截图后检查右侧立绘与底部对话框层级。

## TTS（可选，changan-moon）

- [ ] `GET /proxy/tts/status` 200
- [ ] 含「」台词页播放语音，`#ttsIndicator` 激活

## 截图命名建议

保存到 `docs/self-test-screenshots/YYYY-MM-DD/`：

- `01-start.png` — 开始画面
- `02-ingame-dialog.png` — 对话中（含立绘）
- `03-choices.png` — 三选项
- `04-portrait-inject.png` — LLM 不可用时的注入自测
