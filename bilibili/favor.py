import requests
import json
import pandas as pd
import time
import random

# === 1. 配置请求头（带上完整 Cookie） ===
SEARCH_API_URL = "https://api.bilibili.com/x/web-interface/search/type"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Referer": "https://www.bilibili.com",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Cookie": "buvid3=398C56EA-E2EB-9234-A8B5-483E3915D46904348infoc; b_nut=1755670204; b_lsid=C566ED77_198C6194977; _uuid=1021059534-886D-9262-9E29-EFD10F4BB3AE502750infoc; buvid_fp=f9e6a6e7b1d190041c09aa3d424289c2; enable_web_push=DISABLE; home_feed_column=4; browser_resolution=1392-774; buvid4=124A2355-9D5D-01DA-424C-5BF2C054C98706786-025082014-qv5EdZTw78iXQmuL69JeYg%3D%3D; csrf_state=8fd2456da7098f3f4efbefc318e63d2d; SESSDATA=77f38c34%2C1771222226%2C8f9e1%2A82CjAeXQ1h9lmBvCpNY0CRM-ogSQC0VbIZB6BbOSAYGVGtIge7GGt19GiZJM4yJSwZ_lMSVnE0c1JLcndGS3J4R2ZpYjI4SHVvVEZkOXNNekFqdy1qOXh1c01uSWFTV3U2YVlpSktLZWtZbTNyaDBSb2NlQmRKTWZ4cHVHaFNOekhKWjJjN1FsZk1nIIEC; bili_jct=084548c16163a7ad84de652103ce5e5d; DedeUserID=295649114; DedeUserID__ckMd5=7c888cfe0108b5cc; sid=6zro7vnf; theme-tip-show=SHOWED; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTU5Mjk0NDYsImlhdCI6MTc1NTY3MDE4NiwicGx0IjotMX0.wn3UiOz1wuh4kQx3TK9LLUmC334j4OOPsSRnq0lnUME; bili_ticket_expires=1755929386; CURRENT_FNVAL=2000"
}

# === 2. 查找番剧的 season_id ===
def find_bangumi_season_id(keyword: str):
    print(f"[*] 正在搜索: {keyword}")
    params = {"search_type": "media_bangumi", "keyword": keyword}
    try:
        response = requests.get(SEARCH_API_URL, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("code") == 0:
            results = data.get("data", {}).get("result")
            if not results:
                return None
            top_result = results[0]
            season_id = top_result.get("season_id")
            title = top_result.get("title", "").replace('<em class="keyword">', '').replace('</em>', '')
            if season_id:
                print(f"[✓] 匹配到番剧: {title}, season_id: {season_id}")
                return {"season_id": season_id, "title": title}
    except Exception as e:
        print(f"[!] 搜索失败: {e}")
    return None

# === 3. 根据 season_id 获取番剧数据 ===
def get_series_total_stats(season_id: int):
    url = "https://api.bilibili.com/pgc/view/web/season"
    params = {"season_id": season_id}
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 0:
            print(f"[!] API错误: {data.get('message')}")
            return None

        result = data.get("result", {})
        stat_info = result.get("stat", {})
        rating_info = result.get("rating", {})

        return {
            "title": result.get("season_title", "N/A"),
            "plays": stat_info.get("views"),
            "likes": stat_info.get("likes"),
            "comments": stat_info.get("reply"),
            "shares": stat_info.get("share"),
            "favorites": stat_info.get("favorites"),
            "rating_count": rating_info.get("count")
        }
    except Exception as e:
        print(f"[!] 数据获取失败: {e}")
        return None

# === 4. 主流程 ===
def main():
    input_file = "all.xlsx"      # 输入文件
    sheet_name = "anime"                # Sheet名字
    output_file = "anime_stats_result.xlsx"

    df = pd.read_excel(input_file, sheet_name=sheet_name)
    anime_names = df["anime"].tolist()
    results = []

    for name in anime_names:
        row = {"anime": name}
        info = find_bangumi_season_id(name)
        if info:
            row["season_id"] = info["season_id"]
            row["title_match"] = info["title"]
            stats = get_series_total_stats(info["season_id"])
            if stats:
                row.update(stats)
        else:
            row["season_id"] = None
            row["title_match"] = None
        results.append(row)

        # 随机延迟 2~5 秒，防风控
        time.sleep(random.uniform(2, 5))

    pd.DataFrame(results).to_excel(output_file, index=False)
    print(f"\n✅ 任务完成，结果已保存到: {output_file}")

if __name__ == "__main__":
    main()



