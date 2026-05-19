#!/usr/bin/env python3
"""生成多角色测试对话音频并合并为单个 WAV 文件"""

import json
import wave
import struct
import http.client
import os
import io

TTS_HOST = "192.168.144.1:7860"
OUTPUT_FILE = "/mnt/d/Hermes/test_dialogue_tts.wav"

# 测试对话：谢云岚 & 花映月 — 上元灯夜初遇
DIALOGUE = [
    {
        "charId": "xieyunlan",
        "text": "姑娘请留步。这玉佩上的纹路，似是前朝宫廷之物。",
        "mood": "neutral",
    },
    {
        "charId": "huayingyue",
        "text": "哟，这位公子好眼力。怎么，对一块碎玉也感兴趣？",
        "mood": "happy",
    },
    {
        "charId": "xieyunlan",
        "text": "三年前血月案的卷宗，被人篡改过。而这玉佩，正是关键。",
        "mood": "cold",
    },
    {
        "charId": "huayingyue",
        "text": "……公子这话，可不像是随便说说的。",
        "mood": "surprised",
    },
]


def generate_tts(char_id, text, mood, turn_count, page_idx):
    """调用 TTS API 生成语音，返回 bytes"""
    payload = json.dumps({
        "charId": char_id,
        "text": text,
        "mood": mood,
        "turnCount": turn_count,
        "pageIdx": page_idx,
    })

    conn = http.client.HTTPConnection(TTS_HOST)
    try:
        conn.request("POST", "/tts", body=payload, headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        if resp.status != 200:
            raise RuntimeError(f"TTS API error: {resp.status} {resp.reason}")
        data = resp.read()
        print(f"  Generated: {char_id} '{text[:20]}...' ({len(data)} bytes)")
        return data
    finally:
        conn.close()


def merge_wavs(wav_bytes_list, output_path):
    """合并多个 WAV 字节流为一个文件（假设格式相同）"""
    if not wav_bytes_list:
        return

    # 解析第一个文件的格式参数
    first = io.BytesIO(wav_bytes_list[0])
    with wave.open(first, 'rb') as w:
        nchannels = w.getnchannels()
        sampwidth = w.getsampwidth()
        framerate = w.getframerate()
        nframes = w.getnframes()
        audio_data = w.readframes(nframes)

    # 收集所有音频数据
    all_frames = [audio_data]
    total_frames = nframes

    for wb in wav_bytes_list[1:]:
        bio = io.BytesIO(wb)
        with wave.open(bio, 'rb') as w:
            # 验证格式一致
            if w.getnchannels() != nchannels or w.getsampwidth() != sampwidth or w.getframerate() != framerate:
                print(f"  Warning: format mismatch, skipping")
                continue
            all_frames.append(w.readframes(w.getnframes()))
            total_frames += w.getnframes()

    # 写入合并后的文件
    with wave.open(output_path, 'wb') as w:
        w.setnchannels(nchannels)
        w.setsampwidth(sampwidth)
        w.setframerate(framerate)
        w.setnframes(total_frames)
        for frames in all_frames:
            w.writeframes(frames)

    print(f"  Merged {len(all_frames)} segments → {output_path} ({total_frames/framerate:.1f}s)")


def main():
    print("Generating test dialogue audio...")
    print(f"TTS host: {TTS_HOST}")
    print()

    wav_bytes = []
    for i, line in enumerate(DIALOGUE):
        print(f"[{i+1}/{len(DIALOGUE)}] {line['charId']} ({line['mood']}): {line['text']}")
        data = generate_tts(line["charId"], line["text"], line["mood"], 0, i)
        wav_bytes.append(data)
        print()

    print("Merging audio segments...")
    merge_wavs(wav_bytes, OUTPUT_FILE)
    print(f"\nDone! Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
