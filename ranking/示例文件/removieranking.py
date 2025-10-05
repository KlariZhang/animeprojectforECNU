import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, StandardScaler
import os


# ====== 工具函数 ======
def log_standardize(df, cols, method="minmax"):
    """
    对指定列进行 log(1+X) 转换后标准化。
    Log(1+X) 转换：用于处理数据中存在的巨大差异，使其更接近正态分布。
    标准化：将数据缩放到 [0, 1]（MinMaxScaler）或均值为0、方差为1（StandardScaler），
           使得不同量纲的指标可以进行比较和加权。
    """
    df = df.copy()

    # 避免对非数值列进行操作
    numerical_cols = [col for col in cols if df[col].dtype in ['int64', 'float64']]

    # log(1+X) 转换
    df[numerical_cols] = np.log1p(df[numerical_cols])

    if method == "minmax":
        # MinMaxScaler 将数据缩放到 [0, 1]
        scaler = MinMaxScaler()
    else:
        # StandardScaler 将数据缩放到均值为0，方差为1
        scaler = StandardScaler()

    df[numerical_cols] = scaler.fit_transform(df[numerical_cols])
    return df


def avg_columns(df, cols, new_name):
    """
    对多列数据取平均，生成一个新的列。
    """
    df[new_name] = df[cols].mean(axis=1)
    return df[[df.columns[0], new_name]]


# ====== 数据读取函数 ======
# 这部分函数用于从不同来源读取原始数据
def read_bilibili(filepath="movie_data_structures/bilibili.xlsx"):
    dataall = pd.read_excel(filepath, sheet_name="dataall")
    creations = pd.read_excel(filepath, sheet_name="creations")
    comments = pd.read_excel(filepath, sheet_name="comments")

    plays = dataall[['movie', 'play_count_plays']].copy()
    followers = dataall[['movie', 'followers_followers']].copy()
    interactions = dataall[
        ['movie', 'likes_interactions', 'coins_interactions', 'favorites_interactions', 'shares_interactions',
         'comments_interactions', 'danmu_interactions']].copy()
    ratings = dataall[['movie', 'score_ratings']].copy()

    return plays, followers, interactions, creations, comments, ratings


def read_douban(filepath="movie_data_structures/douban.xlsx"):
    ratings = pd.read_excel(filepath, sheet_name="ratings")
    comments = pd.read_excel(filepath, sheet_name="comments")
    return ratings, comments


def read_imdb(filepath="movie_data_structures/imdb.xlsx"):
    ratings = pd.read_excel(filepath, sheet_name="ratings")
    rank = pd.read_excel(filepath, sheet_name="rank")
    return ratings, rank


# 修改 read_tencent 函数，确保列名正确
def read_tencent(filepath="movie_data_structures/tencent.xlsx"):
    df = pd.read_excel(filepath, sheet_name="plays")
    # 假设电影名称列为 '电影名称'，播放量列为 'play_count_plays'
    # 如果实际名称不同，请在这里修改
    df.rename(columns={"电影名称": "movie", "play_count_plays": "tencent_plays"}, inplace=True)
    return df


# 修改 read_youku 函数，确保列名正确
def read_youku(filepath="movie_data_structures/youku.xlsx"):
    df = pd.read_excel(filepath, sheet_name="plays")
    # 假设电影名称列为 '电影名称'，播放量列为 'play_count_plays'
    # 如果实际名称不同，请在这里修改
    df.rename(columns={"电影名称": "movie", "play_count_plays": "youku_plays"}, inplace=True)
    return df


# 修改 read_guduo 函数，确保列名正确
def read_guduo(filepath="movie_data_structures/guduo.xlsx"):
    df = pd.read_excel(filepath, sheet_name="plays")
    # 假设电影名称列为 '电影名称'，播放量列为 'play_count_plays'
    # 如果实际名称不同，请在这里修改
    df.rename(columns={"电影名称": "movie", "play_count_plays": "guduo_plays"}, inplace=True)
    return df


def read_boxoffice(filepath="movie_data_structures/boxoffice.xlsx"):
    return pd.read_excel(filepath, sheet_name="box_office")


def read_douyin(filepath="movie_data_structures/douyin.xlsx"):
    return pd.read_excel(filepath, sheet_name="creations")


def read_weibo(filepath="movie_data_structures/weibo.xlsx"):
    return pd.read_excel(filepath, sheet_name="discussions")


