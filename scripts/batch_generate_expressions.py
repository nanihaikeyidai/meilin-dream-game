#!/usr/bin/env python3
"""
「月下长安」立绘批量生成 — zImage 文生图 + rembg 去背景
基于已验证的管线（已成功生成6角色 default.png）
"""

import json, os, shutil, sys, time, urllib.request

COMFY_BASE = "http://192.168.1.2:8188"
COMFY_DIR = r"F:\ComfyUI_V6.0\ComfyUI-WorkFisher-V2\ComfyUI"
INPUT_DIR = os.path.join(COMFY_DIR, "input")
OUTPUT_DIR = os.path.join(COMFY_DIR, "output")
ASSETS_DIR = r"D:\HermesWorkspace\girlgame-skill\frontend\assets\portraits\changan-moon"

# 角色 + 表情提示词（已验证的 zImage 风格）
PROMPTS = {}

# ===== 谢云岚 =====
PROMPTS["xieyunlan_default"] = "1boy, male, ancient Chinese official, black official robe with silver patterns, jade hair crown, long black hair tied up, phoenix eyes, cold handsome face, standing straight, hand on sword hilt, imposing presence, half body, anime style, ink wash aesthetic, high quality, solo"
PROMPTS["xieyunlan_smile"] = "1boy, male, ancient Chinese official, black robe, jade crown, rare gentle smile, eyes softening, elegant restrained expression, half body, warm light, anime style, ink wash, high quality, solo"
PROMPTS["xieyunlan_happy"] = "1boy, male, ancient Chinese official, black robe, genuine bright smile, eyes curved, rare moment of joy, relaxed shoulders, half body, golden warm light, anime style, ink wash, high quality, solo"
PROMPTS["xieyunlan_angry"] = "1boy, male, ancient Chinese official, black robe, cold anger, sharp eyes, furrowed brows, tense jaw, hand gripping sword hilt, intimidating, half body, cool light, anime style, high quality, solo"
PROMPTS["xieyunlan_sad"] = "1boy, male, ancient Chinese official, black robe, sad expression, downcast eyes, lips pressed thin, lonely restrained grief, half body, dim blue lighting, melancholic, anime style, high quality, solo"
PROMPTS["xieyunlan_surprised"] = "1boy, male, ancient Chinese official, black robe, eyes wide in surprise, caught off guard, mask slipping, mouth slightly open, half body, anime style, ink wash, high quality, solo"
PROMPTS["xieyunlan_blush"] = "1boy, male, ancient Chinese official, black robe, slight blush on cheeks, looking away awkwardly, flustered, half body, warm pink tone, anime style, ink wash, high quality, solo"
PROMPTS["xieyunlan_cold"] = "1boy, male, ancient Chinese official, black robe, completely cold expression, emotionless eyes, ice-cold gaze, unapproachable aura, half body, cool blue light, anime style, ink wash, high quality, solo"

# ===== 花映月 =====
PROMPTS["huayingyue_default"] = "1girl, female, ancient Chinese courtesan, flowing red silk dress, gold hairpin in loose bun, round silk fan, peach blossom eyes, beauty mole near eye, elegant smile, standing gracefully, half body, anime style, ink wash aesthetic, high quality, solo"
PROMPTS["huayingyue_smile"] = "1girl, female, ancient Chinese courtesan, red silk dress, gold hairpin, warm genuine smile, eyes soft, holding fan, relaxed, half body, warm lighting, anime style, ink wash, high quality, solo"
PROMPTS["huayingyue_happy"] = "1girl, female, ancient Chinese courtesan, red silk dress, gold hairpin, bright laughing eyes, head tilted, genuinely joyful expression, half body, golden light, anime style, ink wash, high quality, solo"
PROMPTS["huayingyue_angry"] = "1girl, female, ancient Chinese courtesan, red silk dress, cold smile, eyes sharp, dangerous expression, fan closed, beauty with thorns, half body, cool dramatic light, anime style, high quality, solo"
PROMPTS["huayingyue_sad"] = "1girl, female, ancient Chinese courtesan, red silk dress, sad eyes, faint forced smile, looking away, lonely and vulnerable, half body, dim blue tone, anime style, high quality, solo"
PROMPTS["huayingyue_surprised"] = "1girl, female, ancient Chinese courtesan, red silk dress, eyes wide in surprise, fan lowered, caught off guard, genuine shock, half body, anime style, ink wash, high quality, solo"
PROMPTS["huayingyue_blush"] = "1girl, female, ancient Chinese courtesan, red silk dress, genuine blush, shy expression, hiding half face behind fan, flustered, half body, warm pink tone, anime style, high quality, solo"
PROMPTS["huayingyue_cold"] = "1girl, female, ancient Chinese courtesan, red silk dress, cold expressionless face, distant eyes, professional smile gone, ice beauty, half body, cool light, anime style, high quality, solo"

