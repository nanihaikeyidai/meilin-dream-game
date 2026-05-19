#!/mnt/f/ComfyUI_V6.0/ComfyUI-WorkFisher-V2/Python3.12.6/python.exe
"""批量生成AVG角色表情立绘 - zImage文生图"""
import json, os, time, urllib.request, subprocess, sys, shutil

COMFY_API = "http://192.168.1.2:8188/api/prompt"
OUTPUT_DIR = r"F:\ComfyUI_V6.0\ComfyUI-WorkFisher-V2\ComfyUI\output"
ASSETS_DIR = r"D:\Hermes\girlgame-skill\frontend\assets\portraits"

PROMPTS = {
    "xieyunlan_smile": "1boy, male, ancient Chinese official, black robe, jade crown, rare gentle smile, eyes softening, elegant restrained, half body, warm light, anime style, ink wash, high quality, solo",
    "xieyunlan_happy": "1boy, male, ancient Chinese official, black robe, genuine bright smile, eyes curved, rare joy, relaxed, half body, golden warm light, anime style, high quality, solo",
    "xieyunlan_angry": "1boy, male, ancient Chinese official, black robe, cold anger, sharp eyes, furrowed brows, tense jaw, intimidating, half body, cool light, anime style, high quality, solo",
    "xieyunlan_sad": "1boy, male, ancient Chinese official, black robe, sad expression, downcast eyes, lips pressed, lonely grief, half body, dim blue lighting, melancholic, anime style, high quality, solo",
    "xieyunlan_surprised": "1boy, male, ancient Chinese official, black robe, eyes wide in surprise, caught off guard, mouth slightly open, half body, anime style, ink wash, high quality, solo",
    "xieyunlan_blush": "1boy, male, ancient Chinese official, black robe, slight blush, looking away awkwardly, flustered, half body, warm pink, anime style, high quality, solo",
    "xieyunlan_cold": "1boy, male, ancient Chinese official, black robe, completely cold, emotionless, ice-cold gaze, half body, cool blue light, anime style, high quality, solo",
    "huayingyue_smile": "1girl, female, ancient Chinese courtesan, red silk dress, gold hairpin, warm smile, eyes soft, holding fan, half body, warm lighting, anime style, high quality, solo",
    "huayingyue_happy": "1girl, female, ancient Chinese courtesan, red silk dress, gold hairpin, bright laughing eyes, joyful, half body, golden light, anime style, high quality, solo",
    "huayingyue_angry": "1girl, female, ancient Chinese courtesan, red silk dress, cold smile, sharp eyes, dangerous, fan closed, half body, cool dramatic light, anime style, high quality, solo",
    "huayingyue_sad": "1girl, female, ancient Chinese courtesan, red silk dress, sad eyes, forced smile, looking away, lonely vulnerable, half body, dim blue, anime style, high quality, solo",
    "huayingyue_surprised": "1girl, female, ancient Chinese courtesan, red silk dress, eyes wide, fan lowered, caught off guard, genuine shock, half body, anime style, high quality, solo",
    "huayingyue_blush": "1girl, female, ancient Chinese courtesan, red silk dress, genuine blush, shy, hiding behind fan, flustered, half body, warm pink, anime style, high quality, solo",
    "huayingyue_cold": "1girl, female, ancient Chinese courtesan, red silk dress, cold expressionless, distant eyes, ice beauty, half body, cool light, anime style, high quality, solo",
    "guqianfan_smile": "1boy, male, ancient Chinese warrior, dark outfit, rare small smile, eyes softer, subtle warmth, half body, warm golden light, anime style, high quality, solo",
    "guqianfan_happy": "1boy, male, ancient Chinese warrior, dark outfit, genuine happy smile, carefree, eyes bright, half body, warm sunlight, anime style, high quality, solo",
    "guqianfan_angry": "1boy, male, ancient Chinese warrior, dark outfit, cold furious glare, sharp eyes, hand on blade, predatory, half body, harsh light, anime style, high quality, solo",
    "guqianfan_sad": "1boy, male, ancient Chinese warrior, dark outfit, sad silent, looking down, hidden pain, lonely burdened, half body, dim light, anime style, high quality, solo",
    "guqianfan_surprised": "1boy, male, ancient Chinese warrior, dark outfit, eyes wide in shock, alert, momentary loss composure, half body, anime style, high quality, solo",
    "guqianfan_blush": "1boy, male, ancient Chinese warrior, dark outfit, slight blush, awkwardly looking away, flustered, half body, warm pink, anime style, high quality, solo",
    "guqianfan_cold": "1boy, male, ancient Chinese warrior, dark outfit, unreadable, dead eyes, emotionless, cold gaze, half body, cool blue, anime style, high quality, solo",
    "shenmingyue_smile": "1girl, female, ancient Chinese lady, moon-white dress, jade hairpin, gentle warm smile, eyes soft, kindness, half body, soft warm light, anime style, high quality, solo",
    "shenmingyue_happy": "1girl, female, ancient Chinese lady, moon-white dress, jade hairpin, bright joyful smile, eyes shining, happiness, half body, golden light, anime style, high quality, solo",
    "shenmingyue_angry": "1girl, female, ancient Chinese lady, moon-white dress, offended expression, furrowed brows, tight lips, upset, half body, cool light, anime style, high quality, solo",
    "shenmingyue_sad": "1girl, female, ancient Chinese lady, moon-white dress, jade hairpin, tears welling, sad, looking down, vulnerable, half body, dim blue, anime style, high quality, solo",
    "shenmingyue_surprised": "1girl, female, ancient Chinese lady, moon-white dress, eyes wide, hand on chest, delicate shock, half body, anime style, high quality, solo",
    "shenmingyue_blush": "1girl, female, ancient Chinese lady, moon-white dress, blushing, shy, looking down, demure but moved, half body, warm pink, anime style, high quality, solo",
    "shenmingyue_cold": "1girl, female, ancient Chinese lady, moon-white dress, cold distant, emotionless eyes, closed off, elegant unreachable, half body, cool blue, anime style, high quality, solo",
    "lihuaijin_smile": "1boy, male, ancient Chinese scholar, green robe, warm gentle smile, eyes soft, kind, scholarly aura, half body, warm light, anime style, high quality, solo",
    "lihuaijin_happy": "1boy, male, ancient Chinese scholar, green robe, rare bright smile, eyes curved, genuine joy, carefree, half body, sunny golden light, anime style, high quality, solo",
    "lihuaijin_angry": "1boy, male, ancient Chinese scholar, green robe, stern cold, disappointed eyes, furrowed brows, calm intimidating, half body, cool harsh light, anime style, high quality, solo",
    "lihuaijin_sad": "1boy, male, ancient Chinese scholar, green robe, sad distant eyes, melancholic, old grief, half body, dim light, anime style, high quality, solo",
    "lihuaijin_surprised": "1boy, male, ancient Chinese scholar, green robe, eyes wide in shock, book slipping, pale, utterly surprised, half body, anime style, high quality, solo",
    "lihuaijin_blush": "1boy, male, ancient Chinese scholar, green robe, slight blush, avoiding eye contact, flustered, half body, warm pink, anime style, high quality, solo",
    "lihuaijin_cold": "1boy, male, ancient Chinese scholar, green robe, cold emotionless eyes, distant smile unreadable, half body, cool grey, anime style, high quality, solo",
    "gongsunlan_smile": "1girl, female, mature ancient doctor, white robe, gentle motherly smile, eyes warm, kind face, half body, warm light, anime style, high quality, solo",
    "gongsunlan_happy": "1girl, female, mature ancient doctor, white robe, genuine bright smile, eyes curved, warm happiness, half body, golden light, anime style, high quality, solo",
    "gongsunlan_angry": "1girl, female, mature ancient doctor, white robe, stern expression, disappointed eyes, firm serious, half body, cool clinical light, anime style, high quality, solo",
    "gongsunlan_sad": "1girl, female, mature ancient doctor, white robe, sad distant eyes, melancholic, waiting, half body, dim blue, anime style, high quality, solo",
    "gongsunlan_surprised": "1girl, female, mature ancient doctor, white robe, eyes wide, hand covering mouth, unexpected, half body, anime style, high quality, solo",
    "gongsunlan_blush": "1girl, female, mature ancient doctor, white robe, slight mature blush, shy eyes, soft smile, half body, warm pink, anime style, high quality, solo",
    "gongsunlan_cold": "1girl, female, mature ancient doctor, white robe, professional detachment, calm emotionless, clinical distance, half body, cool light, anime style, high quality, solo",
}

