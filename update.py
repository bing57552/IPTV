import os

def get_channel_logic(name, url):
    n = str(name).upper().replace(" ", "")
    u = str(url).lower()

    # 只要名字含这些，绝对放行并分到电影组
    premium_movie = ["ASTRO", "CHC", "CATCHPLAY", "POPC", "美亚", "DISNEY", "NETFLIX", "MOVIE", "电影", "影视", "CELESTIAL", "天映"]
    
    if any(brand in n for brand in premium_movie):
        return "电影频道", False
    
    # 港台组
    if any(brand in n for brand in ["TVB", "MYTV", "GTV", "SUPER", "TW", "HK", "纬来", "龙祥", "东森"]):
        return "港台频道", False

    # 购物黑名单
    blacklist = ["QVC", "HSN", "JEWELRY", "JTV", "SHOPHQ", "EVINE", "GEM", "TSC", "TJC", "MOMO", "购物", "特卖", "商城"]
    if any(key in n for key in blacklist):
        return "垃圾购物台", True

    return "综合频道", False

def main():
    # 你的文件已经确认是 demo.txt 了，保持不变
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
