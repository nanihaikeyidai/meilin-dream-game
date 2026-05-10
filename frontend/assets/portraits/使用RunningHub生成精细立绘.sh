#!/bin/bash
# ============================================================
# 「月下长安」立绘批量生成脚本 — RunningHub v2 API
# ============================================================
# 使用方式:
#   1. 先设置你的 API Key:
#      export RH_API_KEY="你的32位hex密钥"
#   2. 运行本脚本:
#      bash "使用RunningHub生成精细立绘.sh"
# ============================================================

API_KEY="${RH_API_KEY:-}"
WORKFLOW_ID="2052651394800336898"
BASE_URL="https://www.runninghub.cn/openapi/v2"
OUTPUT_DIR="$(dirname "$0")"

if [ -z "$API_KEY" ]; then
  echo "❌ 请先设置 RH_API_KEY 环境变量"
  echo "   export RH_API_KEY=\"你的API密钥\""
  exit 1
fi

# 角色列表: ID, 名称, 正向提示词
declare -A PROMPTS

PROMPTS["xieyunlan_default"]="anime style, traditional Chinese ancient style (古风), ink wash painting aesthetic, elegant, flowing fabric, high quality, beautiful detailed eyes, soft lighting, intricate costume details, historical Chinese setting, 1boy, male, ancient Chinese official attire (古风), black official robe with silver patterns, jade hair crown, long black hair tied up, phoenix eyes, cold handsome face, standing straight, hand on sword hilt, sword with old copper coin on tassel, imposing presence, half body, solo"
PROMPTS["xieyunlan_smile"]="1boy, male, ancient Chinese official, black robe, jade crown, rare gentle smile, eyes softening slightly, elegant and restrained, standing, subtle warmth in expression, half body, warm light, ink wash style, solo"
PROMPTS["xieyunlan_happy"]="1boy, male, ancient Chinese official, black robe, genuine bright smile, eyes curved, rare moment of joy, relaxed shoulders, half body, golden warm light, traditional Chinese style, solo"
PROMPTS["xieyunlan_angry"]="1boy, male, ancient Chinese official, black robe, cold anger, sharp eyes, furrowed brows, tense jaw, hand gripping sword hilt tightly, intimidating presence, half body, cool harsh light, solo"
PROMPTS["xieyunlan_sad"]="1boy, male, ancient Chinese official, black robe, sad expression, downcast eyes, lips pressed thin, lonely and restrained grief, standing in shadow, half body, dim blue lighting, melancholic atmosphere, solo"
PROMPTS["xieyunlan_surprised"]="1boy, male, ancient Chinese official, black robe, eyes wide in surprise, caught off guard, mask slipping, mouth slightly open, shocked expression, half body, solo"
PROMPTS["xieyunlan_blush"]="1boy, male, ancient Chinese official, black robe, slight blush on cheeks, looking away awkwardly, flustered expression, turning head slightly, subtle embarrassment, half body, warm pink tone, solo"
PROMPTS["xieyunlan_cold"]="1boy, male, ancient Chinese official, black robe, completely cold expression, emotionless eyes, ice-cold gaze, unapproachable aura, standing with straight back, half body, cool blue light, solo"

