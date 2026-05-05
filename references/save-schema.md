# Galgame Save File JSON Schema

本文档定义了存档文件的 JSON 结构。
AI 在读写 `.galgame/` 下的文件时应遵循此格式。

## 通用说明

- 所有 JSON 文件使用 UTF-8 编码
- 不包含注释（JSON 标准不支持）
- 缺失字段以 `null` 填充
- 数值范围：好感度 0~100，flags 布尔值

---

## session.json（会话缓存）

```json
{
  "meta": {
    "game_version": "1.0",
    "template": "模板ID",
    "template_name": "模板显示名",
    "started_at": "ISO 8601 时间戳",
    "last_updated": "ISO 8601 时间戳",
    "total_decisions": 0,
    "total_minutes_played": 0
  },
  "protagonist": {
    "name": "主角名",
    "gender": "男/女/其他",
    "personality": "一句话性格描述",
    "traits": {
      "extroversion": 5,
      "emotionality": 5,
      "stubbornness": 5,
      "attentiveness": 5,
      "humor": 5
    },
    "background": "背景描述",
    "hidden_past": "不对NPC公开的设定（可选）"
  },
  "npcs": {
    "角色ID": {
      "name": "显示名",
      "affection": 0,
      "route_unlocked": false,
      "met": false,
      "last_interaction": "最后互动场景ID",
      "notes": "AI记录的角色状态备注"
    }
  },
  "state": {
    "current_scene": "当前场景ID",
    "current_act": 1,
    "total_acts": 3,
    "current_route": null,
    "unlocked_routes": [],
    "scene_progress": [],
    "decision_count": 0
  },
  "flags": {},
  "stats": {},
  "recent_history": [],
  "events_summary": []
}
```

### Recent History 格式

```json
{
  "scene": "场景ID",
  "act": 1,
  "choice_index": 0,
  "choice_text": "用户选择的选项文本，或自定义输入的内容",
  "type": "preset | custom",
  "effects": {
    "affection_changes": { "角色ID": 5, "角色ID2": -3 },
    "flags_set": ["flag名"],
    "route_change": null
  },
  "narration_summary": "一句话描述发生了什么"
}
```

- `type: "preset"` — 用户选了预设选项（1/2/3）
- `type: "custom"` — 用户自由输入（choice_index 为 0）
- `choice_index`: 预设选项为编号 1~3，自定义选项为 0
- `choice_text`: type=preset 时是选项文本，type=custom 时是用户的原始输入

限制：最多保留 10 条。超过时移除最早的。

### Events Summary 格式

字符串数组，每幕最多 3 条核心事件摘要：

```json
[
  "在教室遇到了林雪",
  "在老榕树下谈了未来的事",
  "在天台上发现了林雪藏的旧物盒"
]
```

限制：最多 15 条。超过时移除最早的，但保留每幕最后 1 条。

---

## save_N.json（持久化存档）

与 session.json 结构相同，增加以下字段：

```json
{
  "meta": {
    "...": "...",

    "save_slot": 0,
    "save_name": "用户自定义存档名（可选）",
    "save_timestamp": "ISO 8601",
    "save_type": "auto / manual / milestone"
  },
  "game_state_at_save": {
    "scene_description": "存档时的场景描述（用于读档时恢复氛围）",
    "upcoming_context": "即将发生的事件提示（用于AI恢复时衔接）"
  },
  "history": [],
  "perspectives": {
    "protagonist": { "witnessed": [], "heard": [], "said": [], "secrets": [] },
    "linxue": { "witnessed": [], "heard": [], "said": [], "secrets": [] },
    "suyunxi": { "witnessed": [], "heard": [], "said": [], "secrets": [] }
  }
}
```

### History 完整历史

与 `recent_history` 格式相同，但不做截断。
仅 save 文件中保留完整历史，session 中只保留 recent 10 条。

---

## State Card（上下文内工作记忆）

State Card 不是文件，是 AI 在每轮响应末尾附带的文本摘要。
其数据来源于 session.json 的实时状态。

### 标准格式

```
[GALGAME STATE]
Scene: act1_courtyard | Route: nil | Act: 1/3
❤ Linxue: 28  |  Yunxi: 10
🏁 met_linxue ✓
Recent: ① "问她想看教室" ② "走向老榕树"
Progress: 5/25
```

### 缩写规则

- 场景名使用模板中定义的 ID（如 `act1_courtyard`）
- 角色名使用简称（如 `linxue` → `Linxue`，首字母大写）
- 好感度只显示 ≥ 10 的角色
- 选择文本截断至 15 字
- Progress 显示 "已做/预计总决策数"

### 特殊状态指示

| 状态 | State Card 显示 |
|------|----------------|
| 路线未锁定 | `Route: nil` |
| 路线已锁定 | `Route: linxue` |
| 好感度 ≥ 80 | `❤ Linxue: 82 ★`（加星号） |
| 好感度 ≤ 10 | 不显示在该角色栏 |
| flag 未触发 | 不在 🏁 行显示 |
| 游戏结束 | `[GAME OVER]` 替换 `[GALGAME STATE]` |

---

## 文件操作示例

### AI 读取 session

```bash
cat .galgame/session.json
```

### AI 写入 session（每次选择后）

```bash
cat > .galgame/session.json << 'EOF'
{ 完整 JSON 内容 }
EOF
```

### AI 检查是否有存档

```bash
ls .galgame/save_*.json 2>/dev/null && echo "有存档" || echo "无存档"
```

### AI 保存到槽位

```bash
cp .galgame/session.json .galgame/save_2.json
# 然后修改 save_2.json 增加 save 专用字段
```

---

## 兼容性规则

1. 新增字段：AI 应在读取时做 `??` fallback（`data.newField ?? defaultValue`）
2. 废弃字段：保留在文件中以避免解析错误，但不再读取
3. 版本升级：检查 `meta.game_version`，不匹配时尝试兼容读取
