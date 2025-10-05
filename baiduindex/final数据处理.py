import pandas as pd

# 读取文件（第一列是日期，所以设为 index）
df = pd.read_csv("baidu_movie_2023-07-01_to_2025-06-30_new.csv", index_col=0)

# 计算每个动漫的总和和平均值（跳过 NaN，全空会得到 NaN）
sums = df.sum(axis=0, skipna=True)
means = df.mean(axis=0, skipna=True)

# 合并结果：每一行是一个动漫
result = pd.DataFrame({
    "sum": sums,
    "mean": means
})

# 保存结果
result.to_csv("baidu_movie_index_summary.csv", encoding="utf-8-sig")

print("处理完成，结果已保存到 baidu_movie_index_summary.csv")

