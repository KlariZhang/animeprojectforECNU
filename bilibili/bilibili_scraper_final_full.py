# ===【0. 公共导入和配置】===
import os
import re
import time
import json
import requests
import unicodedata
import pandas as pd
from tqdm import tqdm
from datetime import datetime
from dotenv import load_dotenv
from functools import reduce
from hashlib import md5
import urllib.parse



load_dotenv()
BILIBILI_COOKIE = os.getenv("BILIBILI_COOKIE")

# ========== 🧩 1. 插入：catchinformationfinalver.py 所有函数定义（不含 if __name__ == '__main__'） ==========
# === 环境变量与配置读取 ===
load_dotenv()
BILIBILI_COOKIE = os.getenv("BILIBILI_COOKIE")

# === 文件路径配置 ===
INPUT_CSV = "C:/Code/python/animeproject/anime_list.csv"
OUTPUT_CSV = "C:/Code/python/animeproject/fanmade_results.csv"
MAX_PAGES_PER_KEYWORD = 3

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
    df = pd.read_csv(csv_path)
    anime_list = df["anime"].dropna().tolist()
    print(f"✅ 成功读取 {len(anime_list)} 个动漫名称")
    return anime_list

def generate_search_keywords(extended_keywords):
    """返回扩展关键词列表"""
    return extended_keywords

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
        return res.json().get("data", {}).get("result", [])
    except Exception as e:
        print(f"❌ 请求失败：{keyword} - 第{page}页 - 错误：{e}")
        return []

# === 二创视频筛选逻辑 ===
def is_official_author(name):
    return any(k in name for k in ["官方", "出品", "制作委员会", "动画官方"])

def contains_official_tag(tags):
    return contains_any(tags, ["PV", "先导", "预告", "宣传", "片段", "花絮", "官方"])

def collect_fanmade_videos(anime_list):
    results = []
    for anime_name in tqdm(anime_list, desc="处理动漫中"):
        extended_keywords = get_extended_keywords(anime_name)
        search_keywords = generate_search_keywords(extended_keywords)
        main_names = [anime_name] + [kw for kw in extended_keywords if anime_name in kw and kw != anime_name]

        for keyword in search_keywords:
            for page in range(1, MAX_PAGES_PER_KEYWORD + 1):
                for video in bvid_search(keyword, page):
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
                time.sleep(0.5)
    return results

# ========== 🧩 2. 插入：comment_finder_2(2).py 所有函数定义 ==========


SEARCH_API_URL = "https://api.bilibili.com/x/web-interface/search/type"
EPISODE_LIST_API_URL = "https://api.bilibili.com/pgc/view/web/season"
COMMENT_API_URL = "https://api.bilibili.com/x/v2/reply/wbi/main"

HEADERS = {
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Referer': 'https://www.bilibili.com/',
    "Cookie": os.getenv("BILIBILI_COOKIE")
}

# --- 2. WBI签名 ---
mixinKeyEncTab = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
    61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
    36, 20, 34, 44, 52
]


def getMixinKey(orig: str):
    return reduce(lambda s, i: s + orig[i], mixinKeyEncTab, '')[:32]


def encWbi(params: dict, img_key: str, sub_key: str):
    mixin_key = getMixinKey(img_key + sub_key)
    curr_time = round(time.time())
    params['wts'] = curr_time
    params = dict(sorted(params.items()))
    params = {
        k: ''.join(filter(lambda chr: chr not in "'!()*", str(v)))
        for k, v in params.items()
    }
    query = urllib.parse.urlencode(params)
    wbi_sign = md5((query + mixin_key).encode()).hexdigest()
    params['w_rid'] = wbi_sign
    return params


'获取最新的 img_key 和 sub_key,注意该密钥每日更新'


def getWbiKeys() -> tuple[str, str] | None:
    try:
        resp = requests.get('https://api.bilibili.com/x/web-interface/nav', headers=HEADERS)
        resp.raise_for_status()
        json_content = resp.json()
        img_url: str = json_content['data']['wbi_img']['img_url']
        sub_url: str = json_content['data']['wbi_img']['sub_url']
        img_key = img_url.rsplit('/', 1)[1].split('.')[0]
        sub_key = sub_url.rsplit('/', 1)[1].split('.')[0]
        return img_key, sub_key
    except Exception as e:
        print(f"[!] 获取WBI密钥失败: {e}")
        return None


# --- 3. 数据获取 ---
'国创名称-> season_id'


