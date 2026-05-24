#!/usr/bin/env python3
"""
月下长安 — 6角色×3语气 TTS 音色批量生成脚本
迭代3 任务3.6：生成18个组合音色文件

服务器：127.0.0.1:7860 (VoxCPM2)
输出（调试样本，可选）：assets/tts/changan-moon/cache/{charId}_{mood}.wav

用法：
  python frontend/generate_voice_bank.py          # 生成全部18个
  python frontend/generate_voice_bank.py --dry-run # 打印参数不调用API
  python frontend/generate_voice_bank.py --single xieyunlan warm  # 仅生成一个组合

正式参考音请用：
  python scripts/generate_voice_refs.py --template changan-moon
"""

import json
import os
import sys
import time
import http.client
import argparse
from pathlib import Path

# ── 配置 ──────────────────────────────────────────────────────
TTS_HOST = "127.0.0.1:7860"
FRONTEND = Path(__file__).resolve().parent
sys.path.insert(0, str(FRONTEND))
from tts_paths import cache_dir, ensure_template_dirs  # noqa: E402

TEMPLATE_ID = "changan-moon"
VOICE_DIR = cache_dir(TEMPLATE_ID)
ensure_template_dirs(TEMPLATE_ID)

# 3种选定语气（PRD建议：warm / happy / sad）
SELECTED_MOODS = ["warm", "happy", "sad"]

# API超时（秒）
API_TIMEOUT = 60


# ── 6角色×3语气 测试例句 ────────────────────────────────────
# 每句都是古风情境台词，包含MOOD标签，适合对应角色身份
TEST_LINES: dict[str, dict[str, str]] = {
    # ===== 谢云岚 — 冷峻青年男声，沉稳低沉 =====
    "xieyunlan": {
        "warm":  "你放心，有我在，不会让你受半分委屈。",       # 温柔坚定
        "happy": "今日天色晴好，倒是个难得的舒心日子。",       # 难得愉悦
        "sad":   "故人旧事，终究是回不去了……你说得对。",       # 沉郁悲凉
    },
    # ===== 花映月 — 年轻女声，妩媚柔美 =====
    "huayingyue": {
        "warm":  "夜深露重，公子披件衣裳再走罢，仔细着凉。",   # 温柔体贴
        "happy": "今儿个灯市可热闹了，快陪我逛逛去！",         # 欢快雀跃
        "sad":   "这满城烟火，终究没一盏灯是等我回家的。",     # 凄楚落寞
    },
    # ===== 顾千帆 — 洒脱青年男声，明朗随性 =====
    "guqianfan": {
        "warm":  "别急，慢慢说，我听着呢。天塌下来也有我顶着。", # 爽朗耐心
        "happy": "好酒！痛快！来来来，再给你满上一杯！",        # 豪爽大笑
        "sad":   "这一壶太雕，敬那些再也回不来的人罢。",       # 低沉隐忍
    },
    # ===== 沈明月 — 英气女声，清越爽利 =====
    "shenmingyue": {
        "warm":  "你手这样凉，可是穿得太少了？我这个手炉给你。", # 难得柔和
        "happy": "查到了！果然不出我所料——走，抓人去了！",    # 爽朗明亮
        "sad":   "我查了三年，真相竟是如此……让我静一静。",    # 沉重不甘
    },
    # ===== 李怀瑾 — 温雅青年男声，如玉温润 =====
    "lihuaijin": {
        "warm":  "不妨事，慢慢来。无论多久，我都等你。",         # 如玉温润
        "happy": "这曲子我练了些时日，你听听可好？",             # 含笑谦和
        "sad":   "原来这世间最苦，不是求不得，而是已失去。",     # 低沉哀伤
    },
    # ===== 公孙兰 — 沉稳中年女声，平和从容 =====
    "gongsunlan": {
        "warm":  "孩子，这些年你受苦了。回来了就好，回来了就好。", # 慈和温厚
        "happy": "哟，今日这是吹了什么风，你竟也学会哄人开心了。", # 含笑欣慰
        "sad":   "当年的事，我一直没敢告诉你……是我不对。",       # 沉重叹息
    },
}


