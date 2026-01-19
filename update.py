# -*- coding: utf-8 -*-
"""
update.py —— 最终稳定成品版
GitHub Actions / 本地 Python 3.9+ 可运行
"""

import time
import requests
from collections import defaultdict

TIMEOUT = 5
HEADERS = {"User-Agent": "Mozilla/5.0"}
BLOCK_KEYWORDS = ["购物", "导购", "理财", "股票", "期货", "博彩"]

# ================= 工具函数 =================

def has_chinese(text: str) -> bool:
    return any('\u4e00' <= c <= '\u9fff' for c in text)

def is_blocked(title: str) -> bool:
    return any(k in title for k in BLOCK_KEYWORDS)

def is_valid_stream(url: str) -> bool:
    try:
        r = requests.get(url, timeout=TIMEOUT, stream=True, headers=HEADERS)
        return r.status_code in (200, 206)
    except Exception:
        return False

def test_speed(url: str):
    try:
        start = time.time()
        r = requests.get(url, timeout=TIMEOUT, stream=True, headers=HEADERS)
        if r.status_code not in (200, 206):
            return None
        for _ in r.iter_content(chunk_size=1024):
            break
        return time.time() - start
    except Exception:
        return None

# ================= 解析 m3u =================

def parse_m3u(lines):
    channels = []
    title = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("#EXTINF"):
            title = line.split(",", 1)[-1].strip()
        elif line.startswith("http") and title:
            channels.append({"title": title, "url": line})
            title = None
    return channels

# ================= 每频道选最快 =================

def pick_fastest_per_channel(channels):
    best = {}
    for ch in channels:
        if ch.get("ping") is None:
            continue
        t = ch["title"]
        if t not in best or ch["ping"] < best[t]["ping"]:
            best[t] = ch
    return list(best.values())

# ================= 主流程 =================

def main():
    with open("source.m3u", "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    raw_channels = parse_m3u(lines)
    valid_channels = []

    for ch in raw_channels:
        title = ch["title"]
        if is_blocked(title):
            continue
        if not is_valid_stream(ch["url"]):
            continue
        ping = test_speed(ch["url"])
        if ping is not None:
            ch["ping"] = ping
            valid_channels.append(ch)

    best_channels = pick_fastest_per_channel(valid_channels)

    with open("live.m3u", "w", encoding="utf-8") as f:
        for ch in best_channels:
            f.write(f"#EXTINF:-1,{ch['title']}\n")
            f.write(ch["url"] + "\n")

    print("全部完成 ✅")

if __name__ == "__main__":
    main()