# -*- coding: utf-8 -*-
"""
Created on Fri Jul 18 18:42:25 2025
Modified for batch processing, custom page numbers, and resumable crawling on Fri Aug 15 14:53:00 2025

@author: yuxin
"""

import pandas as pd
import time
import re
import random
import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager


# --- 新增代码：自动切换到脚本所在目录 ---
# 获取脚本的绝对路径
script_path = os.path.abspath(sys.argv[0])

# 获取脚本所在的目录
script_dir = os.path.dirname(script_path)
# 将工作目录切换到脚本所在目录
os.chdir(script_dir)
print(f"当前工作目录已切换到: {os.getcwd()}")
# --- 新增代码结束 ---

class XianyuSeleniumScraper:
    def __init__(self):
        # 使用 webdriver-manager 自动管理 driver
        self.service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        self.browser = webdriver.Chrome(service=self.service, options=options)
        self.wait = WebDriverWait(self.browser, 15)
        

        # ====================================================================
        # 选择器配置区 (保持不变)
        # ====================================================================
        self.selectors = {
            "home_search_input": 'input[class*="search-input"]',
            "home_search_button": 'button[class*="search-icon"]',
            "search_results_container": 'div[class*="feeds-list-container"]',
            "item_card": 'a[class*="feeds-item-wrap"]',
            "pagination_input": 'input[class*="search-pagination-to-page-input"]',
            "pagination_confirm_button": 'button[class*="search-pagination-to-page-confirm-button"]',
            "item_title": 'div[class*="row1-wrap-title"]',
            "item_price_integer": 'span[class*="number--"]',
            "item_price_decimal": 'span[class*="decimal--"]',
            "item_location": 'p[class*="seller-text--"]',
            "item_wants": 'div[class*="price-desc--"] .text--MaM9Cmdn',
        }
        print("浏览器已成功创建。")

    def _parse_single_page(self):
        page_data = []
        cards = self.browser.find_elements(By.CSS_SELECTOR, self.selectors["item_card"])
        print(f"当前页面发现 {len(cards)} 个商品卡片。")

        for card in cards:
            try:
                title = card.find_element(By.CSS_SELECTOR, self.selectors["item_title"]).get_attribute('title')
                item_url = card.get_attribute('href')
                
                price_number = card.find_element(By.CSS_SELECTOR, self.selectors["item_price_integer"]).text
                try:
                    price_decimal = card.find_element(By.CSS_SELECTOR, self.selectors["item_price_decimal"]).text
                except NoSuchElementException:
                    price_decimal = ""
                price_value = float(f"{price_number}{price_decimal}")

                location = card.find_element(By.CSS_SELECTOR, self.selectors["item_location"]).text
                
                try:
                    wants_text = card.find_element(By.CSS_SELECTOR, self.selectors["item_wants"]).text
                    wants_count = re.search(r'\d+', wants_text).group() if re.search(r'\d+', wants_text) else 0
                except NoSuchElementException:
                    wants_count = 0

                page_data.append({
                    '标题': title, '价格(元)': price_value, '所在地': location,
                    '想要人数': int(wants_count), '商品URL': item_url,
                })
            except Exception:
                continue
        
        return page_data
    
    def search(self, keyword, pages=5):
        print(f"\n开始爬取关键词 '{keyword}' 的闲鱼商品...")
        self.browser.get("https://www.goofish.com/")

        try:
            search_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors["home_search_input"])))
            search_input.send_keys(keyword)
            search_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, self.selectors["home_search_button"])))
            search_button.click()
            print(f"已为关键词 '{keyword}' 执行搜索。")
        except TimeoutException:
            print(f"关键词 '{keyword}' 搜索失败：在首页未找到搜索框或按钮。")
            return []

        all_item_data = []
        
        print("--- 正在爬取第 1 页 ---")
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors["search_results_container"])))
            time.sleep(random.uniform(2, 4))
            page_data = self._parse_single_page()
            all_item_data.extend(page_data)
            print(f"第 1 页成功解析 {len(page_data)} 条商品。")
        except TimeoutException:
            print("搜索结果页加载失败或未找到商品容器。")
            return all_item_data

        for page_num in range(2, pages + 1):
            print(f"--- 准备跳转到第 {page_num} 页 ---")
            try:
                page_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors["pagination_input"])))
                self.browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", page_input)
                time.sleep(0.5)
                page_input.clear()
                page_input.send_keys(str(page_num))
                confirm_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, self.selectors["pagination_confirm_button"])))
                self.browser.execute_script("arguments[0].click();", confirm_button)
                
                print(f"已请求跳转到第 {page_num} 页。")
                time.sleep(random.uniform(4, 8)) 
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors["search_results_container"])))
                
                page_data = self._parse_single_page()
                if not page_data:
                    print("本页未能解析到任何数据，可能已是最后一页。")
                    break
                all_item_data.extend(page_data)
                print(f"第 {page_num} 页成功解析 {len(page_data)} 条商品。")

            except (TimeoutException, NoSuchElementException):
                print(f"在跳转到第 {page_num} 页时，未找到翻页组件，结束当前关键词爬取。")
                break
            except Exception as e:
                print(f"在爬取第 {page_num} 页时发生未知错误: {e}")
                break

        return all_item_data

    def save_to_csv(self, data, keyword, output_dir):
        if not data:
            print(f"关键词 '{keyword}' 没有收集到数据，不生成文件。")
            return
        
        safe_keyword = re.sub(r'[\\/*?:"<>|]', "", keyword)
        filename = f"{safe_keyword}.csv"
        filepath = os.path.join(output_dir, filename)
        
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f"\n数据已成功保存到文件: {filepath}")

    def close_browser(self):
        print("\n所有任务完成，关闭浏览器。")
        self.browser.quit()

