import os
import re
import requests
import json
import aiohttp
import asyncio
import unicodedata
import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv
import random  # 加入顶部
import openpyxl

# === 随机 User-Agent 列表（防反爬） ===
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/115.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
]


MAX_PAGES_LIMIT = 50  # 最多采集每个关键词的50页，防止死循环


# === 环境变量与配置读取 ===
load_dotenv()
BILIBILI_COOKIE = os.getenv("BILIBILI_COOKIE")

# === 文件路径配置 ===
INPUT_CSV = "C:/Code/python/animeproject/repair.xlsx"
OUTPUT_CSV = "C:/Code/python/animeproject/fanmade_results_movie_repair.csv"


# === 二创相关关键词定义 ===
FANMADE_SUFFIXES = [" MAD", " 二创", " 混剪", " 同人", " AMV", " 鬼畜"]
FANMADE_TAGS = ["二创", "MAD", "混剪", "同人", "鬼畜", "AMV", "剪辑"]

# === 闲角关键词（用于过滤无意义角色） ===
EXCLUDE_ROLE_KEYWORDS = [
    "モブ", "モブキャラ", "モブキャラクター", "エキストラ",
    "路人", "群众", "群演", "小兵", "学生", "老师", "记者", "助手",
    "通行人", "观众", "村人", "村民", "男性", "女性", "少年", "少女",
    "人类", "店员", "保安", "司机", "医生", "士兵", "乘客", "服务员",
    "extra", "mob character", "闲角"
]

# === 工具函数 ===
def normalize_keyword(text):
    """标准化关键词（全角转半角并去除空格）"""
    return unicodedata.normalize('NFKC', text).strip() if isinstance(text, str) else ""

def is_valid_character_name(name):
    """判断名字是否有效且不属于闲角"""
    return bool(name) and not any(x in name for x in EXCLUDE_ROLE_KEYWORDS)

def contains_any(text, keywords):
    """检查文本中是否包含任意关键词"""
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)

def read_anime_names(csv_path):
    """从CSV文件中读取动漫名称列表"""
    df = pd.read_excel(csv_path, sheet_name="movie")  # 读取指定 sheet
    anime_list = df["movie"].dropna().tolist()  # 提取非空的“movie”列为列表
    print(f"✅ 成功读取 {len(anime_list)} 个动漫名称")
    return anime_list

def generate_search_keywords(extended_keywords):
    """返回扩展关键词列表"""
    return extended_keywords



async def search_all_pages(keyword):
    all_results = []
    async with aiohttp.ClientSession() as session:
        page = 1
                # 先访问一次 HTML 页面模拟正常浏览器行为
        search_page_url = f"https://search.bilibili.com/all?keyword={keyword}"
        await session.get(search_page_url, headers={"User-Agent": random.choice(USER_AGENTS)})
        await asyncio.sleep(random.uniform(1.0, 2.0))

        while page <= MAX_PAGES_LIMIT:
            results = await safe_bvid_search(session, keyword, page)
            if not results:
                break
            print(f"✅ 关键词【{keyword}】第 {page} 页，获取 {len(results)} 条")
            all_results.extend(results)
            page += 1
            await asyncio.sleep(random.uniform(0.8, 2.0))  # 加一点延迟更稳妥
    return all_results