# ── API 调用 ──────────────────────────────────────────────────
def call_tts(char_id: str, text: str, mood: str, index: int) -> bytes:
    """调用 TTS API，返回 WAV 二进制数据"""
    payload = json.dumps({
        "templateId": TEMPLATE_ID,
        "charId": char_id,
        "text": text,
        "mood": mood,
        "turnCount": index,   # 用index作为区分，避免缓存冲突
        "pageIdx": 0,
    })
    conn = http.client.HTTPConnection(TTS_HOST, timeout=API_TIMEOUT)
    try:
        conn.request("POST", "/tts", body=payload, headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status}: {resp.read().decode('utf-8', errors='replace')}")
        return resp.read()
    finally:
        conn.close()


def generate_one(char_id: str, mood: str, text: str, index: int, dry_run: bool = False) -> Path:
    """生成一个音色文件并保存"""
    output_name = f"{char_id}_{mood}.wav"
    output_path = VOICE_DIR / output_name

    if not dry_run and output_path.exists():
        print(f"  ⏭  SKIP (已存在): {output_name}")
        return output_path

    print(f"\n  ▶  {char_id} / {mood}")
    print(f"     台词: 「{text}」")

    if dry_run:
        api_call = f"POST /tts {json.dumps({'charId': char_id, 'text': text, 'mood': mood, 'turnCount': index, 'pageIdx': 0})}"
        print(f"     API: {api_call}")
        return output_path

    # 调用TTS API
    wav_data = call_tts(char_id, text, mood, index)
    output_path.write_bytes(wav_data)
    size_kb = len(wav_data) / 1024
    print(f"     ✅ 已保存: {output_name} ({size_kb:.1f} KB)")
    return output_path


# ── 主流程 ──────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="月下长安 TTS 音色批量生成")
    parser.add_argument("--dry-run", action="store_true", help="仅打印参数，不调用API")
    parser.add_argument("--single", nargs=2, metavar=("CHAR", "MOOD"),
                        help="仅生成单个组合，如 --single xieyunlan warm")
    args = parser.parse_args()

    # 确定生成清单
    targets = []
    if args.single:
        char_id, mood = args.single
        if char_id not in TEST_LINES:
            print(f"❌ 未知角色: {char_id} (可选: {', '.join(TEST_LINES.keys())})")
            sys.exit(1)
        if mood not in SELECTED_MOODS:
            print(f"❌ 未知语气: {mood} (可选: {', '.join(SELECTED_MOODS)})")
            sys.exit(1)
        targets.append((char_id, mood, TEST_LINES[char_id][mood]))
    else:
        for char_id, moods in TEST_LINES.items():
            for mood in SELECTED_MOODS:
                targets.append((char_id, mood, moods[mood]))

    total = len(targets)
    print(f"{'='*60}")
    print(f"  月下长安 — TTS 音色批量生成")
    print(f"  6角色 × {len(SELECTED_MOODS)}语气 = {total} 组合")
    print(f"  TTS: http://{TTS_HOST}")
    print(f"  输出: {VOICE_DIR}")
    if args.dry_run:
        print(f"  [DRY RUN 模式 — 不会调用API]")
    print(f"{'='*60}")

    # 逐个生成
    success = 0
    fail = 0
    for i, (char_id, mood, text) in enumerate(targets, 1):
        try:
            print(f"\n[{i}/{total}]", end="")
            generate_one(char_id, mood, text, i, dry_run=args.dry_run)
            success += 1
            # 如果非dry-run且非最后一个，短暂间隔防止过载
            if not args.dry_run and i < total:
                time.sleep(0.5)
        except Exception as e:
            print(f"\n  ❌ 失败: {e}")
            fail += 1

    # 总结
    print(f"\n{'='*60}")
    if args.dry_run:
        print(f"  DRY RUN 完成 — 共列出 {total} 个组合（未调用API）")
    else:
        print(f"  生成完成: ✅ {success} 成功, ❌ {fail} 失败")
        if success == total:
            print(f"\n  所有 {total} 个音色文件已保存至:")
            print(f"    {VOICE_DIR}")
            print(f"\n  文件名格式: {VOICE_DIR}/{{charId}}_{{mood}}.wav")
            print(f"  例如: xieyunlan_warm.wav, huayingyue_happy.wav, ...")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
