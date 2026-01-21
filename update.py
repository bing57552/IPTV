import os
import json
import re
import subprocess
from datetime import datetime

RAW_FILE = "raw_sources.txt"
PREMIUM_FILE = "premium_sources.json"
OUTPUT_DIR = "all.m3u"

# ---------- 工具函数 ----------

def ensure_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)

def safe_id(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_") or "ch"

# ---------- 分类规则 ----------

def detect_group(name: str) -> str:
    n = name.lower()
    if any(k in n for k in ["tvb", "翡翠", "明珠", "无线", "香港", "hk", "j2"]):
        return "HK"
    if any(k in n for k in ["台視", "華視", "民視", "中視", "東森", "緯來", "三立", "八大", "年代", "非凡", "tw", "台灣", "台湾"]):
        return "TW"
    if any(k in n for k in ["astro", "malaysia", "my", "马来", "大马"]):
        return "MY"
    if any(k in n for k in ["singapore", "sg", "新加坡"]):
        return "SG"
    if any(k in n for k in ["chc", "catchplay", "美亚", "美亞", "电影", "電影", "movie", "影院"]):
        return "Movie"
    return "International"

# ---------- 生成 M3U ----------

def write_m3u(filename, channels):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in channels:
            f.write(
                f'#EXTINF:-1 tvg-id="{ch.get("tvg_id", "")}" '
                f'tvg-name="{ch["name"]}" '
                f'tvg-logo="{ch.get("logo", "")}" '
                f'group-title="{ch["group"]}",{ch["name"]}\n'
            )
            f.write(f'{ch["best_source"]}\n')

# ---------- 生成 index.html ----------

def generate_index_html(channels):
    html = [
        "<html><head><meta charset='utf-8'><title>频道导航</title>",
        "<style>body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif;padding:20px;}ul{line-height:1.8}</style>",
        "</head><body>",
        "<h1>频道导航</h1>",
        "<ul>",
    ]
    groups = sorted(set(ch["group"] for ch in channels))
    for g in groups:
        html.append(f'<li><a href="{g.lower()}.m3u">{g}</a></li>')
    html.append("</ul>")
    html.append(f"<p>频道总数：{len(channels)}</p>")
    html.append(f"<p>更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")
    html.append("</body></html>")

    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write("\n".join(html))

# ---------- 生成 api.json ----------

def generate_api_json(channels):
    with open(os.path.join(OUTPUT_DIR, "api.json"), "w", encoding="utf-8") as f:
        json.dump(channels, f, ensure_ascii=False, indent=2)

# ---------- 第一步：从 raw_sources.txt 生成 premium_sources.json ----------

def build_premium_from_raw():
    if not os.path.exists(RAW_FILE):
        print(f"[错误] 未找到 {RAW_FILE}，请在根目录创建并填入：频道名,URL")
        return None

    premium = {}
    with open(RAW_FILE, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]

    for line in lines:
        if "," not in line:
            print(f"[跳过] 格式不正确（缺少逗号）：{line}")
            continue
        name, url = line.split(",", 1)
        name = name.strip()
        url = url.strip()
        if not name or not url:
            print(f"[跳过] 名称或 URL 为空：{line}")
            continue

        cid = safe_id(name)
        group = detect_group(name)

        premium[cid] = {
            "name": name,
            "group": group,
            "logo": "",
            "tvg_id": "",
            "sources": [
                {
                    "url": url,
                    "stability_score": 1.0
                }
            ]
        }

    with open(PREMIUM_FILE, "w", encoding="utf-8") as f:
        json.dump(premium, f, ensure_ascii=False, indent=2)

    print(f"[完成] 已根据 {RAW_FILE} 生成 {PREMIUM_FILE}，频道数：{len(premium)}")
    return premium

# ---------- 第二步：从 premium_sources.json 生成 all.m3u & 子表 ----------

def build_all_from_premium(premium):
    ensure_folder(OUTPUT_DIR)

    channels = []
    groups = {}

    for cid, ch in premium.items():
        sources = ch.get("sources") or []
        if not sources:
            continue
        # 未来可以扩展为按稳定性排序
        best = sorted(
            sources,
            key=lambda s: s.get("stability_score", 0),
            reverse=True
        )[0]

        channel = {
            "id": cid,
            "name": ch.get("name", ""),
            "group": ch.get("group", "Other"),
            "logo": ch.get("logo", ""),
            "tvg_id": ch.get("tvg_id", ""),
            "best_source": best["url"],
        }
        channels.append(channel)
        groups.setdefault(channel["group"], []).append(channel)

    # all.m3u
    write_m3u(os.path.join(OUTPUT_DIR, "all.m3u"), channels)
    print(f"[完成] 生成 {OUTPUT_DIR}/all.m3u，频道数：{len(channels)}")

    # 各 group 子表
    for g, chs in groups.items():
        filename = os.path.join(OUTPUT_DIR, f"{g.lower()}.m3u")
        write_m3u(filename, chs)
        print(f"[完成] 生成 {filename}，频道数：{len(chs)}")

    # index.html & api.json
    generate_index_html(channels)
    generate_api_json(channels)
    print(f"[完成] 生成 {OUTPUT_DIR}/index.html 和 {OUTPUT_DIR}/api.json")

# ---------- 第三步：自动 git 提交 & 推送 ----------

def git_commit_and_push():
    print("[Git] add ...")
    subprocess.run(["git", "add", "."], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print("[Git] commit ...")
    subprocess.run(
        ["git", "commit", "-m", "Auto update all.m3u"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    print("[Git] push ...")
    subprocess.run(["git", "push"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("[Git] 完成推送")

# ---------- 主流程 ----------

def main():
    print("=== IPTV 一键全自动 update.py 开始 ===")

    # 1. 从 raw_sources.txt 构建 premium_sources.json
    premium = build_premium_from_raw()
    if premium is None:
        return

    # 2. 从 premium_sources.json 构建 all.m3u & 子表 & HTML & API
    build_all_from_premium(premium)

    # 3. 自动 git 提交 & 推送
    git_commit_and_push()

    print("=== 全部完成 ===")

if __name__ == "__main__":
    main()