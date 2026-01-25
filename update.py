import os

def get_channel_logic(name, url):
    n = str(name).upper().replace(" ", "")
    u = str(url).lower()

    # ==========================================
    # 1. 【核心白名单】—— 增加天映(Celestial)保护
    # ==========================================
    # 只要名字含这些关键词，直接进电影/港台组，跳过过滤逻辑
    premium_movie = ["ASTRO", "CHC", "CATCHPLAY", "POPC", "美亚", "DISNEY", "NETFLIX", "MOVIE", "电影", "影视", "CELESTIAL", "天映"]
    premium_hk_tw = ["MYTV", "TVB", "GTV", "SUPER", "TW", "HK", "［TW］", "[HK]", "纬来", "龙祥", "东森"]

    if any(brand in n for brand in premium_movie):
        return "电影频道", False
    
    if any(brand in n for brand in premium_hk_tw):
        return "港台频道", False

    # ==========================================
    # 2. 【垃圾购物台黑名单】—— 依然严格过滤
    # ==========================================
    shopping_blacklist = ["QVC", "HSN", "JEWELRY", "JTV", "SHOPHQ", "EVINE", "GEMSHOPPING", "TSC", "TJC", "GEMSTV", "JUWELO", "1-2-3TV", "M6BOUTIQUE", "TELESHOPPING", "中视购物", "央广购物", "环球购物", "家有购物", "快乐购物", "好享购物", "时尚购物", "家家购物", "优购物", "风尚购物", "东方购物", "好易购", "南方购物", "宜和购物", "星空购物", "MOMO购物", "电视广播购物", "CJOSHOP", "GSSHOP", "HYUNDAIHOME", "COUPANG", "SHOPTV", "TRUESHOP", "MNCSHOP", "HOMESHOP18", "NAAPTOL", "TVSN", "购物台", "特卖", "商城"]
    url_features = ["shopping", "liveshopping", "mall", "buy-tv", "tvshop"]

    if any(key in n for key in shopping_blacklist) or any(feat in u for feat in url_features):
        return "垃圾购物台", True

    return "综合频道", False

def main():
    input_file = "demo.txt" 
    if not os.path.exists(input_file): return
    all_res, clean_res = [], []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if "," in line and "://" in line:
                try:
                    name, url = line.strip().split(",", 1)
                    group, is_shop = get_channel_logic(name, url)
                    entry = f'#EXTINF:-1 group-title="{group}",{name}\n{url}\n'
                    all_res.append(entry)
                    if not is_shop: clean_res.append(entry)
                except: continue
    with open("all.m3u", "w", encoding="utf-8") as f: f.write("#EXTM3U\n" + "".join(all_res))
    with open("no-shopping.m3u", "w", encoding="utf-8") as f: f.write("#EXTM3U\n" + "".join(clean_res))

if __name__ == "__main__": main()
