# -*- coding: utf-8 -*-
"""
Created on Fri Jul 18 18:42:25 2025

@author: yuxin
"""

import pandas as pd
import time
import re
import random
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

class XianyuSeleniumScraper:
    def __init__(self, driver_path):
        self.service = ChromeService(executable_path=driver_path)
        options = webdriver.ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        self.browser = webdriver.Chrome(service=self.service, options=options)
        self.wait = WebDriverWait(self.browser, 15)
        
        # ====================================================================
        # 选择器配置区
        # 如果未来闲鱼页面变化，需要修改这里
        # ====================================================================
        self.selectors = {
            "home_search_input": 'input[class*="search-input"]',
            "home_search_button": 'button[class*="search-icon"]',
            "search_results_container": 'div[class*="feeds-list-container"]',
            "item_card": 'a[class*="feeds-item-wrap"]',
            
            # 翻页相关的选择器 
            "pagination_input": 'input[class*="search-pagination-to-page-input"]',
            "pagination_confirm_button": 'button[class*="search-pagination-to-page-confirm-button"]',
            
            # 单个商品卡片内部的选择器
            "item_title": 'div[class*="row1-wrap-title"]',
            "item_price_integer": 'span[class*="number--"]',
            "item_price_decimal": 'span[class*="decimal--"]',
            "item_location": 'p[class*="seller-text--"]',
            "item_wants": 'div[class*="price-desc--"] .text--MaM9Cmdn',
        }
        print("浏览器已成功创建。")

    def _parse_single_page(self):
        page_data = []
        # 使用配置的选择器
        cards = self.browser.find_elements(By.CSS_SELECTOR, self.selectors["item_card"])
        print(f"当前页面发现 {len(cards)} 个商品卡片。")

        for i, card in enumerate(cards):
            try:
                title_element = card.find_element(By.CSS_SELECTOR, self.selectors["item_title"])
                title = title_element.get_attribute('title')
                item_url = card.get_attribute('href')
                
                price_number = card.find_element(By.CSS_SELECTOR, self.selectors["item_price_integer"]).text
                try:
                    price_decimal = card.find_element(By.CSS_SELECTOR, self.selectors["item_price_decimal"]).text
                except NoSuchElementException:
                    price_decimal = ""
                
                price_full = f"{price_number}{price_decimal}"
                price_value = float(price_full)

                location = card.find_element(By.CSS_SELECTOR, self.selectors["item_location"]).text
                
                try:
                    wants_text = card.find_element(By.CSS_SELECTOR, self.selectors["item_wants"]).text
                    wants_count = re.search(r'\d+', wants_text).group() if re.search(r'\d+', wants_text) else 0
                except NoSuchElementException:
                    wants_count = 0

                item = {
                    '标题': title,
                    '价格(元)': price_value,
                    '所在地': location,
                    '想要人数': int(wants_count),
                    '商品URL': item_url,
                }
                page_data.append(item)
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
            print("已执行搜索操作。")
        except TimeoutException:
            print("在首页未找到搜索框或按钮。")
            return []

        all_item_data = []
        

        print("--- 正在爬取第 1 页 ---")
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors["search_results_container"])))
            print("第1页容器已出现，页面加载完成。")
            time.sleep(random.uniform(2, 4))
            page_data = self._parse_single_page()
            all_item_data.extend(page_data)
            print(f"第 1 页成功解析 {len(page_data)} 条商品。")
        except TimeoutException:
            print("搜索结果页加载失败或未找到商品容器。")
            return all_item_data # 返回已有的数据

        # 循环爬取后续页面
        for page_num in range(2, pages + 1):
            print(f"--- 准备跳转到第 {page_num} 页 ---")
            try:
                page_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors["pagination_input"])))
                
                self.browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", page_input)
                time.sleep(0.5)
                
                page_input.clear()
                page_input.send_keys(str(page_num)) # 确保输入的是字符串
                
                confirm_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, self.selectors["pagination_confirm_button"])))
                

                print("已找到'确定'按钮，尝试使用JavaScript点击...")
                self.browser.execute_script("arguments[0].click();", confirm_button)
                
                print(f"已跳转到第 {page_num} 页。")
                
                
                
                time.sleep(random.uniform(4, 8)) 
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors["search_results_container"])))
                
    
                page_data = self._parse_single_page()
                if not page_data:
                    print("本页未能解析到任何数据，可能已是最后一页。")
                    break
                all_item_data.extend(page_data)
                print(f"第 {page_num} 页成功解析 {len(page_data)} 条商品。")

            except (TimeoutException, NoSuchElementException):
                print(f"在跳转到第 {page_num} 页时，未找到翻页组件，爬取结束。")
                break
            except Exception as e:
                print(f"在爬取第 {page_num} 页时发生未知错误: {e}")
                break

        return all_item_data


    def save_to_csv(self, data, keyword):
        if not data:
            print("没有数据可以保存。")
            return
        
        if isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)
            filename = f"xianyu_selenium_{keyword}.csv"
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"\n数据已成功保存到文件: {filename}")
        else:
            print("解析到的数据为空列表，不生成文件。")

    def run(self):
        keyword = input('请输入闲鱼搜索的关键词，按回车键确认：')
        try:
            pages = int(input('请输入想要爬取的页数：'))
        except ValueError:
            pages = 3 
        
        item_data = self.search(keyword, pages)
        self.save_to_csv(item_data, keyword)
        
        print("\n爬取任务完成，关闭浏览器。")
        self.browser.quit()

if __name__ == '__main__':
    CHROME_DRIVER_PATH ="请填入你的chromefriver路径"
    scraper = XianyuSeleniumScraper(CHROME_DRIVER_PATH)
    scraper.run()