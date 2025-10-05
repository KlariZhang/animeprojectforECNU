import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, StandardScaler

# ========== 工具函数 ==========
def log_minmax(series):
    """ log(1+X) + MinMax归一化 """
    series_log = np.log1p(series)
    return (series_log - series_log.min()) / (series_log.max() - series_log.min())

def log_zscore(series):
    """ log(1+X) + Zscore标准化 """
    series_log = np.log1p(series)
    return (series_log - series_log.mean()) / series_log.std()

def minmax(series):
    """ MinMax归一化 """
    return (series - series.min()) / (series.max() - series.min())

def zscore(series):
    """ Zscore标准化 """
    return (series - series.mean()) / series.std()

def bayesian_rating(ratings, counts, C=0, m=0):
    """
    贝叶斯修正评分
    ratings: 平均评分
    counts: 评分人数
    C: 全局平均分
    m: 全局平均评分人数
    """
    return (counts / (counts + m)) * ratings + (m / (counts + m)) * C


# ========== 主处理函数 ==========
def preprocess(df):
    """
    df: 原始DataFrame，每一行=一个作品，每一列=一个指标
    返回: 预处理后的标准化矩阵
    """

    df_processed = pd.DataFrame(index=df.index)

    # 1. 数值类指标（播放量、评论数、二创视频量、票房、衍生品销量等）
    num_log_minmax = ["总播放量", "集均播放量", "评论数", "二创视频量", "票房", "衍生品销量", "演出场次"]
    for col in num_log_minmax:
        if col in df.columns:
            df_processed[col] = log_minmax(df[col])

    num_log_zscore = ["互动数"]  # 举例
    for col in num_log_zscore:
        if col in df.columns:
            df_processed[col] = log_zscore(df[col])

    # 2. 比例类指标（追番比、评论正负面比例、想看/实看比）
    ratio_cols = ["追番比", "正负面比", "想看实看比"]
    for col in ratio_cols:
        if col in df.columns:
            df_processed[col] = minmax(df[col])

    # 3. 评分类指标（豆瓣、IMDb评分）
    if {"豆瓣评分", "豆瓣评分人数"}.issubset(df.columns):
        C = df["豆瓣评分"].mean()
        m = df["豆瓣评分人数"].mean()
        df_processed["豆瓣加权评分"] = bayesian_rating(df["豆瓣评分"], df["豆瓣评分人数"], C, m)

    if {"IMDb评分", "IMDb评分人数"}.issubset(df.columns):
        C = df["IMDb评分"].mean()
        m = df["IMDb评分人数"].mean()
        df_processed["IMDb加权评分"] = bayesian_rating(df["IMDb评分"], df["IMDb评分人数"], C, m)

    # 4. 搜索热度（如百度指数，先求7日均值再归一化）
    if "百度指数" in df.columns:
        df_processed["百度指数"] = minmax(df["百度指数"])

    # 5. 评分人数类（单独标准化）
    count_cols = ["豆瓣评分人数", "IMDb评分人数"]
    for col in count_cols:
        if col in df.columns:
            df_processed[col + "_Z"] = zscore(df[col])

    # 6. 二元/分类变量（是否联动、是否原作反哺）
    binary_cols = ["是否联动", "是否反哺"]
    for col in binary_cols:
        if col in df.columns:
            df_processed[col] = df[col].apply(lambda x: 1 if x else 0)

    return df_processed


# ========== 使用示例 ==========
if __name__ == "__main__":
    # 假设你有一个Excel原始表格，每行=作品，每列=指标
    df_raw = pd.read_excel("原始指标数据.xlsx", index_col=0)

    df_ready = preprocess(df_raw)

    # 保存结果，供赋权方法使用（专家赋权、熵权法、PCA）
    df_ready.to_excel("标准化指标数据.xlsx")
    print("✅ 数据预处理完成，结果已保存为 标准化指标数据.xlsx")