# === Bangumi API：获取衍生关键词 ===
def get_extended_keywords(anime_name):
    print(f"\n🔍 正在处理：{anime_name}")
    keywords = {anime_name}
    headers = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}
    valid_keys = {"别名", "别称", "又称", "英文", "简称", "缩写", "简写", "cp", "情侣", "角色", "登场角色", "主要角色"}

    try:
        # === 1. 获取 subject_id ===
        search_url = "https://api.bgm.tv/v0/search/subjects"
        res = requests.post(search_url, json={"keyword": anime_name, "filter": {"type": [2]}, "sort": "rank", "limit": 3}, headers=headers, timeout=10)
        subject_list = res.json().get("data", [])
        if not subject_list:
            print("⚠️ 未找到相关条目")
            return list(keywords)

        subject = subject_list[0]
        subject_id = subject.get("id")
        keywords.update(filter(None, [subject.get("name", "").strip(), subject.get("name_cn", "").strip()]))
        keywords.update(subject.get("other_names", []))

        # === 2. 获取 infobox 信息 ===
        detail_url = f"https://api.bgm.tv/v0/subjects/{subject_id}"
        infobox = requests.get(detail_url, headers=headers, timeout=10).json().get("infobox", [])

        for entry in infobox:
            key = entry.get("key", "").lower()
            val = entry.get("value", "")
            if any(k.lower() in key for k in valid_keys):
                items = [v.get("v", "") if isinstance(v, dict) else v for v in val] if isinstance(val, list) else re.split(r"[、，,\s/]", val)
                keywords.update(filter(None, map(str.strip, items)))

        # === 3. 获取角色及别名 ===
        char_url = f"https://api.bgm.tv/v0/subjects/{subject_id}/characters"
        characters = requests.get(char_url, headers=headers, timeout=10).json()
        print(f"✅ 共找到 {len(characters)} 个角色")

        for char in characters:
            for name in [char.get("name", ""), char.get("name_cn", "")]:
                name = name.strip()
                if is_valid_character_name(name):
                    keywords.add(name)

            # 获取角色别名
            detail_data = requests.get(f"https://api.bgm.tv/v0/characters/{char['id']}", headers=headers, timeout=10).json()
            for entry in detail_data.get("infobox", []):
                if any(k in entry.get("key", "").lower() for k in ["别名", "简称", "cp", "称呼", "又叫", "外号"]):
                    val = entry.get("value", "")
                    items = [v.get("v", "") if isinstance(v, dict) else v for v in val] if isinstance(val, list) else re.split(r"[、，,\s/]", val)
                    keywords.update(filter(lambda x: is_valid_character_name(x.strip()), map(str.strip, items)))

    except Exception as e:
        print(f"❌ 错误：{e}")

    # === 标准化、去重、过滤 ===
    final_keywords = {normalize_keyword(k) for k in keywords if len(normalize_keyword(k)) >= 2 and is_valid_character_name(normalize_keyword(k))}
    final_list = sorted(final_keywords)
    print(f"📌 最终关键词（{len(final_list)} 项）：{final_list}")
    return final_list



# === 控制并发数量（防止 IP 被封） ===
sem = asyncio.Semaphore(8)

async def safe_bvid_search(session, keyword, page):
    async with sem:
        return await bvid_search(session, keyword, page)


# === 异步版本 B 站搜索接口 ===
async def bvid_search(session, keyword, page, retries=3):
    url = "https://api.bilibili.com/x/web-interface/search/type"
    params = {"search_type": "video", "keyword": keyword, "page": page}
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": "https://www.bilibili.com/",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Origin": "https://www.bilibili.com",
        "Accept": "application/json",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cookie": BILIBILI_COOKIE
    }
    for attempt in range(retries):
        try:
            async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                json_data = await resp.json()
            return json_data.get("data", {}).get("result", [])
        except Exception as e:
            print(f"❌ 请求失败：{keyword} - 第{page}页 - 错误：{e}")
            return []


# === 二创视频筛选逻辑 ===
def is_official_author(name):
    return any(k in name for k in ["官方", "出品", "制作委员会", "动画官方"])

def contains_official_tag(tags):
    return contains_any(tags, ["PV", "先导", "预告", "宣传", "片段", "花絮", "官方"])

async def collect_fanmade_videos(anime_list):
    results = []
    for anime_name in tqdm(anime_list, desc="处理动漫中"):
        extended_keywords = get_extended_keywords(anime_name)
        search_keywords = generate_search_keywords(extended_keywords)
        main_names = [anime_name] + [kw for kw in extended_keywords if anime_name in kw and kw != anime_name]

        for keyword in search_keywords:
            await asyncio.sleep(random.uniform(3.0, 5.0))  # 关键词间延迟防反爬
            all_results = await search_all_pages(keyword)
            for video in all_results:
                title = video.get("title", "")
                desc = video.get("description", "")
                tags = video.get("tag", "")
                author = video.get("author", "")

                if (
                    contains_any(title, extended_keywords)
                    and contains_any(tags, FANMADE_TAGS)
                    and contains_any(tags, main_names)
                    and not contains_official_tag(tags)
                    and not is_official_author(author)
                ):
                    results.append({
                        "所属动漫": anime_name,
                        "视频标题": title,
                        "播放量": video.get("play"),
                        "弹幕数": video.get("video_review"),
                        "收藏数": video.get("favorites"),
                        "UP主": author,
                        "标签": tags,
                        "bvid": video.get("bvid"),
                        "url": f"https://www.bilibili.com/video/{video.get('bvid')}"
                    })
    return results

# === 主程序入口 ===
if __name__ == "__main__":
    anime_names = read_anime_names(INPUT_CSV)
    video_data = asyncio.run(collect_fanmade_videos(anime_names))  # ✅ 正确运行协程
    pd.DataFrame(video_data).to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"\n✅ 共保存 {len(video_data)} 条视频记录到 {OUTPUT_CSV}")