def find_bangumi_season_id(keyword: str) -> dict | None:
    print(f"[*] 步骤 1: 正在为关键词 '{keyword}' 搜索番剧...")
    params = {'search_type': 'media_bangumi', 'keyword': keyword}
    try:
        response = requests.get(SEARCH_API_URL, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get('code') == 0:
            results = data.get('data', {}).get('result')
            if not results: return None
            top_result = results[0]
            season_id = top_result.get('season_id')
            title = top_result.get('title', '').replace('<em class="keyword">', '').replace('</em>', '')
            if season_id:
                print(f"[✓] 成功匹配到番剧: '{title}', Season ID: {season_id}")
                return {'season_id': season_id, 'title': title}
    except Exception as e:
        print(f"[!] 步骤1执行失败: {e}")
    return None


'season_id -> ep_id'


def get_all_episodes_info(season_id: int) -> list | None:
    print(f"\n[*] 步骤 2: 正在用 Season ID: {season_id} 获取所有剧集的信息...")
    params = {'season_id': season_id}
    try:
        response = requests.get(EPISODE_LIST_API_URL, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get('code') == 0:
            episodes = data.get('result', {}).get('episodes')
            if not episodes: return None
            episode_info_list = []
            for ep in episodes:
                if ep.get('aid'):
                    episode_info_list.append({'title': ep.get('long_title'), 'aid': ep.get('aid')})
            print(f"[✓] 成功获取到 {len(episode_info_list)} 集的有效信息.")
            return episode_info_list
    except Exception as e:
        print(f"[!] 步骤2执行失败: {e}")
    return None


def fetch_comments_with_wbi(aid: int, episode_title: str, wbi_keys: tuple[str, str], scrape_all_pages: bool):
    """
    步骤3: 抓取评论。
    """
    all_comments_text = []
    total_comment_count = 0
    pagination_str = json.dumps({"offset": ""})
    print(f"  -> 开始处理 '{episode_title}' (aid: {aid}) 的评论抓取...")

    while True:
        params = {'oid': aid, 'type': 1, 'mode': 3, 'pagination_str': pagination_str, 'plat': 1}
        signed_params = encWbi(params.copy(), img_key=wbi_keys[0], sub_key=wbi_keys[1])
        print(f"    - 正在请求 (cursor: {params['pagination_str'][:40]}...)...")
        try:
            response = requests.get(COMMENT_API_URL, params=signed_params, headers=HEADERS, timeout=20)
            response.raise_for_status()
            data = response.json()
            if data.get('code') == 0:
                if data.get('data', {}).get('cursor', {}).get('all_count') is not None:
                    total_comment_count = data['data']['cursor']['all_count']

                replies = data.get('data', {}).get('replies')
                if replies:
                    for reply in replies:
                        all_comments_text.append(reply.get('content', {}).get('message'))
                    print(f"    [✓] 本页处理完毕，获得 {len(replies)} 条评论。")

                if not scrape_all_pages:
                    print(f"    [i] 已设置为只抓取第一页，停止翻页。")
                    break

                if data.get('data', {}).get('cursor', {}).get('is_end'):
                    print(f"    [i] 已到达最后一页，停止翻页。")
                    break

                pagination_str = data['data']['cursor']['pagination_reply']['next_offset']
                time.sleep(2)
            else:
                print(f"    [!] API返回错误: {data.get('message')}, 停止翻页。")
                break
        except Exception as e:
            print(f"    [!] 请求过程中发生错误: {e}, 停止抓取本集。")
            break

    print(
        f"  [✓] '{episode_title}' 评论抓取完成。共 {len(all_comments_text)} 条(已加载) / {total_comment_count} 条(总计)。")
    return total_comment_count, all_comments_text


def get_season_follower_count(season_id: int) -> int:
    """
    根据给定的season_id，从番剧详情API中获取准确的追番人数(series_follow)。

    :param season_id: 番剧的Season ID。
    :return: 追番人数 (int)。如果获取失败，则返回 -1。
    """
    params = {'season_id': season_id}

    try:
        response = requests.get(EPISODE_LIST_API_URL, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('code') == 0:

            seasons_list = data.get('result', {}).get('seasons')
            if seasons_list:

                for season_item in seasons_list:
                    if season_item.get('season_id') == season_id:

                        stat_data = season_item.get('stat')
                        if stat_data:

                            followers = stat_data.get('series_follow')
                            if followers is not None:
                                print(f"[✓] 成功获取追番人数 (series_follow): {followers}")
                                return followers
                print(f"[!] 在seasons列表中未找到匹配的 season_id: {season_id}。")
                return -1
            else:
                print("[!] API响应成功，但未找到 'seasons' 列表。")
                return -1
        else:
            print(f"[!] API返回错误: {data.get('message')}")
            return -1

    except requests.exceptions.RequestException as e:
        print(f"[!] 请求过程中发生错误: {e}")
        return -1
    except Exception as e:
        print(f"[!] 程序发生未知错误: {e}")
        return -1




# ========== 🧩 3. 插入：guochuang_hotlist(1).py 的 fetch_category_ranking 函数 ==========

# --- 1. url配置 ---

RANKING_API_URL = "https://api.bilibili.com/x/web-interface/ranking/v2"

# 只需要一个简单的User-Agent即可
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
}


# --- 2. 核心抓取函数 ---
def fetch_category_ranking(rid: int) -> list | None:
    """
    根据给定的分区ID(rid)获取B站视频排行榜。

    :param rid: 目标分区的ID。
    :return: 包含榜单所有视频信息的列表，如果失败则返回None。
    """
    params = {
        'rid': rid,
        'type': 'all'  # all表示全部分稿件类型
    }

    # 根据rid生成一个可读的分区名用于显示
    category_name = f"分区(rid={rid})"
    if rid == 0:
        category_name = "全站"

    print(f"[*] 正在向B站API请求 [{category_name}] 的排行榜数据...")

    try:
        response = requests.get(RANKING_API_URL, params=params, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()

        if data.get('code') == 0:
            chart_list = data.get('data', {}).get('list')
            if chart_list:
                print(f"成功获取到 {len(chart_list)} 条榜单数据.")
                return chart_list
            else:
                print("[!] API返回成功，但榜单列表为空。")
                return None
        else:
            print(f"[!] API返回错误: {data.get('message')}")
            return None

    except Exception as e:
        print(f"[!] 请求过程中发生错误: {e}")
        return None




# ========== 🚀 4. 主交互式菜单入口 ==========
def main():
    while True:
        print("\n📌 请选择要执行的功能：")
        print("1. 抓取 B站国创排行榜")
        print("2. 抓取某部番剧的所有剧集评论")
        print("3. 抓取多个动漫的二创视频")
        print("0. 退出程序")

        choice = input("请输入选项编号: ").strip()

        if choice == "1":
            try:
                rid = int(input("请输入分区 rid（如：168=国创）: "))
                data = fetch_category_ranking(rid)
                if data:
                    result_list = []
                    for rank, item in enumerate(data, 1):
                        stat = item.get("stat", {})
                        result_list.append({
                            '排名': rank,
                            '标题': item.get("title"),
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
                    df = pd.DataFrame(result_list)
                    date_str = datetime.now().strftime("%Y-%m-%d")
                    filename = f"bilibili_ranking_rid_{rid}_{date_str}.csv"
                    df.to_csv(filename, index=False, encoding="utf-8-sig")
                    print(f"✅ 已保存排行榜数据到 {filename}")
            except Exception as e:
                print(f"[!] 错误: {e}")

        elif choice == "2":
            work_name = input("请输入番剧名称: ").strip()
            if not work_name:
                print("输入为空，跳过。")
                continue
            scrape_all = input("是否抓取全部评论？1=否（默认）/ 2=是: ").strip() == "2"
            wbi_keys = getWbiKeys()
            if not wbi_keys:
                continue
            bangumi_info = find_bangumi_season_id(work_name)
            if not bangumi_info:
                continue
            episodes = get_all_episodes_info(bangumi_info['season_id'])
            follower_count = get_season_follower_count(bangumi_info['season_id'])
            print(f"🎯 追番人数: {follower_count}")
            if episodes:
                all_data = []
                for ep in episodes:
                    count, comments = fetch_comments_with_wbi(ep['aid'], ep['title'], wbi_keys, scrape_all)
                    all_data.append({
                        'episode_title': ep['title'],
                        'aid': ep['aid'],
                        'total_comment_count': count,
                        'comment_texts': comments
                    })
                    time.sleep(2)
                filename = f"bilibili_Comments_{bangumi_info['title']}.json"
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(all_data, f, ensure_ascii=False, indent=4)
                    print(f"✅ 评论数据保存至 {filename}")

        elif choice == "3":
            input_path = input("请输入包含动漫名称的CSV路径（如 anime_list.csv）: ").strip()
            output_path = input("请输入输出结果CSV路径（如 fanmade_results.csv）: ").strip()
            anime_list = read_anime_names(input_path)
            results = collect_fanmade_videos(anime_list)
            pd.DataFrame(results).to_csv(output_path, index=False, encoding="utf-8-sig")
            print(f"✅ 已保存二创视频记录到 {output_path}")

        elif choice == "0":
            print("退出程序。")
            break
        else:
            print("无效输入，请重试。")

# ========== 🔚 程序入口点 ==========
if __name__ == "__main__":
    main()










