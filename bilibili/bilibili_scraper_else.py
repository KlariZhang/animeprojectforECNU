
# ===【0. 公共导入和配置】===
import pandas as pd
import requests
from datetime import datetime

# --- API 配置 ---
RANKING_API_URL = "https://api.bilibili.com/x/web-interface/ranking/v2"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# --- 核心抓取函数 ---
def fetch_category_ranking(rid: int):
    """
    根据分区ID抓取排行榜视频列表
    """
    params = {'rid': rid, 'type': 'all'}
    resp = requests.get(RANKING_API_URL, params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return data.get('data', {}).get('list', [])

# ========== 程序入口 ==========
if __name__ == "__main__":
    # --- 1. 读取 Excel 中动漫名 ---
    # 假设 Excel 文件名为 anime_list.xlsx，sheet 名为 anime
    # 列名为 anime
    excel_file = "all.xlsx"
    df_anime = pd.read_excel(excel_file, sheet_name="anime")
    anime_list = df_anime['anime'].dropna().tolist()  # 读取动漫名列表

    # --- 2. 抓取排行榜 ---
    rid = 1  # 动画分区
    data = fetch_category_ranking(rid)

    # --- 3. 筛选对应动漫的视频 ---
    result_list = []
    for item in data:
        title = item.get("title", "")
        for anime in anime_list:
            if anime in title:  # 模糊匹配
                stat = item.get("stat", {})
                result_list.append({
                    '动漫名': anime,
                    '标题': title,
                    'BVID': item.get("bvid"),
                    'UP主': item.get("owner", {}).get("name"),
                    '播放量': stat.get("view", 0),
                    '弹幕数': stat.get("danmaku", 0),
                    '评论数': stat.get("reply", 0),
                    '点赞数': stat.get("like", 0),
                    '投币数': stat.get("coin", 0),
                    '收藏数': stat.get("favorite", 0),
                    '分享数': stat.get("share", 0),
                    '视频链接': f"https://www.bilibili.com/video/{item.get('bvid')}"
                })

    # --- 4. 输出 CSV ---
    if result_list:
        df_result = pd.DataFrame(result_list)
        filename = f"anime_ranking_{datetime.now().strftime('%Y-%m-%d')}.csv"
        df_result.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"✅ 数据已保存到 {filename}")
    else:
        print("❌ 未匹配到任何动漫视频")