def build_prompt(text, char_id, expr, seed):
    return {
        "8": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "qwen_image", "device": "default"}},
        "16": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
        "18": {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_bf16.safetensors", "weight_dtype": "default"}},
        "14": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["18", 0], "lora_name": "Kook_Zimage_瑶光.safetensors", "strength_model": 0.4}},
        "13": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["14", 0], "lora_name": "Kook_Zimage_如梦似幻.safetensors", "strength_model": 0.7}},
        "15": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["13", 0], "lora_name": "Z-Image-Fun-Lora-Distill-8-Steps-2603-ComfyUI.safetensors", "strength_model": 0.5}},
        "27": {"class_type": "CR Text", "inputs": {"text": text}},
        "17": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["8", 0], "text": text}},
        "6": {"class_type": "CR Text", "inputs": {"text": "Traditional Chinese ink wash aesthetic, anime style, high quality, detailed face"}},
        "10": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["8", 0], "text": "nsfw, low quality, bad anatomy, extra fingers, mutated hands, ugly, blurry, watermark, text, logo, realistic, 3d, photorealistic, modern clothes, multiple characters, crowd"}},
        "25": {"class_type": "INTConstant", "inputs": {"value": 768}},
        "26": {"class_type": "INTConstant", "inputs": {"value": 1344}},
        "12": {"class_type": "EmptyLatentImage", "inputs": {"width": ["25", 0], "height": ["26", 0], "batch_size": 1}},
        "11": {"class_type": "KSampler", "inputs": {"model": ["15", 0], "positive": ["17", 0], "negative": ["10", 0], "latent_image": ["12", 0], "seed": seed, "steps": 8, "cfg": 1.5, "sampler_name": "res_2s_ode", "scheduler": "kl_optimal", "denoise": 1}},
        "3": {"class_type": "VAEDecode", "inputs": {"samples": ["11", 0], "vae": ["16", 0]}},
        "2": {"class_type": "ImageScaleToTotalPixels", "inputs": {"image": ["3", 0], "upscale_method": "lanczos", "megapixels": 1.0, "resolution_steps": 1}},
        "20": {"class_type": "SaveImage", "inputs": {"images": ["2", 0], "filename_prefix": f"zg_{char_id}_{expr}"}},
    }