# ===== 顾千帆 =====
PROMPTS["guqianfan_default"] = "1boy, male, ancient Chinese warrior, dark green martial outfit, half tied messy hair, sharp eyes, lean fit build, cautious expression, half body, traditional Chinese wuxia style, ink wash aesthetic, high quality, solo"
PROMPTS["guqianfan_smile"] = "1boy, male, ancient Chinese warrior, dark outfit, rare small smile, eyes softer, trustworthy, subtle warmth, half body, warm golden light, anime style, ink wash, high quality, solo"
PROMPTS["guqianfan_happy"] = "1boy, male, ancient Chinese warrior, dark outfit, genuine happy smile, rare carefree moment, eyes bright, relaxed, half body, warm sunlight, anime style, high quality, solo"
PROMPTS["guqianfan_angry"] = "1boy, male, ancient Chinese warrior, dark outfit, cold furious glare, sharp dangerous eyes, hand reaching for blade, predatory stance, half body, harsh light, anime style, high quality, solo"
PROMPTS["guqianfan_sad"] = "1boy, male, ancient Chinese warrior, dark outfit, sad silent expression, looking down, hidden pain in eyes, lonely and burdened, half body, dim light, anime style, high quality, solo"
PROMPTS["guqianfan_surprised"] = "1boy, male, ancient Chinese warrior, dark outfit, eyes wide with shock, momentary loss of composure, alert, half body, anime style, ink wash, high quality, solo"
PROMPTS["guqianfan_blush"] = "1boy, male, ancient Chinese warrior, dark outfit, slight blush on tanned skin, awkwardly looking away, flustered, half body, warm pink tone, anime style, high quality, solo"
PROMPTS["guqianfan_cold"] = "1boy, male, ancient Chinese warrior, dark outfit, completely unreadable expression, dead eyes, emotionless, half body, cool blue light, anime style, high quality, solo"

# ===== 沈明月 =====
PROMPTS["shenmingyue_default"] = "1girl, female, ancient Chinese noble lady, moon-white dress, white jade hairpin, elegant coiled hair bun, gentle eyes, soft refined expression, standing gracefully, hands clasped, half body, traditional Chinese style, ink wash aesthetic, high quality, solo"
PROMPTS["shenmingyue_smile"] = "1girl, female, ancient Chinese lady, moon-white dress, jade hairpin, gentle warm smile, eyes soft, genuine kindness, elegant, half body, soft warm light, anime style, high quality, solo"
PROMPTS["shenmingyue_happy"] = "1girl, female, ancient Chinese lady, moon-white dress, jade hairpin, bright joyful smile, eyes shining, rare happiness, head tilted, genuine laugh, half body, golden light, anime style, high quality, solo"
PROMPTS["shenmingyue_angry"] = "1girl, female, ancient Chinese lady, moon-white dress, offended expression, furrowed brows, tight lips, upset, trying to maintain composure, half body, cool light, anime style, high quality, solo"
PROMPTS["shenmingyue_sad"] = "1girl, female, ancient Chinese lady, moon-white dress, jade hairpin, tears welling in eyes, sad expression, looking down, lonely and vulnerable, half body, dim blue light, anime style, high quality, solo"
PROMPTS["shenmingyue_surprised"] = "1girl, female, ancient Chinese lady, moon-white dress, eyes wide in surprise, hand touching chest, delicate shock, half body, anime style, ink wash, high quality, solo"
PROMPTS["shenmingyue_blush"] = "1girl, female, ancient Chinese lady, moon-white dress, blushing, shy eyes, looking down, fingers fidgeting with sleeve, demure but moved, half body, warm pink tone, anime style, high quality, solo"
PROMPTS["shenmingyue_cold"] = "1girl, female, ancient Chinese lady, moon-white dress, cold distant expression, emotionless eyes, closed off, elegant and unreachable, half body, cool blue light, anime style, high quality, solo"

