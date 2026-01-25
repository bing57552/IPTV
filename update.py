import os

def get_channel_logic(name, url):
    # 频道名统一：大写 + 去空格；URL 暂时没用到，但保留以便以后扩展
    n = str(name).upper().replace(" ", "")
    u = str(url).lower()

    # ===== 电影频道：含华语电影常见关键字，一律归到电影组，绝对不当购物删掉 =====
    premium_movie = [
        "ASTRO", "CHC", "CATCHPLAY", "POPC", "美亚", "美亞", "DISNEY", "NETFLIX",
        "MOVIE", "电影", "電影", "影视", "影視",
        "CELESTIAL", "天映", "天映經典", "天映经典",
        "星卫", "星衛", "龍祥", "龙祥",
        "東森電影", "東森洋片", "东森电影", "东森洋片",
        "緯來電影", "纬来电影", "星衛電影", "星卫电影"
    ]
    if any(brand in n for brand in premium_movie):
        return "电影频道", False

    # ===== 国语 / 华语剧集频道：新加坡、马来西亚、澳洲等常见戏剧台 =====
    mandarin_drama = [
        "电视剧", "電視劇", "戲劇", "戏剧",
        "劇場", "剧场", "華劇", "华剧",
        "偶像劇", "偶像剧", "DRAMA",
        "雙星", "双星", "全佳", "AOD", "華麗台", "华丽台"
    ]
    mandarin_tag = [
        "華語", "华语", "國語", "国语",
        "普通話", "普通话", "MANDARIN", "CHINESE"
    ]
    if any(k in n for k in mandarin_drama) and any(t in n for t in mandarin_tag):
        return "国语剧集频道", False

    # ===== 港台组：TVB / 纬来 / 龙祥 / 东森 等 =====
    if any(brand in n for brand in [
        "TVB", "MYTV", "GTV", "SUPER", "TW", "HK",
        "纬来", "緯來", "龙祥", "龍祥", "东森", "東森"
    ]):
        return "港台频道", False

    # ===== 购物黑名单：命中就判定为垃圾购物台，从 no-shopping.m3u 里剔除 =====
    blacklist = [
        "QVC", "HSN", "JEWELRY", "JTV", "SHOPHQ", "EVINE", "GEM",
        "TSC", "TJC", "MOMO",
        "购物", "購物", "特卖", "特賣", "商城"
    ]
    if any(key in n for key in blacklist):
        return "垃圾购物台", True

    # ===== 默认：综合频道，保留 =====
    return "综合频道", False


def main():
    # 输入文件：每行格式  频道名,URL
    input_file = "demo.txt"
    if not os.path.exists(input_file):
        return

    all_res, clean_res = [], []

    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            if "," in line and "://" in line:
                try:
                    name, url = line.strip().split(",", 1)
                    group, is_shop = get_channel_logic(name, url)
                    entry = f'#EXTINF:-1 group-title="{group}",{name}
{url}
'
                    all_res.append(entry)
                    if not is_shop:
                        clean_res.append(entry)
                except Exception:
                    continue

    with open("all.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U
" + "".join(all_res))

    with 