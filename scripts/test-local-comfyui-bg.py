#!/usr/bin/env python3
"""验证本地 ComfyUI zImage 工作流生成背景图的全链路"""
import json, urllib.request, time, sys, os

COMFYUI_URL = "http://192.168.1.2:8188"
OUTPUT_DIR = "/mnt/d/Hermes/girlgame-skill/frontend/assets/backgrounds/ancient"

# 古风场景 prompt（无人物，纯场景）
SCENE_PROMPT = (
    "night view of ancient Chang'an city, full moon, "
    "traditional rooftops, lanterns lit across the city, "
    "river reflecting moonlight, peaceful and romantic, "
    "anime style background, no characters, epic scenery"
)
STYLE_PROMPT = (
    "masterpiece, best quality, intricate detail, "
    "warm color palette, moonlight atmosphere, "
    "Chinese ink painting influence, cinematic lighting"
)

def build_prompt():
    """构建 zImage 工作流 API prompt"""
    return {
        "8": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "qwen_image", "device": "default"}},
        "18": {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_bf16.safetensors", "weight_dtype": "default"}},
        "14": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["18", 0], "lora_name": "Kook_Zimage_瑶光.safetensors", "strength_model": 0.4}},
        "13": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["14", 0], "lora_name": "Kook_Zimage_如梦似幻.safetensors", "strength_model": 0.7}},
        "15": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["13", 0], "lora_name": "Z-Image-Fun-Lora-Distill-8-Steps-2603-ComfyUI.safetensors", "strength_model": 0.5}},
        "16": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
        "27": {"class_type": "CR Text", "inputs": {"text": SCENE_PROMPT}},
        "6": {"class_type": "CR Text", "inputs": {"text": STYLE_PROMPT}},
        "17": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["8", 0], "text": ["27", 0]}},
        "10": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["8", 0], "text": "worst quality, low quality, blurry, distortion, text, watermark, signature, person, human, face, character, nsfw, deformed, bad anatomy"}},
        "25": {"class_type": "INTConstant", "inputs": {"value": 1344}},
        "26": {"class_type": "INTConstant", "inputs": {"value": 768}},
        "12": {"class_type": "EmptyLatentImage", "inputs": {"width": ["25", 0], "height": ["26", 0], "batch_size": 1}},
        "11": {"class_type": "KSampler", "inputs": {
            "model": ["15", 0], "positive": ["17", 0], "negative": ["10", 0],
            "latent_image": ["12", 0],
            "seed": 323252007, "steps": 8, "cfg": 1,
            "sampler_name": "res_2s_ode", "scheduler": "kl_optimal", "denoise": 1
        }},
        "3": {"class_type": "VAEDecode", "inputs": {"samples": ["11", 0], "vae": ["16", 0]}},
        "2": {"class_type": "ImageScaleToTotalPixels", "inputs": {"image": ["3", 0], "upscale_method": "lanczos", "megapixels": 0.5, "resolution_steps": 1}},
        "20": {"class_type": "SaveImage", "inputs": {"images": ["2", 0], "filename_prefix": "ComfyUI"}},
    }

def queue_prompt(prompt):
    body = json.dumps({"prompt": prompt}).encode()
    req = urllib.request.Request(f"{COMFYUI_URL}/api/prompt", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["prompt_id"]

def get_result(prompt_id, timeout=60):
    deadline = time.time() + timeout
    while time.time() < deadline:
        req = urllib.request.Request(f"{COMFYUI_URL}/history/{prompt_id}")
        with urllib.request.urlopen(req) as resp:
            history = json.loads(resp.read())
        if prompt_id in history:
            return history[prompt_id]
        time.sleep(2)
    raise TimeoutError("ComfyUI timeout")

def download_image(filename, output_path):
    """从 ComfyUI output 下载图片"""
    req = urllib.request.Request(f"{COMFYUI_URL}/api/view?filename={filename}&type=output&subfolder=")
    with urllib.request.urlopen(req) as resp:
        data = resp.read()
    with open(output_path, "wb") as f:
        f.write(data)
    return len(data)

def main():
    print("🚀 构建 zImage 工作流 prompt...")
    prompt = build_prompt()

    print("📤 提交到 ComfyUI...")
    prompt_id = queue_prompt(prompt)
    print(f"   Prompt ID: {prompt_id}")

    print("⏳ 等待生成...")
    result = get_result(prompt_id, 60)
    outputs = result.get("outputs", {})

    # 从 SaveImage 节点取输出
    saved_files = []
    for node_id, node_out in outputs.items():
        if "images" in node_out:
            for img in node_out["images"]:
                saved_files.append(img["filename"])
                print(f"   ✅ 生成: {img['filename']} ({img.get('type','')})")

    if not saved_files:
        print("❌ 没有生成图片")
        print(json.dumps(result, indent=2))
        sys.exit(1)

    # 下载到目标目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for fname in saved_files:
        outpath = os.path.join(OUTPUT_DIR, "moonlit_city_test.png")
        size = download_image(fname, outpath)
        print(f"📥 下载到: {outpath} ({size/1024:.0f} KB)")

    print("\n🎉 测试完成！")

if __name__ == "__main__":
    main()
