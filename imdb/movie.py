import requests
import pandas as pd
import time
import random
import re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
}

API_KEY = "dc12094d"   # 👈 在这里填入你申请的 API Key


# ------------------------
# 1️⃣ 读取动漫名称
# ------------------------
def read_anime_names(file_path):
    df = pd.read_excel(file_path, sheet_name="movie")
    return df["anime"].dropna().tolist()


# ------------------------
# 2️⃣ 获取英文名或中文名（无调试打印）
# ------------------------
def get_primary_names(anime_name):
    headers_bgmtv = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}
    try:
        search_url = "https://api.bgm.tv/v0/search/subjects"
        res = requests.post(
            search_url,
            json={"keyword": anime_name, "filter": {"type": [2]}, "sort": "rank", "limit": 1},
            headers=headers_bgmtv, timeout=10
        )
        data = res.json().get("data", [])
        if not data:
            return [anime_name]

        subject = data[0]
        cn_name = subject.get("name_cn", "").strip()
        en_name = None

        # 1️⃣ 从 other_names 查找英文名
        for name in subject.get("other_names", []):
            if re.match(r"^[A-Za-z0-9 ,:'!?.-]+$", name):
                en_name = name.strip()
                break

        # 2️⃣ 如果还没找到英文名，从 infobox 查找
        if not en_name:
            subject_id = subject.get("id")
            detail_url = f"https://api.bgm.tv/v0/subjects/{subject_id}"
            detail_res = requests.get(detail_url, headers=headers_bgmtv, timeout=10)
            infobox = detail_res.json().get("infobox", [])
            for entry in infobox:
                key = entry.get("key", "").lower()
                val = entry.get("value", "")
                if "英文" in key or "别名" in key or "简称" in key:
                    if isinstance(val, list):
                        vals = [v.get("v", "") if isinstance(v, dict) else v for v in val]
                    else:
                        vals = re.split(r"[、，,\s/]", val)
                    for v in vals:
                        v = v.strip()
                        if re.match(r"^[A-Za-z0-9 ,:'!?.-]+$", v):
                            en_name = v
                            break
                if en_name:
                    break

        names_to_search = []
        if en_name:
            names_to_search.append(en_name)
        if cn_name:
            names_to_search.append(cn_name)

        return names_to_search if names_to_search else [anime_name]

    except Exception:
        return [anime_name]


# ------------------------
# 3️⃣ IMDb 查询（OMDb API）
# ------------------------
def get_imdb_info(name_list):
    for movie_name in name_list:
        try:
            url = "https://www.omdbapi.com/"
            params = {
                "apikey": API_KEY,
                "t": movie_name
            }
            res = requests.get(url, params=params, timeout=10)
            data = res.json()

            if data.get("Response") == "True":
                return {
                    "original_name": name_list[0],
                    "imdb_name": data.get("Title"),
                    "rating": data.get("imdbRating"),
                    "votes": data.get("imdbVotes"),
                    "rank": data.get("imdbID")  # IMDb ID 备用
                }
            else:
                continue
        except Exception:
            continue

    # 所有名字都找不到
    return {
        "original_name": name_list[0],
        "imdb_name": None,
        "rating": None,
        "votes": None,
        "rank": None
    }


# ------------------------
# 4️⃣ 批量处理
# ------------------------
anime_list = read_anime_names("newall_cleaned.xlsx")
results = []

for anime in anime_list:
    names_to_search = get_primary_names(anime)  # 英文名+中文名
    info = get_imdb_info(names_to_search)
    results.append(info)
    time.sleep(random.uniform(1, 3))  # 防止请求过快

# 保存结果
out_df = pd.DataFrame(results, columns=["original_name", "imdb_name", "rating", "votes", "rank"])
out_df.to_csv("movie_imdb_results_new.csv", index=False, encoding="utf-8-sig")



