#!/usr/bin/env python3
"""
Batch Qwen Edit + rembg pipeline for AVG game character portraits.
Generates expression + pose variations from default.png using Qwen Image Edit,
then applies rembg for transparent RGBA background.

Usage:
  python batch_qwen_edit_expressions.py                          # process all
  python batch_qwen_edit_expressions.py --script campus-summer   # single script
  python batch_qwen_edit_expressions.py --char chengnianci       # single character
  python batch_qwen_edit_expressions.py --test                   # test 1 expression
  python batch_qwen_edit_expressions.py --force                  # regenerate existing
"""

import json
import os
import shutil
import sys
import time
import urllib.request
import random

# ============================================================
# CONFIG
# ============================================================
COMFY_BASE = "http://192.168.1.2:8188"
COMFY_INPUT = r"F:\ComfyUI_V6.0\ComfyUI-WorkFisher-V2\ComfyUI\input"
COMFY_OUTPUT = r"F:\ComfyUI_V6.0\ComfyUI-WorkFisher-V2\ComfyUI\output"
PORTRAITS_ROOT = r"D:\HermesWorkspace\girlgame-skill\frontend\assets\portraits"

SCRIPTS = {
    "campus-summer": [
        "chengnianci", "jiangxiaoyu", "linxue", "shenqingci",
        "suyunxi", "xiazhiyao", "yexiaoman",
    ],
    "changan-moon": [
        "gongsunlan", "guqianfan", "huayingyue", "lihuaijin",
        "shenmingyue", "xieyunlan",
    ],
    "cafe-night": [
        "gunian", "linyu", "qinyutong", "suwan",
        "zhaozhu", "zhoudoctor",
    ],
    "suspense-mansion": [
        "chenwu", "gunianan", "jingzhongren", "linyingxue",
        "suwanqing", "zhaomingshen",
    ],
}

EXPRESSIONS = ["default", "smile", "happy", "sad", "angry", "blush", "cold", "surprised"]

EDIT_PROMPTS = {
    "happy": (
        "big happy smile, head tilts slightly to the left, "
        "shoulders relax and shift subtly"
    ),
    "smile": (
        "gentle soft smile, head tilted slightly right, "
        "eyes slightly narrowed, one hand touching hair lightly"
    ),
    "sad": (
        "sad expression with downcast eyes, head lowered slightly, "
        "shoulders hunched, looking down at the ground"
    ),
    "angry": (
        "angry glare, head turned slightly to the right, "
        "arms crossed, eyebrows furrowed"
    ),
    "blush": (
        "shy blushing expression, looking away to the side with "
        "flushed cheeks, hands touching face"
    ),
    "cold": (
        "cold indifferent expression, chin slightly raised, "
        "eyes half-lidded, looking down at viewer"
    ),
    "surprised": (
        "surprised wide-eyed expression, stepping back slightly, "
        "one hand raised to mouth, eyebrows raised"
    ),
}

KEEP_SUFFIX = ", keep face shape, hairstyle, clothes, accessories, background exactly the same"

MAX_RETRIES = 2
POLL_INTERVAL = 3


# ============================================================
# COMFYUI HELPERS
# ============================================================
def _queue_prompt(workflow):
    body = json.dumps({"prompt": workflow}).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFY_BASE}/api/prompt",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"  [ERROR] HTTP {e.code}: {err_body[:300]}", flush=True)
        return None
    except Exception as e:
        print(f"  [ERROR] queue: {e}", flush=True)
        return None
    return result.get("prompt_id")


def _poll_history(prompt_id, timeout=300):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            req = urllib.request.Request(f"{COMFY_BASE}/history/{prompt_id}")
            with urllib.request.urlopen(req, timeout=30) as resp:
                history = json.loads(resp.read())
        except Exception as e:
            print(f"  [WARN] poll: {e}", flush=True)
            time.sleep(POLL_INTERVAL * 2)
            continue

        if prompt_id not in history:
            time.sleep(POLL_INTERVAL)
            continue

        data = history[prompt_id]
        status = data["status"]["status_str"]

        if status == "error":
            for msg in data["status"].get("messages", []):
                if msg[0] == "execution_error":
                    exc = msg[1].get("exception_message", "unknown")
                    print(f"  [ERROR] execution: {exc}", flush=True)
            return None

        if status == "success":
            return data

        time.sleep(POLL_INTERVAL)

    print(f"  [ERROR] timeout after {timeout}s", flush=True)
    return None


