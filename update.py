import os
import requests
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def get_channel_logic(name, url):
    """频道分类逻辑（保持不变）"""
    n = str(name).upper().replace(" ", "")
    
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

def get_quality_priority(url):
    """根据URL获取清晰度优先级"""
    u = str(url).lower()
    if any(x in u for x in ['4k', 'uhd', '2160']):
        return 4, "[4K]"
    elif any(x in u for x in ['1080', 'fhd']):
        return 3, "[1080P]"
    elif any(x in u for x in ['720', 'hd']):
        return 2, "[高清]"
    else:
        return 1, "[标清]"

def check_stream_valid(url):
    """快速检测直播源是否有效（5秒超时）"""
    try:
        # HEAD请求更快，只检查响应头
        response = requests.head(url, timeout=5, allow_redirects=True)
        return response.status_code in [200, 206]
    except:
        # 尝试GET请求（直播流可能不支持HEAD）
        try:
            response = requests.get(url, timeout=5, stream=True)
            return response.status_code in [200, 206]
        except:
            return False

def main():
    input_file = "demo.txt"
    if not os.path.exists(input_file):
        print("demo.txt not found!")
        return

    # 按频道分组
    channels = defaultdict(list)
    
    print("正在读取频道列表...")
    with open(input_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            if "," in line and "://" in line:
                try:
                    name, url = line.strip().split(",", 1)
                    group, is_shop = get_channel_logic(name, url)
                    
                    channels[name].append({
                        'url': url.strip(),
                        'group': group,
                        'is_shop': is_shop,
                        'line_num': line_num
                    })
                except:
                    continue

    print(f"发现 {len(channels)} 个频道，共 {sum(len(s) for s in channels.values())} 个源")

    all_res = []
    clean_res = []
    
    # 并行检测所有直播源
    print("正在检测直播源有效性...")
    valid_streams = {}
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        future_to_url = {executor.submit(check_stream_valid, source['url']): source for sources in channels.values() for source in sources}
        
        for future in as_completed(future_to_url, timeout=60):
            source = future_to_url[future]
            try:
                is_valid = future.result()
                valid_streams[source['url']] = is_valid
            except:
                valid_streams[source['url']] = False

    print(f"有效源检测完成，找到 {sum(valid_streams.values())} 个可用源")

    # 处理每个频道，保留有效源（优先高画质，最多3个）
    print("正在整理频道...")
    for channel_