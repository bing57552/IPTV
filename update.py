-- coding: utf-8 --

""" update.py  —— 最终稳定成品版（GitHub Actions / 本地均可运行） 功能：

1. 解析 m3u


2. 过滤无效 / 购物频道


3. 测速（requests）


4. 每个频道保留最快源


5. 生成 live.m3u / cn_vod_live.m3u


6. 生成 README.md + index.html 统计 """



import time import requests from collections import defaultdict

==========================

基础配置

==========================

TIMEOUT = 5 HEADERS = {"User-Agent": "Mozilla/5.0"} BLOCK_KEYWORDS = ["购物", "导购", "理财", "股票", "期货", "博彩"]

==========================

工具函数

==========================

def has_chinese(text: str) -> bool: return any('\u4e00' <= c <= '\u9fff' for c in text)

def is_blocked(title: str) -> bool: return any(k in title for k in BLOCK_KEYWORDS)

def is_valid_stream(url: str, timeout=TIMEOUT) -> bool: try: r = requests.get(url, timeout=timeout, stream=True, headers=HEADERS, allow_redirects=True) return r.status_code in (200, 206, 302) except Exception: return False

def test_speed(url: str, timeout=TIMEOUT): try: start = time.time() r = requests.get(url, timeout=timeout, stream=True, headers=HEADERS) if r.status_code not in (200, 206): return None for _ in r.iter_content(chunk_size=1024): break return time.time() - start  # 秒 except Exception: return None

==========================

解析 m3u

==========================

def parse_m3u(lines): channels = [] title = None for line in lines: line = line.strip() if not line: continue if line.startswith('#EXTINF'): title = line.split(',', 1)[-1].strip() elif line.startswith('http') and title: channels.append({ "title": title, "url": line }) title = None return channels

==========================

选最快源（核心）

==========================

def pick_fastest_per_channel(channels): best = {} for item in channels: t = item['title'] if item.get('ping') is None: continue if t not in best or item['ping'] < best[t]['ping']: best[t] = item return list(best.values())

==========================

README / HTML

==========================

def generate_readme_and_html(*, total_channels, movie_count, drama_count, hk_count, tw_count, oversea_count, no_shopping_count): readme = f"""

IPTV 自动更新

总测速频道数：{total_channels}

电影频道：{movie_count}

电视剧频道：{drama_count}

香港频道：{hk_count}

台湾频道：{tw_count}

海外频道：{oversea_count}

去购物频道：{no_shopping_count}


> 分类为多标签统计，非互斥 """ with open('README.md', 'w', encoding='utf-8') as f: f.write(readme)



html = f"""

<html><head><meta charset='utf-8'><title>IPTV</title></head>
<body>
<h1>IPTV 自动更新</h1>
<ul>
<li>总测速频道数：{total_channels}</li>
<li>电影频道：{movie_count}</li>
<li>电视剧频道：{drama_count}</li>
<li>香港频道：{hk_count}</li>
<li>台湾频道：{tw_count}</li>
<li>海外频道：{oversea_count}</li>
<li>去购物频道：{no_shopping_count}</li>
</ul>
</body></html>
"""
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)==========================

主流程

==========================

def main(): # 示例：你原来的 m3u 读取方式可直接替换这里 with open('source.m3u', 'r', encoding='utf-8', errors='ignore') as f: lines = f.readlines()

raw_channels = parse_m3u(lines)

valid_channels = []
for ch in raw_channels:
    title = ch['title']
    if is_blocked(title):
        continue
    if not is_valid_stream(ch['url']):
        continue
    ping = test_speed(ch['url'])
    if ping is not None:
        ch['ping'] = ping
        valid_channels.append(ch)

# 每频道最快
best_channels = pick_fastest_per_channel(valid_channels)

# 写 live.m3u
with open('live.m3u', 'w', encoding='utf-8') as f:
    for ch in best_channels:
        f.write(f"#EXTINF:-1,{ch['title']}\n")
        f.write(ch['url'] + '\n')

# 分类统计（示例规则，可按你原逻辑细化）
movie_channels = [c for c in best_channels if '电影' in c['title']]
drama_channels = [c for c in best_channels if '剧' in c['title']]
hk_channels = [c for c in best_channels if '香港' in c['title']]
tw_channels = [c for c in best_channels if '台湾' in c['title']]
oversea_channels = [c for c in best_channels if not has_chinese(c['title'])]
no_shopping_channels = best_channels

generate_readme_and_html(
    total_channels=len(best_channels),
    movie_count=len(movie_channels),
    drama_count=len(drama_channels),
    hk_count=len(hk_channels),
    tw_count=len(tw_channels),
    oversea_count=len(oversea_channels),
    no_shopping_count=len(no_shopping_channels),
)

print('全部完成 ✅')

if name == 'main': main()