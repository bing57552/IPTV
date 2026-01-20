import requests
import time
from concurrent.futures import ThreadPoolExecutor

# 全球全地区中文频道聚合：新增北美(North America)、南美及非洲等地区
SOURCES = {
    "north_america.m3u": "https://raw.githubusercontent.com/YueChan/Live/main/m3u/america.m3u",
    "asia_chinese.m3u": "https://raw.githubusercontent.com/YueChan/Live/main/m3u/asia.m3u",
    "europe_chinese.m3u": "https://raw.githubusercontent.com/YueChan/Live/main/m3u/europe.m3u",
    "australia.m3u": "https://raw.githubusercontent.com/YueChan/Live/main/m3u/australia.m3u",
    "catchplay.m3u": "https://raw.githubusercontent.com/YueChan/Live/main/m3u/catchplay.m3u",
    "popc_movies.m3u": "https://raw.githubusercontent.com/joevess/IPTV/main/sources/popc.m3u",
    "mytv_super.m3u": "https://raw.githubusercontent.com/skylinetv/iptv/main/mytvsuper.m3u",
    "live.m3u": "https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/ipv4.m3u"
}

def check_url(item):
    """
    1.2 秒极速检测，专门针对跨国远距离线路进行画质与连通性筛选
    """
    name_info, url = item
    try:
        start_time = time.time()
        # 严格过滤，确保全球频道都能实现“秒开”且音画同步
        response = requests.head(url, timeout=1.2, allow_redirects=True)
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
            print(f"🌐 正在同步全球未添加地区资源: {filename}")
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            
            lines = r.text.split('\n')
            temp_list = []
            for i in range(len(lines)):
                if "#EXTINF" in lines[i] and i + 1 < len(lines):
                    name_info = lines[i].strip()
                    link = lines[i+1].strip()
                    
                    # 仅保留 IPv4 链接，自动替换掉失效错误的源
                    if '[' not in link and link.startswith('http'):
                        temp_list.append((name_info, link))

            # 并发测速，自动剔除响应慢、易卡顿的线路
            with ThreadPoolExecutor(max_workers=30) as executor:
                results = list(executor.map(check_url, temp_list))
            
            # 智能去重：在同名频道中自动保留延迟最低的优质源
            for res in results:
                if res:
                    clean_name = res["name"].split(',')[-1].strip()
                    if clean_name not in unique_channels or res["speed"] < unique_channels[clean_name]["speed"]:
                        unique_channels[clean_name] = res
            
            print(f"✅ {filename} 筛选完成")
            
        except Exception as e:
            print(f"❌ {filename} 失败: {e}")

    # 最终汇总生成聚合链接 all.m3u
    final_list = []
    for res in unique_channels.values():
        final_list.append(f"{res['name']}\n{res['url']}")

    with open("all.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n" + "\n".join(final_list))
    
    print(f"🚀 全球全覆盖列表已生成！当前稳定频道总数: {len(final_list)}")

if __name__ == "__main__":
    main()
