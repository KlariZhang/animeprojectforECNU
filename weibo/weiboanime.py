# -*- coding: utf-8 -*-
"""
Weibo 爬虫 - Cookie 登录版
使用说明：
1. 下载 ChromeDriver (版本需与 Chrome 主版本一致)
2. 修改 CHROMEDRIVER_PATH 为你的 chromedriver.exe 路径
3. 准备 weibo_cookie.json 文件（从浏览器复制 Cookie 转换得到）
4. 修改 INPUT_EXCEL、SHEET_NAME、KEYWORD_COLUMN、TIME_BEGIN、TIME_END、PAGES
5. 运行脚本
"""

import json
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# ===== 配置区 =====
CHROMEDRIVER_PATH = r"C:/Users/HP/Code/chromedriver-win64/chromedriver-win64/chromedriver.exe"  # 修改为你的 chromedriver 路径
COOKIE_FILE = "weibo_cookie.json"  # Cookie 文件路径
INPUT_EXCEL = "newall_cleaned.xlsx"       # 输入关键词的 Excel 文件
SHEET_NAME = "anime"               # Excel 工作表名
KEYWORD_COLUMN = "anime"            # Excel 中关键词列名

TIME_BEGIN = "2024-01-01"           # 搜索起始时间
TIME_END = "2024-01-31"             # 搜索结束时间
PAGES = 50                           # 每个关键词爬取页数
OUTPUT_CSV = "weibo_anime_results_new2.csv"    # 保存结果的 CSV 文件
# ==================

class WeiboSeleniumScraper:
    def __init__(self, cookie_file: str):
        self.cookie_file = cookie_file
        self.browser = self._init_browser()

    def _init_browser(self):
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        service = Service(executable_path=CHROMEDRIVER_PATH)  # 固定本地驱动
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

    def search_weibo(self, keyword: str, start_time: str, end_time: str, pages: int):
        results = []
        for page in range(1, pages + 1):
            url = f"https://s.weibo.com/weibo?q={keyword}&timescope=custom:{start_time}:{end_time}&page={page}"
            self.browser.get(url)
            time.sleep(2)

            posts = self.browser.find_elements("css selector", "div.card")
            for post in posts:
                try:
                    content = post.find_element("css selector", "p.txt").text.strip()
                    results.append({"关键词": keyword, "内容": content})
                except:
                    continue
        return results

    def run(self, keywords, start_time, end_time, pages):
        if not self._login_with_cookies():
            return []

        all_results = []
        for keyword in keywords:
            print(f"[INFO] 正在抓取关键词: {keyword}")
            data = self.search_weibo(keyword, start_time, end_time, pages)
            all_results.extend(data)
        return all_results

if __name__ == "__main__":
    # 读取 Excel 关键词
    df = pd.read_excel(INPUT_EXCEL, sheet_name=SHEET_NAME)
    keywords = df[KEYWORD_COLUMN].dropna().unique().tolist()

    scraper = WeiboSeleniumScraper(COOKIE_FILE)
    results = scraper.run(keywords, TIME_BEGIN, TIME_END, PAGES)

    if results:
        pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
        print(f"[SUCCESS] 已保存 {len(results)} 条数据到 {OUTPUT_CSV}")
    else:
        print("[WARNING] 未抓取到任何数据")



