import requests
from bs4 import BeautifulSoup
import csv
import time
import re

base_url = "https://chii.in/anime/browser/%E4%B8%AD%E5%9B%BD/airtime/2025-7?sort=date"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "Referer": "https://chii.in/"
}

# 预编译正则表达式匹配日期格式
date_pattern = re.compile(r'\d{4}[-年]\d{1,2}[-月]\d{1,2}[日]?')

anime_list = []
page = 1

while True:
    url = f"{base_url}&page={page}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"请求失败，状态码 {response.status_code}")
            break
    except Exception as e:
        print(f"请求异常: {e}")
        break

    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.text, "html.parser")

    items = soup.select("ul.browserFull > li > div.inner > h3 > a")
    air_dates = soup.select("ul.browserFull > li > div.inner > p.tip")

    if not items:
        break

    for i, item in enumerate(items):
        name = item.get_text(strip=True)
        airdate_text = air_dates[i].get_text(strip=True) if i < len(air_dates) else ""

        # 使用正则表达式提取日期
        date_match = date_pattern.search(airdate_text)
        airdate = date_match.group(0) if date_match else ""

        anime_list.append([name, airdate])

    print(f"第 {page} 页抓取完成，已抓取 {len(anime_list)} 个动漫")
    page += 1
    time.sleep(1)

csv_file = "china_2025_07_anime.csv"
with open(csv_file, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["Anime Name", "Airdate"])
    writer.writerows(anime_list)

print(f"\n抓取完成，总数: {len(anime_list)}，已保存到 {csv_file}")