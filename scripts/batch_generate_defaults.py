"""
批量生成6角色default立绘 + rembg去背景
"""
import urllib.request, json, time, shutil, os, sys

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
        time.sleep(2)
    raise TimeoutError("ComfyUI timeout")

# 6 角色配置
CHARACTERS = [
    {
        "id": "xieyunlan", "name": "谢云岚",
        "prompt": "Portrait of a handsome young Chinese man in ancient Tang dynasty, dark blue brocade robe with silver cloud patterns, jade hairpin, cold and aloof expression, misty moonlit garden with lanterns, anime style, beautiful detailed face, half-body portrait, masterpiece",
        "style": "Ancient Chinese ink wash aesthetic, cool blue palette, moonlight, elegant"
    },
    {
        "id": "huayingyue", "name": "花映月",
        "prompt": "Portrait of a beautiful young Chinese woman in ancient Tang dynasty, flowing silk dress in pink and gold, flower hair ornaments, elegant and mysterious smile, standing in a music pavilion with lanterns, anime style, beautiful detailed face, half-body portrait, masterpiece",
        "style": "Ancient Chinese aesthetic, warm golden light, soft romantic atmosphere, dreamy"
    },
    {
        "id": "shenmingyue", "name": "沈明月",
        "prompt": "Portrait of a heroic young Chinese woman in ancient Tang dynasty, warrior attire in red and white, holding a sword, confident and sharp gaze, standing on a city wall under stars, anime style, beautiful detailed face, half-body portrait, masterpiece",
        "style": "Ancient Chinese martial aesthetic, moonlight, heroic composition, cool tones"
    },
    {
        "id": "lihuaijin", "name": "李怀瑾",
        "prompt": "Portrait of a refined young Chinese man in ancient Tang dynasty, white scholar robe, holding a brush, gentle scholarly expression, in a study with scrolls and candlelight, anime style, beautiful detailed face, half-body portrait, masterpiece",
        "style": "Ancient Chinese literati aesthetic, warm candlelight, scholarly atmosphere, elegant"
    },
    {
        "id": "guqianfan", "name": "顾千帆",
        "prompt": "Portrait of a charismatic Chinese man in ancient Tang dynasty, dark green traveler robe, carrying a medicine bag, roguish smile, standing in a misty forest, anime style, beautiful detailed face, half-body portrait, masterpiece",
        "style": "Ancient Chinese wandering aesthetic, earthy tones, adventurous vibe, natural lighting"
    },
    {
        "id": "gongsunlan", "name": "公孙兰",
        "prompt": "Portrait of a graceful older Chinese woman in ancient Tang dynasty, elegant purple dress, holding a tea cup, wise and knowing eyes, in a bookstore filled with scrolls, anime style, beautiful detailed face, half-body portrait, masterpiece",
        "style": "Ancient Chinese aesthetic, warm amber tones, peaceful bookstore atmosphere, mature elegance"
    }
]

NEGATIVE = "modern, ugly, deformed, blurry, low quality, watermark, text, signature, disfigured, bad anatomy, extra limbs, mutant, distorted face, multiple people"

print(f"🎨 批量生成 {len(CHARACTERS)} 个角色 default 立绘\n")

