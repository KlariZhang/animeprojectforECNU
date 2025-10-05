import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

# === 1. 配置 Selenium ===
chrome_driver_path = r"C:/Code/python/animeproject/chromedriver-win64/chromedriver.exe"
options = Options()
# options.add_argument("--headless")  # 调试时先注释掉
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--lang=zh-CN")

driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)

# === 2. 读取 Excel 动漫 IP 列表 ===
file_path = "newall.xlsx"
df_anime = pd.read_excel(file_path, sheet_name="anime")
anime_list = df_anime['clean_name'].dropna().tolist()

# === 3. 手动登录淘宝 ===
driver.get("https://www.taobao.com")
print("请手动登录淘宝并完成滑块/验证码，登录完成后按回车继续...")
input("登录完成后按回车继续...")

# === 4. 定义抓取函数（带自动检测拦截页） ===
def fetch_taobao_items(keyword, max_pages=2, max_retry=3):
    all_items = []

    for page in range(max_pages):
        s_index = page * 44
        search_url = f"https://s.taobao.com/search?q={keyword}&s={s_index}"

        for attempt in range(max_retry):
            print(f"\n[DEBUG] 抓取关键字: {keyword}, 第 {page+1} 页, URL={search_url}, 尝试 {attempt+1}/{max_retry}")
            driver.get(search_url)
            time.sleep(random.randint(2,4))  # 随机等待页面加载

            # 检测是否被拦截
            if "deny_h5.html" in driver.current_url:
                print("[ALERT] 淘宝拦截了访问，请人工处理（滑块/验证码）...")
                input("处理完成后按回车继续...")
                continue  # 完成人工干预后重试当前页

            # 尝试获取商品列表
            items = driver.find_elements(By.CSS_SELECTOR, "div.item.J_MouserOnverReq")
            if not items:
                items = driver.find_elements(By.CSS_SELECTOR, "div[data-category='auctions'] div.item")

            if items:
                print(f"[DEBUG] 本页找到商品数量: {len(items)}")
                break  # 成功抓取到商品，跳出重试循环
            else:
                print("[WARN] 本页未找到商品，重试...")
                time.sleep(random.randint(3,5))
        else:
            print("[ERROR] 本页多次尝试仍未抓取到商品，跳过")
            continue  # 如果 max_retry 次仍失败，跳到下一页

        # 解析商品信息
        for idx, item in enumerate(items):
            try:
                title = item.find_element(By.CSS_SELECTOR, "div.row.row-2.title").text
            except:
                title = ""
            try:
                price = item.find_element(By.CSS_SELECTOR, "div.price.g_price.g_price-highlight strong").text
            except:
                price = ""
            try:
                sales = item.find_element(By.CSS_SELECTOR, "div.row.row-3.g-clearfix span.sale-num").text
            except:
                sales = ""
            try:
                shop = item.find_element(By.CSS_SELECTOR, "div.shopname").text
            except:
                shop = ""

            all_items.append({
                "anime_ip": keyword,
                "title": title,
                "price": price,
                "sales": sales,
                "shop_name": shop
            })

        # 随机等待，模拟人工翻页
        time.sleep(random.randint(3,6))

    return all_items

# === 5. 循环抓取所有动漫 IP ===
all_data = []
for ip in anime_list:
    print(f"\n====== 正在抓取动漫: {ip} ======")
    try:
        items = fetch_taobao_items(ip, max_pages=2)
        all_data.extend(items)
    except Exception as e:
        print(f"[ERROR] {ip} 抓取失败: {e}")

# === 6. 保存 CSV ===
df_result = pd.DataFrame(all_data)
df_result.to_csv("taobao_anime_results.csv", index=False, encoding="utf-8-sig")

driver.quit()
print("\n抓取完成，已保存到 taobao_anime_results.csv")






