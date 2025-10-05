import pandas as pd

# 读取文件
file_path = "fanmade_results_all.csv"  # 你的CSV文件路径
df = pd.read_csv(file_path)

# 确保“播放量”是数值型（如果有异常字符会自动转为NaN）
df["播放量"] = pd.to_numeric(df["播放量"], errors="coerce")

# 按动漫名分组，统计视频数和播放量总和
result = df.groupby("所属动漫").agg(
    creations=("视频标题", "count"),
    videos=("播放量", "sum")
).reset_index()

# 输出结果
print(result)

# 保存到新的CSV文件
result.to_csv("bilibilianime.csv", index=False, encoding="utf-8-sig")