def _find_output_file(history_data, save_node_id=170, prefix="qwen_batch"):
    outputs = history_data.get("outputs", {})
    node_out = outputs.get(str(save_node_id), {})
    for key, val in node_out.items():
        if isinstance(val, list):
            for item in val:
                if isinstance(item, dict) and "filename" in item:
                    return item["filename"]
    return None


def _find_rembg_output(history_data, save_node_id=3, prefix="rembg_batch"):
    return _find_output_file(history_data, save_node_id, prefix)


def _copy_to_input(src_path, dest_name):
    """Copy a file to ComfyUI input directory."""
    os.makedirs(COMFY_INPUT, exist_ok=True)
    dst = os.path.join(COMFY_INPUT, dest_name)
    shutil.copy2(src_path, dst)
    return dest_name


# ============================================================
# WORKFLOW BUILDERS
# ============================================================
def build_qwen_workflow(input_image_name, edit_prompt, seed):
    """Build Qwen Image Edit workflow JSON."""
    full_prompt = edit_prompt + KEEP_SUFFIX
    return {
        "161": {
            "class_type": "UNETLoader",
            "inputs": {"unet_name": "qwen_image_edit_2511_fp8mixed.safetensors", "weight_dtype": "default"},
        },
        "145": {
            "class_type": "ModelSamplingAuraFlow",
            "inputs": {"model": ["161", 0], "shift": 1.73},
        },
        "153": {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "model": ["145", 0],
                "lora_name": "Qwen\\Qwen-Image-Edit-2511-Lightning-4steps-V1.0-fp32.safetensors",
                "strength_model": 1.0,
            },
        },
        "152": {
            "class_type": "CFGNorm",
            "inputs": {"model": ["153", 0], "strength": 1.0},
        },
        "162": {
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name": "qwen_2.5_vl_7b_fp8_scaled.safetensors",
                "type": "qwen_image",
            },
        },
        "146": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": "qwen_image_vae.safetensors"},
        },
        "219": {
            "class_type": "LoadImage",
            "inputs": {"image": input_image_name},
        },
        "160": {
            "class_type": "FluxKontextImageScale",
            "inputs": {"image": ["219", 0]},
        },
        "156": {
            "class_type": "VAEEncode",
            "inputs": {"pixels": ["160", 0], "vae": ["146", 0]},
        },
        "149": {
            "class_type": "TextEncodeQwenImageEditPlus",
            "inputs": {
                "clip": ["162", 0],
                "vae": ["146", 0],
                "image1": ["219", 0],
                "prompt": full_prompt,
            },
        },
        "151": {
            "class_type": "TextEncodeQwenImageEditPlus",
            "inputs": {
                "clip": ["162", 0],
                "vae": ["146", 0],
                "image1": ["219", 0],
                "prompt": "",
            },
        },
        "147": {
            "class_type": "FluxKontextMultiReferenceLatentMethod",
            "inputs": {
                "conditioning": ["149", 0],
                "reference_latents_method": "index_timestep_zero",
            },
        },
        "148": {
            "class_type": "FluxKontextMultiReferenceLatentMethod",
            "inputs": {
                "conditioning": ["151", 0],
                "reference_latents_method": "index_timestep_zero",
            },
        },
        "169": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["152", 0],
                "positive": ["147", 0],
                "negative": ["148", 0],
                "latent_image": ["156", 0],
                "seed": seed,
                "steps": 4,
                "cfg": 1,
                "sampler_name": "sa_solver",
                "scheduler": "beta",
                "denoise": 1.0,
            },
        },
        "157": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["169", 0], "vae": ["146", 0]},
        },
        "170": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["157", 0],
                "filename_prefix": "qwen_batch",
            },
        },
    }


def build_rembg_workflow(input_image_name):
    """Build rembg workflow JSON."""
    return {
        "1": {
            "class_type": "LoadImage",
            "inputs": {"image": input_image_name},
        },
        "2": {
            "class_type": "Image Rembg (Remove Background)",
            "inputs": {
                "images": ["1", 0],
                "transparency": True,
                "model": "u2net",
                "post_processing": False,
                "only_mask": False,
                "alpha_matting": False,
                "alpha_matting_foreground_threshold": 240,
                "alpha_matting_background_threshold": 10,
                "alpha_matting_erode_size": 10,
                "background_color": "none",
            },
        },
        "3": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["2", 0],
                "filename_prefix": "rembg_batch",
            },
        },
    }