def read_tieba(filepath="movie_data_structures/tieba.xlsx"):
    return pd.read_excel(filepath, sheet_name="stats")


def read_baidu(filepath="movie_data_structures/baidu_index.xlsx"):
    return pd.read_excel(filepath, sheet_name="index")


def read_taobao_xianyu(filepath="movie_data_structures/taobao_xianyu.xlsx"):
    return pd.read_excel(filepath, sheet_name="sales")


def read_industry(filepath="movie_data_structures/industry.xlsx"):
    games = pd.read_excel(filepath, sheet_name="games")
    shows = pd.read_excel(filepath, sheet_name="shows")
    original_works = pd.read_excel(filepath, sheet_name="original_works")
    patents = pd.read_excel(filepath, sheet_name="patents")
    return games, shows, original_works, patents


def read_risk(filepath="movie_data_structures/risk.xlsx"):
    return pd.read_excel(filepath, sheet_name="risk")


# ====== 主流程函数：计算综合指数 ======
def calculate_index():
    # ---- 1. 计算内容价值指数 (Content Value Index) ----
    # 该指数反映电影本身的质量和市场表现，数据来自播放量、追番人数、票房和口碑。

    # 读取所有相关数据
    bilibili_plays, bilibili_followers, _, _, _, bilibili_ratings = read_bilibili()
    douban_ratings, _ = read_douban()
    imdb_ratings, _ = read_imdb()
    tencent = read_tencent()
    youku = read_youku()
    guduo = read_guduo()
    box_office = read_boxoffice()

    # 播放表现：整合多平台播放量（腾讯/B站/优酷/骨朵）
    plays_all = bilibili_plays.merge(tencent, on="movie").merge(youku, on="movie").merge(guduo, on="movie")
    plays_all = log_standardize(plays_all, plays_all.columns[1:])
    plays_all = avg_columns(plays_all, plays_all.columns[1:], "play_index")

    # 追番人数/播放比（B站）
    followers = bilibili_followers.copy()
    followers["ratio"] = followers["followers_followers"] / (bilibili_plays["play_count_plays"] + 1)
    followers = log_standardize(followers, ["ratio"])
    followers.rename(columns={"ratio": "follow_index"}, inplace=True)

    # 票房表现
    box_office = log_standardize(box_office, ["box_office"])
    box_office.rename(columns={"box_office": "box_office_index"}, inplace=True)

    # 口碑得分：整合多平台评分（豆瓣/IMDb/B站）
    rating_merge = douban_ratings.merge(bilibili_ratings, on="movie").merge(imdb_ratings, on="movie")
    rating_merge = log_standardize(rating_merge, ["score_x", "score_ratings", "score_y"])
    rating_merge = avg_columns(rating_merge, ["score_x", "score_ratings", "score_y"], "rating_index")

    # 内容价值综合指数：整合播放、追番、票房、口碑
    content_value = plays_all.merge(followers[["movie", "follow_index"]], on="movie") \
        .merge(box_office, on="movie") \
        .merge(rating_merge, on="movie")
    content_value["content_value"] = content_value.drop(columns=["movie"]).mean(axis=1)

    # ---- 2. 计算讨论热度指数 (Discussion Engagement Index) ----
    # 该指数反映电影在社交媒体和UGC平台的讨论热度。

    # 读取相关数据
    _, _, bilibili_interactions, bilibili_creations, _, _ = read_bilibili()
    _, douban_comments = read_douban()

    # 检查其他文件是否也需要重命名 'movie' 列
    douyin = pd.read_excel("movie_data_structures/douyin.xlsx", sheet_name="creations")
    weibo = pd.read_excel("movie_data_structures/weibo.xlsx", sheet_name="discussions")
    tieba = pd.read_excel("movie_data_structures/tieba.xlsx", sheet_name="stats")

    # B站互动数据：点赞、投币、收藏、分享、评论、弹幕
    bilibili_interactions = log_standardize(bilibili_interactions, bilibili_interactions.columns[1:])
    bilibili_interactions = avg_columns(bilibili_interactions, bilibili_interactions.columns[1:], "interaction_index")

    # 豆瓣评论数量
    douban_comments = log_standardize(douban_comments, ["comment_count"])
    douban_comments.rename(columns={"comment_count": "douban_comment_index"}, inplace=True)

    # B站二创数据：播放、点赞、收藏、分享
    bilibili_creations = log_standardize(bilibili_creations, bilibili_creations.columns[1:])
    bilibili_creations = avg_columns(bilibili_creations, bilibili_creations.columns[1:], "creation_index")

    # 抖音二创数据：点赞、评论、分享
    douyin = log_standardize(douyin, ["likes", "comments", "shares"])
    douyin = avg_columns(douyin, ["likes", "comments", "shares"], "douyin_index")

    # 微博讨论/二创
    weibo = log_standardize(weibo, ["posts"])
    weibo.rename(columns={"posts": "weibo_index"}, inplace=True)

    # 贴吧数据：帖子数、关注数
    tieba = log_standardize(tieba, ["posts", "followers"])
    tieba = avg_columns(tieba, ["posts", "followers"], "tieba_index")

    # 讨论热度综合指数：整合所有平台的热度指标
    discussion = bilibili_interactions.merge(douban_comments, on="movie") \
        .merge(bilibili_creations, on="movie") \
        .merge(douyin, on="movie") \
        .merge(weibo, on="movie") \
        .merge(tieba, on="movie")
    discussion["discussion_value"] = discussion.drop(columns=["movie"]).mean(axis=1)

    # ---- 3. 计算社会影响力指数 (Social Influence Index) ----
    # 该指数反映电影在更广阔的社会和文化层面的影响。

    # 读取相关数据
    baidu_index = log_standardize(read_baidu(), ["baidu_index"])
    baidu_index.rename(columns={"baidu_index": "baidu_index_norm"}, inplace=True)

    rating_votes = douban_ratings.merge(imdb_ratings, on="movie", suffixes=("_douban", "_imdb"))
    rating_votes = log_standardize(rating_votes, ["votes_douban", "votes_imdb"])
    rating_votes = avg_columns(rating_votes, ["votes_douban", "votes_imdb"], "votes_index")

    _, imdb_rank = read_imdb()
    imdb_rank = log_standardize(imdb_rank, ["rank"])
    imdb_rank.rename(columns={"rank": "rank_index"}, inplace=True)

    # 社会影响力综合指数：整合百度热度、评分人数、IMDb排名
    influence = baidu_index.merge(rating_votes, on="movie").merge(imdb_rank, on="movie")
    influence["influence_value"] = influence.drop(columns=["movie"]).mean(axis=1)

    # ---- 4. 计算产业价值指数 (Industry Value Index) ----
    # 该指数反映电影的商业拓展和衍生品价值。

    # 读取相关数据
    sales = log_standardize(read_taobao_xianyu(), ["taobao", "xianyu"])
    sales = avg_columns(sales, ["taobao", "xianyu"], "sales_index")

    games, shows, original_works, patents = read_industry()
    industry_all = games.merge(shows, on="movie").merge(original_works, on="movie").merge(patents, on="movie")
    industry_all = log_standardize(industry_all, industry_all.columns[1:])
    industry_all = avg_columns(industry_all, industry_all.columns[1:], "industry_index")

    # 产业价值综合指数：整合衍生品销量和行业扩展数据
    industry_value = sales.merge(industry_all, on="movie")
    industry_value["industry_value"] = industry_value[["sales_index", "industry_index"]].mean(axis=1)

    # ---- 5. 合并并计算总分 ----
    # 电影综合指数：整合内容价值、讨论热度、社会影响力和产业价值
    result = content_value[["movie", "content_value"]] \
        .merge(discussion[["movie", "discussion_value"]], on="movie") \
        .merge(influence[["movie", "influence_value"]], on="movie") \
        .merge(industry_value[["movie", "industry_value"]], on="movie")

    result["total_score"] = result[["content_value", "discussion_value", "influence_value", "industry_value"]].mean(
        axis=1)

    # ---- 6. 风险预警调整 ----
    # 根据风险指标（豆瓣评分、负面评论比例）对总分进行惩罚性调整。
    risk = read_risk()
    result = result.merge(risk, on="movie", how="left")
    for i, row in result.iterrows():
        if row["douban_score"] <= 6.0 or row["negative_ratio"] >= 0.3:
            result.loc[i, "total_score"] *= 0.8
    return result


if __name__ == "__main__":
    # 执行主流程
    final_scores = calculate_index()
    print("最终计算结果：\n", final_scores)

    # 将结果保存到CSV文件
    final_scores.to_csv("movie_index_results.csv", index=False)
    print("\n结果已保存至 movie_index_results.csv")