"""
本地 ComfyUI rembg 去背景
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

# 复制立绘到 input 目录
shutil.copy2(os.path.join(PORTRAIT_DIR, "xieyunlan/default.png"), os.path.join(INPUT_DIR, "xieyunlan_default.png"))
print("📂 图片已复制到 ComfyUI input")

# rembg 去背景
print("✂️ 运行 rembg 去背景...")
rembg_prompt = {
    "1": {"class_type": "LoadImage", "inputs": {"image": "xieyunlan_default.png"}},
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
status = rr["status"]["status_str"]
print(f"📊 rembg 状态: {status}")

if status == "error":
    for m in rr["status"].get("messages", []):
        if m[0] == "execution_error":
            print(f"❌ 错误: {m[1]['exception_message']}")

out_files = [f for f in os.listdir(OUTPUT_DIR) if f.startswith("rembg_xieyunlan") and f.endswith(".png")]
out_files.sort(key=lambda f: os.path.getmtime(os.path.join(OUTPUT_DIR, f)), reverse=True)

if out_files:
    src = os.path.join(OUTPUT_DIR, out_files[0])
    dst = os.path.join(PORTRAIT_DIR, "xieyunlan/default.png")
    shutil.copy2(src, dst)
    
    from PIL import Image
    img = Image.open(dst)
    print(f"✅ 去背景完成!")
    print(f"   路径: {dst}")
    print(f"   模式: {img.mode}")
    print(f"   尺寸: {img.size[0]}x{img.size[1]}")
    print(f"   大小: {os.path.getsize(dst)/1024:.0f} KB")
    
    if img.mode == "RGBA":
        # 计算非透明占比
        pixels = img.getdata()
        non_transparent = sum(1 for p in pixels if p[3] > 10)
        total = img.size[0] * img.size[1]
        print(f"   人物占比: {non_transparent/total*100:.1f}%")
else:
    print(f"❌ 未找到 rembg 输出")
    recent = sorted([f for f in os.listdir(OUTPUT_DIR) if f.endswith(".png")],
                    key=lambda f: os.path.getmtime(os.path.join(OUTPUT_DIR, f)), reverse=True)
    print(f"   最近文件: {recent[:5]}")