# ===== 李怀瑾 =====
PROMPTS["lihuaijin_default"] = "1boy, male, ancient Chinese scholar, bamboo-green robe, jade hairpin in scholar bun, gentle scholarly face, holding a book scroll, refined elegant posture, half body, traditional Chinese style, ink wash aesthetic, high quality, solo"
PROMPTS["lihuaijin_smile"] = "1boy, male, ancient Chinese scholar, green robe, warm gentle smile, eyes soft, kind, scholarly aura, half body, warm light, anime style, high quality, solo"
PROMPTS["lihuaijin_happy"] = "1boy, male, ancient Chinese scholar, green robe, rare bright smile, eyes curved, genuine joy, carefree moment, half body, sunny golden light, anime style, high quality, solo"
PROMPTS["lihuaijin_angry"] = "1boy, male, ancient Chinese scholar, green robe, stern cold expression, disappointed eyes, furrowed brows, calm but intimidating anger, half body, cool harsh light, anime style, high quality, solo"
PROMPTS["lihuaijin_sad"] = "1boy, male, ancient Chinese scholar, green robe, sad distant eyes, looking into distance, melancholic, old grief, book in hand but not reading, half body, dim light, anime style, high quality, solo"
PROMPTS["lihuaijin_surprised"] = "1boy, male, ancient Chinese scholar, green robe, eyes wide in shock, book slipping from hand, pale face, utterly surprised, half body, anime style, high quality, solo"
PROMPTS["lihuaijin_blush"] = "1boy, male, ancient Chinese scholar, green robe, slight blush, avoiding eye contact, flustered, clearing throat, half body, warm pink tone, anime style, high quality, solo"
PROMPTS["lihuaijin_cold"] = "1boy, male, ancient Chinese scholar, green robe, cold emotionless eyes, distant smile that doesn't reach eyes, unreadable, half body, cool grey light, anime style, high quality, solo"

# ===== 公孙兰 =====
PROMPTS["gongsunlan_default"] = "1girl, female, mature ancient Chinese female doctor, plain white robe, silver hairpin in simple bun, calm gentle expression, herb medicine bag at waist, warm mature aura, half body, traditional Chinese style, ink wash aesthetic, high quality, solo"
PROMPTS["gongsunlan_smile"] = "1girl, female, mature doctor, white robe, gentle motherly smile, eyes warm, kind face, relaxed, half body, warm light, anime style, high quality, solo"
PROMPTS["gongsunlan_happy"] = "1girl, female, mature doctor, white robe, genuine bright smile, eyes curved, rare joyful expression, warm happiness, half body, golden light, anime style, high quality, solo"
PROMPTS["gongsunlan_angry"] = "1girl, female, mature doctor, white robe, stern expression, disappointed eyes, firm and serious, doctor's authority, half body, cool clinical light, anime style, high quality, solo"
PROMPTS["gongsunlan_sad"] = "1girl, female, mature doctor, white robe, sad distant eyes, looking into distance, melancholic, waiting, half body, dim blue light, anime style, high quality, solo"
PROMPTS["gongsunlan_surprised"] = "1girl, female, mature doctor, white robe, eyes wide in surprise, hand covering mouth, unexpected news, half body, anime style, high quality, solo"
PROMPTS["gongsunlan_blush"] = "1girl, female, mature doctor, white robe, slight mature blush, shy eyes, looking down with soft smile, half body, warm pink tone, anime style, high quality, solo"
PROMPTS["gongsunlan_cold"] = "1girl, female, mature doctor, white robe, professional detachment, calm emotionless eyes, clinical distance, half body, cool light, anime style, high quality, solo"

CHARACTERS = ["xieyunlan", "huayingyue", "guqianfan", "shenmingyue", "lihuaijin", "gongsunlan"]
EXPRESSIONS = ["default", "smile", "happy", "angry", "sad", "surprised", "blush", "cold"]


