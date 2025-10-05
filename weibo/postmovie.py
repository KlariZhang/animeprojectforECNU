# -*- coding: utf-8 -*-
"""
Weibo 爬虫 - 只统计关键词的帖子数量
"""

import json
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import InvalidSessionIdException
# ===== 配置区 =====
CHROMEDRIVER_PATH = r"C:/Users/HP/Code/chromedriver-win64/chromedriver-win64/chromedriver.exe"  # 修改为你的 chromedriver 路径
COOKIE_FILE = "weibo_cookie.json"  # Cookie 文件路径
INPUT_EXCEL = "newall_cleaned.xlsx"       # 输入关键词的 Excel 文件
SHEET_NAME = "movie"               # Excel 工作表名
KEYWORD_COLUMN = "anime"            # Excel 中关键词列名

TIME_BEGIN = "2023-06-01"           # 搜索起始时间
TIME_END = "2024-08-31"              # 搜索结束时间
PAGES = 15                          # 每个关键词爬取页数
OUTPUT_CSV = "weibo_anime_counts.csv"    # 保存结果的 CSV 文件
# ==================

class WeiboSeleniumScraper:
    def __init__(self, cookie_file: str):
        self.cookie_file = cookie_file
        self.browser = self._init_browser()

    def _init_browser(self):
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        service = Service(executable_path=CHROMEDRIVER_PATH)
        return webdriver.Chrome(service=service, options=chrome_options)

    def _login_with_cookies(self) -> bool:
        try:
            with open(self.cookie_file, "r", encoding="utf-8") as f:
                cookies = json.load(f)
            self.browser.get("https://weibo.com/")
            time.sleep(3)
            for cookie in cookies:
                self.browser.add_cookie(cookie)
            self.browser.refresh()
            time.sleep(3)
            print("[INFO] Cookie 登录成功")
            return True
        except Exception as e:
            print(f"[ERROR] Cookie 登录失败: {e}")
            return False

    from selenium.common.exceptions import InvalidSessionIdException

    def search_weibo_count(self, keyword: str, start_time: str, end_time: str, pages: int):
        count = 0
        for page in range(1, pages + 1):
            url = f"https://s.weibo.com/weibo?q={keyword}&timescope=custom:{start_time}:{end_time}&page={page}"
            try:
                self.browser.get(url)
                time.sleep(2)  # 可以适当调整，减少浏览器 idle
                posts = self.browser.find_elements("css selector", "div.card")
                count += len(posts)
            except InvalidSessionIdException:
                print(f"[ERROR] 浏览器 session 失效，正在重新初始化浏览器并登录...")
                # 关闭旧浏览器
                try:
                    self.browser.quit()
                except:
                    pass
                # 重新初始化浏览器
                self.browser = self._init_browser()
                if not self._login_with_cookies():
                    print("[ERROR] Cookie 登录失败，停止抓取")
                    break
                # 重试当前页
                self.browser.get(url)
                time.sleep(2)
                posts = self.browser.find_elements("css selector", "div.card")
                count += len(posts)
        return count



    def run(self, keywords, start_time, end_time, pages):
        if not self._login_with_cookies():
            return []

        all_counts = []
        for keyword in keywords:
            print(f"[INFO] 正在抓取关键词: {keyword}")
            count = self.search_weibo_count(keyword, start_time, end_time, pages)
            all_counts.append({"动漫": keyword, "帖子数": count})
        return all_counts


if __name__ == "__main__":
    # 读取 Excel 关键词
    df = pd.read_excel(INPUT_EXCEL, sheet_name=SHEET_NAME)
    keywords = df[KEYWORD_COLUMN].dropna().unique().tolist()

    scraper = WeiboSeleniumScraper(COOKIE_FILE)
    results = scraper.run(keywords, TIME_BEGIN, TIME_END, PAGES)

    if results:
        pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
        print(f"[SUCCESS] 已保存 {len(results)} 个关键词的帖子数量到 {OUTPUT_CSV}")
    else:
        print("[WARNING] 未抓取到任何数据")
