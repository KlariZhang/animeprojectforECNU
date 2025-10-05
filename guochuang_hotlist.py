import requests
import pandas as pd
from datetime import datetime
import time
import json

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
        'type': 'all' # all表示全部分稿件类型
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

# --- 3. 主程序入口 ---
if __name__ == "__main__":

    print("B站分区排行榜爬虫。")
    
    try:
        rid_input = input("目标爬取的分区ID (rid): ")
        target_rid = int(rid_input)
    except ValueError:
        print("[!] 输入无效，请输入一个数字。")
        exit()


    # 获取榜单原始数据
    chart_data = fetch_category_ranking(target_rid)
    
    if chart_data:
        processed_list = []
        
        # 遍历返回的列表，提取我们关心的字段
        for rank, item in enumerate(chart_data, 1):
            stat = item.get('stat', {})
            processed_list.append({
                '排名': rank,
                '标题': item.get('title'),
                'BVID': item.get('bvid'),
                'UP主': item.get('owner', {}).get('name'),
                '播放量': stat.get('view', 0),
                '弹幕数': stat.get('danmaku', 0),
                '评论数': stat.get('reply', 0),
                '点赞数': stat.get('like', 0),
                '投币数': stat.get('coin', 0),
                '收藏数': stat.get('favorite', 0),
                '分享数': stat.get('share', 0),
                '视频链接': f"https://www.bilibili.com/video/{item.get('bvid')}"
            })
        
        df = pd.DataFrame(processed_list)
        
        current_date = datetime.now().strftime("%Y-%m-%d")
        file_name = f"bilibili_ranking_rid_{target_rid}_{current_date}.csv"
        
        try:
            df.to_csv(file_name, index=False, encoding='utf-8-sig')
            print(f"\n[🎉] 任务完成！排行榜数据已成功保存至文件: {file_name}")
            print("\n文件内容预览 (前5行):")
            print(df.head())
        except Exception as e:
            print(f"\n[!] 文件保存失败: {e}")