PROMPTS["huayingyue_default"]="1girl, female, ancient Chinese courtesan (古风云鬟), flowing red silk dress (绯红), gold hairpin in loose bun, round silk fan holding, peach blossom eyes, beauty mole near eye, elegant seductive smile, standing gracefully, half body, traditional Chinese aesthetic, ink wash, high quality, solo"
PROMPTS["huayingyue_smile"]="1girl, female, ancient Chinese courtesan, red silk dress, gold hairpin, warm genuine smile, eyes soft, holding fan, relaxed and warm, half body, warm lighting, solo"
PROMPTS["huayingyue_happy"]="1girl, female, ancient Chinese courtesan, red silk dress, gold hairpin, bright laughing eyes, head tilted, genuinely joyful expression, rare happiness, half body, golden light, solo"
PROMPTS["huayingyue_angry"]="1girl, female, ancient Chinese courtesan, red silk dress, cold smile, eyes sharp, dangerous expression, fan closed in hand, beauty with thorns, half body, cool dramatic light, solo"
PROMPTS["huayingyue_sad"]="1girl, female, ancient Chinese courtesan, red silk dress, sad eyes, faint forced smile, looking away, lonely and vulnerable behind beautiful facade, half body, dim light, blue tone, solo"
PROMPTS["huayingyue_surprised"]="1girl, female, ancient Chinese courtesan, red silk dress, eyes wide in surprise, fan lowered, caught off guard, genuine shock, beauty in surprise, half body, solo"
PROMPTS["huayingyue_blush"]="1girl, female, ancient Chinese courtesan, red silk dress, genuine blush, shy expression, hiding half face behind fan, eyes visible, flustered but trying to compose herself, half body, warm pink tone, solo"
PROMPTS["huayingyue_cold"]="1girl, female, ancient Chinese courtesan, red silk dress, cold expressionless face, distant eyes, professional smile gone, unreadable, ice beauty, half body, cool light, solo"

PROMPTS["guqianfan_default"]="1boy, male, ancient Chinese warrior (古风侠客), dark green martial outfit (墨绿劲装), half tied messy hair, dark headband, sharp eyes, lean fit build, short blade at waist, standing in shadows, cautious watchful expression, half body, traditional Chinese wuxia style, ink wash, high quality, solo"
PROMPTS["guqianfan_smile"]="1boy, male, ancient Chinese warrior, dark outfit, rare small smile, eyes slightly softer, trustworthy expression, subtle warmth, hands relaxed, half body, warm golden light, solo"
PROMPTS["guqianfan_happy"]="1boy, male, ancient Chinese warrior, dark outfit, genuine happy smile, rare carefree moment, eyes bright, relaxed posture, half body, warm sunlight, solo"
PROMPTS["guqianfan_angry"]="1boy, male, ancient Chinese warrior, dark outfit, cold furious glare, sharp dangerous eyes, hand reaching for blade, predatory stance, ready to strike, half body, harsh light, solo"
PROMPTS["guqianfan_sad"]="1boy, male, ancient Chinese warrior, dark outfit, sad silent expression, looking down, hidden pain in eyes, clenched fist at side, lonely and burdened, half body, dim light, solo"
PROMPTS["guqianfan_surprised"]="1boy, male, ancient Chinese warrior, dark outfit, eyes wide with shock, momentary loss of composure, alert and tense, surprised expression, half body, solo"
PROMPTS["guqianfan_blush"]="1boy, male, ancient Chinese warrior, dark outfit, slight blush on tanned skin, awkwardly looking away, uncomfortable with tenderness, flustered expression, half body, warm pink tone, solo"
PROMPTS["guqianfan_cold"]="1boy, male, ancient Chinese warrior, dark outfit, completely unreadable expression, dead eyes, emotionless mask, still as a statue, cold killer gaze, half body, cool blue light, solo"

PROMPTS["shenmingyue_default"]="1girl, female, ancient Chinese noble lady (古风闺秀), moon-white dress (月白襦裙), white jade hairpin, elegant coiled hair bun, gentle eyes, soft refined expression, standing gracefully, hands clasped, half body, traditional Chinese ancient style, ink wash aesthetic, delicate, high quality, solo"
PROMPTS["shenmingyue_smile"]="1girl, female, ancient Chinese lady, moon-white dress, jade hairpin, gentle warm smile, eyes soft, genuine kindness, elegant and warm, half body, soft warm light, solo"
PROMPTS["shenmingyue_happy"]="1girl, female, ancient Chinese lady, moon-white dress, jade hairpin, bright joyful smile, eyes shining, rare happiness, head tilted slightly, genuine laugh, half body, golden light, solo"
PROMPTS["shenmingyue_angry"]="1girl, female, ancient Chinese lady, moon-white dress, offended expression, furrowed brows, tight lips, hurt and upset, trying to maintain composure, half body, cool light, solo"
PROMPTS["shenmingyue_sad"]="1girl, female, ancient Chinese lady, moon-white dress, jade hairpin, tears welling in eyes, sad expression, looking down, lonely heart, fragile and vulnerable, half body, dim blue light, solo"
PROMPTS["shenmingyue_surprised"]="1girl, female, ancient Chinese lady, moon-white dress, eyes wide in surprise, hand touching chest, caught off guard, delicate shock, half body, solo"
PROMPTS["shenmingyue_blush"]="1girl, female, ancient Chinese lady, moon-white dress, blushing, shy eyes, looking down, fingers fidgeting with sleeve, heart fluttering, demure but moved, half body, warm pink tone, solo"
PROMPTS["shenmingyue_cold"]="1girl, female, ancient Chinese lady, moon-white dress, cold distant expression, emotionless eyes, closed off, elegant and unreachable, half body, cool blue light, solo"

