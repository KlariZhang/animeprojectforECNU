import pandas as pd
import numpy as np


def entropy_weight_method(df, need_index=True):
    """
    熵权法计算权重
    输入: 已标准化的 DataFrame (行=对象, 列=指标)
    输出: 权重向量 (Series) + 加权得分 (Series)
    """
    # 如果有作品名，就分离出来
    if need_index:
        names = df.iloc[:, 0]  # 第一列是作品名
        data = df.iloc[:, 1:].astype(float)
    else:
        names = df.index
        data = df.astype(float)

    # Step 1: 归一化为比例矩阵 P
    P = data / data.sum(axis=0)

    # Step 2: 计算熵值 e_j
    n, m = data.shape
    k = 1 / np.log(n)
    entropy = -k * (P * np.log(P + 1e-12)).sum(axis=0)

    # Step 3: 计算差异度 d_j
    d = 1 - entropy

    # Step 4: 计算权重 w_j
    w = d / d.sum()

    # Step 5: 计算每个对象的综合得分
    scores = (data * w).sum(axis=1)

    # 输出结果
    weights = pd.Series(w, index=data.columns, name="weight")
    scores = pd.Series(scores, index=names, name="score")

    return weights, scores


# ===== 使用示例 =====
if __name__ == "__main__":
    # 读取文件（Excel 或 CSV）
    df = pd.read_excel("input.xlsx")  # 或 pd.read_csv("input.csv")

    weights, scores = entropy_weight_method(df, need_index=True)

    print("指标权重：")
    print(weights)
    print("\n作品得分：")
    print(scores)

    # 保存结果
    weights.to_excel("weights.xlsx")
    scores.to_excel("scores.xlsx")
