import requests
import csv
import time
import json
import os
import pickle

# 定义常量
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
SEARCH_API_URL = "https://api.bilibili.com/x/web-interface/search/type"
SEASON_API_URL = "https://api.bilibili.com/pgc/view/web/season"
INPUT_CSV = "series_list.csv"
OUTPUT_CSV = "master_url_list.csv"


def load_cookies_for_requests(cookies_file: str) -> dict:
    """从pickle文件中加载cookies并转换为requests库所需的格式。"""
    if not os.path.exists(cookies_file):
        print(f"[!] 错误：未找到Cookie文件 '{cookies_file}'。请先运行一次 comment_scraper.py 并登录。")
        return None
    
    with open(cookies_file, 'rb') as f:
        selenium_cookies = pickle.load(f)
    
    requests_cookies = {cookie['name']: cookie['value'] for cookie in selenium_cookies}
    print("[✓] Cookie文件加载成功。")
    return requests_cookies


def find_bangumi_season_id(keyword: str, cookies: dict) -> dict | None:
    """根据关键词搜索番剧，并返回第一个结果的season_id和官方标题。"""
    print(f"[*] 步骤 1: 正在为关键词 '{keyword}' 搜索番剧...")
    params = {'search_type': 'media_bangumi', 'keyword': keyword}
    try:
        response = requests.get(SEARCH_API_URL, params=params, headers=HEADERS, cookies=cookies, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get('code') == 0:
            results = data.get('data', {}).get('result')
            if not results:
                print(f"[!] 未找到与 '{keyword}' 相关的番剧。")
                return None
            
            top_result = results[0]
            season_id = top_result.get('season_id')
            title = top_result.get('title', '').replace('<em class="keyword">', '').replace('</em>', '')
            
            if season_id:
                print(f"[✓] 成功匹配到番剧: '{title}', Season ID: {season_id}")
                return {'season_id': season_id, 'title': title}
    except Exception as e:
        print(f"[!] 步骤1执行失败: {e}")
    return None



def get_episode_urls_from_api(season_id: int, cookies: dict) -> list:
    """根据 season_id 获取所有正片分集的URL列表。"""
    print(f"[*] 步骤 2: 正在使用 season_id: {season_id} 获取分集URL...")
    params = {"season_id": season_id}
    
    try:
        # --- 核心修改点 2：在API请求中加入 cookies ---
        response = requests.get(SEASON_API_URL, params=params, headers=HEADERS, cookies=cookies, timeout=10)
        response.raise_for_status()
        result = response.json().get('result', {})
    except Exception as e:
        print(f"[!] API请求失败: {e}")
        return []

    main_episodes = result.get('episodes', []) 
    url_list = []
    for ep in main_episodes:
        if ep.get('link'):
            url_list.append(ep.get('link')) 
    return url_list


def main():
    """主函数，执行完整的读取、处理、写入流程。"""
    cookies_file = 'cookies.pkl'
    cookies = load_cookies_for_requests(cookies_file)
    if not cookies:
        return

    try:
        with open(INPUT_CSV, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            series_names = [row['series_name'] for row in reader]
    except FileNotFoundError:
        print(f"[!] 错误：输入文件 '{INPUT_CSV}' 不存在。请创建该文件并填入番剧名称。")
        return

    all_series_data = []
    for name in series_names:
        search_result = find_bangumi_season_id(name, cookies)
        
        if search_result:
            season_id = search_result['season_id']
            official_title = search_result['title']
            # --- 核心修改点 3：将 cookies 传递给本函数 ---
            urls = get_episode_urls_from_api(season_id, cookies)
            
            if urls:
                all_series_data.append({
                    'series_name': official_title,
                    'season_id': season_id,
                    'episode_urls': json.dumps(urls, ensure_ascii=False)
                })
        time.sleep(2)

    if not all_series_data:
        print("[!] 未能成功获取任何番剧的URL。")
        return
        
    with open(OUTPUT_CSV, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['series_name', 'season_id', 'episode_urls'])
        writer.writeheader()
        writer.writerows(all_series_data)
    
    print(f"\n[✓] 所有番剧URL已汇总到 '{OUTPUT_CSV}'")


if __name__ == "__main__":
    main()