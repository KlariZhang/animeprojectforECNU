# -*- coding: utf-8 -*-
"""
Created on Thu Jul 17 22:37:29 2025

@author: yuxin
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
import time
import json

def get_and_save_cookie(driver_path, cookie_file='cookies.txt'):
    """
    使用Selenium打开微博登录页，等待用户手动登录后，
    获取并以JSON格式保存Cookie。
    """
    
    options = Options()
    service = ChromeService(executable_path=driver_path)
    browser = webdriver.Chrome(service=service, options=options)
    
    print("浏览器已成功创建。")

    try:
        login_url = 'https://weibo.com/login.php'
        browser.get(login_url)
        print(f"已打开微博登录页: {login_url}")
        print("请在弹出的浏览器窗口中，手动扫码或输入账号密码登录。")
        
        input("请在完成登录后，回到这个终端窗口，然后按 'Enter' 键继续...")

        print("登录已完成，正在获取Cookie...")


        cookies_list = browser.get_cookies()
        

        with open(cookie_file, 'w') as f:

            json.dump(cookies_list, f)
        
        print(f"\nCookie已成功获取并保存为JSON格式到 '{cookie_file}' 文件中！")
        
    except Exception as e:
        print(f"获取Cookie时发生错误: {e}")
    finally:
        print("关闭浏览器。")
        browser.quit()

if __name__ == '__main__':

    CHROME_DRIVER_PATH = "请填入chromedriver路径"
    
    # 调用函数，它会默认创建名为 'cookies.txt' 的文件
    get_and_save_cookie(CHROME_DRIVER_PATH)


