# -*- coding: utf-8 -*-
"""
Created on Sun Jul 20 18:01:29 2025

@author: yuxin
"""

import requests
import json
import time
import datetime
import pandas as pd
import random

# ====================================================================
# --- 用户配置区 ---
# ====================================================================
CREDENTIALS = {
    #请在下面粘贴你的BDUSS值
    "cookie_BDUSS": '请粘贴你的BDUSS值'
    #请在下面粘贴你的Cipher-Text值
    "cipherText": '请粘贴你的Cipher-Text值'
}

KEYWORDS_LIST = [
    ['molly']
]
START_DATE = '2025-01-01'
END_DATE = '2025-05-20'
REGION_CODE = 0  # 0代表全国
# ====================================================================


def generate_http_headers(credential):
    #根据凭证生成请求头
    return {
        'Cookie': 'BDUSS=' + credential["cookie_BDUSS"],
        'Cipher-Text': credential["cipherText"],
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'keep-alive',
        'Referer': 'https://index.baidu.com/v2/main/index.html',
        'Host': 'index.baidu.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }

def decrypt(ptbk, index_data):
    #数据解密函数
    n = len(ptbk) // 2
    a = dict(zip(ptbk[:n], ptbk[n:]))
    return "".join([a[s] for s in index_data])

def format_keywords_for_api(keywords):
    #将关键词列表格式化为API所需的JSON字符串
    converted = [[{"name": keyword, "wordType": 1} for keyword in sublist] for sublist in keywords]
    return json.dumps(converted, ensure_ascii=False)

def get_baidu_index(keywords, start_date, end_date, region_code, credential):

    #爬取百度指数并返回包含每日数据的DataFrame。

    print(f"--- 正在查询: {keywords}, 时间范围: {start_date} to {end_date} ---")
    
    # 格式化关键词
    word_for_check = ','.join(['+'.join(kw_group) for kw_group in keywords])
    word_for_api = format_keywords_for_api(keywords)
    
    http_headers = generate_http_headers(credential)
    max_retries = 3
    
    for retry in range(max_retries):
        try:
            # 检查关键词是否存在
            check_url = f'https://index.baidu.com/api/AddWordApi/checkWordsExists?word={word_for_check}'
            check_response = requests.get(check_url, headers=http_headers, timeout=10).json()
            if check_response['data']['result']:
                invalid_words = [item['word'] for item in check_response['data']['result']]
                print(f"错误: 关键词 {invalid_words} 不存在或未被收录，请检查。")
                return None

            # 获取加密数据
            index_url = f'http://index.baidu.com/api/SearchApi/index?area={region_code}&word={word_for_api}&startDate={start_date}&endDate={end_date}'
            index_response = requests.get(index_url, headers=http_headers, timeout=10).json()
            
            encrypted_data = index_response['data']['userIndexes']
            uniqid = index_response['data']['uniqid']

            # 获取解密密钥
            ptbk_url = f'https://index.baidu.com/Interface/ptbk?uniqid={uniqid}'
            ptbk = requests.get(ptbk_url, headers=http_headers, timeout=10).json()['data']

            # 解密并处理数据
            all_series_data = {}
            for data_item in encrypted_data:
                keyword_name = ','.join([word['name'] for word in data_item['word']])
                
                decrypted_str = decrypt(ptbk, data_item['all']['data'])
                decrypted_list = [int(val) if val else 0 for val in decrypted_str.split(',')]
                
                # 生成日期范围
                # 百度指数对于长周期返回的是周数据，需要特殊处理
                days_span = (datetime.datetime.strptime(end_date, '%Y-%m-%d') - datetime.datetime.strptime(start_date, '%Y-%m-%d')).days
                
                if days_span > 365 and len(decrypted_list) < days_span:
     
                     date_range = pd.date_range(start=start_date, periods=len(decrypted_list), freq='W')
                else:
            
                     date_range = pd.date_range(start=start_date, periods=len(decrypted_list))
                
                all_series_data[keyword_name] = pd.Series(decrypted_list, index=date_range)
            
            #合并为DataFrame
            result_df = pd.DataFrame(all_series_data)
            print(f"查询成功！共获取 {len(result_df)} 条数据。")
            return result_df

        except RequestException as e:
            print(f"请求失败 (第 {retry+1}/{max_retries} 次尝试): {e}")
            time.sleep(random.randint(2, 5))
        except Exception as e:
            print(f"发生未知错误 (第 {retry+1}/{max_retries} 次尝试): {e}")
            return None
            
    print("达到最大重试次数，查询失败。")
    return None

def get_user_input():
    """
    一个专门用于获取用户输入的函数，包含输入引导和格式校验。
    """
    print("\n--- 欢迎使用百度指数爬虫 ---")
    
    # 关键词 
    keywords_str = input("请输入关键词，多个词用逗号','分隔；若要对比，请用分号';'分隔组：\n(示例: labubu,molly; dimoo)\n> ")

    keywords_list = [group.split(',') for group in keywords_str.split(';')]
    
    # 日期 
    date_format = "%Y-%m-%d"
    while True:
        start_date_str = input(f"请输入起始日期 (格式 YYYY-MM-DD, 如 2023-01-01): \n> ")
        try:
            datetime.datetime.strptime(start_date_str, date_format)
            break
        except ValueError:
            print("日期格式错误，请重新输入。")
            
    while True:
        end_date_str = input(f"请输入截止日期 (格式 YYYY-MM-DD, 如 2024-05-20): \n> ")
        try:

            if datetime.datetime.strptime(end_date_str, date_format) < datetime.datetime.strptime(start_date_str, date_format):
                print("截止日期不能早于起始日期，请重新输入。")
                continue
            break
        except ValueError:
            print("日期格式错误，请重新输入。")
            
    return keywords_list, start_date_str, end_date_str

if __name__ == '__main__':
    # 从用户处获取查询参数
    keywords, start_date, end_date = get_user_input()
    
    # 调用核心爬取函数
    final_dataframe = get_baidu_index(keywords, start_date, end_date, 0, CREDENTIALS)
    
    # 保存结果
    if final_dataframe is not None and not final_dataframe.empty:
        print("\n--- 数据预览 ---")
        print(final_dataframe.head())
        

        filename_keywords = "_".join([",".join(group) for group in keywords])
        safe_filename_keywords = "".join(c for c in filename_keywords if c.isalnum() or c in (',', '_'))
        
        output_filename = f"baidu_index_{safe_filename_keywords}_{start_date}_to_{end_date}.csv"
        
        final_dataframe.to_csv(output_filename)
        print(f"\n数据已成功保存到文件: {output_filename}")