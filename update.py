import os
import requests
from collections import defaultdict

SOURCE_URL = os.environ.get(
    "M3U_SOURCE_URL",
    "https://raw.githubusercontent.com/bing57552/g/main/global_cn_4k1080p_multi.m3u"
)

OUTPUT_FILE = "ALL_IN_ONE.m3u"


def fetch_m3u(url: str) -> str:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.text


def parse_m3u(content: str):
    """
    返回结构:
    {
      (name, tvg_id, group): [url1, url2, ...]
    }
    """
    channels = defaultdict(list)

    lines = [l.strip() for l in content.splitlines() if l.strip()]
    current_info = None

    for line in lines:
        if line.startswith("#EXTINF"):
            # 解析 EXTINF
            name = line.split(",")[-1].strip()

            def pick(key):
                if f'{key}="' in line:
                    return line.split(f'{key}="')[1].split('"')[0]
                return ""

            tvg_id = pick("tvg-id")
            group = pick("group-title") or "其他"

            current_info = (name, tvg_id, group)

        elif line.startswith("#"):
            continue
        else:
            # URL 行
            if current_info:
                channels[current_info].append(line)

    return channels


def write_all_in_one(channels: dict):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")

        for (name, tvg_id, group), urls in sorted(channels.items()):
            f.write(
                f'#EXTINF:-1 tvg-id="{tvg_id}" group-title="{group}",{name}\n'
            )

            # URL 去重但保持顺序
            seen = set()
            for u in urls:
                if u not in seen:
                    seen.add(u)
                    f.write(u + "\n")

            f.write("\n")


def main():
    print("📥 下载源:", SOURCE_URL)
    content = fetch_m3u(SOURCE_URL)

    print("🔍 解析并聚合频道…")
    channels = parse_m3u(content)

    print(f"📺 聚合完成：{len(channels)} 个频道")

    print("✍️ 写入 ALL_IN_ONE.m3u")
    write_all_in_one(channels)

    print("✅ 完成")


if __name__ == "__main__":
    main()