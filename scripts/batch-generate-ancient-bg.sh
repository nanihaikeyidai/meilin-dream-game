#!/bin/bash
# 批量生成「月下长安」古风场景背景图
set -euo pipefail

RH_API_KEY="${RH_API_KEY:-82bcf24442a84508a5b1d24f494bbb84}"
WORKFLOW_ID="2052651394800336898"
BG_DIR="/mnt/d/Hermes/girlgame-skill/frontend/assets/backgrounds/ancient"
mkdir -p "$BG_DIR"

# 场景配置: 场景ID | 场景名 | 提示词
SCENES=(
  "lantern_night|上元灯夜|ancient Chinese street at lantern festival night, thousands of colorful lanterns, bustling crowd, traditional architecture, warm golden light, full moon in sky, anime style background, no characters, detailed festive atmosphere"
  "government_hall|玄天司官署|ancient Chinese government hall, solemn and majestic, dark wood pillars, official seals, scrolls on desk, incense burner, scholarly atmosphere, anime style background, no characters, traditional Chinese architecture interior"
  "music_pavilion|不夜天乐坊|ancient Chinese music pavilion at night, silk curtains, lanterns, stage with musical instruments, wine tables, warm candlelight, traditional entertainment house, anime style background, no characters, elegant atmosphere"
  "changan_street|长安街市|ancient Chang'an street during daytime, traditional Chinese shops, stone pavement, horse carriages, bustling marketplace, blue sky, anime style background, no characters, Tang dynasty architecture"
  "bookstore|书肆雅阁|ancient Chinese bookstore interior, wooden shelves filled with scrolls and books, scholar's desk with brush and ink stone, quiet atmosphere, warm light through window, anime style background, no characters"
  "courtyard|庭院残荷|ancient Chinese courtyard garden, withered lotus pond in autumn, stone path, traditional pavilion, melancholic atmosphere, fallen leaves, misty, anime style background, no characters, poetic"
  "clinic|医馆药香|ancient Chinese medical clinic, wooden cabinets with herb drawers, mortar and pestle, hanging dried herbs, warm sunlight, traditional interior, anime style background, no characters"
  "city_wall|长安城楼|ancient Chinese city wall and gate tower, overlooking the city, sunset or twilight, traditional battlements, wide view of rooftops, anime style background, no characters, epic scenery"
  "moonlit_city|月下长安|night view of ancient Chang'an city, full moon, traditional rooftops, lanterns lit across the city, river reflecting moonlight, peaceful and romantic, anime style background, no characters"
  "lantern_river|灯河送别|river at night with floating lanterns, willow trees on bank, traditional bridge, gentle water reflections, stars in sky, farewell atmosphere, anime style background, no characters, bittersweet beauty"
)

echo "🚀 开始批量生成「月下长安」古风场景背景图"
echo "目标目录: $BG_DIR"
echo "共 ${#SCENES[@]} 个场景"
echo ""

FAILED=()
SUCCESS=0

