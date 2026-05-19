#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
下载 MiniCPM-V 4.6 模型并测试视频推理
"""
import os, time, torch
from huggingface_hub import snapshot_download

MODEL_DIR = "D:/Hermes/minicpm-v-4.6"
MODEL_ID = "openbmb/MiniCPM-V-4.6"

print("=" * 50)
print(f"📥 下载模型: {MODEL_ID}")
print(f"📂 目标路径: {MODEL_DIR}")
print("=" * 50)

# 下载模型
print("\n⏳ 开始下载（首次可能较慢）...")
start = time.time()
model_path = snapshot_download(
    repo_id=MODEL_ID,
    local_dir=MODEL_DIR,
    local_dir_use_symlinks=False,
    resume_download=True,
    max_workers=4
)
elapsed = time.time() - start

# 统计
total_size = 0
file_count = 0
for root, dirs, files in os.walk(model_path):
    for f in files:
        fp = os.path.join(root, f)
        total_size += os.path.getsize(fp)
        file_count += 1

print(f"\n✅ 下载完成!")
print(f"   耗时: {elapsed:.0f}秒")
print(f"   文件数: {file_count}")
print(f"   总大小: {total_size/1024/1024/1024:.2f} GB")
print(f"   路径: {model_path}")

# 检查 safetensors 文件
safetensors = [f for f in os.listdir(model_path) if f.endswith('.safetensors')]
print(f"\n📦 safetensors 文件 ({len(safetensors)}):")
for sf in sorted(safetensors):
    fp = os.path.join(model_path, sf)
    print(f"   {sf}: {os.path.getsize(fp)/1024/1024:.0f}MB")
