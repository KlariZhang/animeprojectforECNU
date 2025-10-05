import pandas as pd
import numpy as np

# 读取结果数据
df = pd.read_csv("baidu_movie_index_summary.csv", index_col=0)

# 只计算有数据动漫的分位数（排除空值）
valid_means = df["mean"].replace(0, np.nan).dropna()  # 将0转为NaN然后删除
fill_value = valid_means.quantile(0.05)

print("5%分位数填充值:", fill_value)

# 只对mean列：所有空值（0和NaN）都用5%分位数填充
mean_mask = (df["mean"] == 0) | (df["mean"].isna())
df.loc[mean_mask, "mean"] = fill_value

print(f"填充了 {mean_mask.sum()} 个mean值")

# 保存结果
df.to_csv("baidu_movie_index_summary_filled.csv", encoding="utf-8-sig")
print("处理完成，已保存到 baidu_anime_index_summary_filled.csv")