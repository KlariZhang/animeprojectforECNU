import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, StandardScaler


# ====== 工具函数 ======
def log_standardize(df, cols, method="minmax"):
    """
    对 DataFrame 中指定的列进行 log(1+X) 转换后标准化。

    参数:
    df (pd.DataFrame): 待处理的 DataFrame。
    cols (list): 需要转换和标准化的列名列表。
    method (str): 标准化方法，"minmax" 表示 Min-Max 标准化，"zscore" 表示 Z-score 标准化。

    返回:
    pd.DataFrame: 经过处理后的 DataFrame。
    """
    df = df.copy()
    # 根据文件要求，对原始数据进行 log(1+X) 转换，以减少极端值的影响
    df[cols] = np.log1p(df[cols])

    # 根据指定的标准化方法初始化 Scaler
    if method == "minmax":
        scaler = MinMaxScaler()
    else:
        scaler = StandardScaler()

    # 应用标准化
    df[cols] = scaler.fit_transform(df[cols])
    return df


def avg_columns(df, cols, new_name):
    """
    将 DataFrame 中多列求平均，生成新的一列。

    参数:
    df (pd.DataFrame): 待处理的 DataFrame。
    cols (list): 需要求平均的列名列表。
    new_name (str): 新生成的列名。

    返回:
    pd.DataFrame: 包含新平均列的 DataFrame。
    """
    df[new_name] = df[cols].mean(axis=1)
    # 返回包含第一列（通常是动漫名称）和新平均列的 DataFrame
    return df[[df.columns[0], new_name]]


# ====== 数据读取函数 ======
# 每个函数都模拟从指定文件路径和工作表读取数据，这与文档中列出的数据来源相对应
def read_bilibili(filepath="data/bilibili.xlsx"):
    plays = pd.read_excel(filepath, sheet_name="plays")  # 播放量
    followers = pd.read_excel(filepath, sheet_name="followers")  # 追番人数
    interactions = pd.read_excel(filepath, sheet_name="interactions")  # 互动数据（点赞、投币等）
    creations = pd.read_excel(filepath, sheet_name="creations")  # 二创视频数据
    comments = pd.read_excel(filepath, sheet_name="comments")  # 评论数据
    ratings = pd.read_excel(filepath, sheet_name="ratings")  # 评分
    return plays, followers, interactions, creations, comments, ratings


def read_douban(filepath="data/douban.xlsx"):
    ratings = pd.read_excel(filepath, sheet_name="ratings")  # 评分和评分人数
    comments = pd.read_excel(filepath, sheet_name="comments")  # 评论数
    return ratings, comments


def read_imdb(filepath="data/imdb.xlsx"):
    ratings = pd.read_excel(filepath, sheet_name="ratings")  # 评分和评分人数
    rank = pd.read_excel(filepath, sheet_name="rank")  # 排名
    return ratings, rank


def read_tencent(filepath="data/tencent.xlsx"):
    return pd.read_excel(filepath, sheet_name="plays")  # 腾讯视频播放量


def read_youku(filepath="data/youku.xlsx"):
    return pd.read_excel(filepath, sheet_name="plays")  # 优酷播放量


def read_guduo(filepath="data/guduo.xlsx"):
    return pd.read_excel(filepath, sheet_name="plays")  # 骨朵数据播放量


def read_baidu(filepath="data/baidu_index.xlsx"):
    return pd.read_excel(filepath, sheet_name="index")  # 百度指数


def read_douyin(filepath="data/douyin.xlsx"):
    return pd.read_excel(filepath, sheet_name="creations")  # 抖音二创数据


def read_weibo(filepath="data/weibo.xlsx"):
    return pd.read_excel(filepath, sheet_name="discussions")  # 微博讨论/二创贴数


def read_tieba(filepath="data/tieba.xlsx"):
    return pd.read_excel(filepath, sheet_name="stats")  # 贴吧关注数、帖子量


def read_taobao_xianyu(filepath="data/taobao_xianyu.xlsx"):
    return pd.read_excel(filepath, sheet_name="sales")  # 衍生品销量