# ============================================================
# PIPELINE STEPS
# ============================================================
def run_qwen_edit(src_image_path, edit_prompt, seed):
    """Run Qwen Edit on src_image_path and return path to output file."""
    input_name = f"qwen_src_{seed}.png"
    _copy_to_input(src_image_path, input_name)

    workflow = build_qwen_workflow(input_name, edit_prompt, seed)
    pid = _queue_prompt(workflow)
    if pid is None:
        return None

    print(f"    prompt_id={pid}", flush=True)
    history = _poll_history(pid)
    if history is None:
        return None

    fname = _find_output_file(history)
    if fname is None:
        print(f"    [ERROR] no output file in history", flush=True)
        return None

    out_path = os.path.join(COMFY_OUTPUT, fname)
    if not os.path.exists(out_path):
        print(f"    [ERROR] output file not found: {out_path}", flush=True)
        return None

    return out_path


def run_rembg(src_image_path):
    """Run rembg on src_image_path and return path to output file."""
    input_name = f"rembg_src_{int(time.time())}.png"
    _copy_to_input(src_image_path, input_name)

    workflow = build_rembg_workflow(input_name)
    pid = _queue_prompt(workflow)
    if pid is None:
        return None

    print(f"    prompt_id={pid}", flush=True)
    history = _poll_history(pid)
    if history is None:
        return None

    fname = _find_rembg_output(history)
    if fname is None:
        print(f"    [ERROR] no rembg output in history", flush=True)
        return None

    out_path = os.path.join(COMFY_OUTPUT, fname)
    if not os.path.exists(out_path):
        print(f"    [ERROR] rembg output not found: {out_path}", flush=True)
        return None

    return out_path


def verify_rgba(png_path):
    """Check that the PNG is RGBA with some transparency. Returns True if valid."""
    try:
        from PIL import Image
        img = Image.open(png_path)
        if img.mode != "RGBA":
            print(f"    [WARN] not RGBA (mode={img.mode}), converting...", flush=True)
            # Convert to RGBA if needed
            if img.mode == "RGB":
                rgba = Image.new("RGBA", img.size)
                rgba.paste(img)
                rgba.save(png_path)
            return True
        # Check for actual transparent pixels
        bbox = img.getbbox()
        if bbox is None:
            print(f"    [WARN] fully transparent image!", flush=True)
            return False
        total_px = img.size[0] * img.size[1]
        opaque_px = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        transparent_pct = (total_px - opaque_px) / total_px * 100
        print(f"    RGBA verified: {img.size[0]}x{img.size[1]}, "
              f"transparent={transparent_pct:.1f}%", flush=True)
        return True
    except ImportError:
        print(f"    [WARN] Pillow not installed, skipping RGBA check", flush=True)
        return True
    except Exception as e:
        print(f"    [ERROR] verify_rgba: {e}", flush=True)
        return False


