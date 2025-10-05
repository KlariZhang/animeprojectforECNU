import requests
import json
import time
from datetime import datetime
from functools import reduce
from hashlib import md5
import urllib.parse

# --- 1. url ---
SEARCH_API_URL = "https://api.bilibili.com/x/web-interface/search/type"
EPISODE_LIST_API_URL = "https://api.bilibili.com/pgc/view/web/season"
COMMENT_API_URL = "https://api.bilibili.com/x/v2/reply/wbi/main" 

HEADERS =  {
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Referer': 'https://www.bilibili.com/',
    "Cookie":""
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
    pagination_str = json.dumps({"offset":""})
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
            
    print(f"  [✓] '{episode_title}' 评论抓取完成。共 {len(all_comments_text)} 条(已加载) / {total_comment_count} 条(总计)。")
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


# --- 4. 主程序 ---
if __name__ == "__main__":
    work_name = input("请输入要爬取的番剧名称: ")
    if not work_name:
        print("[!] 输入为空，程序退出。")
    else:
        scrape_mode = input("请选择爬取模式 (1: 只爬取第一页, 2: 爬取所有评论) [默认为 1]: ")
        scrape_all = (scrape_mode == '2')
            
        if scrape_all:
            print("[i] 已选择完整模式，将抓取所有一级评论。")
        else:
            print("[i] 已选择首页模式，将只抓取每集的第一页评论。")

    WORK_NAME = work_name 
    print("[*] 正在获取最新的WBI密钥...")
    wbi_keys = getWbiKeys()
    if wbi_keys:
            print(f"[✓] WBI密钥获取成功!")
            bangumi_info = find_bangumi_season_id(work_name)
            if bangumi_info:
                all_episodes = get_all_episodes_info(bangumi_info['season_id'])
                follower_count = get_season_follower_count(bangumi_info['season_id'])
                print(follower_count)
                if all_episodes:
                    print(f"\n[+] 找到 {len(all_episodes)} 集，将使用WBI签名模式开始遍历抓取...")
                    all_series_data = []

                    for i, episode in enumerate(all_episodes, 1):
                        print(f"\n--- 处理第 {i}/{len(all_episodes)} 集: {episode['title']} ---")
                        total_count, comments_text_list = fetch_comments_with_wbi(
                            aid=episode['aid'], 
                            episode_title=episode['title'],
                            wbi_keys=wbi_keys,
                            scrape_all_pages=scrape_all # 将用户的选择传递给函数
                        )
                        all_series_data.append({
                            'episode_title': episode['title'],
                            'aid': episode['aid'],
                            'total_comment_count': total_count,
                            'comment_texts': comments_text_list
                        })
                        if i < len(all_episodes):
                            print("  [i] 休息3秒，准备抓取下一集...")
                            time.sleep(3)

                    file_name = f"bilibili_Comments_{bangumi_info['title']}.json"
                try:
                    with open(file_name, 'w', encoding='utf-8') as f:
                        json.dump(all_series_data, f, ensure_ascii=False, indent=4)
                        print(f"\n[🎉] 全部任务成功！评论数据已汇总保存至文件: {file_name}")
                except Exception as e:
                            print(f"\n[!] 文件保存失败: {e}")        
   
        