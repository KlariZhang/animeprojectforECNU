import os
import csv
import json
import re
import time
import pickle
import pandas as pd
import ast
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException

# --- 辅助函数区 ---
def save_progress(progress):
    """保存当前进度到progress.txt"""
    try:
        with open("progress.txt", "w", encoding='utf-8') as f:
            json.dump(progress, f, indent=4)
    except Exception as e:
        print(f"进度存档时出错: {e}")

def write_to_csv(filename, comments_data):
    """将一个或多个评论追加写入到指定的CSV文件"""
    if not comments_data:
        return
    
    file_exists = os.path.exists(filename)
    
    try:
        with open(filename, mode='a', encoding='utf-8', newline='') as csvfile:
            fieldnames = ['评论内容', '集数']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerows(comments_data)
        print(f"已将 {len(comments_data)} 条评论成功写入到 {filename}")
    except Exception as e:
        print(f"写入CSV '{filename}' 时出错: {e}")

def scroll_to_bottom(driver, max_scrolls=4):
    """滚动页面以加载评论"""
    print("开始向下滚动以加载评论...")
    SCROLL_PAUSE_TIME = 4
    last_height = driver.execute_script("return document.documentElement.scrollHeight")

    for scroll_count in range(max_scrolls):
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.documentElement.scrollHeight")
        if new_height == last_height:
            print("已滚动到底部。")
            break
        last_height = new_height
        print(f'下滑滚动第{scroll_count + 1}次 / 最大滚动{max_scrolls}次')

def sanitize_filename(name):
    """清理字符串，使其成为合法的文件名"""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

# --- 核心抓取函数 ---
def scrape_top_level_comments(driver, url):
    """访问URL，滚动并仅抓取一级评论的文本内容"""
    comments_data = []
    try:
        driver.get(url)
        scroll_to_bottom(driver)
        
        wait = WebDriverWait(driver, 20)
        bili_comments_host = wait.until(EC.presence_of_element_located((By.TAG_NAME, "bili-comments")))
        print("评论区组件 'bili-comments' 已加载。")
        
        script = """
        return arguments[0].shadowRoot.querySelector('#contents').querySelector('#feed')
               .querySelectorAll('bili-comment-thread-renderer');
        """
        thread_renderers = driver.execute_script(script, bili_comments_host)
        print(f"已定位到 {len(thread_renderers)} 条一级评论线程。开始解析文本...")

        for renderer in thread_renderers:
            try:
                text_script = """
                return arguments[0].shadowRoot.querySelector('bili-comment-renderer')
                       .shadowRoot.querySelector('bili-rich-text')
                       .shadowRoot.querySelector('#contents').innerText;
                """
                content = driver.execute_script(text_script, renderer).strip()
                
                if content:
                    comments_data.append({"评论内容": content})
            except Exception:
                continue

        return comments_data

    except TimeoutException:
        print(f"错误：在20秒内未能找到评论区组件 'bili-comments'。")
        return []
    except Exception as e:
        print(f"抓取过程中发生未知错误: {e}")
        return []

# --- 主程序 ---
def main():
    # 登录与会话管理
    cookies_file = 'cookies.pkl'
    if not os.path.exists(cookies_file):
        print("首次运行，需要手动登录以获取Cookie。")
        driver_login = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        driver_login.get('https://www.bilibili.com/')
        input("请在弹出的浏览器中登录B站，登录成功后回到此处按回车键继续...")
        with open(cookies_file, 'wb') as f:
            pickle.dump(driver_login.get_cookies(), f)
        print("Cookie已保存。")
        driver_login.quit()

    # 设置工作浏览器
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument("--disable-plugins-discovery")
    options.add_argument("--mute-audio")
    options.add_argument("--autoplay-policy=user-gesture-required") # 增加此项以尝试禁止视频自动播放
    options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    driver.get('https://www.bilibili.com/')
    with open(cookies_file, 'rb') as f:
        cookies = pickle.load(f)
    for cookie in cookies:
        driver.add_cookie(cookie)
    print("Cookie加载成功，已进入登录状态。")

    # --- 新增：创建输出文件夹 ---
    output_folder = "results"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"输出文件夹 '{output_folder}' 不存在，已自动创建。")

    # 读取任务与进度
    if os.path.exists("progress.txt"):
        with open("progress.txt", "r", encoding='utf-8') as f:
            try:
                progress = json.load(f)
            except json.JSONDecodeError:
                print("警告: progress.txt 文件为空或已损坏，将从头开始。")
                progress = {"last_completed_series_index": -1, "last_completed_episode_index": -1}
    else:
        progress = {"last_completed_series_index": -1, "last_completed_episode_index": -1}

    try:
        tasks_df = pd.read_csv('master_url_list.csv')
    except FileNotFoundError:
        print("错误：未找到 master_url_list.csv 文件。请检查文件是否存在。")
        driver.quit()
        return

    # --- 主循环 ---
    for series_index, series_data in tasks_df.iterrows():
        if series_index <= progress["last_completed_series_index"]:
            print(f"跳过已完成的番剧 {series_index + 1}/{len(tasks_df)}: {series_data['series_name']}")
            continue

        series_name = series_data['series_name']
        
        # --- 修改：构建包含文件夹路径的完整文件名 ---
        csv_basename = sanitize_filename(series_name) + ".csv"
        output_filename = os.path.join(output_folder, csv_basename)
        # ----------------------------------------
        
        try:
            episode_urls = ast.literal_eval(series_data['episode_urls'])
            if not isinstance(episode_urls, list):
                print(f"警告：番剧 {series_name} 的URL列表格式不正确，已跳过。")
                continue
        except (ValueError, SyntaxError):
            print(f"警告：无法解析番剧 {series_name} 的URL列表，已跳过。")
            continue
            
        print(f"\n--- 开始处理番剧 {series_index + 1}/{len(tasks_df)}: {series_name} ---")

        start_episode_index = 0
        if series_index == progress.get("last_completed_series_index", -1) + 1:
             start_episode_index = progress.get("last_completed_episode_index", -1) + 1

        for episode_index in range(start_episode_index, len(episode_urls)):
            url = episode_urls[episode_index]
            try:
                epid_search = re.search(r'/(ep\d+)', url)
                epid = epid_search.group(1) if epid_search else f"未知ep_{episode_index+1}"
                print(f"  > 正在处理剧集 {episode_index + 1}/{len(episode_urls)}: {epid}")
                
                comments = scrape_top_level_comments(driver, url)
                
                if comments:
                    comments_with_epid = [{'评论内容': c['评论内容'], '集数': epid} for c in comments]
                    write_to_csv(output_filename, comments_with_epid)
                else:
                    print(f"  剧集 {epid} 未抓取到任何评论。")

                progress["last_completed_episode_index"] = episode_index
                save_progress(progress)

            except WebDriverException as e:
                print(f"发生严重错误，可能浏览器已崩溃，程序终止: {e}")
                driver.quit()
                return
            except Exception as e:
                print(f"  处理URL {url} 时发生未知错误: {e}")
                continue

        progress["last_completed_series_index"] = series_index
        progress["last_completed_episode_index"] = -1
        save_progress(progress)
        print(f"--- 番剧《{series_name}》已全部处理完成 ---")

    driver.quit()
    print(f"\n--- 所有任务已完成！结果已保存至 '{output_folder}' 文件夹。 ---")

if __name__ == "__main__":
    main()