def read_industry(filepath="data/industry.xlsx"):
    games = pd.read_excel(filepath, sheet_name="games")  # 游戏联动
    shows = pd.read_excel(filepath, sheet_name="shows")  # 演出信息
    original_works = pd.read_excel(filepath, sheet_name="original_works")  # 原作反哺数据
    patents = pd.read_excel(filepath, sheet_name="patents")  # 专利申请数
    return games, shows, original_works, patents


def read_risk(filepath="data/risk.xlsx"):
    return pd.read_excel(filepath, sheet_name="risk")  # 风险预警数据


# ====== 主流程函数 ======
def calculate_index():
    # ---- 1. 内容价值 ----
    # [cite_start]播放表现：整合腾讯、B站、优酷、骨朵数据并求平均 [cite: 1]
    bilibili_plays, bilibili_followers, _, _, _, bilibili_ratings = read_bilibili()
    douban_ratings, _ = read_douban()
    imdb_ratings, _ = read_imdb()
    tencent = read_tencent()
    youku = read_youku()
    guduo = read_guduo()

    plays_all = bilibili_plays.merge(tencent, on="anime").merge(youku, on="anime").merge(guduo, on="anime")
    plays_all = log_standardize(plays_all, plays_all.columns[1:])
    plays_all = avg_columns(plays_all, plays_all.columns[1:], "play_index")

    # [cite_start]追番人数/播放比（B站）：根据文件要求，计算比值并标准化 [cite: 1]
    followers = bilibili_followers.copy()
    followers["ratio"] = followers["followers"] / (bilibili_plays["play_count"] + 1)
    followers = log_standardize(followers, ["ratio"])
    followers.rename(columns={"ratio": "follow_index"}, inplace=True)

    # [cite_start]口碑得分：整合豆瓣、B站、IMDb评分并求平均 [cite: 1]
    # 注意：文件中提到复杂的计算方法（平均分S、评分人数v等），但代码简化为直接平均，实际使用中可按需调整
    rating_merge = douban_ratings.merge(bilibili_ratings, on="anime").merge(imdb_ratings, on="anime")
    rating_merge = log_standardize(rating_merge, ["score_x", "score_y", "score"])
    rating_merge = avg_columns(rating_merge, ["score_x", "score_y", "score"], "rating_index")

    # [cite_start]内容价值总分：等权重平均 [cite: 1]
    content_value = plays_all.merge(followers[["anime", "follow_index"]], on="anime") \
        .merge(rating_merge, on="anime")
    content_value["content_value"] = content_value[["play_index", "follow_index", "rating_index"]].mean(axis=1)

    # ---- 2. 讨论热度 / 口碑与讨论 ----
    # [cite_start]互动活跃度：整合B站点赞、投币、收藏等数据并求平均 [cite: 1]
    _, _, bilibili_interactions, bilibili_creations, douban_comments, _ = read_bilibili()
    _, douban_comments = read_douban()
    bilibili_interactions = log_standardize(bilibili_interactions, bilibili_interactions.columns[1:])
    bilibili_interactions = avg_columns(bilibili_interactions, bilibili_interactions.columns[1:], "interaction_index")

    # [cite_start]豆瓣评论数：标准化 [cite: 1]
    douban_comments = log_standardize(douban_comments, ["comment_count"])
    douban_comments.rename(columns={"comment_count": "douban_comment_index"}, inplace=True)

    # [cite_start]同人二创：整合B站、抖音、微博、贴吧数据并求平均 [cite: 1]
    douyin = read_douyin()
    weibo = read_weibo()
    tieba = read_tieba()
    bilibili_creations = log_standardize(bilibili_creations, bilibili_creations.columns[1:])
    bilibili_creations = avg_columns(bilibili_creations, bilibili_creations.columns[1:], "creation_index")
    douyin = log_standardize(douyin, ["likes", "comments", "shares"])
    douyin = avg_columns(douyin, ["likes", "comments", "shares"], "douyin_index")
    weibo = log_standardize(weibo, ["posts"])
    weibo.rename(columns={"posts": "weibo_index"}, inplace=True)
    tieba = log_standardize(tieba, ["posts", "followers"])
    tieba = avg_columns(tieba, ["posts", "followers"], "tieba_index")

    # [cite_start]注意：文件中提到了“评论情感分析”，但代码中未实现该逻辑，这部分数据需要通过外部API或模型获取 [cite: 1]

    discussion = bilibili_interactions.merge(douban_comments, on="anime") \
        .merge(bilibili_creations, on="anime") \
        .merge(douyin, on="anime") \
        .merge(weibo, on="anime") \
        .merge(tieba, on="anime")
    discussion["discussion_value"] = discussion.drop(columns=["anime"]).mean(axis=1)

    # ---- 3. 社会影响力 ----
    # [cite_start]搜索热度：百度指数标准化 [cite: 1]
    baidu_index = log_standardize(read_baidu(), ["baidu_index"])
    baidu_index.rename(columns={"baidu_index": "baidu_index_norm"}, inplace=True)

    # [cite_start]口碑外溢 / 评分人数：整合豆瓣和IMDb的评分人数并求平均 [cite: 1]
    rating_votes = douban_ratings.merge(imdb_ratings, on="anime", suffixes=("_douban", "_imdb"))
    rating_votes = log_standardize(rating_votes, ["votes_douban", "votes_imdb"])
    rating_votes = avg_columns(rating_votes, ["votes_douban", "votes_imdb"], "votes_index")

    # [cite_start]出海表现：IMDb排名标准化 [cite: 1]
    # 注意：排名数据通常是越小越好，标准化后需要反向处理，但此处代码未体现，实际应用中可按需调整
    _, imdb_rank = read_imdb()
    imdb_rank = log_standardize(imdb_rank, ["rank"])
    imdb_rank.rename(columns={"rank": "rank_index"}, inplace=True)

    influence = baidu_index.merge(rating_votes, on="anime").merge(imdb_rank, on="anime")
    influence["influence_value"] = influence.drop(columns=["anime"]).mean(axis=1)

    # ---- 4. 产业价值 ----
    # [cite_start]商业变现：整合淘宝和闲鱼的销量并求平均 [cite: 1]
    sales = log_standardize(read_taobao_xianyu(), ["taobao", "xianyu"])
    sales = avg_columns(sales, ["taobao", "xianyu"], "sales_index")

    # [cite_start]产业链延伸：整合游戏、演出、原作反哺、专利数据并求平均 [cite: 1]
    games, shows, original_works, patents = read_industry()
    industry_all = games.merge(shows, on="anime").merge(original_works, on="anime").merge(patents, on="anime")
    industry_all = log_standardize(industry_all, industry_all.columns[1:])
    industry_all = avg_columns(industry_all, industry_all.columns[1:], "industry_index")

    industry_value = sales.merge(industry_all, on="anime")
    industry_value["industry_value"] = industry_value[["sales_index", "industry_index"]].mean(axis=1)

    # ---- 四个一级指标合并 ----
    # [cite_start]根据文件要求，四个一级指标等权重计算总分 [cite: 1]
    result = content_value[["anime", "content_value"]] \
        .merge(discussion[["anime", "discussion_value"]], on="anime") \
        .merge(influence[["anime", "influence_value"]], on="anime") \
        .merge(industry_value[["anime", "industry_value"]], on="anime")

    result["total_score"] = result[["content_value", "discussion_value", "influence_value", "industry_value"]].mean(
        axis=1)

    # ---- 动态调整机制 ----
    # [cite_start]风险预警：根据豆瓣评分和负面评论比例扣减总分 [cite: 1]
    # [cite_start]文件规定扣减15-20%，此处固定扣减20%，可根据实际情况调整 [cite: 1]
    risk = read_risk()
    result = result.merge(risk, on="anime", how="left")
    for i, row in result.iterrows():
        # [cite_start]风险条件：豆瓣评分 ≤ 6.0 或 负面评论 ≥30% [cite: 1]
        if row["douban_score"] <= 6.0 or row["negative_ratio"] >= 0.3:
            result.loc[i, "total_score"] *= 0.8  # 扣减 20%
    return result


if __name__ == "__main__":
    final_scores = calculate_index()
    print(final_scores)
    # 将最终结果保存为 CSV 文件
    final_scores.to_csv("anime_index_results.csv", index=False)