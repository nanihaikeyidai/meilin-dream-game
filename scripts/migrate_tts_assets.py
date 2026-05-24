#!/usr/bin/env python3
"""将旧版 assets/voice_refs/*.wav 迁移到 assets/tts/{template}/voice_refs/。"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
sys.path.insert(0, str(FRONTEND))

from tts_paths import LEGACY_VOICE_REF_DIR, ensure_template_dirs, voice_ref_path  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", default="changan-moon")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    legacy = LEGACY_VOICE_REF_DIR
    if not legacy.is_dir():
        print(f"[migrate] no legacy dir: {legacy}", flush=True)
        return 0

    ensure_template_dirs(args.template)
    moved = 0
    for src in sorted(legacy.glob("*.wav")):
        dst = voice_ref_path(args.template, src.stem)
        if dst.exists() and not args.force:
            print(f"[migrate] skip {src.name} (dst exists)", flush=True)
            continue
        shutil.copy2(src, dst)
        print(f"[migrate] {src.name} → {dst.relative_to(FRONTEND)}", flush=True)
        moved += 1

    print(f"[migrate] {moved} file(s). Re-run generate_voice_refs.py --force for ~50字 refs.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
