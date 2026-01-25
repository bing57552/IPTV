import requests


# 你的m3u链接 - 按这个格式填
REMOTE_URL = "https://bing57552.github.io/g/demo.m3u"

def classify(name):
    n = name.upper()
    if any(x in n for x in ["ASTRO","CHC","CATCHPLAY","美亚","电影"]): return "电影频道", False
    if any(x in n for x in ["TVB","纬来"]): return "港台频道", False  
    if any(x in n for x in ["QVC","购物"]): return "垃圾购物台", True
    return "综合频道", False

r = requests.get(REMOTE_URL, timeout=10)
lines = r.text.split('\n')

all_m3u = ["#EXTM3U"]
clean = ["#EXTM3U"]

i = 0
while i < len(lines)-1:
    if '#EXTINF' in lines[i]:
        name = lines[i].split(',',1)[1]
        i += 1
        url = lines[i].strip()
        if url.startswith('http'):
            group, shop = classify(name)
            line = f'#EXTINF:-1 group-title="{group}",{name}
{url}
'
            all_m3u.append(line)
            if not shop: clean.append(line)
    i += 1

open("all.m3u", 'w', encoding='utf-8').write(''.join(all_m3u))
open("no-shopping.m3u", 'w', encoding='utf-8').write(''.join(clean))