for i in "${!SCENES[@]}"; do
  IFS='|' read -r SCENE_ID SCENE_NAME PROMPT <<< "${SCENES[$i]}"

  # 跳过已存在的
  if [ -f "$BG_DIR/${SCENE_ID}.png" ]; then
    SIZE=$(stat --format=%s "$BG_DIR/${SCENE_ID}.png" 2>/dev/null || echo "0")
    if [ "$SIZE" -gt 100000 ]; then
      echo "  ⏭️ [$((i+1))/${#SCENES[@]}] $SCENE_NAME ($SCENE_ID) 已存在，跳过"
      continue
    fi
  fi

  echo ""
  echo "========================================"
  echo "🎨 [$((i+1))/${#SCENES[@]}] 生成: $SCENE_NAME ($SCENE_ID)"
  echo "========================================"

  # 1. 提交
  echo "  提交任务..."
  RESPONSE=$(curl -s --max-time 20 --location --request POST "https://www.runninghub.cn/openapi/v2/run/workflow/$WORKFLOW_ID" \
    --header "Content-Type: application/json" \
    --header "Authorization: Bearer $RH_API_KEY" \
    --data-raw "{
      \"addMetadata\": true,
      \"nodeInfoList\": [
        {\"nodeId\": \"24\", \"fieldName\": \"text\", \"fieldValue\": \"$PROMPT\"}
      ],
      \"instanceType\": \"default\",
      \"usePersonalQueue\": \"false\"
    }")

  TASK_ID=$(echo "$RESPONSE" | python3 -c "import sys,json;print(json.load(sys.stdin).get('taskId',''))" 2>/dev/null || echo "")
  if [ -z "$TASK_ID" ]; then
    echo "  ❌ 提交失败: $RESPONSE"
    FAILED+=("$SCENE_ID")
    continue
  fi
  echo "  任务ID: $TASK_ID"

  # 2. 轮询
  echo "  等待生成..."
  DONE=false
  for poll_i in $(seq 1 30); do
    sleep 10
    RESULT=$(curl -s --max-time 15 --location --request POST "https://www.runninghub.cn/openapi/v2/query" \
      --header "Content-Type: application/json" \
      --header "Authorization: Bearer $RH_API_KEY" \
      --data-raw "{\"taskId\":\"$TASK_ID\"}")
    STATUS=$(echo "$RESULT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('status',''))" 2>/dev/null)

    if [ "$STATUS" = "SUCCESS" ]; then
      echo "  ✅ 生成成功 ($((poll_i*10))s)"
      NODE27_URL=$(echo "$RESULT" | python3 -c "
import sys,json
data = json.load(sys.stdin)
for r in data.get('results', []):
    if r.get('nodeId') == '27':
        print(r['url'])
" 2>/dev/null)
      if [ -n "$NODE27_URL" ]; then
        curl -s -o "$BG_DIR/${SCENE_ID}.png" "$NODE27_URL"
        SIZE=$(stat --format=%s "$BG_DIR/${SCENE_ID}.png" 2>/dev/null || echo "0")
        echo "  📥 下载完成: $BG_DIR/${SCENE_ID}.png ($((SIZE/1024/1024))MB)"
      else
        # fallback: 取第一个结果
        FIRST_URL=$(echo "$RESULT" | python3 -c "
import sys,json
data = json.load(sys.stdin)
results = data.get('results', [])
if results: print(results[0]['url'])" 2>/dev/null)
        if [ -n "$FIRST_URL" ]; then
          curl -s -o "$BG_DIR/${SCENE_ID}.png" "$FIRST_URL"
          echo "  📥 下载完成: $BG_DIR/${SCENE_ID}.png"
        fi
      fi
      SUCCESS=$((SUCCESS+1))
      DONE=true
      break
    elif [ "$STATUS" = "FAILED" ]; then
      ERR=$(echo "$RESULT" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('errorMessage','unknown'))" 2>/dev/null)
      echo "  ❌ 生成失败: $ERR"
      FAILED+=("$SCENE_ID")
      DONE=true
      break
    fi
  done

  if [ "$DONE" = false ]; then
    echo "  ⏰ 超时"
    FAILED+=("$SCENE_ID")
  fi

  # 冷却
  sleep 5
done

echo ""
echo "========== 报告 =========="
echo "总场景: ${#SCENES[@]}"
echo "成功: $SUCCESS"
if [ ${#FAILED[@]} -gt 0 ]; then
  echo "失败: ${#FAILED[@]} (${FAILED[*]})"
fi
echo ""
echo "背景图目录 ($BG_DIR):"
ls -lh "$BG_DIR"/*.png 2>/dev/null || echo "  (无文件)"
echo ""
if [ "$SUCCESS" -eq "${#SCENES[@]}" ]; then
  echo "🎉 全部生成成功！"
else
  echo "⚠️ 部分失败，需要重试"
fi
