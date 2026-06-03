"""
Qwen3-VL 分析立绘质量 + 本地 ComfyUI rembg 去背景
"""
import urllib.request, json, time, shutil, os

COMFY_UI = "http://192.168.144.1:8188"
INPUT_DIR = "F:/ComfyUI_V6.0/ComfyUI-WorkFisher-V2/ComfyUI/input"
OUTPUT_DIR = "F:/ComfyUI_V6.0/ComfyUI-WorkFisher-V2/ComfyUI/output"
PORTRAIT_DIR = "D:/HermesWorkspace/girlgame-skill/frontend/assets/portraits/changan-moon"

def queue_prompt(p):
    body = json.dumps({"prompt": p}).encode()
    req = urllib.request.Request(f"{COMFY_UI}/api/prompt", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())["prompt_id"]

def wait(pid, timeout=300):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{COMFY_UI}/history/{pid}", timeout=30) as r:
                h = json.loads(r.read())
            if pid in h: return h[pid]
        except: pass
        time.sleep(3)
    raise TimeoutError("ComfyUI timeout")

# ====== 第一步：Qwen3-VL 分析图片质量 ======
print("🔍 Qwen3-VL 分析立绘质量...")
qwen_prompt = {
    "1": {"class_type": "LoadImage", "inputs": {"image": "portrait_check.png"}},
    "3": {"class_type": "Qwen3_VQA", "inputs": {
        "image": ["1", 0], "text": "评价这张半身人物立绘的质量。关注：面部精致度、构图、光影、整体氛围。给出简短评价。",
        "model": "Qwen3-VL-4B-Instruct", "quantization": "none", "keep_model_loaded": True,
        "temperature": 0.3, "max_new_tokens": 256, "seed": 42, "attention": "sdpa"
    }},
    "9": {"class_type": "ShowText|pysssss", "inputs": {"text": ["3", 0]}}
}

qid = queue_prompt(qwen_prompt)
qr = wait(qid)
for out in qr["outputs"].values():
    for v in out.values():
        text = "".join(str(x) for x in v) if isinstance(v, list) else str(v)
        print(f"📝 Qwen评价: {text}")

# ====== 第二步：rembg 去背景 ======
print("\n✂️ 运行 rembg 去背景...")
rembg_prompt = {
    "1": {"class_type": "LoadImage", "inputs": {"image": "portrait_check.png"}},
    "2": {"class_type": "Image Rembg (Remove Background)", "inputs": {
        "images": ["1", 0], "transparency": True, "model": "u2net",
        "post_processing": False, "only_mask": False, "alpha_matting": False,
        "alpha_matting_foreground_threshold": 240, "alpha_matting_background_threshold": 10,
        "alpha_matting_erode_size": 10, "background_color": "none"
    }},
    "3": {"class_type": "SaveImage", "inputs": {"images": ["2", 0], "filename_prefix": "rembg_xieyunlan"}}
}

rid = queue_prompt(rembg_prompt)
rr = wait(rid)

# 找到 rembg 输出
out_files = [f for f in os.listdir(OUTPUT_DIR) if f.startswith("rembg_xieyunlan") and f.endswith(".png")]
out_files.sort(key=lambda f: os.path.getmtime(os.path.join(OUTPUT_DIR, f)), reverse=True)

if out_files:
    src = os.path.join(OUTPUT_DIR, out_files[0])
    dst = os.path.join(PORTRAIT_DIR, "xieyunlan/default.png")
    shutil.copy2(src, dst)
    
    from PIL import Image
    img = Image.open(dst)
    is_rgba = img.mode == "RGBA"
    transparent_pixels = 0
    if is_rgba:
        bbox = img.getbbox()
        total = img.size[0] * img.size[1]
        transparent_pixels = total - (bbox[2]-bbox[0])*(bbox[3]-bbox[1]) if bbox else total
    
    print(f"✅ 去背景完成: {dst}")
    print(f"   模式: {img.mode}")
    print(f"   尺寸: {img.size[0]}x{img.size[1]}")
    if is_rgba:
        print(f"   透明像素占比: {transparent_pixels/max(1,img.size[0]*img.size[1])*100:.1f}%")
    print(f"   大小: {os.path.getsize(dst)/1024:.0f} KB")
else:
    print(f"❌ 未找到 rembg 输出")
    recent = sorted([f for f in os.listdir(OUTPUT_DIR) if f.endswith(".png")],
                    key=lambda f: os.path.getmtime(os.path.join(OUTPUT_DIR, f)), reverse=True)
    print(f"   最近文件: {recent[:5]}")
