#!/usr/bin/env python3
"""立绘透明背景处理：采样边缘像素 → 阈值透明化"""
import sys, os
from PIL import Image

def make_transparent(input_path, output_path, threshold=60):
    img = Image.open(input_path).convert("RGBA")
    px = img.load()
    w, h = img.size
    
    # 采样边缘像素确定背景色
    samples = []
    for x in range(w):
        samples.append(px[x, 0])
        samples.append(px[x, h-1])
    for y in range(h):
        samples.append(px[0, y])
        samples.append(px[w-1, y])
    
    r_sum = g_sum = b_sum = count = 0
    for s in samples:
        if len(s) >= 3 and s[3] > 128:
            r_sum += s[0]; g_sum += s[1]; b_sum += s[2]
            count += 1
    
    if count == 0:
        bg = (255, 255, 255)
    else:
        bg = (r_sum // count, g_sum // count, b_sum // count)
    
    # 阈值透明化
    new_img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    new_px = new_img.load()
    
    for x in range(w):
        for y in range(h):
            pixel = px[x, y]
            r, g, b = pixel[0], pixel[1], pixel[2]
            a = pixel[3] if len(pixel) >= 4 else 255
            
            if a < 128:
                continue
            
            diff = abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2])
            if diff < threshold:
                new_px[x, y] = (r, g, b, 0)
            else:
                new_px[x, y] = (r, g, b, 255)
    
    new_img.save(output_path, "PNG")
    size_kb = os.path.getsize(output_path) // 1024
    print("  [OK] Transparent: " + output_path + " (" + str(size_kb) + "KB)")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python3 make_transparent.py <input.png> <output.png> [threshold]")
        sys.exit(1)
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    threshold = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    make_transparent(input_path, output_path, threshold)
