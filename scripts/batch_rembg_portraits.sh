#!/bin/bash
# ===== 批量立绘rembg去背景 =====
# 对 assets/portraits/{charId}/{expr}.png 中所有 RGB 文件执行 rembg
# 输出 RGBA 透明 PNG，覆盖原文件
# 用法: bash scripts/batch_rembg_portraits.sh
# 需要: ComfyUI 已启动 + rembg 管线就绪

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ASSETS_DIR="$SCRIPT_DIR/../frontend/assets/portraits"
COMFY_INPUT="F:\\ComfyUI_V6.0\\ComfyUI-WorkFisher-V2\\ComfyUI\\input"
COMFY_OUTPUT="F:\\ComfyUI_V6.0\\ComfyUI-WorkFisher-V2\\ComfyUI\\output"
PYTHON="/mnt/f/ComfyUI_V6.0/ComfyUI-WorkFisher-V2/Python3.12.6/python.exe"
LOGFILE="/tmp/rembg-batch-$(date +%Y%m%d-%H%M%S).log"

echo "=== Batch Rembg Processing ===" > "$LOGFILE"
echo "Started: $(date)" >> "$LOGFILE"

# 扫描所有非RGBA的PNG
for char_dir in "$ASSETS_DIR"/*/; do
    char_id=$(basename "$char_dir")
    for png in "$char_dir"/*.png; do
        [ -f "$png" ] || continue
        expr=$(basename "$png" .png)
        
        # 检查是否是RGBA (color_type=6)
        ct=$(python3 -c "
import struct
with open('$png','rb') as f:
    ct = f.read(32)[25]
print(ct)
")
        if [ "$ct" = "6" ]; then
            echo "⏭ $char_id/$expr (already RGBA)" >> "$LOGFILE"
            continue
        fi
        
        echo "🎨 $char_id/$expr (RGB -> RGBA)..." >> "$LOGFILE"
        
        # cp到ComfyUI input
        cp "$png" "/mnt/f/ComfyUI_V6.0/ComfyUI-WorkFisher-V2/ComfyUI/input/rembg_${char_id}_${expr}.png"
        
        # 调用ComfyUI rembg模板
        "$PYTHON" -X utf8 /home/daixiaowei/.hermes/profiles/july/skills/mlops/comfyui-local/templates/comfy_rembg.py \
            "rembg_${char_id}_${expr}.png" "rembg_${char_id}_${expr}" >> "$LOGFILE" 2>&1
        
        # 找输出文件
        found=$(ls "$COMFY_OUTPUT"/rembg_${char_id}_${expr}_*.png 2>/dev/null | head -1)
        if [ -n "$found" ]; then
            cp "$found" "$png"
            echo "✅ $char_id/$expr replaced with RGBA" >> "$LOGFILE"
        else
            echo "❌ $char_id/$expr rembg output not found" >> "$LOGFILE"
        fi
    done
done

echo "Finished: $(date)" >> "$LOGFILE"
echo "=== DONE ===" >> "$LOGFILE"
echo "=== Batch rembg complete ==="
echo "Check log: $LOGFILE"