def make_zimage_prompt(prompt_text, char_id, expression, seed=42):
    """构建 zImage 文生图 prompt"""
    return {
        "8": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "qwen_image", "device": "default"}},
        "16": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
        "18": {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_bf16.safetensors", "weight_dtype": "default"}},
        "14": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["18", 0], "lora_name": "Kook_Zimage_瑶光.safetensors", "strength_model": 0.4}},
        "13": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["14", 0], "lora_name": "Kook_Zimage_如梦似幻.safetensors", "strength_model": 0.7}},
        "15": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["13", 0], "lora_name": "Z-Image-Fun-Lora-Distill-8-Steps-2603-ComfyUI.safetensors", "strength_model": 0.5}},
        "27": {"class_type": "CR Text", "inputs": {"text": prompt_text}},
        "17": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["8", 0], "text": prompt_text}},
        "6": {"class_type": "CR Text", "inputs": {"text": "Traditional Chinese ink wash painting aesthetic, anime style, high quality, detailed face, elegant, soft lighting"}},
        "10": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["8", 0], "text": "nsfw, low quality, bad anatomy, extra fingers, mutated hands, ugly, blurry, watermark, text, logo, realistic, 3d, photorealistic, modern clothes, multiple characters, crowd"}},
        "25": {"class_type": "INTConstant", "inputs": {"value": 768}},
        "26": {"class_type": "INTConstant", "inputs": {"value": 1344}},
        "12": {"class_type": "EmptyLatentImage", "inputs": {"width": ["25", 0], "height": ["26", 0], "batch_size": 1}},
        "11": {"class_type": "KSampler", "inputs": {
            "model": ["15", 0], "positive": ["17", 0], "negative": ["10", 0], "latent_image": ["12", 0],
            "seed": seed, "steps": 8, "cfg": 1.5, "sampler_name": "res_2s_ode", "scheduler": "kl_optimal", "denoise": 1
        }},
        "3": {"class_type": "VAEDecode", "inputs": {"samples": ["11", 0], "vae": ["16", 0]}},
        "2": {"class_type": "ImageScaleToTotalPixels", "inputs": {"image": ["3", 0], "upscale_method": "lanczos", "megapixels": 1.0, "resolution_steps": 1}},
        "20": {"class_type": "SaveImage", "inputs": {"images": ["2", 0], "filename_prefix": f"zimg_{char_id}_{expression}"}},
    }


def submit_and_wait(prompt, timeout=180):
    body = json.dumps({"prompt": prompt}).encode("utf-8")
    req = urllib.request.Request(f"{COMFY_BASE}/api/prompt", data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"  ❌ HTTP {e.code}: {e.read().decode()[:300]}", flush=True)
        return None

    pid = result["prompt_id"]
    print(f"  prompt_id={pid}", flush=True)

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            req = urllib.request.Request(f"{COMFY_BASE}/history/{pid}")
            with urllib.request.urlopen(req, timeout=30) as resp:
                history = json.loads(resp.read())
            if pid in history:
                data = history[pid]
                s = data["status"]["status_str"]
                if s == "error":
                    for m in data["status"].get("messages", []):
                        if m[0] == "execution_error":
                            print(f"  ❌ {m[1].get('exception_message','unknown')}", flush=True)
                    return None
                if s == "success":
                    # Get output images from node 20
                    for out_data in data.get("outputs", {}).values():
                        for val in out_data.values():
                            if isinstance(val, list) and val and isinstance(val[0], dict) and "filename" in val[0]:
                                return val
            time.sleep(3)
        except Exception as e:
            print(f"  poll: {e}", flush=True)
            time.sleep(5)
    print(f"  ⏰ timeout", flush=True)
    return None


def run(char_id, expression):
    key = f"{char_id}_{expression}"
    prompt_text = PROMPTS.get(key)
    if not prompt_text:
        print(f"  ⚠ no prompt for {key}", flush=True)
        return False

    # Skip if already exists
    dst = os.path.join(ASSETS_DIR, char_id, f"{expression}.png")
    if os.path.exists(dst) and expression != "default":
        print(f"  ⏭ {key}.png 已存在", flush=True)
        return True

    seed = abs(hash(key)) % (2**31)
    prompt = make_zimage_prompt(prompt_text, char_id, expression, seed)

    result = submit_and_wait(prompt)
    if not result:
        return False

    for img in result:
        fname = img.get("filename", "")
        if fname.endswith((".png", ".jpg", ".jpeg")):
            src = os.path.join(OUTPUT_DIR, fname)
            if os.path.exists(src):
                os.makedirs(os.path.join(ASSETS_DIR, char_id), exist_ok=True)
                shutil.copy2(src, dst)
                print(f"  ✅ {key}.png ({os.path.getsize(src)//1024}KB)", flush=True)
                return True

    print(f"  ❌ no output file", flush=True)
    return False


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="只测试一张")
    parser.add_argument("--char", type=str)
    parser.add_argument("--expr", type=str)
    args = parser.parse_args()

    chars = CHARACTERS
    if args.char:
        chars = [c for c in chars if c == args.char]
    exprs = EXPRESSIONS
    if args.expr:
        exprs = [e for e in exprs if e == args.expr]
        if "default" not in exprs:
            exprs = ["default"] + exprs  # always generate default first for reference

    if args.test:
        exprs = ["default"]

    ok, fail = 0, 0
    for cid in chars:
        for expr in exprs:
            if run(cid, expr):
                ok += 1
            else:
                fail += 1
            time.sleep(2)

    print(f"\n{'='*40}")
    print(f"完成! 成功={ok} 失败={fail}")
    print(f"{'='*40}", flush=True)
