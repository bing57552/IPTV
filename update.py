import os
import re
import json
import time
import requests
from collections import defaultdict, OrderedDict

# =========================
# 基础参数（稳定优先）
# =========================
TIMEOUT = 8
CHECK_BYTES = 256 * 1024
MAX_SOURCES_PER_CHANNEL = 5
FAIL_LIMIT = 3
COOLDOWN_HOURS = 24

SOURCE_POOL = "source_pool.txt"
OUTPUT_MAIN = "output_best.m3u"
OUTPUT_BACKUP = "output_backup.m3u"
HEALTH_FILE = "stream_health.json"

# =========================
# 广告 / 购物台精准过滤
# =========================
SHOPPING_CHANNELS = {
    "qvc", "hsn", "shop", "购物", "home shopping", "tv shopping",
    "momo", "东森购物", "viva购物", "森森购物", "家有购物",
    "优购物", "快乐购", "央广购物", "jtv", "shop channel"
}

AD_KEYWORDS = {
    "advert", "promo", "ad ", "广告", "推广", "促销", "classified"
}

# =========================
# 工具函数
# =========================
def fetch_text(url):
    try:
        r = requests.get(url, timeout=TIMEOUT)
        if r.status_code == 200 and "#EXTM3U" in r.text:
            return r.text
    except:
        pass
    return ""

def is_stream_alive(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, stream=True, timeout=TIMEOUT, headers=headers)
        ct = r.headers.get("Content-Type", "").lower()
        if "text/html" in ct:
            return False

        size = 0
        start = time.time()
        for chunk in r.iter_content(8192):
            if not chunk:
                continue
            size += len(chunk)
            if size >= CHECK_BYTES:
                return True
            if time.time() - start > 3:
                return False
    except:
        return False
    return False

def score_url(url):
    u = url.lower()
    score = 0
    if "4k" in u: score += 40
    if "2160" in u: score += 35
    if "1080" in u: score += 25
    if u.startswith("https"): score += 10
    if ".m3u8" in u: score += 10
    return score

def parse_m3u(text):
    lines = text.splitlines()
    res, cur = [], None
    for l in lines:
        if l.startswith("#EXTINF"):
            cur = l
        elif l and not l.startswith("#") and cur:
            res.append((cur, l.strip()))
            cur = None
    return res

def extract_meta(extinf):
    name = re.search(r",(.+)", extinf)
    tvg = re.search(r'tvg-id="([^"]*)"', extinf)
    return name.group(1).strip(), tvg.group(1).strip() if tvg else ""

def is_ad_channel(name):
    n = name.lower()
    return any(k in n for k in SHOPPING_CHANNELS | AD_KEYWORDS)

# =========================
# 加载源池
# =========================
def load_sources():
    urls = []
    with open(SOURCE_POOL, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            urls.append(line)
    return list(set(urls))

# =========================
# 主逻辑
# =========================
def main():
    now = int(time.time())
    health = {}
    if os.path.exists(HEALTH_FILE):
        with open(HEALTH_FILE, "r", encoding="utf-8") as f:
            health = json.load(f)

    channels = OrderedDict()
    for src in load_sources():
        text = fetch_text(src)
        if not text:
            continue
        for extinf, url in parse_m3u(text):
            name, tvg = extract_meta(extinf)
            if not name or is_ad_channel(name):
                continue
            key = (name, tvg)
            channels.setdefault(key, []).append((extinf, url))

    final_main = []
    final_backup = []

    ch_no = 1
    for (name, tvg), items in channels.items():
        scored = []
        for extinf, url in items:
            h = health.get(url, {})
            fails = h.get("fails", 0)
            last = h.get("last", 0)

            if fails >= FAIL_LIMIT and now - last < COOLDOWN_HOURS * 3600:
                continue

            alive = is_stream_alive(url)
            health[url] = {
                "alive": alive,
                "last": now,
                "fails": 0 if alive else fails + 1
            }

            if alive:
                score = score_url(url)
                extinf_fix = extinf
                if 'tvg-logo' not in extinf_fix:
                    extinf_fix = extinf_fix.replace(
                        "#EXTINF:",
                        f'#EXTINF:tvg-chno="{ch_no}" tvg-id="{tvg}" tvg-name="{name}" tvg-logo="",'
                    )
                scored.append((score, extinf_fix, url))

        scored.sort(reverse=True)

        if not scored:
            continue

        for s in scored[:MAX_SOURCES_PER_CHANNEL]:
            final_main.append((s[1], s[2]))

        for s in scored[MAX_SOURCES_PER_CHANNEL:MAX_SOURCES_PER_CHANNEL*2]:
            final_backup.append((s[1], s[2]))

        ch_no += 1

    if not final_main:
        print("❌ 没有生成任何频道，已中止写文件")
        return

    with open(OUTPUT_MAIN, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for e, u in final_main:
            f.write(e + "\n" + u + "\n")

    with open(OUTPUT_BACKUP, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for e, u in final_backup:
            f.write(e + "\n" + u + "\n")

    with open(HEALTH_FILE, "w", encoding="utf-8") as f:
        json.dump(health, f, indent=2, ensure_ascii=False)

    print("✅ 终极 IPTV 全自动运维完成")

if __name__ == "__main__":
    main()