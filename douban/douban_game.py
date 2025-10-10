import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
from urllib.parse import urlparse, parse_qs, unquote
import csv

# 初始化请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
    'Referer': 'https://www.douban.com/'
}

base_url = "https://www.douban.com"


def read_keywords_from_csv(file_path):
    """从CSV文件中读取关键词列表"""
    keywords = []
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader, None)  # 跳过标题行
        for row in reader:
            if row:  # 确保行不为空
                keywords.append(row[0].strip())  # 假设关键词在第一列
    return keywords


def get_real_url(link):
    """从豆瓣搜索页面的跳转链接中提取真实的关键词详情页URL"""
    if "link2/?url=" in link:
        parsed = urlparse(link)
        query_params = parse_qs(parsed.query)
        if 'url' in query_params:
            real_url = unquote(query_params['url'][0])
            return real_url
    return link


def search_collaboration_games(keyword):
    """搜索关键词是否有联动游戏"""
    try:
        # 构造搜索URL
        search_url = f"https://www.douban.com/search?q={keyword}+联动游戏+OR+联动手游"
        time.sleep(1)
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 检查结果中是否包含游戏相关的关键词
        results = soup.get_text().lower()
        game_keywords = ['游戏', '手游', 'ps4', 'ps5', 'switch', 'steam', 'pc', 'mobile game', 'collaboration']

        # 如果有多个游戏关键词匹配，则认为有联动游戏
        matches = sum(1 for keyword in game_keywords if keyword in results)

        return "是" if matches >= 2 else "否"

    except Exception as e:
        print(f"搜索 {keyword} 时出错: {e}")
        return "查询失败"


def get_game_detail_url(keyword):
    """根据关键词获取关键词详情页链接"""
    try:
        # 1. 构造全站搜索URL
        search_url = f"https://www.douban.com/search?source=suggest&q={keyword}"
        time.sleep(1)
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 2. 找到"关键词"分类链接
        game_a_tag = soup.find("a", string="关键词")
        if not game_a_tag:
            game_a_tag = soup.find("a", href=lambda href: href and "cat=3114" in href)

        if not game_a_tag:
            print(f"关键词「{keyword}」未找到关键词分类链接")
            return None

        # 3. 构建关键词分类页面完整链接
        relative_link = game_a_tag.get("href")
        full_game_link = f"{base_url}{relative_link}" if relative_link.startswith('/') else relative_link
        time.sleep(1)
        game_page = requests.get(full_game_link, headers=headers, timeout=10)
        game_page.raise_for_status()
        game_soup = BeautifulSoup(game_page.content, 'html.parser')

        # 4. 提取目标详情页链接并解析真实URL
        selectors = [
            ".subject-list .subject-item h2 a",
            ".search-result .result h3 a",
            ".content h3 a",
            ".title a"
        ]

        target_link = None
        for selector in selectors:
            target_tag = game_soup.select_one(selector)
            if target_tag and target_tag.get("href"):
                target_link = target_tag.get("href").strip()
                break

        if target_link:
            real_detail_url = get_real_url(target_link)
            print(f"关键词「{keyword}」提取到真实详情页链接：{real_detail_url}")
            return real_detail_url
        else:
            print(f"关键词「{keyword}」未找到目标链接")
            return None

    except Exception as e:
        print(f"关键词「{keyword}」链接提取失败：{str(e)}")
        return None


def create_empty_info_dict(keyword):
    """创建一个包含所有字段的空信息字典"""
    return {
        '动漫名称': keyword,
        '关键词名': '未找到',
        '类型': '无',
        '平台': '无',
        '别名': '无',
        '发行日期': '无',
        '豆瓣评分': '无',
        '评分人数': '无',
        '短评数量': '无',
        '文字数': '无',
        '攻略数量': '无',
        '是否有联动游戏': '无'  # 这里改为"无"而不是"否"
    }


