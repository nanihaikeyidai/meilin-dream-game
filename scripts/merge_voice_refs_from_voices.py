#!/usr/bin/env python3
"""
【已废弃】旧方案：从 assets/voices/ 合并参考音。
请改用按剧本目录 + 约 50 字 bootstrap：
  python scripts/generate_voice_refs.py --template changan-moon

原逻辑：将 frontend/assets/voices/ 合并到 voice_refs/{charId}.wav。

优先合并 mood 样本（warm / happy / sad），再合并对局缓存（{turn}_{page}）。

用法:
  python scripts/merge_voice_refs_from_voices.py
  python scripts/merge_voice_refs_from_voices.py --char xieyunlan
  python scripts/merge_voice_refs_from_voices.py --max-duration 20
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
sys.path.insert(0, str(FRONTEND))

from tts_voice_config import CHARACTER_IDS  # noqa: E402

VOICE_DIR = FRONTEND / "assets" / "voices"
VOICE_REF_DIR = FRONTEND / "assets" / "voice_refs"

MOOD_PRIORITY = ["warm", "happy", "sad", "neutral", "angry", "cold", "surprised", "blush"]
GAME_KEY_RE = re.compile(r"^(\d+)_(\d+)$")
DEFAULT_GAP_SEC = 0.12
DEFAULT_MAX_DURATION = 25.0


def _read_mono(path: Path) -> tuple[np.ndarray, int]:
    data, sr = sf.read(str(path), dtype="float32", always_2d=False)
    if data.ndim > 1:
        data = data.mean(axis=1)
    return data, sr


def _sort_key_for_stem(stem_suffix: str) -> tuple[int, int, str]:
    if stem_suffix in MOOD_PRIORITY:
        return (0, MOOD_PRIORITY.index(stem_suffix), stem_suffix)
    m = GAME_KEY_RE.match(stem_suffix)
    if m:
        turn, page = int(m.group(1)), int(m.group(2))
        return (1, turn * 1000 + page, stem_suffix)
    return (2, 9999, stem_suffix)


def collect_voice_files(char_id: str, voice_dir: Path) -> list[Path]:
    prefix = f"{char_id}_"
    items: list[tuple[tuple[int, int, str], Path]] = []
    for path in voice_dir.glob(f"{prefix}*.wav"):
        suffix = path.stem[len(prefix) :]
        if not suffix:
            continue
        items.append((_sort_key_for_stem(suffix), path))
    items.sort(key=lambda x: x[0])
    return [p for _, p in items]


def merge_wavs(
    paths: list[Path],
    gap_sec: float = DEFAULT_GAP_SEC,
    max_duration: float = DEFAULT_MAX_DURATION,
) -> tuple[np.ndarray, int, list[str]]:
    if not paths:
        raise ValueError("no input wav files")

    segments: list[np.ndarray] = []
    used_names: list[str] = []
    sample_rate: int | None = None
    gap_samples = 0

    for path in paths:
        audio, sr = _read_mono(path)
        if sample_rate is None:
            sample_rate = sr
            gap_samples = int(sr * gap_sec)
        elif sr != sample_rate:
            # 简单重采样：按长度比例（voices 目录应同为 48k）
            ratio = sample_rate / sr
            new_len = int(len(audio) * ratio)
            audio = np.interp(
                np.linspace(0, len(audio) - 1, new_len),
                np.arange(len(audio)),
                audio,
            ).astype(np.float32)

        dur_so_far = sum(len(s) for s in segments) / sample_rate + len(segments) * gap_sec
        seg_dur = len(audio) / sample_rate
        if dur_so_far + seg_dur > max_duration:
            break

        if segments and gap_samples > 0:
            segments.append(np.zeros(gap_samples, dtype=np.float32))
        segments.append(audio)
        used_names.append(path.name)

    assert sample_rate is not None
    merged = np.concatenate(segments) if segments else np.array([], dtype=np.float32)

    # 峰值归一化，避免拼接后削波
    peak = np.max(np.abs(merged)) if merged.size else 0.0
    if peak > 0.98:
        merged = merged * (0.98 / peak)

    return merged, sample_rate, used_names


def merge_character(
    char_id: str,
    voice_dir: Path,
    ref_dir: Path,
    gap_sec: float,
    max_duration: float,
    dry_run: bool,
) -> bool:
    paths = collect_voice_files(char_id, voice_dir)
    if not paths:
        print(f"[merge] skip {char_id}: no files in {voice_dir}", flush=True)
        return False

    merged, sr, used = merge_wavs(paths, gap_sec=gap_sec, max_duration=max_duration)
    duration = len(merged) / sr
    out_path = ref_dir / f"{char_id}.wav"

    print(f"[merge] {char_id}: {len(used)} clips → {duration:.2f}s → {out_path.name}", flush=True)
    for name in used:
        print(f"         + {name}", flush=True)

    if dry_run:
        return True

    ref_dir.mkdir(parents=True, exist_ok=True)
    sf.write(str(out_path), merged, sr)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge per-character voice clips into voice_refs")
    parser.add_argument("--char", action="append", help="Only merge these character ids (repeatable)")
    parser.add_argument("--gap", type=float, default=DEFAULT_GAP_SEC, help="Silence between clips (seconds)")
    parser.add_argument("--max-duration", type=float, default=DEFAULT_MAX_DURATION, help="Max merged length")
    parser.add_argument("--voices-dir", type=Path, default=VOICE_DIR)
    parser.add_argument("--out-dir", type=Path, default=VOICE_REF_DIR)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.voices_dir.is_dir():
        print(f"[merge] voices dir not found: {args.voices_dir}", flush=True)
        return 1

    char_ids = args.char if args.char else list(CHARACTER_IDS)
    ok = 0
    for char_id in char_ids:
        if merge_character(
            char_id,
            args.voices_dir,
            args.out_dir,
            gap_sec=args.gap,
            max_duration=args.max_duration,
            dry_run=args.dry_run,
        ):
            ok += 1

    print(f"[merge] Done ({ok}/{len(char_ids)}). Restart server_tts.py if it is running.", flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
