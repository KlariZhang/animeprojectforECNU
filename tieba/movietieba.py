# -*- coding: utf-8 -*-
"""
批量抓取百度贴吧的关注数 & 帖子数（Excel 输入版）
----------------------------------------------------
· 读入 all.xlsx → sheet1 → anime 列（UTF-8）
· 调用 get_stats() 得到 (followers, posts)
· 写出 tieba_stats_from_excel.csv：anime,followers,posts
"""
import csv, requests, json, re, time
from pathlib import Path
from urllib.parse import quote_plus
from typing import Optional, Dict, Tuple

# 如果你的环境没有 pandas，请先：pip install pandas openpyxl
import pandas as pd

# ---------- 原始配置 & 函数，保持不变 ----------
MOBILE_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                   "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                   "Version/16.0 Mobile/15E148 Safari/604.1"),
    "Referer": "https://tieba.baidu.com/",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

def safe_json(txt: str):
    txt = txt.strip()
    if txt.startswith(("callback(", "jsonp")):
        txt = re.sub(r'^[^(]*\(|\)\s*;?$', "", txt, 1)
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return {}

def get_stats(kw: str,
              cookies: Optional[Dict[str, str]] = None
              ) -> Optional[Tuple[int, int]]:
    kw_enc = quote_plus(kw)
    apis = [
        f"https://tieba.baidu.com/mo/q/forum/getforum?kw={kw_enc}&with_group=1&ie=utf-8",
        f"https://tieba.baidu.com/f/commit/ShareApi?ie=utf-8&kw={kw_enc}&fr=share",
    ]

    sess = requests.Session()
    if cookies:
        sess.cookies.update(cookies)

    followers = posts = None
    for url in apis:
        try:
            r = sess.get(url, headers=MOBILE_HEADERS, timeout=10)
        except requests.RequestException:
            continue

        data = safe_json(r.text)
        fi   = data.get("data", {}).get("forum_info", {})

        followers = followers or fi.get("member_num") or data.get("data", {}).get("fans")
        posts     = posts     or fi.get("post_num")   or fi.get("thread_num") \
                               or data.get("data", {}).get("post_num")

        if followers and posts:
            break

        if not followers:
            m = re.search(r'"member_num":\s*"?(?P<n>\d+)"?', r.text)
            if m: followers = m.group("n")
        if not posts:
            m = re.search(r'"(?:post_num|thread_num)":\s*"?(?P<n>\d+)"?', r.text)
            if m: posts = m.group("n")

        if followers and posts:
            break

    if followers and posts:
        return int(followers), int(posts)
    return None
# ---------------------------------------------------

def main():
    # === 修改点 1：输入改为 Excel 的 sheet1.anime ===
    excel_path = Path("newall_cleaned.xlsx")
    sheet_name = "movie"      # 若你的工作表名是 "Sheet1" 或其他，请改这里
    target_col = "anime"       # 目标列名（不区分大小写）

    if not excel_path.exists():
        print("❌ all.xlsx 不存在，请把 Excel 放到脚本同目录或修改 excel_path。")
        return

    try:
        df = pd.read_excel(excel_path, sheet_name=sheet_name, engine="openpyxl")
    except ValueError:
        # 如果 sheet1 不存在，就读第一个工作表
        df = pd.read_excel(excel_path, sheet_name=0, engine="openpyxl")

    # 兼容大小写与两侧空格
    cols_lc = {str(c).strip().lower(): c for c in df.columns}
    if target_col.lower() not in cols_lc:
        print(f"❌ 没找到名为 '{target_col}' 的列。当前列有：{list(df.columns)}")
        return
    real_col = cols_lc[target_col.lower()]

    names = (
        df[real_col]
        .dropna()
        .astype(str)
        .map(lambda s: s.strip())
    )
    names = [n for n in names if n]  # 去空
    if not names:
        print("❌ anime 列为空。")
        return

    outfile = Path("tieba_stats_from_excelmovie_new.csv")
    results = []  # [(anime, followers, posts), …]

    for name in names:
        stats = get_stats(name)
        if stats:
            followers, posts = stats
            print(f"{name} ✔︎ 关注 {followers:,}  帖子 {posts:,}")
        else:
            followers = posts = None
            print(f"{name} ✘ 获取失败")

        results.append((name, followers, posts))
        time.sleep(1)  # 适当休眠

    # === 输出 CSV（与原版一致，只是文件名不同）===
    with outfile.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["movie", "followers", "posts"])
        writer.writerows(results)

    print(f"\n✅ 已写出 {outfile}（{len(results)} 行）")

if __name__ == "__main__":
    main()
