"""生成化州话测试音频"""
import requests, json

TTS_URL = "http://192.168.144.1:7860/tts"

# 试试几句化州话
lines = [
    {
        "charId": "xieyunlan",
        "mood": "neutral",
        "text": "你食咗饭未啊？今日天气几好喔。",
        "voice_override": "(冷峻青年男声，讲化州话，沉稳低沉，语气平淡自然)"
    },
    {
        "charId": "huayingyue",
        "mood": "happy",
        "text": "喂，去边度玩啊？带埋我去得唔得啊？",
        "voice_override": "(年轻女声，讲化州话，妩媚柔美，语气轻快)"
    },
    {
        "charId": "guqianfan",
        "mood": "neutral",
        "text": "化州牛腩粉好好食嘎，得闲我带你去试下。",
        "voice_override": "(洒脱青年男声，讲化州话，明朗随性，语气轻松)"
    },
]

for i, line in enumerate(lines):
    print(f"\n[{i+1}] 台词: {line['text']}")
    print(f"    音色: {line['voice_override']}")
    
    # 先用默认音色配置试
    payload = {
        "charId": line["charId"],
        "text": line["voice_override"] + " " + line["text"],
        "mood": line["mood"],
        "turnCount": i + 100,
        "pageIdx": 0,
    }
    
    try:
        resp = requests.post(TTS_URL, json=payload, timeout=120)
        if resp.status_code == 200:
            out_path = f"/mnt/d/Hermes/test_huazhou_{i+1}.wav"
            with open(out_path, "wb") as f:
                f.write(resp.content)
            print(f"    ✅ 生成成功 → {out_path} ({len(resp.content)/1024:.1f}KB)")
        else:
            print(f"    ❌ HTTP {resp.status_code}: {resp.text[:100]}")
    except Exception as e:
        print(f"    ❌ Error: {e}")

print("\n=== 全搞定 ===")
