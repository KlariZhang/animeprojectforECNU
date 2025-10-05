import pandas as pd
import os

# 创建文件夹
folder_name = "movie_data_structures"
if not os.path.exists(folder_name):
    os.makedirs(folder_name)
    print(f"文件夹 '{folder_name}' 已创建。")
else:
    print(f"文件夹 '{folder_name}' 已存在。")

# 示例数据
movies = ['电影 A', '电影 B', '电影 C']

# --- bilibili.xlsx ---
with pd.ExcelWriter(os.path.join(folder_name, 'bilibili.xlsx')) as writer:
    dataall = pd.DataFrame({
        'movie': movies,
        'play_count_plays': [12000000, 8500000, 500000],
        'followers_followers': [350000, 210000, 15000],
        'likes_interactions': [150000, 98000, 5000],
        'coins_interactions': [80000, 55000, 3000],
        'favorites_interactions': [75000, 48000, 2800],
        'shares_interactions': [25000, 18000, 1500],
        'comments_interactions': [50000, 32000, 2000],
        'danmu_interactions': [200000, 150000, 8000],
        'score_ratings': [9.5, 8.8, 7.2]
    })
    dataall.to_excel(writer, sheet_name='dataall', index=False)

    creations = pd.DataFrame({
        'movie': movies,
        'play_count': [500000, 300000, 10000],
        'likes': [25000, 15000, 500],
        'favorites': [18000, 10000, 300],
        'shares': [8000, 6000, 200]
    })
    creations.to_excel(writer, sheet_name='creations', index=False)

    comments = pd.DataFrame({
        'movie': movies,
        'comment_count': [50000, 32000, 2000]
    })
    comments.to_excel(writer, sheet_name='comments', index=False)
print("bilibili.xlsx 创建成功。")

# --- douban.xlsx ---
with pd.ExcelWriter(os.path.join(folder_name, 'douban.xlsx')) as writer:
    ratings = pd.DataFrame({
        'movie': movies,
        'score_x': [8.5, 7.9, 5.8],
        'votes_douban': [800000, 450000, 80000]
    })
    ratings.to_excel(writer, sheet_name='ratings', index=False)
    comments = pd.DataFrame({
        'movie': movies,
        'comment_count': [120000, 75000, 15000]
    })
    comments.to_excel(writer, sheet_name='comments', index=False)
print("douban.xlsx 创建成功。")

# --- imdb.xlsx ---
with pd.ExcelWriter(os.path.join(folder_name, 'imdb.xlsx')) as writer:
    ratings = pd.DataFrame({
        'movie': movies,
        'score_y': [8.1, 7.5, 6.2],
        'votes_imdb': [1500000, 900000, 120000]
    })
    ratings.to_excel(writer, sheet_name='ratings', index=False)
    rank = pd.DataFrame({
        'movie': movies,
        'rank': [150, 400, 950]
    })
    rank.to_excel(writer, sheet_name='rank', index=False)
print("imdb.xlsx 创建成功。")

# --- tencent.xlsx, youku.xlsx, guduo.xlsx ---
for file in ['tencent.xlsx', 'youku.xlsx', 'guduo.xlsx']:
    df = pd.DataFrame({
        '电影名称': movies,
        'play_count_plays': [800000000, 550000000, 12000000]
    })
    df.to_excel(os.path.join(folder_name, file), sheet_name='plays', index=False)
    print(f"{file} 创建成功。")

# --- 其他文件 ---
boxoffice = pd.DataFrame({
    'movie': movies,
    'box_office': [1500000000, 980000000, 15000000]
})
boxoffice.to_excel(os.path.join(folder_name, 'boxoffice.xlsx'), sheet_name='box_office', index=False)
print("boxoffice.xlsx 创建成功。")

douyin = pd.DataFrame({
    'movie': movies,
    'likes': [5000000, 3200000, 80000],
    'comments': [120000, 80000, 3000],
    'shares': [200000, 150000, 5000]
})
douyin.to_excel(os.path.join(folder_name, 'douyin.xlsx'), sheet_name='creations', index=False)
print("douyin.xlsx 创建成功。")

weibo = pd.DataFrame({
    'movie': movies,
    'posts': [500000, 350000, 15000]
})
weibo.to_excel(os.path.join(folder_name, 'weibo.xlsx'), sheet_name='discussions', index=False)
print("weibo.xlsx 创建成功。")

tieba = pd.DataFrame({
    'movie': movies,
    'posts': [8000, 4500, 200],
    'followers': [50000, 28000, 500]
})
tieba.to_excel(os.path.join(folder_name, 'tieba.xlsx'), sheet_name='stats', index=False)
print("tieba.xlsx 创建成功。")

baidu_index = pd.DataFrame({
    'movie': movies,
    'baidu_index': [30000, 18000, 500]
})
baidu_index.to_excel(os.path.join(folder_name, 'baidu_index.xlsx'), sheet_name='index', index=False)
print("baidu_index.xlsx 创建成功。")

taobao_xianyu = pd.DataFrame({
    'movie': movies,
    'taobao': [5000, 2500, 150],
    'xianyu': [800, 400, 20]
})
taobao_xianyu.to_excel(os.path.join(folder_name, 'taobao_xianyu.xlsx'), sheet_name='sales', index=False)
print("taobao_xianyu.xlsx 创建成功。")

# --- industry.xlsx ---
with pd.ExcelWriter(os.path.join(folder_name, 'industry.xlsx')) as writer:
    games = pd.DataFrame({'movie': movies, 'game_count': [5, 3, 1]})
    games.to_excel(writer, sheet_name='games', index=False)

    shows = pd.DataFrame({'movie': movies, 'show_count': [10, 8, 2]})
    shows.to_excel(writer, sheet_name='shows', index=False)

    original_works = pd.DataFrame({'movie': movies, 'work_count': [15, 10, 3]})
    original_works.to_excel(writer, sheet_name='original_works', index=False)

    patents = pd.DataFrame({'movie': movies, 'patent_count': [2, 1, 0]})
    patents.to_excel(writer, sheet_name='patents', index=False)
print("industry.xlsx 创建成功。")

# --- risk.xlsx ---
risk = pd.DataFrame({
    'movie': movies,
    'douban_score': [8.5, 7.9, 5.8],
    'negative_ratio': [0.1, 0.2, 0.35]
})
risk.to_excel(os.path.join(folder_name, 'risk.xlsx'), sheet_name='risk', index=False)
print("risk.xlsx 创建成功。")

print("\n所有文件已生成，请在 'movie_data_structures' 文件夹中查看。")