# -*- coding: utf-8 -*-
"""
Created on Sun Jul 20 20:05:18 2025

@author: yuxin
"""

import pandas as pd
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class SogouWeixinScraper:
    def __init__(self, driver_path):
        self.service = ChromeService(executable_path=driver_path)
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        self.browser = webdriver.Chrome(service=self.service, options=options)
        self.wait = WebDriverWait(self.browser, 10)
        print("浏览器已成功创建。")

    def _parse_single_page(self):

        page_data = []
        try:
            article_list = self.browser.find_element(By.CSS_SELECTOR, 'ul.news-list')
            articles = article_list.find_elements(By.TAG_NAME, 'li')
            print(f"当前页面发现 {len(articles)} 篇文章容器(li)。")

            for i, article in enumerate(articles):

                try:
                    title_element = article.find_element(By.CSS_SELECTOR, 'h3 a')
                    title = title_element.text
                    article_url = title_element.get_attribute('href')
                    


                    author = article.find_element(By.CSS_SELECTOR, 'span.all-time-y2').text
                    
                    summary = article.find_element(By.CSS_SELECTOR, 'p.txt-info').text
                    post_time_raw = article.find_element(By.CSS_SELECTOR, 'span.s2').text

                    item = {
                        '标题': title,
                        '作者': author,
                        '摘要': summary,
                        '发布时间(原始)': post_time_raw,
                        '文章链接': article_url,
                    }
                    page_data.append(item)

                except Exception as e:

                    continue
            return page_data
        except NoSuchElementException:
            print("在当前页未找到文章列表容器(ul.news-list)，可能页面结构已改变或没有结果。")
            return []

    def search(self, keyword, pages=3):
        print(f"\n开始在搜狗微信搜索爬取关键词 '{keyword}' 的文章...")
        
        # 搜狗微信搜索的URL
        search_url = f"https://weixin.sogou.com/weixin?type=2&query={keyword}"
        self.browser.get(search_url)

        # 首次访问可能需要处理验证码
        time.sleep(2)
        
        # 检查是否需要输入验证码
        try:
            captcha_img = self.browser.find_element(By.ID, 'seccodeImage')
            if captcha_img:
                print("!!!!!! 检测到验证码 !!!!!!")
                input("请在弹出的浏览器中手动输入验证码，然后回到这里按 'Enter' 键继续...")
        except NoSuchElementException:
            print("未检测到验证码，正常继续。")

        all_articles = []
        for i in range(pages):
            current_page = i + 1
            print(f"--- 正在爬取第 {current_page} 页 ---")
            
            try:
                self.wait.until(EC.presence_of_element_located((By.ID, "main")))
                time.sleep(random.uniform(2, 4))
                
                page_data = self._parse_single_page()
                if not page_data:
                    break
                all_articles.extend(page_data)

                if current_page < pages:
                    next_page_button = self.wait.until(EC.element_to_be_clickable((By.ID, 'sogou_next')))
                    next_page_button.click()
                    print("已点击'下一页'。")
                    time.sleep(random.uniform(3, 6))

            except TimeoutException:
                print("等待页面元素超时，可能已到达最后一页。")
                break
            except NoSuchElementException:
                print("未找到'下一页'按钮，爬取结束。")
                break
            except Exception as e:
                print(f"爬取第 {current_page} 页时发生未知错误: {e}")
                break
        
        return all_articles

    def save_to_csv(self, data, keyword):
        if not data:
            print("没有数据可以保存。")
            return
            
        df = pd.DataFrame(data)
        filename = f"sogou_weixin_{keyword}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\n数据已成功保存到文件: {filename}")

    def run(self):
        keyword = input('请输入要搜索的公众号文章关键词: ')
        try:
            pages = int(input('请输入想要爬取的页数 (注意：搜狗最多只显示100页): '))
        except ValueError:
            pages = 3
        
        article_data = self.search(keyword, pages)
        self.save_to_csv(article_data, keyword)
        
        print("\n爬取任务完成，关闭浏览器。")
        self.browser.quit()

if __name__ == '__main__':
    CHROME_DRIVER_PATH = "请填入你的chromedriver路径"
    scraper = SogouWeixinScraper(CHROME_DRIVER_PATH)
    scraper.run()