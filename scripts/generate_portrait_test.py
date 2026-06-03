"""
zImage 人物立绘生成 - 先验证一张
使用 ComfyUI zImage 漫剧工作流生成古风角色半身立绘
"""
import urllib.request, json, time, shutil, os, sys
import glob

COMFY_UI = "http://192.168.144.1:8188"
# Windows Python 用 Windows 路径
OUTPUT_DIR = "F:/ComfyUI_V6.0/ComfyUI-WorkFisher-V2/ComfyUI/output"
GAME_PORTRAIT_DIR = "D:/HermesWorkspace/girlgame-skill/frontend/assets/portraits/changan-moon"

def queue_prompt(prompt_workflow):
    body = json.dumps({"prompt": prompt_workflow}).encode()
    req = urllib.request.Request(f"{COMFY_UI}/api/prompt", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read())
    return result["prompt_id"]

def wait_for_result(prompt_id, timeout=300):
    deadline = time.time() + timeout
    while time.time() < deadline:
        req = urllib.request.Request(f"{COMFY_UI}/history/{prompt_id}")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                history = json.loads(resp.read())
        except:
            time.sleep(3)
            continue
        if prompt_id in history:
            return history[prompt_id]
        time.sleep(3)
    raise TimeoutError("ComfyUI timeout")

# ====== 配置 ======
CHARACTER_NAME = "xieyunlan"
CHARACTER_CN = "谢云岚"
EXPRESSION = "default"

POSITIVE_PROMPT = (
    f"Portrait of a handsome young Chinese man in ancient Tang dynasty scholar-official attire, {CHARACTER_CN} character, "
    "wearing a dark blue brocade robe with subtle silver cloud patterns, jade hairpin, "
    "serene expression, standing in a misty moonlit garden with lanterns, "
    "anime style, beautiful detailed face, delicate facial features, soft lighting, "
    "bokeh background, masterpiece, high quality, 4K, elegant composition, half-body portrait"
)

STYLE_PROMPT = "Ancient Chinese ink wash painting aesthetic, warm golden lantern light against deep blue night, cinematic portraiture, professional character design, soft bokeh"
NEGATIVE_PROMPT = "modern, ugly, deformed, blurry, low quality, watermark, text, signature, disfigured, bad anatomy, extra limbs, mutant, distorted face"

print(f"🎨 生成测试立绘: {CHARACTER_CN} ({CHARACTER_NAME}) - {EXPRESSION}")

prompt = {
    "8": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "qwen_image", "device": "default"}},
    "18": {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_bf16.safetensors", "weight_dtype": "default"}},
    "14": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["18", 0], "lora_name": "Kook_Zimage_瑶光.safetensors", "strength_model": 0.4}},
    "13": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["14", 0], "lora_name": "Kook_Zimage_如梦似幻.safetensors", "strength_model": 0.7}},
    "15": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["13", 0], "lora_name": "Z-Image-Fun-Lora-Distill-8-Steps-2603-ComfyUI.safetensors", "strength_model": 0.5}},
    "16": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
    "27": {"class_type": "CR Text", "inputs": {"text": POSITIVE_PROMPT}},
    "17": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["8", 0], "text": POSITIVE_PROMPT}},
    "6": {"class_type": "CR Text", "inputs": {"text": STYLE_PROMPT}},
    "10": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["8", 0], "text": NEGATIVE_PROMPT}},
    "25": {"class_type": "INTConstant", "inputs": {"value": 768}},
    "26": {"class_type": "INTConstant", "inputs": {"value": 1344}},
    "12": {"class_type": "EmptyLatentImage", "inputs": {"width": ["25", 0], "height": ["26", 0], "batch_size": 1}},
    "11": {"class_type": "KSampler", "inputs": {
        "model": ["15", 0], "positive": ["17", 0], "negative": ["10", 0], "latent_image": ["12", 0],
        "seed": 888888, "steps": 8, "cfg": 1.5, "sampler_name": "res_2s_ode", "scheduler": "kl_optimal", "denoise": 1
    }},
    "3": {"class_type": "VAEDecode", "inputs": {"samples": ["11", 0], "vae": ["16", 0]}},
    "2": {"class_type": "ImageScaleToTotalPixels", "inputs": {"image": ["3", 0], "upscale_method": "lanczos", "megapixels": 1.0, "resolution_steps": 1}},
    "20": {"class_type": "SaveImage", "inputs": {"images": ["2", 0], "filename_prefix": f"portrait_{CHARACTER_NAME}_{EXPRESSION}"}},
}

print("🚀 提交工作流...")
prompt_id = queue_prompt(prompt)
print(f"📋 Prompt ID: {prompt_id}")
print("⏳ 等待生成...")

result = wait_for_result(prompt_id)
status = result["status"]["status_str"]
print(f"📊 状态: {status}")

if status == "error":
    for m in result["status"].get("messages", []):
        if m[0] == "execution_error":
            print(f"❌ 错误: {m[1]['exception_message']}")
    sys.exit(1)

# 找最新生成的 PNG
out_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".png") and CHARACTER_NAME in f]
out_files.sort(key=lambda f: os.path.getmtime(os.path.join(OUTPUT_DIR, f)), reverse=True)
print(f"📂 找到 {len(out_files)} 个匹配文件")

if out_files:
    src = os.path.join(OUTPUT_DIR, out_files[0])
    dst_dir = os.path.join(GAME_PORTRAIT_DIR, CHARACTER_NAME)
    os.makedirs(dst_dir, exist_ok=True)
    dst = os.path.join(dst_dir, f"{EXPRESSION}.png")
    shutil.copy2(src, dst)
    size_kb = os.path.getsize(dst) / 1024
    print(f"✅ 立绘已保存: {dst}")
    print(f"   大小: {size_kb:.0f} KB")
    
    # 验证图片格式
    from PIL import Image
    img = Image.open(dst)
    print(f"   尺寸: {img.size[0]}x{img.size[1]}")
    print(f"   模式: {img.mode}")
else:
    # 回退：列出所有最新文件
    all_files = sorted([f for f in os.listdir(OUTPUT_DIR) if f.endswith(".png")],
                       key=lambda f: os.path.getmtime(os.path.join(OUTPUT_DIR, f)), reverse=True)
    print(f"   最近输出文件: {all_files[:5]}")
