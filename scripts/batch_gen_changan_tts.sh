#!/bin/bash
# 月下长安 TTS 批量预生成 — edge-tts
# 用法: bash scripts/batch_gen_changan_tts.sh
# 输出: frontend/assets/tts/changan-moon/cache/*.mp3
# 
# edge-tts v7: --rate 用百分比 (如 -10%), --pitch 用 Hz (如 -10Hz)

SCRIPT_DIR="$(cd "$(dirname "$0")/../frontend" && pwd)"
TTS_DIR="$SCRIPT_DIR/assets/tts/changan-moon/cache"
mkdir -p "$TTS_DIR"

echo "=== 月下长安 TTS 批量预生成 ==="
echo "输出目录: $TTS_DIR"
echo ""

COUNT=0

# 1️⃣ 谢云岚 (xieyunlan) — 冷峻沉稳
echo "[1/18] 谢云岚 neutral..."
edge-tts --voice zh-CN-YunxiNeural --rate="-10%" --pitch="-10Hz" \
  --text "上元灯夜长安城中灯火万千，我奉命查访旧案路过朱雀大街，见你神色不对。" \
  --write-media "$TTS_DIR/xieyunlan_neutral_01.mp3" && ((COUNT++))

echo "[2/18] 谢云岚 cold..."
edge-tts --voice zh-CN-YunxiNeural --rate="-15%" --pitch="-20Hz" \
  --text "此事与你无关，不必再问。再纠缠下去，我只能请你到玄天司走一趟了。" \
  --write-media "$TTS_DIR/xieyunlan_cold_01.mp3" && ((COUNT++))

echo "[3/18] 谢云岚 warm..."
edge-tts --voice zh-CN-YunxiNeural --rate="-10%" --pitch="-5Hz" \
  --text "罢了，你既执意要查，便跟紧我。长安城的水，比你想的要深。" \
  --write-media "$TTS_DIR/xieyunlan_warm_01.mp3" && ((COUNT++))

# 2️⃣ 花映月 (huayingyue) — 妩媚柔美
echo "[4/18] 花映月 happy..."
edge-tts --voice zh-CN-XiaoxiaoNeural --rate="+10%" --pitch="+30Hz" \
  --text "夜深露重，公子怎的还在街上徘徊？快进屋歇歇，仔细着凉。" \
  --write-media "$TTS_DIR/huayingyue_happy_01.mp3" && ((COUNT++))

echo "[5/18] 花映月 warm..."
edge-tts --voice zh-CN-XiaoxiaoNeural --rate="+5%" --pitch="+20Hz" \
  --text "灯市里的人潮喧闹，我却只盼你能多留片刻。" \
  --write-media "$TTS_DIR/huayingyue_warm_01.mp3" && ((COUNT++))

echo "[6/18] 花映月 sad..."
edge-tts --voice zh-CN-XiaoxiaoNeural --rate="-5%" --pitch="+5Hz" \
  --text "我这一生，从没有人问过我愿不愿意。你……是第一个。" \
  --write-media "$TTS_DIR/huayingyue_sad_01.mp3" && ((COUNT++))

# 3️⃣ 沈明月 (shenmingyue) — 清冷爽利
echo "[7/18] 沈明月 neutral..."
edge-tts --voice zh-CN-XiaoyiNeural --rate="-5%" --pitch="0Hz" \
  --text "你手这样凉，可是穿得太少？我这个手炉给你。" \
  --write-media "$TTS_DIR/shenmingyue_neutral_01.mp3" && ((COUNT++))

echo "[8/18] 沈明月 cold..."
edge-tts --voice zh-CN-XiaoyiNeural --rate="-10%" --pitch="-10Hz" \
  --text "案卷上的线索我已记下，说重点，莫要绕圈子。" \
  --write-media "$TTS_DIR/shenmingyue_cold_01.mp3" && ((COUNT++))

