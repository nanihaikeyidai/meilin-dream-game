#!/usr/bin/env python3
"""
按剧本为各角色生成 VoxCPM2 参考音（约 50 字文案 → 目标 ~20s）。

输出: frontend/assets/tts/{templateId}/voice_refs/{charId}.wav

用法:
  python scripts/generate_voice_refs.py --template changan-moon
  python scripts/generate_voice_refs.py --all
  python scripts/generate_voice_refs.py --all --force
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
sys.path.insert(0, str(FRONTEND))

import numpy as np
import soundfile as sf

from tts_paths import ensure_template_dirs, voice_ref_path
from tts_templates import ALL_TEMPLATE_IDS, get_template_config
from tts_voice_config import REF_GEN_KWARGS, get_ref_sample_line, get_voice_desc

MODEL_PATH = os.environ.get(
    "VOXCPM2_PATH",
    r"F:\ComfyUI_V6.0\ComfyUI-WorkFisher-V2\ComfyUI\models\VoxCPM2",
)

TARGET_DURATION_MIN = 15.0
TARGET_DURATION_MAX = 25.0


def generate_for_template(model, sample_rate: int, template_id: str, force: bool) -> int:
    cfg = get_template_config(template_id)
    ensure_template_dirs(template_id)
    done = 0

    print(f"\n[refs] === {template_id} ({len(cfg.CHARACTER_IDS)} roles) ===", flush=True)

    for char_id in cfg.CHARACTER_IDS:
        out_path = voice_ref_path(template_id, char_id)
        if out_path.exists() and not force:
            print(f"[refs] skip {template_id}/{char_id} (exists)", flush=True)
            continue

        line = get_ref_sample_line(char_id, template_id)
        char_len = len(line.replace(" ", "").replace("\n", ""))
        voice_desc = get_voice_desc(char_id, "neutral", template_id)
        full_text = f"{voice_desc}{line}"
        print(f"[refs] {char_id} ({char_len}字): {line[:36]}…", flush=True)

        audio: np.ndarray = model.generate(
            text=full_text,
            normalize=False,
            **REF_GEN_KWARGS,
        )
        sf.write(str(out_path), audio, sample_rate)
        duration = len(audio) / sample_rate
        flag = ""
        if duration < TARGET_DURATION_MIN:
            flag = " [short]"
        elif duration > TARGET_DURATION_MAX:
            flag = " [long]"
        print(f"[refs] saved {out_path.relative_to(FRONTEND)} ({duration:.2f}s){flag}", flush=True)
        done += 1

    return done


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate per-character TTS reference WAVs by template")
    parser.add_argument("--template", help="Single template id")
    parser.add_argument("--all", action="store_true", help="All registered templates")
    parser.add_argument("--force", action="store_true", help="Overwrite existing refs")
    args = parser.parse_args()

    if args.all:
        template_ids = list(ALL_TEMPLATE_IDS)
    elif args.template:
        template_ids = [args.template]
    else:
        template_ids = ["changan-moon"]

    if not Path(MODEL_PATH).exists():
        print(f"[refs] ERROR: VoxCPM2 model not found: {MODEL_PATH}", flush=True)
        print("[refs] Set VOXCPM2_PATH and ensure TTS server deps installed.", flush=True)
        return 1

    print(f"[refs] Loading VoxCPM2 from {MODEL_PATH}", flush=True)
    from voxcpm.core import VoxCPM

    model = VoxCPM(
        voxcpm_model_path=MODEL_PATH,
        zipenhancer_model_path=None,
        enable_denoiser=False,
        optimize=True,
    )
    sample_rate = getattr(model.tts_model, "sample_rate", 48000)

    total = 0
    for tid in template_ids:
        total += generate_for_template(model, sample_rate, tid, args.force)

    print(f"\n[refs] Done. Generated/updated {total} file(s) under assets/tts/", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
