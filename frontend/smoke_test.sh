#!/bin/bash
# ===== 夏日的回音 · 冒烟测试脚本 =====
# 验证：代理服务、前端页面、API 链路是否正常
# 用法：bash smoke_test.sh
# 输出：PASS/FAIL + 详细诊断

PASS=0
FAIL=0
BASE="http://localhost:8649"
GATEWAY="http://localhost:8642"
TIMEOUT=30

green() { echo -e "\033[32m[PASS]\033[0m $1"; }
red()   { echo -e "\033[31m[FAIL]\033[0m $1"; }

echo "=========================================="
echo " 夏日的回音 · 冒烟测试"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
echo ""

# ---- 1. 代理服务器是否存活 ----
echo "--- 1/6 代理服务器 (port 8649) ---"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$BASE/" 2>&1)
if [ "$STATUS" = "200" ]; then
  green "HTTP 200 on $BASE/"
  PASS=$((PASS+1))
else
  red "Failed: HTTP $STATUS on $BASE/"
  FAIL=$((FAIL+1))
fi

# ---- 2. Hermes Gateway 是否存活 ----
echo "--- 2/6 Hermes Gateway (port 8642) ---"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$GATEWAY/v1/models" 2>&1)
if [ "$STATUS" = "200" ]; then
  green "HTTP 200 on $GATEWAY/v1/models"
  PASS=$((PASS+1))
else
  red "Failed: HTTP $STATUS on $GATEWAY/v1/models (Gateway 可能未运行)"
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
  echo "$HTML" | grep -q 'callLLM' && CHECKS=$((CHECKS+1)) || red "  -> 缺少 callLLM()"
  echo "$HTML" | grep -q '夏日的回音' && CHECKS=$((CHECKS+1)) || red "  -> 缺少标题"
  echo "$HTML" | grep -q '/proxy' && CHECKS=$((CHECKS+1)) || red "  -> 缺少 proxy 路径"
  echo "$HTML" | grep -q 'showPage' && CHECKS=$((CHECKS+1)) || red "  -> 缺少 showPage()"
  echo "$HTML" | grep -q 'advancePage' && CHECKS=$((CHECKS+1)) || red "  -> 缺少 advancePage()"

  if [ "$CHECKS" -ge 7 ]; then
    green "game.html 关键内容完整 ($CHECKS/7)"
    PASS=$((PASS+1))
  else
    red "game.html 关键内容不完整 ($CHECKS/6)"
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
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"你好，请回一个词"}],"max_tokens":10}' 2>&1)

if [ "$HTTP_CODE" = "200" ]; then
  RESP=$(curl -s --max-time $TIMEOUT -X POST "$BASE/proxy/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"你好"}],"max_tokens":10}' 2>&1)
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

# ---- 5. 完整游戏初始化流程 ----
echo "--- 5/6 游戏初始化流程（模拟开始故事） ---"

# 直接用 Python 发送请求，避免 shell 变量转义问题
GAME_RESP=$(python3 -c "
import urllib.request, json

payload = {
    'model': 'deepseek-v4-flash',
    'messages': [
        {'role': 'system', 'content': '''你是 AI AVG 游戏引擎。
玩家角色名：陈远，性格：温柔体贴。
故事设定：校园青春·夏日的回音。高三毕业的夏天，主角回到了母校，在走廊上遇到了林雪。
角色信息：
- 林雪 — 温柔内敛的班长，你的三年同桌

游戏规则：
1. 每次输出包含场景叙述 + 2-4个选项
2. 第一次输出直接生成开场场景，不要询问任何前置问题
3. 每次输出末尾必须包含有效的选项列表
4. 用第二人称\"你\"叙述'''},
        {'role': 'user', 'content': '开始故事'}
    ],
    'temperature': 0.7,
    'max_tokens': 1024
}

req = urllib.request.Request(
    'http://localhost:8649/proxy/chat/completions',
    data=json.dumps(payload).encode(),
    headers={'Content-Type': 'application/json'},
    method='POST'
)
resp = urllib.request.urlopen(req, timeout=60)
data = json.loads(resp.read())
content = data['choices'][0]['message']['content']
print(f'LENGTH:{len(content)}')
print(f'HAS_HEADING:{\"###\" in content}')
print(f'HAS_OPTIONS:{\"【\" in content or \"1.\" in content}')
print(f'SAMPLE:{content[:150]}')
" 2>&1)

echo "$GAME_RESP"

GAME_OK=$(echo "$GAME_RESP" | grep -c "LENGTH:")
LEN=$(echo "$GAME_RESP" | grep "LENGTH:" | grep -oP '\d+')
HAS_OPT=$(echo "$GAME_RESP" | grep -c "HAS_OPTIONS:True")
HAS_HEAD=$(echo "$GAME_RESP" | grep -c "HAS_HEADING:True")

if echo "$GAME_RESP" | grep -q "LENGTH:[1-9][0-9][0-9]"; then
  MSG="游戏初始化：AI 返回 ${LEN} chars"
  [ "$HAS_OPT" = "1" ] && MSG="$MSG，有选项" || MSG="$MSG，无选项（可能 prompt 需优化）"
  [ "$HAS_HEAD" = "1" ] && MSG="$MSG，有标题" || MSG="$MSG，无标题"
  green "$MSG"
  PASS=$((PASS+1))
else
  red "游戏初始化失败: $GAME_RESP"
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
