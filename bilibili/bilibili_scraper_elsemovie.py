# ===【0. 公共导入和配置】===
import os
import time
import json
import requests
import pandas as pd
from tqdm import tqdm
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
BILIBILI_COOKIE = os.getenv("BILIBILI_COOKIE")

# === 文件路径配置 ===
INPUT_XLSX = "C:/Code/python/animeproject/bilibili/all.xlsx"  # 输入文件
OUTPUT_CSV = "C:/Code/python/animeproject/bilibili/fanmade_results_all_movie.csv"  # 输出文件
MAX_PAGES_PER_KEYWORD = 3  # 每个关键词爬取页数

# === B 站搜索接口 ===
def bvid_search(keyword, page):
    url = "https://api.bilibili.com/x/web-interface/search/type"
    params = {"search_type": "video", "keyword": keyword, "page": page}
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.bilibili.com/",
        "Origin": "https://www.bilibili.com",
        "Accept": "application/json",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cookie": BILIBILI_COOKIE
    }
    try:
        res = requests.get(url, params=params, headers=headers)
        res.raise_for_status()
        return res.json().get("data", {}).get("result", [])
    except Exception as e:
        print(f"❌ 请求失败：{keyword} - 第{page}页 - 错误：{e}")
        return []

# === CSV 读取动漫名称 ===
# === CSV/Excel 读取动漫名称 ===
def read_anime_names(excel_path):
    # 指定 sheet_name="anime"，读取 anime 列
    df = pd.read_excel(excel_path, sheet_name="movie")
    anime_list = df["movie"].dropna().tolist()
    print(f"✅ 成功读取 {len(anime_list)} 个动漫名称")
    return anime_list


# === 抓取所有搜索结果 ===
def collect_all_videos(anime_list):
    results = []
    for anime_name in tqdm(anime_list, desc="处理动漫中"):
        for page in range(1, MAX_PAGES_PER_KEYWORD + 1):
            videos = bvid_search(anime_name, page)
            for video in videos:
                results.append({
                    "所属动漫": anime_name,
                    "视频标题": video.get("title", ""),
                    "播放量": video.get("play"),
                    "弹幕数": video.get("video_review"),
                    "收藏数": video.get("favorites"),
                    "UP主": video.get("author", ""),
                    "标签": video.get("tag", ""),
                    "bvid": video.get("bvid"),
                    "url": f"https://www.bilibili.com/video/{video.get('bvid')}"
                })
            time.sleep(0.5)
    return results

# === 主交互式菜单入口 ===
def main():
    while True:
        print("\n📌 请选择要执行的功能：")
        print("1. 抓取多个动漫的全部搜索视频（不筛选）")
        print("0. 退出程序")

        choice = input("请输入选项编号: ").strip()

        if choice == "1":
            input_path = input(f"请输入包含动漫名称的CSV路径（默认: {INPUT_XLSX}）: ").strip() or INPUT_XLSX

            output_path = input(f"请输入输出结果CSV路径（默认: {OUTPUT_CSV}）: ").strip() or OUTPUT_CSV
            anime_list = read_anime_names(input_path)
            results = collect_all_videos(anime_list)
            pd.DataFrame(results).to_csv(output_path, index=False, encoding="utf-8-sig")
            print(f"✅ 已保存所有搜索视频记录到 {output_path}")

        elif choice == "0":
            print("退出程序。")
            break
        else:
            print("无效输入，请重试。")

# === 程序入口点 ===
if __name__ == "__main__":
    main()