PROMPTS["lihuaijin_default"]="1boy, male, ancient Chinese scholar (古风文士), bamboo-green robe (青衫), jade hairpin in scholar bun, gentle scholarly face, holding a book scroll, standing in bookstore, refined elegant posture, half body, traditional Chinese ancient style, ink wash painting aesthetic, high quality, solo"
PROMPTS["lihuaijin_smile"]="1boy, male, ancient Chinese scholar, green robe, warm gentle smile, eyes soft, kind expression, warm scholarly aura, holding book, half body, warm light, solo"
PROMPTS["lihuaijin_happy"]="1boy, male, ancient Chinese scholar, green robe, rare bright smile, eyes curved, genuine joy, carefree moment, half body, sunny golden light, solo"
PROMPTS["lihuaijin_angry"]="1boy, male, ancient Chinese scholar, green robe, stern cold expression, disappointed eyes, furrowed brows, calm but intimidating anger, half body, cool harsh light, solo"
PROMPTS["lihuaijin_sad"]="1boy, male, ancient Chinese scholar, green robe, sad distant eyes, looking into distance, melancholic expression, old grief, book in hand but not reading, half body, dim light, solo"
PROMPTS["lihuaijin_surprised"]="1boy, male, ancient Chinese scholar, green robe, eyes wide in shock, book slipping from hand, pale face, utterly surprised, half body, solo"
PROMPTS["lihuaijin_blush"]="1boy, male, ancient Chinese scholar, green robe, slight blush, avoiding eye contact, flustered, clearing throat, trying to regain composure, half body, warm pink tone, solo"
PROMPTS["lihuaijin_cold"]="1boy, male, ancient Chinese scholar, green robe, cold emotionless eyes, distant smile that doesn't reach eyes, unreadable, closed off, half body, cool grey light, solo"

PROMPTS["gongsunlan_default"]="1girl, female, mature ancient Chinese female doctor (古风女医), plain white robe (素白衣裙), silver hairpin in simple bun, calm gentle expression, herb medicine bag at waist, standing in apothecary, warm mature aura, half body, traditional Chinese ancient style, ink wash aesthetic, high quality, solo"
PROMPTS["gongsunlan_smile"]="1girl, female, mature ancient Chinese doctor, white robe, gentle motherly smile, eyes warm, kind face, relaxed, holding herbs, half body, warm light, solo"
PROMPTS["gongsunlan_happy"]="1girl, female, mature ancient Chinese doctor, white robe, genuine bright smile, eyes curved, rare joyful expression, warm happiness, half body, golden light, solo"
PROMPTS["gongsunlan_angry"]="1girl, female, mature ancient Chinese doctor, white robe, stern expression, disappointed eyes, firm and serious, doctor's authority, half body, cool clinical light, solo"
PROMPTS["gongsunlan_sad"]="1girl, female, mature ancient Chinese doctor, white robe, sad distant eyes, looking into distance holding letter, melancholic, waiting for someone who never came, half body, dim blue light, solo"
PROMPTS["gongsunlan_surprised"]="1girl, female, mature ancient Chinese doctor, white robe, eyes wide in surprise, hand covering mouth, unexpected news, half body, solo"
PROMPTS["gongsunlan_blush"]="1girl, female, mature ancient Chinese doctor, white robe, slight mature blush, shy eyes, looking down with soft smile, flustered in a composed way, half body, warm pink tone, solo"
PROMPTS["gongsunlan_cold"]="1girl, female, mature ancient Chinese doctor, white robe, professional detachment, calm emotionless eyes, clinical distance, unreadable, half body, cool light, solo"

