#!/bin/bash
# 验证背景图是否全部生成成功
BG_DIR="/mnt/d/Hermes/girlgame-skill/frontend/assets/backgrounds"
REQUIRED=("schoolyard" "photo_hall" "rooftop" "festival" "night_sky" "summer_farewell")

echo "=== 背景图完整性检查 ==="
ALL_OK=true
for ID in "${REQUIRED[@]}"; do
  FILE="$BG_DIR/${ID}.png"
  if [ -f "$FILE" ] && [ $(stat --format=%s "$FILE") -gt 100000 ]; then
    SIZE_MB=$(echo "scale=1; $(stat --format=%s "$FILE") / 1048576" | bc)
    echo "  ✅ $ID.png  ($SIZE_MB MB)"
  else
    echo "  ❌ $ID.png  缺失或文件过小"
    ALL_OK=false
  fi
done

echo ""
if [ "$ALL_OK" = true ]; then
  echo "✅ 全部 $(( ${#REQUIRED[@]} + 1 )) 张背景图就绪（含已有 classroom）"
else
  echo "⚠️ 部分背景图缺失，请检查"
fi
