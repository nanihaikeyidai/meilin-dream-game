@echo off
python -X utf8 -c "
import requests, json

TTS_URL = 'http://localhost:7860/tts'

lines = [
    ('xieyunlan', '(冷峻青年男声，讲化州方言，语气平淡自然) 你食咗饭未啊？今日天气几好喔。'),
    ('huayingyue', '(年轻女声，讲化州方言，语气轻快活泼) 喂，去边度玩啊？带埋我去得唔得啊？'),
    ('guqianfan', '(洒脱青年男声，讲化州方言，语气轻松随意) 化州牛腩粉好好食嘎，得闲我带你去试下。'),
]

for i, (charId, text) in enumerate(lines):
    print(f'[{i+1}] 生成中... {text[:30]}')
    payload = {'charId': charId, 'text': text, 'mood': 'neutral', 'turnCount': i+100, 'pageIdx': 0}
    resp = requests.post(TTS_URL, json=payload, timeout=120)
    if resp.status_code == 200:
        path = f'D:\\Hermes\\test_huazhou_{i+1}.wav'
        with open(path, 'wb') as f:
            f.write(resp.content)
        print(f'  OK -> {path} ({len(resp.content)//1024}KB)')
    else:
        print(f'  FAIL HTTP {resp.status_code}')

print('DONE')
"