#!/usr/bin/env python3
"""
为月下长安 6 角色生成 VoxCPM2 参考音（Voice Design bootstrap → voice_refs/*.wav）

用法:
  python scripts/generate_voice_refs.py
  python scripts/generate_voice_refs.py --force   # 覆盖已有参考音
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

from tts_voice_config import (
    CHARACTER_IDS,
    DESIGN_GEN_KWARGS,
    get_ref_sample_line,
    get_voice_desc,
)

MODEL_PATH = os.environ.get(
    "VOXCPM2_PATH",
    r"F:\ComfyUI_V6.0\ComfyUI-WorkFisher-V2\ComfyUI\models\VoxCPM2",
)
VOICE_REF_DIR = FRONTEND / "assets" / "voice_refs"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate VoxCPM2 voice reference WAVs")
    parser.add_argument("--force", action="store_true", help="Overwrite existing refs")
    args = parser.parse_args()

    VOICE_REF_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[refs] Loading VoxCPM2 from {MODEL_PATH}", flush=True)
    from voxcpm.core import VoxCPM

    model = VoxCPM(
        voxcpm_model_path=MODEL_PATH,
        zipenhancer_model_path=None,
        enable_denoiser=False,
        optimize=True,
    )
    sample_rate = getattr(model.tts_model, "sample_rate", 48000)

    for char_id in CHARACTER_IDS:
        out_path = VOICE_REF_DIR / f"{char_id}.wav"
        if out_path.exists() and not args.force:
            print(f"[refs] skip {char_id} (exists, use --force to overwrite)", flush=True)
            continue

        line = get_ref_sample_line(char_id)
        voice_desc = get_voice_desc(char_id, "neutral")
        full_text = f"{voice_desc}{line}"
        print(f"[refs] design {char_id}: {full_text}", flush=True)

        audio: np.ndarray = model.generate(
            text=full_text,
            normalize=False,
            **DESIGN_GEN_KWARGS,
        )
        sf.write(str(out_path), audio, sample_rate)
        duration = len(audio) / sample_rate
        print(f"[refs] saved {out_path.name} ({duration:.2f}s)", flush=True)

    print(f"[refs] Done. Files in {VOICE_REF_DIR}", flush=True)
    print("[refs] Tip: delete frontend/assets/voices/*.wav to clear old dialogue cache.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
