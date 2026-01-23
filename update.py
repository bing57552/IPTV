import os

def get_channel_logic(name, url):
    """
    零失误逻辑：
    1. 白名单保护：只要名字匹配优质频道，无条件通过。
    2. 特征过滤：识别购物台专属的域名、路径关键词和频道特征。
    """
    # 预处理：统一转大写，移除空格
    n = str(name).upper().replace(" ", "")
    u = str(url).lower()

    # ==========================================
    # 第一步：【绝对白名单】—— 保护你要求的优质内容
    # ==========================================
    premium_brands = [
        "ASTRO", "CHC", "CATCHPLAY", "POPC", "MYTV", "TVB", "GTV", 
        "美亚", "DISNEY", "NETFLIX", "MOVIE", "电影", "影视",
        "TW", "HK", "［TW］", "[HK]", "SUPER", "纬来", "龙祥", "东森"
    ]

    if any(brand in n for brand in premium_brands):
        # 确定分组：港台类或电影类
        if any(x in n for x in ["TVB", "MYTV", "GTV", "SUPER", "TW", "HK"]):
            return "港台频道", False 
        return "电影频道", False

    # ==========================================
    # 第二步：【内容指纹过滤】—— 识破垃圾购物台
    # ==========================================
    shopping_fingerprints = [
        # 名字黑名单
        "QVC", "HSN", "JTV", "SHOPHQ", "EVINE", "GEMSHOPPING", "TSC", "TJC",
        "GEMSTV", "JUWELO", "1-2-3TV", "中视购物", "央广购物", "环球购物", 
        "家有购物", "快乐购物", "好享购物", "时尚购物", "家家购物", "优购物", 
        "风尚购物", "东方购物", "好易购", "南方购物", "宜和购物", "星空购物", 
        "MOMO购物", "电视广播购物", "CJOSHOP", "GSSHOP", "HYUNDAIHOME",
        "TRUESHOP", "MNCSHOP", "TVSN", "购物台", "特卖", "商城",
        # 播放地址(URL)指纹识别：通过内容来源识别
        "shopping", "liveshopping", "mall", "gxtv", "buy-tv", "tvshop"
    ]

    # 只有不在白名单的前提下，才匹配黑名单
    if any(feature in n or feature in u for feature in shopping_fingerprints):
        return "垃圾购物台", True

    return "综合频道", False

def main():
    # 注意：如果你的源文件名不是 demo.txt，请把下面这行改掉
    input_filename = "demo.txt" 
    output_all = "all.m3u"
    output_clean = "no-shopping.m3u"

    if not os.path.exists(input_filename):
        print(f"❌ 错误：找不到源文件 {input_filename}")
        return

    all_m3u = []
    clean_m3u = []

    with open(input_filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if "," in line and "://" in line:
                try:
                    name, url = line.split(",", 1)
                    group, should_filter = get_channel_logic(name, url)

                    entry = f'#EXTINF:-1 group-title="{group}",{name}\n{url}\n'
                    all_m3u.append(entry)
                    if not should_filter:
                        clean_m3u.append(entry)
                except:
                    continue

    # 写入文件
    with open(output_all, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n" + "".join(all_m3u))
    
    with open(output_clean, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n" + "".join(clean_m3u))

    print(f"✅ 任务成功：已过滤垃圾购物台，保护了优质频道。")

if __name__ == "__main__":
    main()
