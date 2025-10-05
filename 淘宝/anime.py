import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# === 1. 配置 Selenium ===
chrome_driver_path = r"C:/Code/python/animeproject/chromedriver-win64/chromedriver.exe" # 替换为本机 ChromeDriver 路径
options = Options()
options.add_argument("--headless")  # 无界面模式，可去掉看浏览器操作
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--lang=zh-CN")

driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)

# === 2. 读取 Excel 动漫 IP 列表 ===
file_path = "newall.xlsx"
df_anime = pd.read_excel(file_path, sheet_name="anime")
anime_list = df_anime['clean_name'].dropna().tolist()


# === 3. 定义函数抓取淘宝商品 ===
def fetch_taobao_items(keyword, max_pages=2):
    all_items = []
    for page in range(0, max_pages):
        # 每页44条商品，用s参数翻页
        s_index = page * 44
        search_url = f"https://s.taobao.com/search?q={keyword}&s={s_index}"
        driver.get(search_url)
        time.sleep(3)  # 等待页面加载

        # 商品列表
        items = driver.find_elements(By.CSS_SELECTOR, "div[data-category='auctions'] div.item")
        if not items:
            # 尝试另一种选择器
            items = driver.find_elements(By.CSS_SELECTOR, "div.item.J_MouserOnverReq")

        for item in items:
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
    return all_items


# === 4. 循环抓取所有动漫 IP ===
all_data = []
for ip in anime_list:
    print(f"正在抓取: {ip}")
    try:
        items = fetch_taobao_items(ip, max_pages=2)  # 每个动漫抓取前2页，可修改
        all_data.extend(items)
    except Exception as e:
        print(f"{ip} 抓取失败: {e}")

# === 5. 保存 CSV ===
df_result = pd.DataFrame(all_data)
df_result.to_csv("taobao_anime_results.csv", index=False, encoding="utf-8-sig")

driver.quit()
print("抓取完成，已保存到 taobao_anime_results.csv")
