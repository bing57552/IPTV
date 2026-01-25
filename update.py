import os
from collections import defaultdict

def get_channel_logic(name, url):
    """频道分类逻辑（不变）"""
    n = str(name).upper().replace(" ", "")
    u = str(url).lower()

    # 电影频道
    premium_movie = [
        "ASTRO", "CHC", "CATCHPLAY", "POPC", "美亚", "美亞", "DISNEY", "NETFLIX",
        "MOVIE", "电影", "電影", "影视", "影視", "CELESTIAL", "天映", "星卫", "星衛",
        "龍祥", "龙祥", "東森電影", "緯來電影", "纬来电影"
    ]
    if any(brand in n for brand in premium_movie):
        return "电影频道", False

    # 国语剧集频道
    mandarin_drama = ["电视剧", "戲劇", "戏剧", "劇場", "华剧", "華劇", "偶像剧", "DRAMA", "雙星", "全佳", "AOD", "华丽台"]
    mandarin_tag = ["华语", "華語", "国语", "國語", "普通话", "MANDARIN", "CHINESE"]
    if any(k in n for k in mandarin_drama) and any(t in n for t in mandarin_tag):
        return "国语剧集频道", False

    # 港台频道
    if any(brand in n for brand in ["TVB", "MYTV", "GTV", "SUPER", "TW", "HK", "纬来", "东森"]):
        return "港台频道", False

    # 购物黑名单
    blacklist = ["QVC", "HSN", "JEWELRY", "JTV", "SHOPHQ", "EVINE", "GEM", "TSC", "TJC", "MOMO", "购物", "特卖", "商城"]
    if any(key in n for key in blacklist):
        return "垃圾购物台", True

    return "综合频道", False

def get_quality_tag(url):
    """根据URL判断清晰度标签"""
    u = str(url).lower()
    if any(x in u for x in ['4k', 'uhd', '2160']):
        return "[4K]"
    elif any(x in u for x in ['1080', 'fhd']):
        return "[1080P]"
    elif any(x in u for x in ['720', 'hd']):
        return "[高清]"
    else:
        return "[标清]"

def main():
    input_file = "demo.txt"
    if not os.path.exists(input_file):
        return

    # 按频道名分组，保留所有源
    channels = defaultdict(list)
    
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            if "," in line and "://" in line:
                try:
                    name, url = line.strip().split(",", 1)
                    group, is_shop = get_channel_logic(name, url)
                    quality_tag = get_quality_tag(url)
                    
                    # 保存：频道基础名、分组、是否购物、清晰度标签、URL
                    channels[name].append({
                        'group': group,
                        'is_shop': is_shop,
                        'quality': quality_tag,
                        'url': url
                    })
                except:
                    continue

    all_res = []
    clean_res = []

    # 按频道处理，每个频道输出多条源（按清晰度排序）
    for channel_name, sources in channels.items():
        group = sources[0]['group']  # 取第一个的分组（同名频道分组一致）
        is_shop = sources[0]['is_shop']
        
        # 按清晰度优先级排序：4K > 1080P > 高清 > 标清
        quality_order = {"[4K]": 4, "[1080P]": 3, "[高清]": 2, "[标清]": 1}
        sorted_sources = sorted(sources, key=lambda x: quality_order.get(x['quality'], 0), reverse=True)
        
        # 生成多条 #EXTINF（同名频道 + 不同清晰度）
        for source in sorted_sources:
            display_name = f"{channel_name} {source['quality']}"
            entry = f'#EXTINF:-1 group-title="{source["group"]}",{display_name}
{source["url"]}
'
            
            all_res.append(entry)
            if not source['is_shop']:
                clean_res.append(entry)

    # 输出文件
    with open("all.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U
" + "".join(all_res))
    
    with open("no-shopping.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U
" + "".join(clean_res))

if __name__ == "__main__":
    main()

   