#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import socket
import requests
from collections import defaultdict
from urllib.parse import urlparse

# =========================
# 基础配置
# =========================
M3U_SOURCE_URL = (
    "https://raw.githubusercontent.com/bing57552/g/main/global_cn_4k1080p_multi.m3u"
)
INPUT_FILE = "input.m3u"
OUTPUT_FILE = "output.m3u"
TIMEOUT = 6

# =========================
# 购物 / 广告台 精准过滤
# =========================
SHOPPING_CHANNELS = {
    "hsn", "qvc", "shophq", "jewelry",
    "购物", "家有购物", "优购物", "快乐购",
    "东森购物", "momo", "viva", "森森",
    "shop channel", "homeshopping",
}

AD_CHANNEL_KEYWORDS = {
    "广告", "ad ", "promo", "shopping",
    "brand", "marketing", "campaign",
}

# =========================
# 影视 / 剧集 白名单（防误杀）
# =========================
DRAMA_MOVIE_WHITELIST = {
    "cctv-6", "cctv-8", "drama", "movie",
    "chc", "影迷", "动作电影", "家庭影院",
    "电影", "影院", "影视", "戏剧", "剧场",
    "tvb", "翡翠", "明珠", "j2", "星河",
    "凤凰电影", "凤凰中文", "catchplay",
    "celestial", "天映", "popc", "8tv",
    "hbo", "cinemax", "iqiyi", "meiah",
    "viu", "now", "disney+", "netflix",
    "纬来", "东森", "三立", "八大",
    "华视", "台视", "民视",
    "mediacorp", "channel 8", "channel u",
    "astro"
}

# =========================
# EPG 精准映射（模糊命中）
# =========================
EPG_ID_MAP = {
    "凤凰中文": "PhoenixChinese",
    "凤凰资讯": "PhoenixInfo",
    "凤凰香港": "PhoenixHK",
    "now": "NowBaoguMovies",
    "爆谷": "NowBaoguMovies",
    "中天新闻": "CTiNews",
}

# =========================
# 工具函数
# =========================
def is_ad_or_shop(name: str) -> bool:
    n = name.lower()
    for w in DRAMA_MOVIE_WHITELIST:
        if w.lower() in n:
            return False
    for k in SHOPPING_CHANNELS | AD_CHANNEL_KEYWORDS:
        if k in n:
            return True
    return False


def is_stream_alive(url: str) -> bool:
    try:
        r = requests.head(url, timeout=TIMEOUT, allow_redirects=True)
        return r.status_code < 400
    except Exception:
        return False


def detect_quality(url: str) -> int:
    u = url.lower()
    if "2160" in u or "4k" in u:
        return 4
    if "1080" in u:
        return 3
    if "720" in u:
        return 2
    return 1


def get_epg_id(name: str) -> str:
    for k, v in EPG_ID_MAP.items():
        if k.lower() in name.lower():
            return v
    return ""


# =========================
# 下载 M3U
# =========================
print("⬇️ 下载源文件...")
resp = requests.get(M3U_SOURCE_URL, timeout=15)
resp.raise_for_status()
with open(INPUT_FILE, "w", encoding="utf-8") as f:
    f.write(resp.text)

# =========================
# 读取 M3U
# =========================
with open(INPUT_FILE, "r", encoding="utf-8", errors="ignore") as f:
    lines = [l.strip() for l in f if l.strip()]

channels = []
i = 0
while i < len(lines) - 1:
    if lines[i].startswith("#EXTINF"):
        channels.append((lines[i], lines[i + 1]))
        i += 2
    else:
        i += 1

# =========================
# 聚合 + 过滤 + 探活
# =========================
all_channels = defaultdict(list)

for extinf, url in channels:
    m = re.search(r",(.+)$", extinf)
    if not m:
        continue

    name = m.group(1).strip()
    if is_ad_or_shop(name):
        continue
    if not is_stream_alive(url):
        continue

    all_channels[name].append(url)

# =========================
# 生成 final（多源 + 稳定优先）
# =========================
final = []

for name, urls in all_channels.items():
    epg_id = get_epg_id(name)
    logo = (
        f"https://raw.githubusercontent.com/fanmingming/live/main/tv/{epg_id}.png"
        if epg_id else ""
    )

    urls.sort(key=detect_quality, reverse=True)

    for url in urls:
        q = detect_quality(url)
        label = {4: "4K", 3: "1080P", 2: "720P", 1: "HD"}[q]

        ext = f'#EXTINF:-1 tvg-name="{name}"'
        if epg_id:
            ext += f' tvg-id="{epg_id}"'
        if logo:
            ext += f' tvg-logo="{logo}"'
        ext += f",{name} | {label}"

        final.append((name, q, ext, url))

# =========================
# 稳定排序 + 编号
# =========================
final.sort(key=lambda x: (x[0], -x[1]))

output = []
chno = 1
for _, _, ext, url in final:
    ext = ext.replace("#EXTINF:-1 ", f'#EXTINF:-1 tvg-chno="{chno}" ')
    output.append((ext, url))
    chno += 1

# =========================
# 写出文件
# =========================
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    for ext, url in output:
        f.write(ext + "\n")
        f.write(url + "\n")

print(f"✅ 完成：{len(output)} 条频道 → {OUTPUT_FILE}")