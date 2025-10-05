# -*- coding: utf-8 -*-
"""
Created on Fri Jul 18 11:12:38 2025

@author: yuxin
"""

import pandas as pd
import json
import time
import re
import datetime
import random
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException

# Cookie Acquisition 
def get_and_save_cookie_if_needed(driver_path, cookie_file='cookies.txt'):
    if os.path.exists(cookie_file):
        print(f"发现已存在的Cookie文件 '{cookie_file}'，将直接使用。")
        return True

    print(f"未找到Cookie文件 '{cookie_file}'，启动浏览器进行首次登录...")
    service = ChromeService(executable_path=driver_path)
    browser = webdriver.Chrome(service=service)
    
    try:
        browser.get('https://weibo.com/login.php')
        print("请在弹出的浏览器窗口中手动登录。")
        input("完成登录后，回到此终端窗口，按 'Enter' 键继续...")

        cookies_list = browser.get_cookies()
        with open(cookie_file, 'w') as f:
            json.dump(cookies_list, f)
        
        print(f"\nCookie已成功获取并保存到 '{cookie_file}'。")
        return True
    except Exception as e:
        print(f"获取Cookie时发生错误: {e}")
        return False
    finally:
        browser.quit()

# The Main Selenium Scraper 
class WeiboSeleniumScraper:
    def __init__(self, driver_path, cookie_file='cookies.txt'):
        self.service = ChromeService(executable_path=driver_path)
        self.browser = webdriver.Chrome(service=self.service)
        self.cookie_file = cookie_file
        self.wait = WebDriverWait(self.browser, 15) # 设置一个全局的智能等待
        print("浏览器已成功创建。")

    def _login_with_cookies(self):
        """加载Cookie以保持登录状态"""
        try:
            # 访问微博域名
            self.browser.get("https://weibo.com/")
            with open(self.cookie_file, 'r') as f:
                cookies_list = json.load(f)
                for cookie in cookies_list:
                    # 浮点数转换
                    if 'expiry' in cookie and isinstance(cookie['expiry'], float):
                        cookie['expiry'] = int(cookie['expiry'])
                    self.browser.add_cookie(cookie)
            print("Cookie加载成功。")
            return True
        except Exception as e:
            print(f"加载Cookie失败: {e}")
            return False






    def _parse_single_page(self):

        page_data = []
        cards = self.browser.find_elements(By.XPATH, '//div[@class="card-wrap" and @action-type="feed_list_item"]')
        print(f"当前页面发现 {len(cards)} 个微博卡片。")

        for i, card in enumerate(cards):
            try:
                # 提取基础信息
                user_name = card.find_element(By.CSS_SELECTOR, 'a[nick-name]').get_attribute('nick-name')
                
                # 时间和来源 
       
                from_element = card.find_element(By.XPATH, './/div[@class="from"] | .//p[@class="from"]')
                post_time = from_element.find_element(By.CSS_SELECTOR, 'a').text.strip()
                
                # 微博正文
                content = ""
                # 优先寻找“展开全文”后的内容
                try:
                    expand_button = card.find_element(By.CSS_SELECTOR, 'p.txt a[action-type="fl_unfold"]')
                    self.browser.execute_script("arguments[0].click();", expand_button)
                    time.sleep(0.5)
                    content_element = card.find_element(By.CSS_SELECTOR, 'p[node-type="feed_list_content_full"]')
                    content = content_element.text
                except NoSuchElementException:
                    # 如果没有“展开”按钮，就找普通的内容容器
                    content_element = card.find_element(By.CSS_SELECTOR, 'p[node-type="feed_list_content"]')
                    content = content_element.text
                
                # 处理转评赞

                try: # 普通帖子
                    forwards = card.find_element(By.CSS_SELECTOR, 'a[action-type="fl_forward"] span.woo-font').text.strip()
                    comments = card.find_element(By.CSS_SELECTOR, 'a[action-type="fl_comment"] span.woo-font').text.strip()
                    likes = card.find_element(By.CSS_SELECTOR, 'button[action-type="fl_like"] span.woo-font').text.strip()
                except NoSuchElementException: # 热门帖子
                    forwards = card.find_element(By.XPATH, './/a[contains(@action-type, "forward")]').text.strip()
                    comments = card.find_element(By.XPATH, './/a[contains(@action-type, "comment")]').text.strip()
                    likes = card.find_element(By.CSS_SELECTOR, 'a[action-type="feed_list_like"] span.woo-like-count').text.strip()


                item = {
                    '博主昵称': user_name,
                    '发文时间': post_time,
                    '微博正文': content,
                    # 提取数字，并处理空字符串的情况
                    '转发数': re.search(r'\d+', forwards).group() if forwards and re.search(r'\d+', forwards) else 0,
                    '评论数': re.search(r'\d+', comments).group() if comments and re.search(r'\d+', comments) else 0,
                    '点赞数': likes if likes.isdigit() else 0
                }
                page_data.append(item)
                print(f"卡片 {i+1} 解析成功！ User: {user_name}")

            except Exception:
    
                continue
        
        return page_data
    
    
    
    
    def search(self, keyword, pages=5, scope='ori'):
        if not self._login_with_cookies():
            return []
            
        print(f"\n开始爬取关键词 '{keyword}' 的微博...")
        
        # 构造搜索URL
        search_url = f"https://s.weibo.com/weibo?q={keyword}&scope={scope}"
        self.browser.get(search_url)
        
        all_weibo_data = []
        for i in range(pages):
            current_page = i + 1
            print(f"--- 正在爬取第 {current_page} 页 ---")
            
            try:
                # 智能等待页面关键元素加载完成
                self.wait.until(EC.presence_of_element_located((By.ID, "pl_feedlist_index")))
                
                page_data = self._parse_single_page()
                if not page_data:
                    print("本页未能解析到任何数据，可能已无更多结果。")
                    break
                
                all_weibo_data.extend(page_data)
                print(f"第 {current_page} 页成功解析 {len(page_data)} 条微博。")

                # 点击“下一页”按钮
                next_page_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.next')))
                next_page_button.click()
                time.sleep(random.uniform(2, 4)) # 模仿思考时间

            except TimeoutException:
                print("等待页面元素超时，可能已到达最后一页或页面加载失败。")
                break
            except NoSuchElementException:
                print("未找到'下一页'按钮，爬取结束。")
                break
            except Exception as e:
                print(f"在爬取第 {current_page} 页时发生未知错误: {e}")
                break

        return all_weibo_data

    def save_to_csv(self, data, keyword):
        if not data:
            print("没有数据可以保存。")
            return
            
        df = pd.DataFrame(data)
        filename = f"weibo_selenium_{keyword}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\n数据已成功保存到文件: {filename}")

    def run(self):
        keyword = input('请输入微博搜索的关键词，按回车键确认：')
        scope_choice = input('仅搜索原创请输入ori，搜索全部请直接回车：')
        scope = 'ori' if scope_choice.lower() == 'ori' else ''
        
        try:
            pages = int(input('请输入想要爬取的页数：'))
        except ValueError:
            pages = 5 # 默认值
        
        weibo_data = self.search(keyword, pages, scope)
        self.save_to_csv(weibo_data, keyword)
        
        print("\n爬取任务完成，关闭浏览器。")
        self.browser.quit()


if __name__ == '__main__':
    CHROME_DRIVER_PATH ="请填入你的chromedriver路径"
    
    if get_and_save_cookie_if_needed(CHROME_DRIVER_PATH):
        scraper = WeiboSeleniumScraper(CHROME_DRIVER_PATH)
        scraper.run()