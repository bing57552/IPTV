# -*- coding: utf-8 -*-
import re
import requests

# =========================
# 基础参数
# =========================
TIMEOUT = 8
CHECK_BYTES = 1024 * 256
MAX_SOURCES_PER_CHANNEL = 5

# =========================
# 影视 / 剧集白名单（防误杀）
# =========================
DRAMA_MOVIE_WHITELIST = {
    "cctv-6", "cctv-8",
    "chc", "影迷", "动作电影", "家庭影院",
    "电影", "影院", "影视", "戏剧", "剧场",
    "tvb", "翡翠", "明珠", "j2", "星河",
    "凤凰电影", "凤凰中文",
    "celestial", "天映",
    "hbo", "cinemax",
    "viu", "now",
    "纬来", "东森", "三立", "八大",
    "华视", "台视", "民视",
    "mediacorp", "channel 8", "channel u",
    "astro"
}

# =========================
# 购物台（直接过滤）
# =========================
SHOPPING_CHANNELS = {
    "hsn", "home shopping network", "qvc us",
    "shophq", "jewelry television", "jtv",
    "the shopping channel", "tsc",
    "qvc uk", "qvc germany", "qvc italy", "qvc france",
    "hse24", "hse extra", "ideal world", "jml direct",
    "央广购物", "家有购物", "好易购", "优购物", "快乐购",
    "东森购物", "momo购物", "momo 购物台", "viva购物", "森森购物",
    "shop channel japan", "qvc japan",
    "gs shop", "cj o shopping", "lotte homeshopping",
    "ns home shopping", "hyundai home shopping",
    "star cj alive", "homeshop18", "naaptol",
    "dubai shopping", "gulf shopping",
    "tvsn", "openshop"
}

# =========================
# 广告台关键词（直接过滤）
# =========================
AD_CHANNEL_KEYWORDS = {
    "advert", "promo", "promotion", "commercial",
    "shopping", "shop", "sale",
    "classified", "infomercial",
    "广告", "推广", "促销", "购物"
}

# =========================
# 工具函数
# =========================
def normalize(text: str) -> str:
    return text.lower().strip()

def is_ad_or_shopping(name: str) -> bool:
    n = normalize(name)
    if any(k in n for k in SHOPPING_CHANNELS):
        return True
    if any(k in n for k in AD_CHANNEL_KEYWORDS):
        return True
    return False

def is_whitelisted(name: str) -> bool:
    n = normalize(name)
    return any(k in n for k in DRAMA_MOVIE_WHITELIST)

def is_stream_alive(url: str) -> bool:
    try:
        r = requests.get(
            url,
            timeout=TIMEOUT,
            stream=True,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        return r.status_code == 200
    except:
        return False

# =========================
# 主流程
# =========================
def process_m3u(lines, output_file):
    final = []

    extinf = None
    for line in lines:
        line = line.strip()
        if line.startswith("#EXTINF"):
            extinf = line
        elif line and not line.startswith("#") and extinf:
            name = extinf.split(",")[-1]

            # 🚫 广告 / 购物台过滤（影视白名单放行）
            if is_ad_or_shopping(name) and not is_whitelisted(name):
                extinf = None
                continue

            final.append((extinf, line))
            extinf = None

    # =========================
    # ✅ 排序 / 编号 / LOGO（核心区）
    # =========================
    sorted_final = []
    channel_index = 1

    for extinf, u in final:
        # 清理旧字段
        extinf = re.sub(r'tvg-chno="[^"]*"', '', extinf)
        extinf = re.sub(r'tvg-logo="[^"]*"', '', extinf)

        # 添加编号（LOGO 以后在这加）
        extinf = extinf.replace(
            "#EXTINF:",
            f'#EXTINF:-1 tvg-chno="{channel_index}" '
        )

        sorted_final.append((extinf.strip(), u))
        channel_index += 1

    # =========================
    # 写入文件
    # =========================
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for extinf, u in sorted_final:
            f.write(extinf + "\n")
            f.write(u + "\n")

    print(f"✅ 完成：共 {channel_index - 1} 个频道")

# =========================
# 启动入口
# =========================
if __name__ == "__main__":
    with open("input.m3u", "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    process_m3u(lines, "output.m3u")