import pandas as pd
import requests
import time
import ast  # 用于安全地将字符串转换回列表
from tqdm import tqdm # 引入tqdm来显示进度条

# --- 配置区 ---
INPUT_MAPPING_FILE = 'anime_mapping_grouped.csv'    #此处为示例，填写映射关系文件名

OUTPUT_EXCEL_FILE = 'bilibili_stats.xlsx'   # 输出Excel文件名
API_URL = "https://api.bilibili.com/pgc/view/web/season"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
# --- 配置结束 ---

def get_season_stats(season_id: int) -> dict | None:
    """
    根据单个 season_id 从Bilibili API获取统计数据。
    """
    params = {"season_id": season_id}
    try:
        response = requests.get(API_URL, params=params, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get('code') == 0 and 'result' in data:
            result = data['result']
            stat = result.get('stat', {})
            rating = result.get('rating', {})
            
            # 返回一个包含所有我们需要数据的字典
            return {
                'views': stat.get('views', 0),
                'favorites': stat.get('favorites', 0), # 追番
                'danmakus': stat.get('danmakus', 0),
                'reply': stat.get('reply', 0),
                'likes': stat.get('likes', 0),
                'coins': stat.get('coins', 0),
                'favorite': stat.get('favorite', 0), # 收藏
                'share': stat.get('share', 0),
                'rating_score': rating.get('score'),
                'rating_count': rating.get('count', 0),
                'pub_time': result.get('publish', {}).get('pub_time', '1970-01-01 00:00:00')
            }
        else:
            return None
            
    except requests.exceptions.RequestException:
        return None
    except Exception:
        return None

def main():
    """
    主函数，执行整个数据采集和聚合流程。
    """

    
    try:
        mapping_df = pd.read_csv(INPUT_MAPPING_FILE)
        print(f"[✓] 成功读取映射文件 '{INPUT_MAPPING_FILE}'，共找到 {len(mapping_df)} 个动漫系列。")
    except FileNotFoundError:
        print(f"[!] 错误：映射文件 '{INPUT_MAPPING_FILE}' 未找到。请先运行映射关系生成脚本。")
        return

    aggregated_results = []
    
    print("\n[*] 开始采集和聚合数据，请稍候...")
    for _, row in tqdm(mapping_df.iterrows(), total=len(mapping_df), desc="处理进度"):
        series_name = row['series_name']
        
        try:
            seasons_list = ast.literal_eval(row['seasons_list'])
            if not isinstance(seasons_list, list) or not seasons_list:
                continue
        except (ValueError, SyntaxError):
            continue

        total_stats = {
            'views': 0, 'danmakus': 0, 'reply': 0, 'likes': 0,
            'coins': 0, 'favorite': 0, 'share': 0, 'rating_count': 0
        }
        
        max_favorites = 0 
        latest_season_info = {'pub_time': '1970-01-01 00:00:00', 'score': None}

        for season_name, season_id in seasons_list:
            season_data = get_season_stats(season_id)
            
            if season_data:
                for key in total_stats:
                    total_stats[key] += season_data.get(key, 0)
                
                max_favorites = max(max_favorites, season_data.get('favorites', 0))
                
                if season_data['pub_time'] > latest_season_info['pub_time']:
                    latest_season_info['pub_time'] = season_data['pub_time']
                    latest_season_info['score'] = season_data.get('rating_score')

            time.sleep(1.5)
        
        final_row = {
            'series_name': series_name,
            'total_views': total_stats['views'],
            'total_favorites': max_favorites,
            'total_danmakus': total_stats['danmakus'],
            'total_reply': total_stats['reply'],
            'total_likes': total_stats['likes'],
            'total_coins': total_stats['coins'],
            'total_favorite': total_stats['favorite'],
            'total_share': total_stats['share'],
            'total_rating_count': total_stats['rating_count'],
            'latest_rating_score': latest_season_info['score']
        }
        aggregated_results.append(final_row)

    if aggregated_results:
        output_df = pd.DataFrame(aggregated_results)
        
        # *** 修改：将DataFrame保存到Excel文件 ***
        try:
            output_df.to_excel(
                OUTPUT_EXCEL_FILE, 
                sheet_name='anime',  # 按要求设置工作表名称
                index=False          # 不保存索引列
            )
            print(f"\n数据已成功保存到Excel文件 '{OUTPUT_EXCEL_FILE}' 的 'anime' 工作表中。")

        except Exception as e:
            print(f"\n[!] 保存到Excel文件时出错: {e}")
            
    else:
        print("[!] 没有采集到任何数据，请检查映射文件是否正确。")

if __name__ == '__main__':
    main()