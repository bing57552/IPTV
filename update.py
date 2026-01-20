import requests

# 预设高清 IPv4 中文电影/电视源（不再读取本地 source.m3u）
SOURCES = {
    "live.m3u": "https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/ipv4.m3u",
    "movie.m3u": "https://raw.githubusercontent.com/mizhenye/iptv/main/m3u/movie.m3u"
}

def main():
    for filename, url in SOURCES.items():
        try:
            print(f"正在同步高清源: {filename}")
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            
            # 核心过滤：只保留 IPv4 链接（剔除带方括号 '[' 的行）
            lines = [line.strip() for line in r.text.split('\n') if '[' not in line]
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            print(f"✅ {filename} 更新成功")
        except Exception as e:
            print(f"❌ {filename} 更新失败: {e}")

if __name__ == "__main__":
    main()
