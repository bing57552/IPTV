import glob, re, qrcode, datetime

def parse_m3u(file):
    entries = []
    with open(file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for i in range(len(lines)):
        if lines[i].startswith("#EXTINF"):
            info = lines[i].strip()
            url = lines[i+1].strip() if i+1 < len(lines) else ""
            entries.append((info, url))
    return entries

# 合并
all_entries = []
seen = set()

for file in glob.glob("sources/*.m3u"):
    for info, url in parse_m3u(file):
        key = (info, url)
        if key not in seen:
            seen.add(key)
            all_entries.append((info, url))

# 输出 all.m3u
with open("all.m3u", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    for info, url in all_entries:
        f.write(info + "\n")
        f.write(url + "\n")

# 统计
groups = {}
for info, _ in all_entries:
    m = re.search(r'group-title="([^"]+)"', info)
    if m:
        g = m.group(1)
        groups[g] = groups.get(g, 0) + 1

# 生成 README.md
now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

with open("README.md", "w", encoding="utf-8") as f:
    f.write("# 📺 Auto IPTV Playlist\n")
    f.write(f"**Last update:** {now}\n\n")
    f.write(f"**Total channels:** {len(all_entries)}\n\n")
    f.write("## 📌 Group Statistics\n")
    for g, c in groups.items():
        f.write(f"- **{g}**: {c}\n")

    f.write("\n## 🔗 Playlist URL\n")
    f.write("```\n")
    f.write("https://raw.githubusercontent.com/USERNAME/REPO/main/all.m3u\n")
    f.write("```\n")

# 生成 HTML 入口页
html = """
<html>
<head><meta charset="utf-8"><title>IPTV Playlist</title></head>
<body>
<h2>IPTV Playlist</h2>
<p>Click to download:</p>
<a href="all.m3u">Download all.m3u</a>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

# 生成二维码
img = qrcode.make("https://raw.githubusercontent.com/USERNAME/REPO/main/all.m3u")
img.save("qrcode.png")

print("更新完成，共输出频道：", len(all_entries))