# 背景标识速查表

在场景脚本中使用 `{ type: 'bg', bg: 'bg_id' }` 切换背景。

## 可用背景

| ID | 描述 | CSS 色值 |
|-----|------|----------|
| `classroom` | 教室 · 白天 | 暖米色渐变 |
| `classroom_evening` | 教室 · 黄昏 | 深蓝紫色渐变 |
| `classroom_memory` | 教室 · 回忆色 | 米白暖调 |
| `hallway` | 走廊 | 亚麻色渐变 |
| `courtyard` | 中庭/操场 | 绿色渐变 |
| `rooftop` | 天台 · 白天 | 天蓝色渐变 |
| `rooftop_sunset` | 天台 · 夕阳 | 橙红金渐变 |
| `rooftop_night` | 天台 · 夜晚 | 深紫星空渐变 |
| `sakura` | 樱花/街区 | 粉色调渐变 |
| `gate` | 校门口 | 深蓝紫色渐变 |
| `white` | 纯白 | #ffffff |

## 扩展背景

在 `game/main.js` 的 `setBackground` 方法中添加新的背景：

```javascript
'sunset_beach': 'linear-gradient(135deg, #ff6b35, #f7931e, #ffd700)',
'snowy_street': 'linear-gradient(135deg, #e8f0f8, #d0dce8, #b8c8d8)',
'rainy_window': 'linear-gradient(135deg, #4a5568, #2d3748, #1a202c)',
```

## 自定义图片背景

如需使用图片而非 CSS 渐变：
```javascript
setBackground(bgId) {
  if (bgId in this.IMAGE_BACKGROUNDS) {
    bgLayer.style.backgroundImage = `url(${this.IMAGE_BACKGROUNDS[bgId]})`;
  } else if (bgId in this.COLOR_BACKGROUNDS) {
    bgLayer.style.background = this.COLOR_BACKGROUNDS[bgId];
  }
}
```