def submit_and_wait(text, char_id, expr, timeout=600):
    seed = abs(hash(f"{char_id}_{expr}")) % (2**31)
    prompt = build_prompt(text, char_id, expr, seed)
    body = json.dumps({"prompt": prompt}).encode("utf-8")
    req = urllib.request.Request(COMFY_API, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err = e.read().decode()[:200]
        sys.stderr.write(f"HTTP {e.code}: {err}\n")
        sys.stderr.flush()
        return None, None

    pid = result["prompt_id"]
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            req = urllib.request.Request(f"http://192.168.1.2:8188/history/{pid}")
            with urllib.request.urlopen(req, timeout=30) as resp:
                history = json.loads(resp.read())
            if pid in history:
                data = history[pid]
                s = data["status"]["status_str"]
                if s == "error":
                    for m in data["status"].get("messages", []):
                        if m[0] == "execution_error":
                            sys.stderr.write(f"ERR: {m[1].get('exception_message','unknown')}\n")
                    return None, None
                if s == "success":
                    for out_data in data.get("outputs", {}).values():
                        for val in out_data.values():
                            if isinstance(val, list) and val and isinstance(val[0], dict) and "filename" in val[0]:
                                return "OK", val[0]["filename"]
            time.sleep(5)
        except:
            time.sleep(5)
    return "TIMEOUT", None

if __name__ == "__main__":
    chars = ["xieyunlan","huayingyue","guqianfan","shenmingyue","lihuaijin","gongsunlan"]
    exprs = ["smile","happy","angry","sad","surprised","blush","cold"]
    ok, fail = 0, 0

    for cid in chars:
        for expr in exprs:
            key = f"{cid}_{expr}"
            text = PROMPTS.get(key)
            if not text:
                continue
            dst = os.path.join(ASSETS_DIR, cid, f"{expr}.png")
            if os.path.exists(dst):
                print(f"⏭ {key}")
                continue
            print(f"🎨 {key}...", end=" ", flush=True)
            status, filename = submit_and_wait(text, cid, expr)
            if status == "OK" and filename:
                src = os.path.join(OUTPUT_DIR, filename)
                if os.path.exists(src):
                    os.makedirs(os.path.join(ASSETS_DIR, cid), exist_ok=True)
                    shutil.copy2(src, dst)
                    kb = os.path.getsize(src) // 1024
                    print(f"✅ {kb}KB")
                    ok += 1
                else:
                    print(f"❌ no file: {filename}")
                    fail += 1
            else:
                print(f"❌ {status}")
                fail += 1
            time.sleep(3)

    print(f"\n成功={ok} 失败={fail}")