def get_game_info(game_url, keyword):
    """提取单个关键词页面的详细信息"""
    try:
        response = requests.get(game_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        info_dict = {'动漫名称': keyword}
        # 1. 提取关键词名
        game_name_tag = soup.find('h1')
        info_dict['关键词名'] = game_name_tag.get_text(strip=True) if game_name_tag else '未知关键词名'

        # 2. 提取基本信息（类型、平台等）
        dl_tag = soup.find('dl', class_='thing-attr')
        if dl_tag:
            for dt in dl_tag.find_all('dt'):
                key = dt.get_text(strip=True).strip(':')
                dd = dt.find_next_sibling('dd')
                info_dict[key] = dd.get_text(strip=True) if dd else '无'
        else:
            info_dict['类型'] = '无'
            info_dict['平台'] = '无'
            info_dict['别名'] = '无'
            info_dict['发行日期'] = '无'

        # 3. 提取豆瓣评分和评分人数
        rating_div = soup.find('div', class_='rating_self')
        if rating_div:
            rating_num = rating_div.find('strong', class_='rating_num')
            info_dict['豆瓣评分'] = rating_num.get_text(strip=True) if rating_num else '暂无评分'
            votes = rating_div.find('span', property='v:votes')
            info_dict['评分人数'] = votes.get_text(strip=True) if votes else '0人评价'
        else:
            info_dict['豆瓣评分'] = '暂无评分'
            info_dict['评分人数'] = '0人评价'

        # 4. 提取短评数量
        short_comment_tag = soup.find('div', id='comments')
        if short_comment_tag:
            comment_h2 = short_comment_tag.find('h2')
            if comment_h2:
                comment_link = comment_h2.find('a')
                info_dict['短评数量'] = comment_link.get_text(strip=True).split()[1] if comment_link else '0'
            else:
                info_dict['短评数量'] = '0'
        else:
            info_dict['短评数量'] = '0'

        # 5. 提取文字（长评）数量
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

        # 6. 提取攻略数量
        strategy_section = soup.find('section', class_='reviews mod game-content')
        if strategy_section:
            h2_tag = strategy_section.find('h2')
            if h2_tag and '攻略' in h2_tag.get_text():
                span_tag = h2_tag.find('span', class_='pl')
                if span_tag:
                    a_tag = span_tag.find('a')
                    if a_tag:
                        text = a_tag.get_text(strip=True)
                        strategy_count = text.split()[1] if len(text.split()) >= 2 else '0'
                        info_dict['攻略数量'] = strategy_count
                    else:
                        info_dict['攻略数量'] = '0'
                else:
                    info_dict['攻略数量'] = '0'
        else:
            info_dict['攻略数量'] = '0'

        # 新增：检查是否有联动游戏
        info_dict['是否有联动游戏'] = search_collaboration_games(keyword)

        return info_dict

    except Exception as e:
        print(f"提取信息出错: {str(e)}")
        return None


if __name__ == '__main__':
    # 从CSV文件读取关键词列表
    keywords = read_keywords_from_csv('anime_list.csv')

    all_game_info = []
    for keyword in keywords:
        print(f"\n===== 处理动漫：{keyword} =====")
        detail_url = get_game_detail_url(keyword)

        if detail_url:
            game_info = get_game_info(detail_url, keyword)
            if game_info:
                all_game_info.append(game_info)
        else:
            # 如果没有找到详情页，创建空记录
            empty_info = create_empty_info_dict(keyword)
            all_game_info.append(empty_info)

    if all_game_info:
        df = pd.DataFrame(all_game_info)
        # 调整列顺序，将动漫名称放在第一列
        columns = ['动漫名称', '关键词名', '类型', '平台', '别名', '发行日期',
                   '豆瓣评分', '评分人数', '短评数量', '文字数', '攻略数量', '是否有联动游戏']
        df = df.reindex(columns=columns)

        print("\n===== 提取结果 =====")
        print(df)
        df.to_csv('重爬.csv', index=False, encoding='utf-8-sig')
        print("\n已保存为 '动漫联动游戏信息汇总.csv'")
    else:
        print("\n未提取到任何有效信息")