echo "[9/18] 沈明月 warm..."
edge-tts --voice zh-CN-XiaoyiNeural --rate="-5%" --pitch="+10Hz" \
  --text "既然信我，就把你的伤给我看看。医者仁心，不会害你。" \
  --write-media "$TTS_DIR/shenmingyue_warm_01.mp3" && ((COUNT++))

# 4️⃣ 李怀瑾 (lihuaijin) — 温润如玉
echo "[10/18] 李怀瑾 neutral..."
edge-tts --voice zh-CN-YunyangNeural --rate="0%" --pitch="+10Hz" \
  --text "不妨事，慢慢来。无论多久，我都等你把话说完。" \
  --write-media "$TTS_DIR/lihuaijin_neutral_01.mp3" && ((COUNT++))

echo "[11/18] 李怀瑾 warm..."
edge-tts --voice zh-CN-YunyangNeural --rate="0%" --pitch="+15Hz" \
  --text "朝堂风云虽险，你我只管把真相查清，不负本心。" \
  --write-media "$TTS_DIR/lihuaijin_warm_01.mp3" && ((COUNT++))

echo "[12/18] 李怀瑾 sad..."
edge-tts --voice zh-CN-YunyangNeural --rate="-10%" --pitch="-5Hz" \
  --text "有些事，知道了反而痛苦。但我……还是想告诉你。" \
  --write-media "$TTS_DIR/lihuaijin_sad_01.mp3" && ((COUNT++))

# 5️⃣ 顾千帆 (guqianfan) — 磁性低沉
echo "[13/18] 顾千帆 cold..."
edge-tts --voice zh-CN-YunjianNeural --rate="-15%" --pitch="-20Hz" \
  --text "别急，慢慢说，我听着呢。天塌下来也有我顶着。" \
  --write-media "$TTS_DIR/guqianfan_cold_01.mp3" && ((COUNT++))

echo "[14/18] 顾千帆 neutral..."
edge-tts --voice zh-CN-YunjianNeural --rate="-15%" --pitch="-15Hz" \
  --text "你且把今夜所见一五一十讲来，莫要遗漏半分。" \
  --write-media "$TTS_DIR/guqianfan_neutral_01.mp3" && ((COUNT++))

echo "[15/18] 顾千帆 warm..."
edge-tts --voice zh-CN-YunjianNeural --rate="-15%" --pitch="-5Hz" \
  --text "这么多年了……你是第一个让我想停下来的人。" \
  --write-media "$TTS_DIR/guqianfan_warm_01.mp3" && ((COUNT++))

# 6️⃣ 公孙兰 (gongsunlan) — 慵懒淡雅
echo "[16/18] 公孙兰 warm..."
edge-tts --voice zh-CN-XiaoxiaoNeural --rate="-5%" --pitch="-10Hz" \
  --text "孩子，这些年你受苦了。回来了就好，回来了就好。" \
  --write-media "$TTS_DIR/gongsunlan_warm_01.mp3" && ((COUNT++))

echo "[17/18] 公孙兰 neutral..."
edge-tts --voice zh-CN-XiaoxiaoNeural --rate="-5%" --pitch="-15Hz" \
  --text "当年的事我一直没敢告诉你，今日既已至此，便不再隐瞒。" \
  --write-media "$TTS_DIR/gongsunlan_neutral_01.mp3" && ((COUNT++))

echo "[18/18] 公孙兰 sad..."
edge-tts --voice zh-CN-XiaoxiaoNeural --rate="-15%" --pitch="-25Hz" \
  --text "那丫头若还在，也该有你这么大了……罢了，不提了。" \
  --write-media "$TTS_DIR/gongsunlan_sad_01.mp3" && ((COUNT++))

echo ""
echo "=== 月下长安 TTS 批量预生成完成 ==="
echo "成功生成: $COUNT / 18 条"
echo "输出目录: $TTS_DIR"
ls -lh "$TTS_DIR"/*.mp3 2>/dev/null
