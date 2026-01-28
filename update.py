import requests
import time
import os
import logging
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (IPTV-Checker)"
}

TIMEOUT = 6


# =========================
# 基础检测：是否可播
# =========================
def check_stream(url: str):
    try:
        start = time.time()
        r = requests.head(
            url,
            headers=HEADERS,
            timeout=TIMEOUT,
            allow_redirects=True,
            verify=False
        )
        delay = time.time() - start

        if r.status_code != 200:
            return False, 0

        score = 0

        # 响应时间评分
        if delay < 0.8:
            score += 100
        elif delay < 1.5:
            score += 70
        elif delay < 3:
            score += 40
        else:
            score += 10

        # 内容类型加权
        ctype = r.headers.get("Content-Type", "").lower()
        if "mpegurl" in ctype or "m3u8" in url:
            score += 50

        # 清晰度关键词加权（仅排序用）
        u = url.lower()
        if "2160" in u or "4k" in u or "uhd" in u:
            score += 300
        elif "1080" in u or "fhd" in u:
            score += 200
        elif "720" in u:
            score += 100
        else:
            score += 30

        return True, score

    except Exception:
        return False, 0


# =========================
# 主处理逻辑
# =========================
def process_m3u(m3u_text: str) -> str:
    lines = [l.strip() for l in m3u_text.splitlines() if l.strip()]
    result = ["#EXTM3U"]

    # 以「EXTINF 原文」为核心，不做任何修改
    channel_map = defaultdict(list)

    i = 0
    while i < len(lines) - 1:
        if lines[i].startswith("#EXTINF"):
            extinf = lines[i]
            url = lines[i + 1]

            # 用 EXTINF 本身作为频道唯一标识
            channel_map[extinf].append({
                "extinf": extinf,
                "url": url
            })
            i += 2
        else:
            i += 1

    logging.info(f"解析频道数：{len(channel_map)}")

    for extinf, sources in channel_map.items():
        checked = []

        for s in sources:
            ok, score = check_stream(s["url"])
            if ok:
                s["score"] = score
                checked.append(s)

        if not checked:
            logging.warning("频道无可用源，跳过")
            continue

        # 按评分排序（只影响顺序）
        checked.sort(key=lambda x: x["score"], reverse=True)

        logging.info(f"频道保留源数量：{len(checked)}")

        # ⚠️ EXTINF 原样写回，多次写 = 多源
        for s in checked:
            result.append(extinf)
            result.append(s["url"])

    return "\n".join(result)


# =========================
# 入口
# =========================
def main():
    src_url = os.getenv("M3U_SOURCE_URL")
    if not src_url:
        logging.error("未配置 M3U_SOURCE_URL")
        return

    try:
        r = requests.get(
            src_url,
            headers=HEADERS,
            timeout=15,
            allow_redirects=True,
            verify=False
        )
        r.raise_for_status()
    except Exception as e:
        logging.error(f"拉取源失败：{e}")
        return

    output = process_m3u(r.text)

    with open("output_best.m3u", "w", encoding="utf-8") as f:
        f.write(output)

    logging.info("✅ output_best.m3u 生成完成")


if __name__ == "__main__":
    main()