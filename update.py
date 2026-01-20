import requests
import time
from concurrent.futures import ThreadPoolExecutor

# 1. 整合亚洲、欧洲、北美及影视专项源
SOURCES = {
    "north_america": "https://raw.githubusercontent.com/YueChan/Live/main/m3u/america.m3u",
    "europe": "https://raw.githubusercontent.com/YueChan/Live/main/m3u/europe.m3u",
    "asia_chinese": "https://raw.githubusercontent.com/YueChan/Live/main/m3u/asia.m3u",
    "southeast_asia": "https://raw.githubusercontent.com/YueChan/Live/main/m3u/singapore_malaysia.m3u",
    "itv_movie_special": "https://itvlist.cc/itv.m3u",
    "global_chinese": "https://iptv-org.github.io/iptv/languages/zho.m3u",
    "live_hd": "https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/ipv4.m3u"
}

# 2. 电影与电视剧关键词过滤清单
KEYWORDS = ["电影", "电视剧", "剧场", "影院", "TVB", "翡翠", "星河", "华丽", "Drama", "Movie", "中文", "华语", "Channel 8", "U频道"]

def check_url(item):
    name_info, url = item
    # 模拟真实浏览器请求头，减少断流与同步问题
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        start_time = time.time()
        # 将超时放宽至 2.0s 以适配海外物理延迟
        response = requests.head(url, headers=headers, timeout=2.0, allow_redirects=True)
        end_time = time.time()
        
        if response.status_code == 200:
            return {"name": name_info, "url": url, "speed": end_time - start_time}
    except:
        pass
    return None

def main():
    unique_channels = {}
    
    for filename, url in SOURCES.items():
        try:
            print(f"🌐 正在同步: {filename}")
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            lines = r.text.split('\n')
            temp_list = []
            
            for i in range(len(lines)):
                if "#EXTINF" in lines[i] and i + 1 < len(lines):
                    name_info = lines[i].strip()
                    link = lines[i+1].strip()
                    
                    if link.startswith('http'):
                        clean_name = name_info.split(',')[-1].strip()
                        # 仅保留符合电影、电视剧及中文关键词的频道
                        if any(kw.lower() in clean_name.lower() for kw in KEYWORDS):
                            temp_list.append((name_info, link))

            # 并发检测
            with ThreadPoolExecutor(max_workers=30) as executor:
                results = list(executor.map(check_url, temp_list))

            # 去重：同名频道保留速度最快的
            for res in results:
                if res:
                    c_name = res["name"].split(',')[-1].strip()
                    if c_name not in unique_channels or res["speed"] < unique_channels[c_name]["speed"]:
                        unique_channels[c_name] = res
            
            print(f"✅ {filename} 筛选完成")
        except Exception as e:
            print(f"❌ {filename} 失败: {e}")

    # 生成最终文件
    final_list = []
    for res in unique_channels.values():
        final_list.append(f"{res['name']}\n{res['url']}")

    with open("all.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n" + "\n".join(final_list))
    
    print(f"\n🚀 处理完成！已生成全覆盖列表。当前稳定频道总数: {len(final_list)}")

if __name__ == "__main__":
    main()

