import requests
import pandas as pd
import time
from datetime import datetime, timedelta
import logging


def get_ranking_data(target_date: str):
    """
    获取指定日期的国漫热度排行榜数据。
    (此函数内容与上一版完全相同)
    """
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Origin': 'https://d.guduodata.com',
        'Referer': 'https://d.guduodata.com/rank',
    }
    params = {
        'type': 'DAILY',
        'category': 'ALL_ANIME',
        'date': target_date,
        'attach': 'gdi',
        'orderTitle': 'gdi',
        'platformId': '0'
    }
    try:
        logging.info(f"正在请求 {target_date} 的数据...")
        response = requests.get("https://d.guduodata.com/m/v3/billboard/list", headers=headers, params=params, timeout=15)
        response.raise_for_status()
        json_data = response.json()
        ranking_list = json_data.get('data')
        if isinstance(ranking_list, list):
            processed_data = []
            for item in ranking_list:
                processed_data.append({
                    '排名': item.get('rank'),
                    '名称': item.get('name'),
                    '全网热度': item.get('gdiFloat'),
                    '上线天数': item.get('days')
                })
            logging.info(f"成功处理 {target_date} 的数据，共找到 {len(processed_data)} 条记录。")
            return processed_data
        else:
            logging.error(f"处理 {target_date} 数据失败：'data'字段中预期的列表不存在。")
            return None
    except Exception as e:
        logging.error(f"处理 {target_date} 数据时发生未知错误: {e}")
        return None

def main_save_long_period_to_excel():
    # --- 设置爬取时间范围 ---
    # 起始日期设置为 2023年6月1日
    start_date = datetime(2023, 6, 1)
    
    # 结束日期为昨天
    end_date = datetime.now() - timedelta(days=1)
    
    output_filename = f"骨朵国漫热度榜_{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}.xlsx"
    
    # 使用 pd.ExcelWriter 来操作同一个Excel文件
    with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
        logging.info(f"开始爬取任务，时间范围：{start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
        logging.info(f"数据将保存至: {output_filename}")
        
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            daily_data = get_ranking_data(date_str)
            
            if daily_data:
                df_daily = pd.DataFrame(daily_data)
                # 将每日数据写入以日期命名的Sheet中
                df_daily.to_excel(writer, sheet_name=date_str, index=False)
                logging.info(f"已将 {date_str} 的数据写入工作表。")
            else:
                # 即使某天没有数据或请求失败，也记录一下
                logging.warning(f"未能获取到 {date_str} 的数据，将跳过这一天。")

            # 保持礼貌性延迟，这对于长时间抓取尤其重要，可防止IP被封
            time.sleep(2)
            current_date += timedelta(days=1)

    logging.info(f"所有任务已完成！数据已全部保存在 {output_filename}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    # 确保你已经安装了 openpyxl: pip install pandas openpyxl
    main_save_long_period_to_excel()