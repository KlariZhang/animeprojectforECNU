import requests  # 用于发送HTTP请求
import pandas as pd  # 用于数据处理和CSV操作
import time  # 用于添加延迟
from tqdm import tqdm  # 用于显示进度条
import re  # 用于正则表达式操作
from dotenv import load_dotenv
import os
import json  # 放在文件开头用于打印格式化的JSON
from bs4 import BeautifulSoup
import unicodedata

load_dotenv()  # 读取.env文件
BILIBILI_COOKIE = os.getenv("BILIBILI_COOKIE")  # 获取 Cookie


# === 配置参数 ===
INPUT_CSV = "C:/Code/python/animeproject/anime_list.csv"  # 输入CSV文件名，包含动漫列表
OUTPUT_CSV = "C:/Code/python/animeproject/fanmade_results.csv"  # 输出CSV文件名，保存二创视频结果
MAX_PAGES_PER_KEYWORD = 3  # 每个关键词最多搜索的页数

# 二创视频常见的后缀词（用于生成搜索关键词）
FANMADE_SUFFIXES = [" MAD", " 二创", " 混剪", " 同人", " AMV", " 鬼畜"]
# 二创视频常见的标签（用于识别视频类型）
FANMADE_TAGS = ["二创", "MAD", "混剪", "同人", "鬼畜", "AMV", "剪辑"]


# === 步骤 1：读取输入动漫名 ===
def read_anime_names(csv_path):
    """从CSV文件中读取动漫名称列表"""
    df = pd.read_csv(csv_path)  # 读取CSV文件
    print(f"✅ 成功读取 {len(df["anime"].dropna().tolist())} 个动漫名称")  # ✅ added for debug
    return df["anime"].dropna().tolist()  # 返回"anime"列的非空值列表


# === 步骤 2：自动扩展关键词：===


# ✅ 标准化关键词（统一全角/半角，去空格）
def normalize_keyword(text):
    if not text or not isinstance(text, str):
        return ""
    return unicodedata.normalize('NFKC', text).strip()

# ✅ 闲角关键词（用于过滤掉无意义角色）
EXCLUDE_ROLE_KEYWORDS = [
    "モブ", "モブキャラ", "モブキャラクター", "エキストラ",
    "路人", "群众", "群演", "小兵", "学生", "老师", "记者", "助手",
    "通行人", "观众", "村人", "村民", "男性", "女性", "少年", "少女",
    "人类", "店员", "保安", "司机", "医生", "士兵", "乘客", "服务员",'extra', 'mob character','闲角'
]

def is_valid_character_name(name):
    return name and not any(x in name for x in EXCLUDE_ROLE_KEYWORDS)

def get_extended_keywords(anime_name):
    print(f"\n🔍 正在处理：{anime_name}")
    keywords = set()
    keywords.add(anime_name)

    # ✅ 有效字段关键词（用于模糊匹配 infobox 的 key）
    valid_keys = set([
        "别名", "别称", "又称", "英文", "简称", "缩写", "简写",
        "cp", "CP", "情侣", "搭档", "角色", "登场角色", "主要角色"
    ])

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json"
    }

    try:
        # === 1. 获取 subject_id ===
        print("🚀 获取条目信息...")
        search_url = "https://api.bgm.tv/v0/search/subjects"
        search_payload = {
            "keyword": anime_name,
            "filter": {"type": [2]},  # type=2 → 动画
            "sort": "rank",
            "limit": 3
        }
        res = requests.post(search_url, json=search_payload, headers=headers, timeout=10)
        res.raise_for_status()
        subject_list = res.json().get("data", [])

        if not subject_list:
            print("⚠️ 未找到相关条目")
            return list(keywords)

        subject = subject_list[0]
        subject_id = subject.get("id")
        name = subject.get("name", "")
        name_cn = subject.get("name_cn", "")
        print(f"🎯 subject_id: {subject_id} ｜ 原名: {name} ｜ 中文名: {name_cn}")

        keywords.update([name.strip(), name_cn.strip()])

        # === 2. 提取 other_names（英文别名/简写等）===
        for other in subject.get("other_names", []):
            if isinstance(other, str) and other.strip():
                keywords.add(other.strip())

        # === 3. 提取 infobox 中条目别名、CP、英文名等 ===
        detail_url = f"https://api.bgm.tv/v0/subjects/{subject_id}"
        detail_res = requests.get(detail_url, headers=headers, timeout=10)
        detail_res.raise_for_status()
        detail_data = detail_res.json()
        infobox = detail_data.get("infobox", [])

        has_role_info = False

        for entry in infobox:
            key = entry.get("key", "").strip().lower()
            val = entry.get("value", "")
            if any(valid.lower() in key for valid in valid_keys):
                if "角" in key:
                    has_role_info = True

                if isinstance(val, list):
                    for v in val:
                        v = v.get("v", "") if isinstance(v, dict) else v
                        if isinstance(v, str) and v.strip():
                            keywords.add(v.strip())
                elif isinstance(val, str):
                    for part in re.split(r"[、，,/\s]", val):
                        if part.strip():
                            keywords.add(part.strip())

        # === 4. 角色列表提取 name, name_cn + infobox 中别名 ===
        print("📥 获取角色列表...")
        char_url = f"https://api.bgm.tv/v0/subjects/{subject_id}/characters"
        char_res = requests.get(char_url, headers=headers, timeout=10)
        characters = char_res.json()
        print(f"✅ 共找到 {len(characters)} 个角色")

        for char in characters:
            char_id = char.get("id")
            name = char.get("name", "").strip()
            name_cn = char.get("name_cn", "").strip()
            if is_valid_character_name(name):
                keywords.add(name)
            if is_valid_character_name(name_cn):
                keywords.add(name_cn)

            # 获取角色详情
            detail_url = f"https://api.bgm.tv/v0/characters/{char_id}"
            detail_res = requests.get(detail_url, headers=headers, timeout=10)
            detail_data = detail_res.json()
            char_infobox = detail_data.get("infobox", [])

            for entry in char_infobox:
                key = entry.get("key", "").lower()
                val = entry.get("value", "")
                if any(k in key for k in ["别名", "简称", "cp", "称呼", "又叫", "外号"]):
                    if isinstance(val, list):
                        for item in val:
                            v = item.get("v", "") if isinstance(item, dict) else item
                            if v and len(v.strip()) >= 2 and is_valid_character_name(v):
                                keywords.add(v.strip())
                    elif isinstance(val, str):
                        for part in re.split(r"[、，,/\s]", val):
                            if part.strip() and is_valid_character_name(part):
                                keywords.add(part.strip())

    except Exception as e:
        print(f"❌ 错误：{e}")

    # === 5. 标准化、去重、去空、排除闲角 ===
    final_keywords = set()
    for k in keywords:
        k_norm = normalize_keyword(k)
        if len(k_norm) >= 2 and is_valid_character_name(k_norm):
            final_keywords.add(k_norm)

    final_list = sorted(final_keywords)
    print(f"📌 最终关键词（{len(final_list)} 项）：{final_list}")
    return final_list


