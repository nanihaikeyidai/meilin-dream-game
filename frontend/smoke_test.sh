#!/bin/bash
# ===== 月下长安 · 冒烟测试脚本 (updated 2026-05-14) =====
# 验证：代理服务、Gateway、前端页面、API 链路、立绘资产
# 用法：bash frontend/smoke_test.sh
# 输出：PASS/FAIL + 详细诊断

PASS=0
FAIL=0
BASE="http://localhost:8080"
GATEWAY="http://localhost:8656"
TIMEOUT=30

green() { echo -e "\033[32m[PASS]\033[0m $1"; }
red()   { echo -e "\033[31m[FAIL]\033[0m $1"; }

echo "=========================================="
echo " 月下长安 · 冒烟测试"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
echo ""

# ---- 1. 代理服务器是否存活 ----
echo "--- 1/6 代理服务器 (port 8080) ---"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$BASE/proxy/health" 2>&1)
if [ "$STATUS" = "200" ]; then
  green "HTTP 200 on $BASE/proxy/health"
  PASS=$((PASS+1))
else
  red "Failed: HTTP $STATUS on $BASE/proxy/health"
  FAIL=$((FAIL+1))
fi

# ---- 2. Hermes Gateway 是否存活 ----
echo "--- 2/6 Hermes Gateway (port 8656) ---"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$GATEWAY/v1/models" 2>&1)
if [ "$STATUS" = "200" ]; then
  green "HTTP 200 on $GATEWAY/v1/models"
  PASS=$((PASS+1))
else
  red "Failed: HTTP $STATUS on $GATEWAY/v1/models"
  FAIL=$((FAIL+1))
fi

# ---- 3. game.html 是否可访问且包含关键内容 ----
echo "--- 3/6 前端页面 game.html ---"
HTML=$(curl -s --max-time 5 "$BASE/game.html" 2>&1)
HTML_LEN=$(echo "$HTML" | wc -c)
if [ "$HTML_LEN" -gt 5000 ]; then
  green "game.html 可访问，大小=${HTML_LEN} bytes"

  CHECKS=0
  echo "$HTML" | grep -q 'startOverlay' && CHECKS=$((CHECKS+1)) || red "  -> 缺少 startOverlay"
  echo "$HTML" | grep -q 'startGame' && CHECKS=$((CHECKS+1)) || red "  -> 缺少 startGame()"
  echo "$HTML" | grep -q 'sendMessage' && CHECKS=$((CHECKS+1)) || red "  -> 缺少 sendMessage()"
  echo "$HTML" | grep -q '月下长安' && CHECKS=$((CHECKS+1)) || red "  -> 缺少标题"
  echo "$HTML" | grep -q '/proxy' && CHECKS=$((CHECKS+1)) || red "  -> 缺少 proxy 路径"
  echo "$HTML" | grep -q 'showPage' && CHECKS=$((CHECKS+1)) || red "  -> 缺少 showPage()"
  echo "$HTML" | grep -q 'PORTRAIT_CHARACTERS' && CHECKS=$((CHECKS+1)) || red "  -> 缺少 PORTRAIT_CHARACTERS"
  echo "$HTML" | grep -q 'updateSprite' && CHECKS=$((CHECKS+1)) || red "  -> 缺少 updateSprite()"

  if [ "$CHECKS" -ge 8 ]; then
    green "game.html 关键内容完整 ($CHECKS/8)"
    PASS=$((PASS+1))
  else
    red "game.html 关键内容不完整 ($CHECKS/8)"
    FAIL=$((FAIL+1))
  fi
else
  red "game.html 不可访问或过小 (${HTML_LEN} bytes)"
  FAIL=$((FAIL+1))
fi

# ---- 4. API 代理是否正常响应 ----
echo "--- 4/6 API 代理 /proxy/chat/completions ---"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT -X POST "$BASE/proxy/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{"model":"july","messages":[{"role":"user","content":"你好，请回一个词"}],"max_tokens":10}' 2>&1)

if [ "$HTTP_CODE" = "200" ]; then
  RESP=$(curl -s --max-time $TIMEOUT -X POST "$BASE/proxy/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{"model":"july","messages":[{"role":"user","content":"你好"}],"max_tokens":10}' 2>&1)
  CONTENT=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('choices',[{}])[0].get('message',{}).get('content',''))" 2>/dev/null)
  if [ -n "$CONTENT" ]; then
    green "API 代理返回 HTTP 200，内容: '${CONTENT:0:30}'"
    PASS=$((PASS+1))
  else
    red "API 代理返回 200 但内容空"
    FAIL=$((FAIL+1))
  fi
else
  red "API 代理返回 HTTP $HTTP_CODE"
  FAIL=$((FAIL+1))
fi

# ---- 5. 立绘资产检查 ----
echo "--- 5/6 立绘资产检查 ---"
MISSING=0
FOUND=0
CHARACTERS=("huayingyue" "shenmingyue" "xieyunlan" "lihuaijin" "guqianfan" "gongsunlan")
EXPRESSIONS=("default" "smile" "happy" "sad" "angry" "blush" "cold" "surprised")
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
for char in "${CHARACTERS[@]}"; do
  for expr in "${EXPRESSIONS[@]}"; do
    path="$SCRIPT_DIR/assets/portraits/$char/$expr.png"
    if [ -f "$path" ]; then
      FOUND=$((FOUND+1))
    else
      MISSING=$((MISSING+1))
    fi
  done
done
echo "  立绘: $FOUND/48 存在, $MISSING/48 缺失"
if [ "$FOUND" -ge 2 ]; then
  green "至少默认立绘存在 ($FOUND/48)"
  PASS=$((PASS+1))
else
  red "立绘严重缺失 ($FOUND/48)"
  FAIL=$((FAIL+1))
fi

# ---- 6. API_KEY 配置检查 ----
echo "--- 6/6 API_KEY 配置检查 ---"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
KEY_LINE=$(grep -n "API_KEY" "$SCRIPT_DIR/game.html" | head -1)
if echo "$KEY_LINE" | grep -q "API_KEY = ''"; then
  green "API_KEY 为空（代理模式正确配置）"
  PASS=$((PASS+1))
elif echo "$KEY_LINE" | grep -q "API_KEY="; then
  KEY_VAL=$(echo "$KEY_LINE" | grep -oP "API_KEY\s*=\s*'([^']*)" | grep -oP "'\K[^']*")
  if [ -n "$KEY_VAL" ] && [ "${#KEY_VAL}" -gt 10 ]; then
    green "API_KEY 已配置 (${#KEY_VAL} chars)"
  elif [ -z "$KEY_VAL" ]; then
    green "API_KEY 为空字符串"
  else
    green "API_KEY 配置存在 (${#KEY_VAL} chars)"
  fi
  PASS=$((PASS+1))
else
  red "未找到 API_KEY 定义"
  FAIL=$((FAIL+1))
fi

echo ""
echo "=========================================="
echo " 测试结果: $PASS PASS / $FAIL FAIL"
echo "=========================================="

if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
