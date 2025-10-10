"""
豆瓣动漫信息爬取工具

功能：
    从anime_list.csv读取动漫名称列表，自动爬取豆瓣网站上对应的动漫详情信息（包括名称、类型、平台、评分等），
    并将结果汇总保存为CSV文件。

依赖库：
    - requests：用于发送HTTP请求
    - pandas：用于数据处理和CSV保存
    - beautifulsoup4：用于解析HTML页面
    - time、urllib.parse：辅助功能（如请求延迟、URL解析）
    安装命令：pip install requests pandas beautifulsoup4

使用方法：
    1. 在当前目录下创建anime_list.csv文件，包含一列动漫名称
    2. 运行脚本，程序会自动读取文件中的动漫名称，爬取信息并生成CSV文件
    3. 结果保存在当前目录下的"豆瓣关键词信息汇总.csv"

注意事项：
    - anime_list.csv文件应包含标题行"动漫名称"或"name"
    - 为避免触发豆瓣反爬机制，脚本已添加time.sleep(1)控制请求频率，请勿随意删除
    - 若爬取失败（如网络问题、页面结构变化），程序会打印错误信息，可尝试重新运行
    - 豆瓣页面结构可能更新，若某些字段提取失败，需检查对应HTML选择器是否需要调整
"""
import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
from urllib.parse import urlparse, parse_qs, unquote
import os

# 初始化请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
    'Referer': 'https://www.douban.com/'
}

base_url = "https://www.douban.com"


def load_keywords_from_csv():
    """从anime_list.csv文件中加载动漫名称列表"""
    try:
        if not os.path.exists('anime_list.csv'):
            raise FileNotFoundError("anime_list.csv文件不存在")

        df = pd.read_csv('anime_list.csv')

        # 检查可能的列名
        possible_columns = ['动漫名称', '动漫名', 'name', 'title', '关键词']
        for col in possible_columns:
            if col in df.columns:
                keywords = df[col].dropna().unique().tolist()
                print(f"从anime_list.csv中读取到{len(keywords)}个动漫名称")
                return keywords

        # 如果没有匹配的列名，尝试使用第一列
        first_column = df.columns[0]
        keywords = df[first_column].dropna().unique().tolist()
        print(f"使用第一列'{first_column}'作为动漫名称，共读取到{len(keywords)}个名称")
        return keywords

    except Exception as e:
        print(f"读取anime_list.csv文件失败: {str(e)}")
        return []


def get_real_url(link):
    """从豆瓣搜索页面的跳转链接中提取真实的动漫详情页URL"""
    if "link2/?url=" in link:
        parsed = urlparse(link)
        query_params = parse_qs(parsed.query)
        if 'url' in query_params:
            real_url = unquote(query_params['url'][0])
            return real_url
    return link


def get_anime_detail_url(keyword):
    """根据动漫名称获取动漫详情页链接"""
    try:
        search_url = f"https://www.douban.com/search?source=suggest&q={keyword}"
        time.sleep(1)
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        anime_a_tag = soup.find("a", string="动漫")
        if not anime_a_tag:
            anime_a_tag = soup.find("a", href=lambda href: href and "cat=1002" in href)

        if not anime_a_tag:
            print(f"动漫「{keyword}」未找到动漫分类链接")
            return None

        relative_link = anime_a_tag.get("href")
        full_anime_link = f"{base_url}{relative_link}" if relative_link.startswith('/') else relative_link
        time.sleep(1)
        anime_page = requests.get(full_anime_link, headers=headers, timeout=10)
        anime_page.raise_for_status()
        anime_soup = BeautifulSoup(anime_page.content, 'html.parser')

        selectors = [
            ".subject-list .subject-item h2 a",
            ".search-result .result h3 a",
            ".content h3 a",
            ".title a"
        ]

        target_link = None
        for selector in selectors:
            target_tag = anime_soup.select_one(selector)
            if target_tag and target_tag.get("href"):
                target_link = target_tag.get("href").strip()
                break

        if target_link:
            real_detail_url = get_real_url(target_link)
            print(f"动漫「{keyword}」提取到真实详情页链接：{real_detail_url}")
            return real_detail_url
        else:
            print(f"动漫「{keyword}」未找到目标链接")
            return None

    except Exception as e:
        print(f"动漫「{keyword}」链接提取失败：{str(e)}")
        return None


