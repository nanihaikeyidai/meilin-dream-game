#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MiniCPM-V 4.6 视频反推测试 - 手动帧提取版
"""
import os, time, torch, av
import numpy as np
from PIL import Image
from transformers import AutoProcessor, AutoModelForImageTextToText

MODEL_DIR = "D:/Hermes/minicpm-v-4.6"
TEST_VIDEO = "D:/Hermes/girlgame-skill/test_video.mp4"

print("=" * 50)
print("MiniCPM-V 4.6 视频反推测试（手动帧提取）")
print("=" * 50)

free_vram = torch.cuda.mem_get_info()[0] / 1024**3
total_vram = torch.cuda.mem_get_info()[1] / 1024**3
print(f"🖥️  GPU: {torch.cuda.get_device_name(0)}")
print(f"💾 VRAM: {free_vram:.1f}GB / {total_vram:.1f}GB 空闲")

# ===== 用 PyAV 提取关键帧 =====
print(f"\n📹 提取视频帧: {TEST_VIDEO}")
container = av.open(TEST_VIDEO)
stream = container.streams.video[0]
fps = float(stream.average_rate)
total_frames = stream.frames
duration = float(stream.duration * stream.time_base)
print(f"   时长: {duration:.1f}s | FPS: {fps:.0f} | 总帧: {total_frames}")

# 均匀取 8 帧（覆盖视频全程）
num_frames = 8
frame_indices = [int(i * total_frames / num_frames) for i in range(num_frames)]
frames = []
container.seek(0)
for i, frame in enumerate(container.decode(video=0)):
    if i in frame_indices:
        img = frame.to_image()
        # 缩放到合理尺寸
        img.thumbnail((672, 672), Image.LANCZOS)
        frames.append(img)
        print(f"   帧 {i}: {img.size[0]}x{img.size[1]}")
    if len(frames) >= num_frames:
        break

container.close()
print(f"\n✅ 提取 {len(frames)} 帧")

# ===== 加载模型 =====
print("\n⏳ 加载模型...")
start = time.time()
processor = AutoProcessor.from_pretrained(MODEL_DIR, trust_remote_code=True)
model = AutoModelForImageTextToText.from_pretrained(
    MODEL_DIR,
    torch_dtype=torch.bfloat16,
    attn_implementation="sdpa",
    device_map="auto",
    trust_remote_code=True
)
load_time = time.time() - start
print(f"✅ 模型加载: {load_time:.1f}秒")
used_vram = total_vram - torch.cuda.mem_get_info()[0] / 1024**3
print(f"💾 VRAM占用: {used_vram:.1f}GB")

# ===== 逐帧推理 =====
print("\n" + "=" * 50)
print("📝 逐帧推理")
print("=" * 50)

for i, frame_img in enumerate(frames):
    # 构建单帧消息
    messages = [{
        "role": "user",
        "content": [
            {"type": "image"},
            {"type": "text", "text": f"这是视频第{i+1}/{num_frames}帧。描述这一帧的内容：场景、人物、动作、氛围。"}
        ]
    }]
    
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = processor(
        text=[text],
        images=[frame_img],
        return_tensors="pt",
        padding=True
    ).to(model.device)
    
    print(f"\n⏳ 帧 {i+1}/{num_frames} 推理中...")
    t0 = time.time()
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            temperature=0.7,
            do_sample=True,
        )
    infer_time = time.time() - t0
    
    output_text = processor.decode(outputs[0], skip_special_tokens=True)
    if "<|im_start|>assistant" in output_text:
        output_text = output_text.split("<|im_start|>assistant")[-1]
    output_text = output_text.replace("<|im_end|>", "").strip()
    
    print(f"⏱ {infer_time:.1f}秒 | {output_text[:120]}...")

# ===== 全视频整体理解 =====
print("\n" + "=" * 50)
print("🎬 全视频整体理解（多帧输入）")
print("=" * 50)

messages = [{
    "role": "user",
    "content": [
        {"type": "image"} for _ in range(8)  # 8张图片占位
    ] + [{"type": "text", "text": "以上是按时间顺序提取的8帧。请综合所有帧描述这个视频的整体内容：发生了什么事？场景如何变化？人物有什么动作？"}]
}]

text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = processor(
    text=[text],
    images=frames,
    return_tensors="pt",
    padding=True
).to(model.device)

print("⏳ 整体推理中...")
t0 = time.time()
with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=512,
        temperature=0.7,
        do_sample=True,
    )
infer_time = time.time() - t0

output_text = processor.decode(outputs[0], skip_special_tokens=True)
if "<|im_start|>assistant" in output_text:
    output_text = output_text.split("<|im_start|>assistant")[-1]
output_text = output_text.replace("<|im_end|>", "").strip()

print(f"⏱ {infer_time:.1f}秒")
print(f"\n📝 视频整体描述:\n{'-'*40}")
print(output_text)
print("-" * 40)

# ===== 统计 =====
peak_vram = torch.cuda.max_memory_allocated() / 1024**3
print(f"\n📊 统计:")
print(f"   模型加载: {load_time:.1f}秒")
print(f"   逐帧推理: {num_frames}帧 × ~5秒/帧")
print(f"   整体理解: {infer_time:.1f}秒")
print(f"   峰值VRAM: {peak_vram:.1f}GB / {total_vram:.1f}GB")
print(f"   模型路径: {MODEL_DIR}")
