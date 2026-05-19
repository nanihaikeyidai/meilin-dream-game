"""生成游戏内对话测试音频——调用 TTS API"""
import requests, json, time, os

TTS_URL = "http://192.168.144.1:7860/tts"

# 一段游戏内对话场景：长安灯夜初遇
scenes = [
    # 场景：谢云岚独白
    {
        "charId": "xieyunlan",
        "mood": "neutral",
        "text": "长安城中风云际会，姑娘还是莫要掺和这浑水为好。"
    },
    # 场景：花映月登场
    {
        "charId": "huayingyue",
        "mood": "happy",
        "text": "哟，云岚哥哥又在吓唬人家了？这长安城的灯这么好，不出来走走才可惜呢。"
    },
    # 场景：谢云岚冷声
    {
        "charId": "xieyunlan",
        "mood": "cold",
        "text": "花姑娘，血月案的线索不是玩笑。你若知晓什么，最好说出来。"
    },
    # 场景：花映月惊讶
    {
        "charId": "huayingyue",
        "mood": "surprised",
        "text": "血月案…你怎么知道我与那事有关？你究竟是何人？"
    },
    # 场景：谢云岚
    {
        "charId": "xieyunlan",
        "mood": "warm",
        "text": "我本不想连累你。但你已经入了局，便只能往前走。"
    },
    # 场景：花映月温柔
    {
        "charId": "huayingyue",
        "mood": "warm",
        "text": "那便一起走呗。我花映月什么时候怕过？"
    },
]

output_dir = "/mnt/d/Hermes/test_dialogue_tts"
os.makedirs(output_dir, exist_ok=True)

for i, scene in enumerate(scenes):
    char_name = {"xieyunlan": "谢云岚", "huayingyue": "花映月"}.get(scene["charId"], scene["charId"])
    mood_name = scene["mood"]
    text_short = scene["text"][:20]
    
    print(f"\n[{i+1}/{len(scenes)}] {char_name}（{mood_name}）: {scene['text'][:40]}...")
    
    payload = {
        "charId": scene["charId"],
        "text": scene["text"],
        "mood": scene["mood"],
        "turnCount": i,
        "pageIdx": 0,
    }
    
    t0 = time.time()
    try:
        resp = requests.post(TTS_URL, json=payload, timeout=120)
        elapsed = time.time() - t0
        if resp.status_code == 200:
            out_path = f"{output_dir}/line_{i+1}_{scene['charId']}_{mood_name}.wav"
            with open(out_path, "wb") as f:
                f.write(resp.content)
            print(f"  ✅ {elapsed:.1f}s → {out_path} ({len(resp.content)/1024:.0f}KB)")
        else:
            print(f"  ❌ HTTP {resp.status_code}: {resp.text[:100]}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

# 合并所有音频为一个文件（简单拼接）
print("\n=== 尝试合并音频 ===")
try:
    import numpy as np
    import soundfile as sf
    
    all_audio = []
    sample_rate = None
    for i in range(len(scenes)):
        path = f"{output_dir}/line_{i+1}_{scenes[i]['charId']}_{scenes[i]['mood']}.wav"
        if os.path.exists(path):
            data, sr = sf.read(path)
            if sample_rate is None:
                sample_rate = sr
            all_audio.append(data)
            # 添加0.5秒静音间隔
            silence = np.zeros(int(sr * 0.5))
            all_audio.append(silence)
    
    if all_audio:
        combined = np.concatenate(all_audio)
        combined_path = "/mnt/d/Hermes/test_dialogue_tts.wav"
        sf.write(combined_path, combined, sample_rate or 48000)
        print(f"  ✅ 合并完成: {combined_path} ({len(combined)/1024:.0f}KB)")
    else:
        print("  ❌ 没有生成成功的音频文件")
        
except ImportError:
    # 如果没有soundfile就用cmd拼接
    print("  ⚠️ 无soundfile库，不做拼接")
except Exception as e:
    print(f"  ❌ 合并失败: {e}")

print("\n=== 完成 ===")
