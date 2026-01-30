#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import requests
from collections import defaultdict

# =========================
# 基础配置
# =========================
M3U_SOURCE_URL = "https://gh-proxy.com/raw.githubusercontent.com/suxuang/myIPTV/main/ipv4.m3u"  # 港澳台+大陆+马来西亚源较齐全
INPUT_FILE = "input.m3u"
OUTPUT_FILE = "output_best.m3u"
TIMEOUT = 5

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
    "tvb", "翡翠", "翡翠台", "jade", "明珠", "pearl", "j2", "tvb plus", "tvbplus",
    "無綫新聞", "tvb news", "星河", "tvb mytv super", "mytvsuper", "tvbmytvsuper",
    "美亞", "mei ah", "天映", "catchplay", "astro", "华丽台", "aod", "欢喜台", "aec", "兆烽台", "喜悅台", "cinema", "hbo", "hub", "chc", "viu", "viutv", "hotstar", "viki", "iqiyi", "愛奇藝", "disney", "netflix"
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
    "翡翠台": "Jade.hk",
    "明珠台": "Pearl.hk",
    "J2": "J2.hk",
    "TVB Plus": "TVBPlus.hk",
    "無綫新聞台": "TVBNews.hk",
    "美亞電影台": "MeiAh.hk",
    "Astro 华丽台": "AstroWahLaiToi.my",
    "Astro AOD": "AstroAOD.my",
    "Astro 欢喜台": "AstroHuanXi.my",
    "Astro AEC": "AstroAEC.my",
    "Astro 兆烽台": "AstroZhaoFeng.my",
    "Astro 喜悅台": "AstroXiYue.my",
    "Astro Cinema": "AstroCinema.my",
    "HBO": "HBO",
    "ViuTV": "ViuTV.hk",
}

# =========================
# 強制添加你喜欢的频道（多源備份） - 可以随时在这里添加/修改
# =========================
FORCED_SOURCES = {
    "翡翠台": [
        "https://edge6a.v2h-cdn.com/jade/jade.stream/chunklist.m3u8",
        "http://iptv.tvfix.org/hls/jade.m3u8",
        "http://php.jdshipin.com/TVOD/iptv.php?id=fct",
        "http://cdn.132.us.kg/live/fct4k/stream.m3u8"
    ],
    "明珠台": [
        "http://iptv.tvfix.org/hls/pearl.m3u8",
        "http://php.jdshipin.com/TVOD/iptv.php?id=mz"
    ],
    "J2": [
        "http://iptv.tvfix.org/hls/j2.m3u8",
        "http://php.jdshipin.com/TVOD/iptv.php?id=j2"
    ],
    "美亞電影台": [
        "http://50.7.161.82:8278/streams/d/meiya_pye/playlist.m3u8",
        "http://iptv.tvfix.org/hls/mydy2.m3u8",
        "http://198.16.64.10:8278/meiyamovie_twn/playlist.m3u8"
    ],
    "天映電影": [
        "https://hls-gateway.vpstv.net/streams/476310.m3u8",
        "http://50.7.161.82:8278/streams/d/celestial_pye/playlist.m3u8",
        "http://iptv.tvfix.org/hls/tyjd2.m3u8"
    ],
    "Astro Catchplay": [
        "https://hls-gateway.vpstv.net/streams/708881.m3u8",
        "http://50.7.161.82:8278/streams/d/catchplay_pye/playlist.m3u8",
        "http://iptv.tvfix.org/hls/catchplay.m3u8"
    ],
    "Astro AOD": [
        "http://50.7.161.82:8278/streams/d/aod_pye/playlist.m3u8",
        "http://pixman.mytvsuper.com.mp/Smart.php?id=AOD",
        "http://iptv.tvfix.org/hls/aod.m3u8",
        "http://23.26.239.95:3599/xsj.php?id=astro-aod"
    ],
    "Astro 华丽台": [
        "http://50.7.161.82:8278/streams/d/Wlt/playlist.m3u8",
        "http://iptv.tvfix.org/hls/wlt.m3u8",
        "http://23.26.239.95:3599/xsj.php?id=astro-wlt",
        "http://pixman.mytvsuper.com.mp/Smart.php?id=WLT"
    ],
    "HBO": [
        "http://cloud-play.hhalloy.com/live/fcdd3a3c591bdd0b07a17a92cb555cc1.m3u8",
        "http://220.134.196.147:9520/http/60.251.39.91:8081/hls/71/813/ch41.m3u8"
    ],
    "HUB 戏剧台": [
        "http://cloud-play.hhalloy.com/live/440b3d3c474813d7ead7d3a795978e69.m3u8"
    ],
    "CHC 高清電影": [
        "http://iptv.tvfix.org/hls/chchd.m3u8",
        "http://223.151.51.27:85/tsfile/live/1020_1.m3u8",
        "http://59.56.75.17/live.aishang.ctlcdn.com"
    ],
    "ViuTV": [
        "http://iptv.tvfix.org/hls/viutv.m3u8",
        "http://php.jdshipin.com/TVOD/iptv.php?id=viutv"
    ]
    # 你想加新频道就在这里继续写，例如：
    # "凤凰中文": [
    #     "http://iptv.tvfix.org/hls/phoenixchinese.m3u8",
    #     "http://23.26.239.95:3599/xsj.php?id=phoenixchinese"
    # ],
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


def get_logo(epg_id: str) -> str:
    if epg_id:
        return f"https://raw.githubusercontent.com/fanmingming/live/main/tv/{epg_id}.png"
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
# 強制添加自定义频道（多源備份）
# =========================
for name, forced_urls in FORCED_SOURCES.items():
    if forced_urls:
        existing = all_channels.get(name, [])
        combined = list(set(forced_urls + existing))
        alive = [u for u in combined if is_stream_alive(u)]
        if alive:
            all_channels[name] = alive
            print(f"✅ 強制添加频道 {name} ({len(alive)} 条有效源)")

# =========================
# 生成 final（多源 + 稳定优先）
# =========================
final = []

for name, urls in all_channels.items():
    epg_id = get_epg_id(name)
    logo = get_logo(epg_id)

    urls.sort(key=detect_quality, reverse=True)
    multi_url = "|".join(urls) if len(urls) > 1 else urls[0]

    q = max(detect_quality(u) for u in urls) if urls else 1
    label = {4: "4K", 3: "1080P", 2: "720P", 1: "HD"}[q]

    ext = f'#EXTINF:-1 tvg-name="{name}"'
    if epg_id:
        ext += f' tvg-id="{epg_id}"'
    if logo:
        ext += f' tvg-logo="{logo}"'
    ext += f",{name} | {label}"

    # 加注释（OTT/马来西亚频道）
    if any(k in name.lower() for k in ["astro", "hbo", "hub", "chc", "美亞", "天映", "catchplay", "viu", "disney", "netflix", "hotstar", "viki", "iqiyi"]):
        ext += "  # OTT/马来西亚频道 - 建议合法订阅 + VPN；源灰色易失效"

    final.append((name, q, ext, multi_url))

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