# ============================================================
# MAIN PROCESSOR
# ============================================================
def process_expression(script_name, char_name, expression, force=False):
    """Process one expression for one character. Returns True on success."""
    char_dir = os.path.join(PORTRAITS_ROOT, script_name, char_name)
    dst_path = os.path.join(char_dir, f"{expression}.png")
    default_path = os.path.join(char_dir, "default.png")

    # Skip if already exists (resume support)
    if not force and os.path.exists(dst_path):
        print(f"    [SKIP] already exists", flush=True)
        return True

    # Check default.png exists
    if not os.path.exists(default_path):
        print(f"    [ERROR] default.png not found for {script_name}/{char_name}", flush=True)
        return False

    # Build edit prompt
    edit_prompt = EDIT_PROMPTS.get(expression)
    if edit_prompt is None:
        print(f"    [SKIP] no edit prompt for {expression}", flush=True)
        return True  # default stays as-is

    # Generate seed from script/char/expr for reproducibility
    seed = abs(hash(f"{script_name}_{char_name}_{expression}")) % (2**31)

    # === Qwen Edit (with retries) ===
    qwen_out = None
    for attempt in range(1, MAX_RETRIES + 2):  # initial + MAX_RETRIES
        print(f"    Qwen Edit (attempt {attempt})...", flush=True)
        qwen_out = run_qwen_edit(default_path, edit_prompt, seed + attempt)
        if qwen_out is not None:
            break
        if attempt <= MAX_RETRIES:
            print(f"    retrying in 5s...", flush=True)
            time.sleep(5)

    if qwen_out is None:
        print(f"    [FAIL] Qwen Edit failed after {MAX_RETRIES + 1} attempts", flush=True)
        return False

    qwen_size = os.path.getsize(qwen_out) // 1024
    print(f"    Qwen output: {os.path.basename(qwen_out)} ({qwen_size}KB)", flush=True)

    # === rembg (with retries) ===
    rembg_out = None
    for attempt in range(1, MAX_RETRIES + 2):
        print(f"    Rembg (attempt {attempt})...", flush=True)
        rembg_out = run_rembg(qwen_out)
        if rembg_out is not None:
            break
        if attempt <= MAX_RETRIES:
            print(f"    retrying in 5s...", flush=True)
            time.sleep(5)

    if rembg_out is None:
        print(f"    [FAIL] rembg failed after {MAX_RETRIES + 1} attempts", flush=True)
        return False

    # === Save to target ===
    os.makedirs(char_dir, exist_ok=True)
    shutil.copy2(rembg_out, dst_path)

    # Verify RGBA
    ok = verify_rgba(dst_path)
    final_size = os.path.getsize(dst_path) // 1024
    print(f"    [{'OK' if ok else 'WARN'}] saved {expression}.png ({final_size}KB)", flush=True)
    return True


def run(script_filter=None, char_filter=None, force=False, test=False):
    """Main batch processing loop."""
    total_expressions = 0
    processed = 0
    ok_count = 0
    fail_count = 0
    skip_count = 0

    # Count total work
    for script_name in SCRIPTS:
        if script_filter and script_name != script_filter:
            continue
        chars = SCRIPTS[script_name]
        for char_name in chars:
            if char_filter and char_name != char_filter:
                continue
            for expr in EXPRESSIONS:
                if test and expr != "smile":
                    continue
                total_expressions += 1

    n = 0
    for script_name, chars in SCRIPTS.items():
        if script_filter and script_name != script_filter:
            continue

        for char_name in chars:
            if char_filter and char_name != char_filter:
                continue

            char_dir = os.path.join(PORTRAITS_ROOT, script_name, char_name)

            for expr in EXPRESSIONS:
                if test and expr != "smile":
                    continue

                n += 1
                dst_path = os.path.join(char_dir, f"{expr}.png")

                # Skip existing if not forced
                if not force and expr != "default" and os.path.exists(dst_path):
                    print(f"[{n}/{total_expressions}] {script_name}/{char_name}/{expr} [SKIP]", flush=True)
                    skip_count += 1
                    continue

                if expr == "default":
                    print(f"[{n}/{total_expressions}] {script_name}/{char_name}/default [SKIP (base)]", flush=True)
                    skip_count += 1
                    continue

                print(f"[{n}/{total_expressions}] {script_name}/{char_name}/{expr}", flush=True)
                processed += 1
                if process_expression(script_name, char_name, expr, force=force):
                    ok_count += 1
                else:
                    fail_count += 1

                # Brief pause between expressions to let ComfyUI breathe
                time.sleep(2)

    # Summary
    print()
    print("=" * 55)
    print(f"  BATCH COMPLETE")
    print(f"  Total expressions: {total_expressions}")
    print(f"  Processed:         {processed}")
    print(f"  Succeeded:         {ok_count}")
    print(f"  Skipped:           {skip_count}")
    print(f"  Failed:            {fail_count}")
    print("=" * 55)
    return fail_count == 0


# ============================================================
# CLI
# ============================================================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Batch Qwen Edit + rembg pipeline for AVG portraits"
    )
    parser.add_argument(
        "--script", type=str, default=None,
        help="Filter: only process this script (e.g. campus-summer)"
    )
    parser.add_argument(
        "--char", type=str, default=None,
        help="Filter: only process this character"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Regenerate existing expressions"
    )
    parser.add_argument(
        "--test", action="store_true",
        help="Test mode: only process one expression (smile)"
    )
    args = parser.parse_args()

    start = time.time()
    success = run(
        script_filter=args.script,
        char_filter=args.char,
        force=args.force,
        test=args.test,
    )
    elapsed = time.time() - start
    print(f"\nElapsed: {elapsed:.0f}s", flush=True)
    sys.exit(0 if success else 1)
