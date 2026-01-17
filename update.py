import os
import requests
import time

# 过滤购物台关键词
BLOCK_KEYWORDS = ["购物", "shop", "momo", "东森购物", "年代购物", "tvbs欢乐购物"]

# 响应时间阈值（秒）
MAX_DELAY = 2

# 超时时间（秒）
TIMEOUT = 3

def is_shopping_channel(line):
    return any(keyword.lower() in line.lower() for keyword in BLOCK_KEYWORDS)

def test_url(url):
    """测试直播源是否可用 + 测速"""
    try:
        start = time.time()
        r = requests.get(url, timeout=TIMEOUT)
        delay = time.time() - start
        if r.status_code == 200 and delay < MAX_DELAY:
            return True
    except:
        pass
    return False

def clean_m3u_file(filepath):
    print(f"清理文件：{filepath}")

    new_lines = []
    urls_seen = set()
    current_title = ""

    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()

        # 处理频道名称
        if line.startswith("#EXTINF"):
            if is_shopping_channel(line):
                continue
            current_title = line
            continue

        # 处理 URL
        if line.startswith("http"):
            url = line

            # 去重
            if url in urls_seen:
                continue
            urls_seen.add(url)

            # 测试可用性
            if test_url(url):
                new_lines.append(current_title + "\n")
                new_lines.append(url + "\n")

    # 写回文件
    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"完成：{filepath}（保留 {len(new_lines)//2} 个频道）")

def main():
    print("开始清理所有 m3u 文件...\n")

    for filename in os.listdir("."):
        if filename.endswith(".m3u"):
            clean_m3u_file(filename)

    print("\n全部完成！")

if __name__ == "__main__":
    main()