def get_anime_info(anime_url):
    """提取单个动漫页面的详细信息"""
    try:
        response = requests.get(anime_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        info_dict = {}

        # 动漫名
        anime_name_tag = soup.find('h1')
        info_dict['动漫名'] = anime_name_tag.get_text(strip=True) if anime_name_tag else '未知动漫名'

        # 豆瓣评分
        rating_div = soup.find('div', class_='rating_self')
        if rating_div:
            rating_num = rating_div.find('strong', class_='rating_num')
            info_dict['豆瓣评分'] = rating_num.get_text(strip=True) if rating_num else '暂无评分'
            votes = rating_div.find('span', property='v:votes')
            info_dict['评分人数'] = votes.get_text(strip=True) if votes else '0人评价'
        else:
            info_dict['豆瓣评分'] = '暂无评分'
            info_dict['评分人数'] = '0人评价'

        # 文字数（评论数）
        review_section = soup.find('section', id='reviews-wrapper')
        if review_section:
            review_h2 = review_section.find('h2')
            if review_h2:
                review_link = review_h2.find('a')
                info_dict['文字数'] = review_link.get_text(strip=True).split()[1] if review_link else '0'
            else:
                info_dict['文字数'] = '0'
        else:
            info_dict['文字数'] = '0'

        # 提取基本信息（导演、编剧、主演等）
        info_div = soup.find('div', id='info')
        if info_div:
            info_text = info_div.get_text('\n', strip=True)
            info_lines = info_text.split('\n')

            # 初始化所有字段
            info_dict['类型'] = ''
            info_dict['制片国家/地区'] = ''
            info_dict['语言'] = ''
            info_dict['上映日期'] = ''

            current_key = None
            for line in info_lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()

                    if key == '类型':
                        info_dict['类型'] = value
                    elif key == '制片国家/地区':
                        info_dict['制片国家/地区'] = value
                    elif key == '语言':
                        info_dict['语言'] = value
                    elif key == '上映日期':
                        info_dict['上映日期'] = value
                    current_key = key
                elif current_key:
                    # 处理多行值
                    if current_key == '类型':
                        info_dict['类型'] += ' / ' + line.strip()
                    elif current_key == '制片国家/地区':
                        info_dict['制片国家/地区'] += ' / ' + line.strip()
                    elif current_key == '语言':
                        info_dict['语言'] += ' / ' + line.strip()
                    elif current_key == '上映日期':
                        info_dict['上映日期'] += ' / ' + line.strip()

        return info_dict

    except Exception as e:
        print(f"提取信息出错: {str(e)}")
        return None


if __name__ == '__main__':
    # 从CSV文件加载动漫名称列表
    keywords = load_keywords_from_csv()
    if not keywords:
        print("未读取到有效的动漫名称，请检查anime_list.csv文件")
        exit()

    all_anime_info = []
    for keyword in keywords:
        print(f"\n===== 处理动漫：{keyword} =====")
        detail_url = get_anime_detail_url(keyword)
        if not detail_url:
            continue

        anime_info = get_anime_info(detail_url)
        if anime_info:
            all_anime_info.append(anime_info)

    if all_anime_info:
        df = pd.DataFrame(all_anime_info)
        # 指定输出字段顺序
        columns = ['动漫名', '豆瓣评分', '评分人数', '文字数','类型', '制片国家/地区', '语言', '上映日期']
        df = df.reindex(columns=columns)

        print("\n===== 提取结果 =====")
        print(df)
        df.to_csv('重爬douban_grade_anime.csv', index=False, encoding='utf-8-sig')
        print("\n已保存为 '豆瓣动漫信息汇总.csv'")
    else:
        print("\n未提取到任何有效信息")