for ch in CHARACTERS:
    print(f"[{ch['id']}] {ch['name']}...", end=" ", flush=True)
    
    prompt = {
        "8": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "qwen_image", "device": "default"}},
        "18": {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_bf16.safetensors", "weight_dtype": "default"}},
        "14": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["18", 0], "lora_name": "Kook_Zimage_瑶光.safetensors", "strength_model": 0.4}},
        "13": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["14", 0], "lora_name": "Kook_Zimage_如梦似幻.safetensors", "strength_model": 0.7}},
        "15": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["13", 0], "lora_name": "Z-Image-Fun-Lora-Distill-8-Steps-2603-ComfyUI.safetensors", "strength_model": 0.5}},
        "16": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
        "27": {"class_type": "CR Text", "inputs": {"text": ch["prompt"]}},
        "17": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["8", 0], "text": ch["prompt"]}},
        "6": {"class_type": "CR Text", "inputs": {"text": ch["style"]}},
        "10": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["8", 0], "text": NEGATIVE}},
        "25": {"class_type": "INTConstant", "inputs": {"value": 768}},
        "26": {"class_type": "INTConstant", "inputs": {"value": 1344}},
        "12": {"class_type": "EmptyLatentImage", "inputs": {"width": ["25", 0], "height": ["26", 0], "batch_size": 1}},
        "11": {"class_type": "KSampler", "inputs": {
            "model": ["15", 0], "positive": ["17", 0], "negative": ["10", 0], "latent_image": ["12", 0],
            "seed": 888888 + hash(ch["id"]) % 99999, "steps": 8, "cfg": 1.5,
            "sampler_name": "res_2s_ode", "scheduler": "kl_optimal", "denoise": 1
        }},
        "3": {"class_type": "VAEDecode", "inputs": {"samples": ["11", 0], "vae": ["16", 0]}},
        "2": {"class_type": "ImageScaleToTotalPixels", "inputs": {"image": ["3", 0], "upscale_method": "lanczos", "megapixels": 1.0, "resolution_steps": 1}},
        "20": {"class_type": "SaveImage", "inputs": {"images": ["2", 0], "filename_prefix": f"portrait_{ch['id']}_default"}},
    }
    
    try:
        pid = queue_prompt(prompt)
        result = wait(pid)
        status = result["status"]["status_str"]
        
        if status == "success":
            # 找到输出文件
            out_files = [f for f in os.listdir(OUTPUT_DIR) if f.startswith(f"portrait_{ch['id']}_default") and f.endswith(".png")]
            out_files.sort(key=lambda f: os.path.getmtime(os.path.join(OUTPUT_DIR, f)), reverse=True)
            
            if out_files:
                src = os.path.join(OUTPUT_DIR, out_files[0])
                dst_dir = os.path.join(PORTRAIT_DIR, ch["id"])
                os.makedirs(dst_dir, exist_ok=True)
                dst = os.path.join(dst_dir, "default.png")
                shutil.copy2(src, dst)
                
                # rembg
                shutil.copy2(dst, os.path.join(INPUT_DIR, f"{ch['id']}_default.png"))
                
                rembg_p = {
                    "1": {"class_type": "LoadImage", "inputs": {"image": f"{ch['id']}_default.png"}},
                    "2": {"class_type": "Image Rembg (Remove Background)", "inputs": {
                        "images": ["1", 0], "transparency": True, "model": "u2net",
                        "post_processing": False, "only_mask": False, "alpha_matting": False,
                        "alpha_matting_foreground_threshold": 240, "alpha_matting_background_threshold": 10,
                        "alpha_matting_erode_size": 10, "background_color": "none"
                    }},
                    "3": {"class_type": "SaveImage", "inputs": {"images": ["2", 0], "filename_prefix": f"rembg_{ch['id']}_default"}}
                }
                
                rpid = queue_prompt(rembg_p)
                wait(rpid)
                
                rembg_files = [f for f in os.listdir(OUTPUT_DIR) if f.startswith(f"rembg_{ch['id']}_default") and f.endswith(".png")]
                rembg_files.sort(key=lambda f: os.path.getmtime(os.path.join(OUTPUT_DIR, f)), reverse=True)
                
                if rembg_files:
                    shutil.copy2(os.path.join(OUTPUT_DIR, rembg_files[0]), dst)
                    size_kb = os.path.getsize(dst) / 1024
                    print(f"✅ {size_kb:.0f}KB")
                else:
                    print(f"⚠️ 生成OK但rembg文件未找到")
            else:
                print(f"❌ 输出文件未找到")
        else:
            print(f"❌ 状态={status}")
    except Exception as e:
        print(f"❌ 错误: {e}")

print("\n🎉 批量完成!")
print(f"\n所有立绘已保存到: {PORTRAIT_DIR}/[角色id]/default.png")