# *** NEW: 任务处理函数 ***
def process_task(scraper, input_csv_path, keyword_column_name, output_folder, pages_to_scrape):
    """
    处理单个输入文件，执行爬取并保存结果。
    包含断点续爬逻辑。
    """
    print(f"\n{'='*25}\n 开始处理文件: {input_csv_path}\n{'='*25}")

    # 1. 创建输出文件夹
    os.makedirs(output_folder, exist_ok=True)

    # 2. 读取关键词列表
    try:
        df = pd.read_csv(input_csv_path)
        if keyword_column_name not in df.columns:
            print(f"错误：输入文件 '{input_csv_path}' 中未找到名为 '{keyword_column_name}' 的列。")
            return
        keywords = df[keyword_column_name].dropna().unique().tolist()
        print(f"成功从 '{input_csv_path}' 读取到 {len(keywords)} 个唯一关键词。")
    except FileNotFoundError:
        print(f"错误：输入文件 '{input_csv_path}' 未找到。请确保文件路径正确。")
        return
    except Exception as e:
        print(f"读取CSV文件时发生错误: {e}")
        return

    if not keywords:
        print("关键词列表为空，跳过此任务。")
        return
        
    # 3. 循环处理当前任务的所有关键词
    total_keywords = len(keywords)
    for i, keyword in enumerate(keywords):
        print(f"\n--- 正在处理 '{input_csv_path}' 中第 {i+1}/{total_keywords} 个关键词: {keyword} ---")
        
        # *** 断点续爬核心逻辑 ***
        # 检查结果文件是否已存在
        safe_keyword = re.sub(r'[\\/*?:"<>|]', "", keyword)
        expected_filepath = os.path.join(output_folder, f"{safe_keyword}.csv")
        
        if os.path.exists(expected_filepath):
            print(f"结果文件 '{expected_filepath}' 已存在，跳过此关键词。")
            continue
        
        # 如果文件不存在，则执行爬取
        item_data = scraper.search(keyword, pages=pages_to_scrape)
        scraper.save_to_csv(item_data, keyword, output_folder)
        
        if i < total_keywords - 1:
            sleep_time = random.uniform(5, 15)
            print(f"\n当前关键词处理完毕，随机等待 {sleep_time:.2f} 秒...")
            time.sleep(sleep_time)

# *** 主要修改区域 ***
def main():
    # --- 配置区 ---
    # 在这里配置所有要处理的任务
    tasks = [
        {
            "input_file": "anime_list.csv",
            "column_name": "Anime Name", # 请根据实际CSV文件中的列名修改
            "output_folder": "xianyu_anime_results"
        },
        {
            "input_file": "movie_list.csv",
            "column_name": "movie", # 请根据实际CSV文件中的列名修改
            "output_folder": "xianyu_movie_results"
        }
    ]
    # --- 配置结束 ---

    # 获取用户希望爬取的页数
    try:
        pages_str = input("请输入希望为每个关键词爬取的页数 (默认为3，按回车确认): ")
        if pages_str.strip() == '':
            PAGES_TO_SCRAPE = 3
        else:
            PAGES_TO_SCRAPE = int(pages_str)
            if PAGES_TO_SCRAPE <= 0:
                print("页数必须大于0。将使用默认值 3。")
                PAGES_TO_SCRAPE = 3
    except ValueError:
        print("输入不是有效的数字。将使用默认值 3。")
        PAGES_TO_SCRAPE = 3
    
    print(f"已设定：将为每个关键词爬取 {PAGES_TO_SCRAPE} 页数据。")
    print("-" * 50)

    # 初始化一次爬虫
    scraper = XianyuSeleniumScraper()

    # 循环处理所有配置的任务
    for task in tasks:
        process_task(
            scraper=scraper,
            input_csv_path=task["input_file"],
            keyword_column_name=task["column_name"],
            output_folder=task["output_folder"],
            pages_to_scrape=PAGES_TO_SCRAPE
        )

    # 所有任务完成后关闭浏览器
    scraper.close_browser()

if __name__ == '__main__':
    main()