CHARACTERS=("xieyunlan" "huayingyue" "guqianfan" "shenmingyue" "lihuaijin" "gongsunlan")
EXPRESSIONS=("default" "smile" "happy" "angry" "sad" "surprised" "blush" "cold")

TOTAL=$(( ${#CHARACTERS[@]} * ${#EXPRESSIONS[@]} ))
COUNT=0
SUCCESS=0
FAIL=0

echo "=========================================="
echo "  「月下长安」立绘批量生成"
echo "  角色: ${#CHARACTERS[@]}  ×  表情: ${#EXPRESSIONS[@]}  =  ${TOTAL} 张"
echo "=========================================="
echo ""

for char_id in "${CHARACTERS[@]}"; do
  for expr in "${EXPRESSIONS[@]}"; do
    key="${char_id}_${expr}"
    prompt="${PROMPTS[$key]}"
    
    COUNT=$((COUNT + 1))
    echo "[${COUNT}/${TOTAL}] ${char_id}/${expr}.png"
    
    # Submit task
    RESPONSE=$(curl -s --location --request POST "${BASE_URL}/run/workflow/${WORKFLOW_ID}" \
      --header "Content-Type: application/json" \
      --header "Authorization: Bearer ${API_KEY}" \
      --data-raw "{
        \"addMetadata\": true,
        \"nodeInfoList\": [
          {\"nodeId\": \"6\", \"fieldName\": \"text\", \"fieldValue\": \"${prompt}\"},
          {\"nodeId\": \"7\", \"fieldName\": \"text\", \"fieldValue\": \"nsfw, low quality, bad anatomy, extra fingers, mutated hands, ugly, blurry, watermark, text, logo, realistic, 3d, photorealistic, modern clothes, modern setting, mecha, sci-fi, western fantasy, multiple characters\"}
        ],
        \"instanceType\": \"default\",
        \"usePersonalQueue\": \"false\"
      }")
    
    TASK_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('taskId',''))" 2>/dev/null)
    
    if [ -z "$TASK_ID" ]; then
      echo "  ❌ 提交失败: $(echo $RESPONSE | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('errorMessage',d))" 2>/dev/null)"
      FAIL=$((FAIL + 1))
      continue
    fi
    
    echo "  ✅ 任务ID: $TASK_ID (等待中...)"
    
    # Poll for result
    RESULT_URL=""
    for i in $(seq 1 30); do
      sleep 8
      RESULT=$(curl -s --location --request POST "${BASE_URL}/query" \
        --header "Content-Type: application/json" \
        --header "Authorization: Bearer ${API_KEY}" \
        --data-raw "{\"taskId\":\"$TASK_ID\"}")
      
      STATUS=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null)
      
      if [ "$STATUS" = "SUCCESS" ]; then
        RESULT_URL=$(echo "$RESULT" | python3 -c "
import sys,json
data = json.load(sys.stdin)
for r in data.get('results', []):
    if r.get('url'):
        print(r['url'])
        break
" 2>/dev/null)
        break
      elif [ "$STATUS" = "FAILED" ]; then
        echo "  ❌ 生成失败"
        FAIL=$((FAIL + 1))
        break
      fi
      echo "  ⏳ ${STATUS:-waiting}..."
    done
    
    if [ -n "$RESULT_URL" ]; then
      OUTDIR="$OUTPUT_DIR/$char_id"
      mkdir -p "$OUTDIR"
      curl -s -o "$OUTDIR/$expr.png" "$RESULT_URL"
      # Remove the SVG placeholder
      rm -f "$OUTDIR/$expr.svg"
      echo "  ✅ 已保存: $OUTDIR/$expr.png"
      SUCCESS=$((SUCCESS + 1))
    fi
    
    # Rate limit: wait between characters
    sleep 5
    echo ""
  done
done

echo "=========================================="
echo "  完成! 成功: $SUCCESS / 失败: $FAIL"
echo "=========================================="
