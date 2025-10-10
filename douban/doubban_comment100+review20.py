import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
from urllib.parse import urlparse, parse_qs, unquote
import os
import re
import random

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


def get_anime_reviews(anime_url, max_reviews=100):
    """获取动漫的影评和短评（短评分页，影评只取第一页）"""
    try:
        anime_id = re.search(r'subject/(\d+)/', anime_url).group(1)
        reviews = []

        # ===== 1. 短评爬取（带分页）=====
        print(f"正在爬取动漫ID {anime_id} 的短评...")
        short_comment_url = f"https://movie.douban.com/subject/{anime_id}/comments"
        params = {
            'start': 0,
            'limit': 20,
            'status': 'P',
            'sort': 'new_score'
        }

        while len(reviews) < max_reviews:
            print(f"正在爬取短评页: {params['start']}")

            time.sleep(random.uniform(2, 5))
            response = requests.get(
                short_comment_url,
                params=params,
                headers={
                    **headers,
                    'Host': 'movie.douban.com',
                    'Referer': f'https://movie.douban.com/subject/{anime_id}/'
                },
                timeout=15
            )

            if response.status_code != 200:
                print(f"短评请求失败，状态码：{response.status_code}")
                break

            soup = BeautifulSoup(response.text, 'html.parser')
            comments = soup.select('#comments .comment-item')

            if not comments:
                print("没有找到更多短评")
                break

            for comment in comments:
                content = comment.select_one('.comment-content > span.short')
                if not content:
                    continue

                rating = '无评分'
                rating_tag = comment.select_one('span[class^=allstar]')
                if rating_tag:
                    rating = rating_tag['class'][0].replace('allstar', '')

                reviews.append({
                    '类型': '短评',
                    '内容': content.get_text(strip=True),
                    '评分': rating,
                    '来源': response.url
                })

                if len(reviews) >= max_reviews:
                    break

            # 检查下一页
            next_page = soup.select_one('#paginator a.next')
            if not next_page:
                break

            params['start'] += 20

        # ===== 2. 影评爬取（只爬取第一页）=====
        print(f"正在爬取动漫ID {anime_id} 的影评...")
        review_url = f"https://movie.douban.com/subject/{anime_id}/reviews"
        time.sleep(2)
        response = requests.get(review_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 提取影评 - 更健壮的选择器
        review_items = soup.select('.review-list .review')
        if not review_items:
            review_items = soup.select('.review-item')

        for i, item in enumerate(review_items[:max_reviews // 2]):
            title_elem = item.select_one('.title a') or item.select_one('h2 a')
            title = title_elem.get_text(strip=True) if title_elem else "无标题"

            content_elem = item.select_one('.short-content') or item.select_one('.review-short')
            content = content_elem.get_text(strip=True) if content_elem else "无内容"

            rating_tag = item.find('span', class_=re.compile(r'main-title-rating|rating'))
            rating = rating_tag['class'][0].replace('main-title-rating', '').replace('rating',
                                                                                     '') if rating_tag else '无评分'

            reviews.append({
                '类型': '影评',
                '标题': title,
                '内容': content,
                '评分': rating,
                '来源': review_url
            })

        return reviews

    except Exception as e:
        print(f"获取影评/短评时发生错误: {str(e)}")
        return []


if __name__ == '__main__':
    # 从CSV文件加载动漫名称列表
    keywords = load_keywords_from_csv()
    if not keywords:
        print("未读取到有效的动漫名称，请检查anime_list.csv文件")
        exit()

    all_reviews = []
    for keyword in keywords:
        print(f"\n===== 处理动漫：{keyword} =====")
        detail_url = get_anime_detail_url(keyword)
        if not detail_url:
            continue

        reviews = get_anime_reviews(detail_url)
        if reviews:
            for review in reviews:
                review['动漫名称'] = keyword
                review['动漫链接'] = detail_url
            all_reviews.extend(reviews)
            print(f"成功获取{len(reviews)}条评论")

    if all_reviews:
        df = pd.DataFrame(all_reviews)
        # 重新排列列顺序
        columns = ['动漫名称', '动漫链接', '类型', '标题', '内容', '评分', '来源']
        df = df.reindex(columns=[col for col in columns if col in df.columns])

        print("\n===== 提取结果 =====")
        print(df.head())
        df.to_csv('重爬douban_comment_anime.csv', index=False, encoding='utf-8-sig')
        print(f"\n已保存 {len(all_reviews)} 条评论到 '豆瓣动漫评论汇总.csv'")
    else:
        print("\n未提取到任何有效评论")