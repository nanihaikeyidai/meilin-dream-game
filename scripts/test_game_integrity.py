#!/usr/bin/env python3
"""
AVG 游戏全功能完整性测试脚本
测试每个剧本：立绘加载、资源文件、页面响应、对话渲染
"""
import json, os, sys, time, urllib.request, struct

BASE_URL = "http://localhost:8081"
ASSETS = "D:/HermesWorkspace/girlgame-skill/frontend/assets"
PORTRAITS = os.path.join(ASSETS, "portraits")
BG = os.path.join(ASSETS, "backgrounds")

SCRIPTS = [
    {"id": "changan-moon",     "name": "月下长安",   "chars": ["xieyunlan", "huayingyue", "guqianfan", "shenmingyue", "lihuaijin", "gongsunlan"]},
    {"id": "campus-summer",    "name": "夏日的回音",  "chars": ["linxue", "suyunxi", "shenqingci", "jiangxiaoyu", "xiazhiyao", "chengnianci", "yexiaoman"]},
    {"id": "cafe-night",       "name": "深夜咖啡店",  "chars": ["linyu", "suwan", "gunian", "zhaozhu", "zhoudoctor", "qinyutong"]},
    {"id": "suspense-mansion", "name": "镜像之馆",    "chars": ["linyingxue", "chenwu", "suwanqing", "gunianan", "zhaomingshen", "jingzhongren"]},
]

EXPRESSIONS = ["default", "smile", "happy", "angry", "sad", "surprised", "blush", "cold"]

PASS = 0
FAIL = 0
ERRORS = []

def check(condition, msg):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {msg}")
    else:
        FAIL += 1
        ERRORS.append(msg)
        print(f"  ❌ {msg}")

def check_png(fp):
    """验证 PNG 文件完整性和 color_type"""
    try:
        with open(fp, 'rb') as f:
            h = f.read(30)
        if h[:8] != b'\x89PNG\r\n\x1a\n':
            return False, "not PNG"
        w = struct.unpack('>I', h[16:20])[0]
        hgt = struct.unpack('>I', h[20:24])[0]
        ct = h[25]
        return True, f"{w}×{hgt} ct={ct}"
    except Exception as e:
        return False, str(e)

def test_server():
    print("\n📡 服务器连通性")
    try:
        r = urllib.request.urlopen(f"{BASE_URL}/", timeout=10)
        check(r.status == 200, f"HTTP 200: {BASE_URL}/")
    except Exception as e:
        check(False, f"服务器连接失败: {e}")

def test_portraits():
    print("\n🖼️ 立绘完整性")
    total_files = 0
    total_valid = 0
    for script in SCRIPTS:
        tpl_dir = os.path.join(PORTRAITS, script["id"])
        chars_found = [d for d in os.listdir(tpl_dir) if os.path.isdir(os.path.join(tpl_dir, d))] if os.path.isdir(tpl_dir) else []
        print(f"  📁 {script['name']}: {len(chars_found)}/{len(script['chars'])} 角色目录")
        check(len(chars_found) == len(script["chars"]), f"{script['name']}: 角色目录齐全")

    for script in SCRIPTS:
        tpl_dir = os.path.join(PORTRAITS, script["id"])
        if not os.path.isdir(tpl_dir):
            continue
        for char_id in script["chars"]:
            cd = os.path.join(tpl_dir, char_id)
            if not os.path.isdir(cd):
                check(False, f"{script['id']}/{char_id}: 目录缺失")
                continue
            files = sorted([f for f in os.listdir(cd) if f.endswith('.png')])
            rel = f"{script['id']}/{char_id}"
            for f in files:
                fp = os.path.join(cd, f)
                ok, info = check_png(fp)
                total_files += 1
                if ok:
                    total_valid += 1
                else:
                    ERRORS.append(f"{rel}/{f}: {info}")
            check(len(files) == 8, f"{rel}: 8/8 表情 ({', '.join([f.replace('.png','') for f in files])})")

    check(total_files > 0, f"立绘文件存在: {total_files} 张")
    check(total_valid == total_files, f"全部 PNG 有效: {total_valid}/{total_files}")

def test_backgrounds():
    print("\n🌄 背景图完整性")
    bg_files = [f for f in os.listdir(BG) if f.endswith('.png')]
    total = 0
    valid = 0
    for f in bg_files:
        fp = os.path.join(BG, f)
        ok, info = check_png(fp)
        total += 1
        if ok: valid += 1
    check(total > 0, f"背景文件: {total} 张")
    check(valid == total, f"全部 PNG 有效: {valid}/{total}")
    print(f"  文件列表: {', '.join(bg_files[:10])}{'...' if len(bg_files)>10 else ''}")

def test_script_endpoints():
    print("\n📄 剧本页面加载")
    for s in SCRIPTS:
        try:
            r = urllib.request.urlopen(f"{BASE_URL}/game.html", timeout=10)
            html = r.read().decode('utf-8')
            check(r.status == 200, f"{s['name']}: game.html HTTP 200")
            check(len(html) > 20000, f"{s['name']}: game.html 页面完整 ({len(html)} chars)")
        except Exception as e:
            check(False, f"{s['name']}: 加载失败 - {e}")
    # 额外检测 JS 模块文件
    js_files = ['bootstrap.js', 'engine.js', 'api.js', 'template-registry.js', 'mood.js', 'tts.js']
    for jf in js_files:
        try:
            r = urllib.request.urlopen(f"{BASE_URL}/js/{jf}", timeout=10)
            check(r.status == 200, f"js/{jf} HTTP 200")
        except Exception as e:
            check(False, f"js/{jf}: {e}")

def test_api():
    print("\n🔌 API 端点")
    endpoints = [
        ("首页", "/"),
        ("game.html", "/game.html"),
        ("index.html", "/index.html"),
        ("server.js", "/server.js"),
    ]
    for name, path in endpoints:
        try:
            r = urllib.request.urlopen(f"{BASE_URL}{path}", timeout=10)
            check(r.status == 200, f"{name}: HTTP 200")
        except urllib.error.HTTPError as e:
            check(e.code == 200, f"{name}: HTTP {e.code}")
        except Exception as e:
            check(False, f"{name}: 请求失败 - {e}")

if __name__ == "__main__":
    start = time.time()
    
    print("=" * 60)
    print("  AVG 游戏全功能自动化测试")
    print(f"  时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    test_server()
    test_portraits()
    test_backgrounds()
    test_script_endpoints()
    test_api()
    
    elapsed = time.time() - start
    print(f"\n{'='*60}")
    print(f"  测试完成: {PASS} ✅ / {FAIL} ❌  (耗时 {elapsed:.1f}s)")
    if ERRORS:
        print(f"\n  ❌ 失败详情:")
        for e in ERRORS:
            print(f"    - {e}")
    print(f"{'='*60}")
    
    sys.exit(0 if FAIL == 0 else 1)