# === 步骤 3：构造搜索关键词（衍生词 × 二创后缀） ===

def generate_search_keywords(extended_keywords):
    """仅使用扩展关键词，不添加后缀"""
    return extended_keywords


# === 步骤 4：B 站搜索视频 ===
def bvid_search(keyword, page):
    url = "https://api.bilibili.com/x/web-interface/search/type"
    params = {
        "search_type": "video",
        "keyword": keyword,
        "page": page
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Referer": "https://www.bilibili.com/",
        "Origin": "https://www.bilibili.com",
        "Accept": "application/json",
        "Accept-Language": "zh-CN,zh;q=0.9",
        # ✅ 复制你登录状态下的 Cookie 放在此处
        "Cookie": BILIBILI_COOKIE
    }

    try:
        res = requests.get(url, params=params, headers=headers)
        res.raise_for_status()
        return res.json().get("data", {}).get("result", [])
    except Exception as e:
        print(f"❌ 请求失败：{keyword} - 第{page}页 - 错误：{e}")
        return []


# === 步骤 5：匹配规则判断是否为目标作品二创视频 ===
def contains_any(text, keywords):
    """检查文本中是否包含任意关键词（不区分大小写）"""
    return any(kw.lower() in text.lower() for kw in keywords)


# === 步骤 6：主逻辑爬取 ===
def is_official_author(author_name):
    """判断UP主是否为官方账号"""
    OFFICIAL_USER_KEYWORDS = ["官方", "出品", "制作委员会", "动画官方"]
    return any(keyword in author_name for keyword in OFFICIAL_USER_KEYWORDS)


def contains_official_tag(tags):
    """判断标签中是否包含官方标签"""
    OFFICIAL_TAGS = ["PV", "先导", "预告", "宣传", "片段", "花絮", "官方"]
    return contains_any(tags, OFFICIAL_TAGS)


def collect_fanmade_videos(anime_list):
    """收集所有动漫的二创视频数据（必须满足三大筛选条件）"""
    results = []

    for anime_name in tqdm(anime_list, desc="处理动漫中"):
        extended_keywords = get_extended_keywords(anime_name)
        search_keywords = generate_search_keywords(extended_keywords)

        # 动漫主名（用于 tag 中“官方名称”判断）
        main_names = [anime_name]
        main_names += [kw for kw in extended_keywords if kw != anime_name and len(kw) >= 2 and anime_name in kw]

        for keyword in search_keywords:
            for page in range(1, MAX_PAGES_PER_KEYWORD + 1):
                videos = bvid_search(keyword, page)
                time.sleep(0.5)

                for video in videos:
                    title = video.get("title", "")
                    desc = video.get("description", "")
                    tags = video.get("tag", "")  # 逗号分隔字符串
                    author = video.get("author", "")  # UP主名称

                    # === 三大判断条件 ===
                    # 1️⃣ 标题中包含扩展衍生词
                    title_contains_keyword = contains_any(title, extended_keywords)

                    # 2️⃣ 标签中必须同时包含：二创标签 + 官方名称
                    tag_contains_fanmade = contains_any(tags, FANMADE_TAGS)
                    tag_contains_anime_name = contains_any(tags, main_names)

                    # 3️⃣ 非官方发布
                    not_official = not contains_official_tag(tags) and not is_official_author(author)

                    # ✅ 同时满足三条标准
                    if title_contains_keyword and tag_contains_fanmade and tag_contains_anime_name and not_official:
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

        # === 步骤 7：保存结果 ===
if __name__ == "__main__":
    anime_names = read_anime_names(INPUT_CSV)  # 读取动漫列表
    video_data = collect_fanmade_videos(anime_names)  # 收集二创视频

    # 创建DataFrame并保存为CSV
    df = pd.DataFrame(video_data)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")  # 使用BOM头保存中文

    print(f"\n✅ 共保存 {len(df)} 条视频记录到 {OUTPUT_CSV}")