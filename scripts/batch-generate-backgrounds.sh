#!/bin/bash
# 批量生成 AVG 游戏场景背景图
# 通过 RunningHub 短剧工作流逐个生成并下载到 assets/backgrounds/
#
# 用法: bash batch-generate-backgrounds.sh
# 需要环境变量: RH_API_KEY

set -euo pipefail

RH_API_KEY="${RH_API_KEY:-82bcf24442a84508a5b1d24f494bbb84}"
WORKFLOW_ID="2052651394800336898"
BG_DIR="/mnt/d/Hermes/girlgame-skill/frontend/assets/backgrounds"
mkdir -p "$BG_DIR"

# 场景配置: 场景ID | 活动名 | 提示词
SCENES=(
  "schoolyard|校园大扫除|school campus outdoor cleaning day, students cleaning, summer afternoon, empty schoolyard, trees, sports field, anime style background, no characters, bright daylight, detailed scenery"
  "photo_hall|旧照片展|indoor school exhibition hall, photos pinned on boards, warm lighting, wooden floor, afternoon sunlight through windows, anime style background, no characters, nostalgic atmosphere"
  "rooftop|天台夏夜会|school rooftop at summer night, stars in sky, city lights in distance, gentle breeze, moonlight, anime style background, no characters, romantic night atmosphere, blue purple sky"
  "festival|社团文化祭|school cultural festival, booths and stalls, lanterns, evening, colorful decorations, anime style background, no characters, festival atmosphere, warm lights"
  "night_sky|星空下的坦白|starry night sky, school rooftop or field, milky way visible, quiet peaceful night, deep blue sky with stars, anime style background, no characters"
  "summer_farewell|夏日祭告别|summer festival night, fireworks in sky, riverbank, lanterns floating, warm golden lights, anime style background, no characters, bittersweet farewell atmosphere"
)

generate_scene() {
  local SCENE_ID="$1"
  local SCENE_NAME="$2"
  local PROMPT="$3"

  echo ""
  echo "========================================"
  echo "🎨 [$((i+1))/${#SCENES[@]}] 生成: $SCENE_NAME ($SCENE_ID)"
  echo "========================================"

  # 1. 提交任务
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
    return 1
  fi
  echo "  任务ID: $TASK_ID"

  # 2. 轮询结果
  echo "  等待生成..."
  for poll_i in $(seq 1 30); do
    sleep 10
    RESULT=$(curl -s --max-time 15 --location --request POST "https://www.runninghub.cn/openapi/v2/query" \
      --header "Content-Type: application/json" \
      --header "Authorization: Bearer $RH_API_KEY" \
      --data-raw "{\"taskId\":\"$TASK_ID\"}")

    STATUS=$(echo "$RESULT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('status',''))" 2>/dev/null)

    if [ "$STATUS" = "SUCCESS" ]; then
      echo "  ✅ 生成成功 ($((poll_i*10))s)"

      # 提取 Node 27 (标准版) URL
      NODE27_URL=$(echo "$RESULT" | python3 -c "
import sys,json
data = json.load(sys.stdin)
for r in data.get('results', []):
    if r.get('nodeId') == '27':
        print(r['url'])
" 2>/dev/null)

      if [ -n "$NODE27_URL" ]; then
        curl -s -o "$BG_DIR/${SCENE_ID}.png" "$NODE27_URL"
        local SIZE=$(stat --format=%s "$BG_DIR/${SCENE_ID}.png" 2>/dev/null || echo "0")
        echo "  📥 下载完成: $BG_DIR/${SCENE_ID}.png ($((SIZE/1024/1024))MB)"
      else
        echo "  ⚠️ 未找到 Node 27 输出，尝试第一个结果"
        FIRST_URL=$(echo "$RESULT" | python3 -c "
import sys,json
data = json.load(sys.stdin)
results = data.get('results', [])
if results:
    print(results[0]['url'])
" 2>/dev/null)
        if [ -n "$FIRST_URL" ]; then
          curl -s -o "$BG_DIR/${SCENE_ID}.png" "$FIRST_URL"
          echo "  📥 下载完成: $BG_DIR/${SCENE_ID}.png"
        fi
      fi
      return 0
    elif [ "$STATUS" = "FAILED" ]; then
      local ERR=$(echo "$RESULT" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('errorMessage','unknown'))" 2>/dev/null)
      echo "  ❌ 生成失败: $ERR"
      return 1
    fi
  done

  echo "  ⏰ 超时"
  return 1
}

# 批量生成
echo "🚀 开始批量生成场景背景图"
echo "目标目录: $BG_DIR"
echo "共 ${#SCENES[@]} 个场景"
echo ""

FAILED=()
for i in "${!SCENES[@]}"; do
  IFS='|' read -r SCENE_ID SCENE_NAME PROMPT <<< "${SCENES[$i]}"

  # 检查是否已经存在
  if [ -f "$BG_DIR/${SCENE_ID}.png" ]; then
    local SIZE=$(stat --format=%s "$BG_DIR/${SCENE_ID}.png" 2>/dev/null || echo "0")
    if [ "$SIZE" -gt 100000 ]; then
      echo "  ⏭️  $SCENE_ID.png 已存在，跳过"
      continue
    fi
  fi

  if generate_scene "$SCENE_ID" "$SCENE_NAME" "$PROMPT"; then
    echo "  ✅ $SCENE_NAME 完成"
  else
    echo "  ❌ $SCENE_NAME 失败"
    FAILED+=("$SCENE_ID")
  fi

  # 冷却 5 秒，避免限速
  sleep 5
done

echo ""
echo "========== 报告 =========="
echo "总场景: ${#SCENES[@]}"
echo "成功: $(( ${#SCENES[@]} - ${#FAILED[@]} ))"
if [ ${#FAILED[@]} -gt 0 ]; then
  echo "失败: ${#FAILED[@]} (${FAILED[*]})"
fi
echo "背景图目录:"
ls -lh "$BG_DIR"/*.png 2>/dev/null || echo "  (无文件)"
echo "✅ 完成"
