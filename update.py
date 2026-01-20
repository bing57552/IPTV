import requests
import time
from concurrent.futures import ThreadPoolExecutor

# 1. 配置全球影视多维源：涵盖北美、欧洲、亚洲(新马)及专业影视
SOURCES = {
    "north_america": "https://raw.githubusercontent.com/YueChan/Live/main/m3u/america.m3u",
    "europe": "https://raw.githubusercontent.com/YueChan/Live/main/m3u/europe.m3u",
    "asia_chinese": "https://raw.githubusercontent.com/YueChan/Live/main/m3u/asia.m3u",
    "southeast_asia": "https://raw.githubusercontent.com/YueChan/Live/main/m3u/singapore_malaysia.m3u",
    "itv_movie_special": "https://itvlist.cc/itv.m3u",
    "global_zh": "https://iptv-org.github.io/iptv/languages/zho.m3u",
    "fanmingming_live": "https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/ipv4.m3u"
}

# 2. 电影与电视剧精准筛选关键词
KEYWORDS = ["电影", "电视剧", "剧场", "影院", "TVB", "翡翠", "星河", "华丽", "Drama", "Movie", "中文", "华语", "Channel 8", "U频道"]

def check_url(item):
    """自动筛选有效不卡顿的直播源"""
    name_info, url = item
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        start_time = time.time()
        # 针对全球线路，设置2.0s超时，防止误删优质海外源但确保流畅性
        response = requests.head(url, headers=headers, timeout=2.0, allow_redirects=True)
        end_time = time.time()
        
        # 只有返回 200 (状态正常) 的链接会被保留，实现自动删除无效源
        if response.status_code == 200:
            return {"name": name_info, "url": url, "speed": end_time - start_time}
    except:
        pass
    return None

def main():
    # 使用字典进行自动去重，确保每个频道只保留最优源
    unique_channels = {}
    
    for filename, url in SOURCES.items():
        try:
            print(f"🌐 正在同步全球资源: {filename}")
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
                        # 仅保留包含影视关键词的频道
                        if any(kw.lower() in clean_name.lower() for kw in KEYWORDS):
                            temp_list.append((name_info, link))

            # 并发测速筛选
            with ThreadPoolExecutor(max_workers=30) as executor:
                results = list(executor.map(check_url, temp_list))

            # 智能更新：若同名频道已有，则仅保留响应最快的源
            for res in results:
                if res:
                    c_name = res["name"].split(',')[-1].strip()
                    if c_name not in unique_channels or res["speed"] < unique_channels[c_name]["speed"]:
                        unique_channels[c_name] = res
            
            print(f"✅ {filename} 筛选完成")
        except Exception as e:
            print(f"❌ {filename} 同步失败: {e}")

    # 汇总生成最终的 all.m3u 文件
    final_list = ["#EXTM3U"]
    for res in unique_channels.values():
        final_list.append(f"{res['name']}\n{res['url']}")

    with open("all.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(final_list))
    
    print(f"\n🚀 处理完成！已生成全球影视全覆盖列表。当前频道总数: {len(unique_channels)}")

if __name__ == "__main__":
    main()



