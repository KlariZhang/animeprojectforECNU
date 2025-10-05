import time
import random
import requests
import pandas as pd
import json

# --- 配置 ---
EXCEL_FILE = 'all.xlsx'
SHEET_NAME = 'anime'
OUTPUT_FILE = 'bilibili_anime_api_debug.csv'

# User-Agent 列表
HEADERS_LIST = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/115.0.1901.188 Safari/537.36',
]

# Referer 列表
REFERER_LIST = [
    'https://www.bilibili.com/',
    'https://search.bilibili.com/',
]

# 你提供的 Cookie
COOKIE = "buvid3=A72DE410-2553-5390-2051-99B7A7DDDFE203941infoc; b_nut=1739331003; _uuid=9317E2D9-DDC2-9A18-7DE6-81E7E5B6646F04412infoc; enable_web_push=DISABLE; rpdid=|(um)~ukumuY0J'u~JmJJu|R); DedeUserID=295649114; DedeUserID__ckMd5=7c888cfe0108b5cc; enable_feed_channel=ENABLE; CURRENT_QUALITY=80; header_theme_version=OPEN; theme-tip-show=SHOWED; theme-avatar-tip-show=SHOWED; CURRENT_BLACKGAP=0; fingerprint=d4d803363f8f0c21211f934b1ce4c9a6; buvid_fp_plain=undefined; buvid_fp=907c40814013dbb3bead5da6755ee907; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTU1MDQ1OTgsImlhdCI6MTc1NTI0NTMzOCwicGx0IjotMX0.Em-WJm9yMm1TQkqIjxNsJ8dXjphpWhbqBHZ1gwg9gJQ; bili_ticket_expires=1755504538; SESSDATA=2fd2b766%2C1770797407%2C47550%2A81CjCVybRKQ-ooQv0HZsPISJqlvwiGfy8jpBi9IWocOQnR7Y_KKAzbNyezH7_tj9itnXQSVjd6a24waXJzdUhtb3pESnBkbE8xZFpwa2FheWV2S0NJdGtjeV84a2xLQlhJT293c21Xb2trM0VvdS0tQW0wYnBRRGR3V1pUWWR6TEJZb05wMnlYZmpnIIEC; bili_jct=ed5e481f151e60ebcb2f59624331dbea; sid=5bcskz6u; buvid4=C43207A2-C710-D74A-9155-C7A8E221F08705247-025021203-kA6ymuW8/J7OKMkj706GDA%3D%3D; b_lsid=2F5D5537_198B8824EFE; home_feed_column=4; bp_t_offset_295649114=1102112642790588416; CURRENT_FNVAL=2000; browser_resolution=395-774"

# 搜索 API
SEARCH_API = "https://api.bilibili.com/x/web-interface/search/type"

# --- 读取 Excel ---
df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)
anime_names = df['anime'].dropna().tolist()

all_results = []

# --- 遍历动漫名 ---
for idx, anime in enumerate(anime_names, 1):
    print(f"\n🔹 正在处理 {idx}/{len(anime_names)}: {anime}")

    tabs = {
        '番剧': 13,
        '影视': 11
    }

    for tab_name, search_type in tabs.items():
        page = 1
        while True:
            headers = {
                'User-Agent': random.choice(HEADERS_LIST),
                'Referer': random.choice(REFERER_LIST),
                'Cookie': COOKIE
            }
            params = {
                'keyword': anime,
                'search_type': search_type,
                'page': page,
                'order': 'totalrank'
            }

            # --- 请求重试机制 ---
            for attempt in range(3):
                try:
                    resp = requests.get(SEARCH_API, headers=headers, params=params, timeout=10)
                    resp.raise_for_status()
                    data = resp.json()
                    break
                except requests.exceptions.HTTPError as e:
                    print(f"⚠️ 请求失败 [{e}], 尝试 {attempt + 1}/3 ...")
                    time.sleep(random.uniform(2, 4))
                except Exception as e:
                    print(f"⚠️ 请求异常 [{e}], 尝试 {attempt + 1}/3 ...")
                    time.sleep(random.uniform(2, 4))
            else:
                print(f"❌ {tab_name} 栏目 第 {page} 页连续失败，跳过")
                break

            # --- debug 输出 ---
            print(f"📌 请求 URL: {resp.url}")
            print(f"📌 返回 JSON keys: {list(data.keys())}")

            result_items = data.get('data', {}).get('result', [])
            if not result_items:
                print(f"📄 {tab_name} 栏目 第 {page} 页无条目，结束分页")
                break
            else:
                print(f"📌 本页条目数: {len(result_items)}")
                print(f"📌 前 1 条示例: {json.dumps(result_items[0], ensure_ascii=False)}")

            matched_count = 0
            for item in result_items:
                title = item.get('title', '')
                if anime in title:
                    bvid = item.get('bvid', '')
                    owner = item.get('author', '')
                    stat = item.get('stat', {})
                    view = stat.get('view', '')
                    danmaku = stat.get('danmaku', '')
                    like = stat.get('like', '')
                    coin = stat.get('coin', '')
                    fav = stat.get('favorite', '')

                    all_results.append({
                        '标题': title,
                        '栏目': tab_name,
                        'BVID': bvid,
                        'UP主': owner,
                        '播放量': view,
                        '弹幕数': danmaku,
                        '点赞数': like,
                        '投币数': coin,
                        '收藏数': fav,
                        '视频链接': f"https://www.bilibili.com/video/{bvid}"
                    })
                    matched_count += 1

            print(f"📄 {tab_name} 栏目 第 {page} 页匹配数量: {matched_count}")

            page += 1
            if page > 5:  # debug阶段限制页数
                break
            time.sleep(random.uniform(2, 5))

    delay = random.uniform(3, 6)
    print(f"⏳ 延时 {delay:.2f} 秒后继续")
    time.sleep(delay)

# --- 输出 CSV ---
if all_results:
    pd.DataFrame(all_results).to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"\n✅ 共抓取 {len(all_results)} 条结果，保存到 {OUTPUT_FILE}")
else:
    print("\n⚠️ 没有抓取到任何数据。")
