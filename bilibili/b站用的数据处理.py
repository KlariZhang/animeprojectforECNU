import pandas as pd
from rapidfuzz import process, fuzz

# 读取表单 - 修改为实际文件名
dfA = pd.read_csv("bilibilimovie.csv")   # 含有: 所属动漫, videos, creations
dfB = pd.read_excel("newall_cleaned.xlsx", sheet_name="movie")   # 含有: anime (动漫名)

# 重命名表单A的列，使其更清晰
dfA = dfA.rename(columns={"所属动漫": "动漫名", "videos": "总播放量", "creations": "视频数"})

# 重命名表单B的列
dfB = dfB.rename(columns={"anime": "标准动漫名"})

# 定义模糊匹配函数（返回匹配结果和分数）
def fuzzy_match(name, choices, score_cutoff=80):
    match = process.extractOne(
        name, choices, scorer=fuzz.token_set_ratio
    )
    if match:
        matched_name, score, _ = match
        if score >= score_cutoff:
            return matched_name, score
    return None, 0

# 存储匹配结果
matches = []
for name in dfA["动漫名"]:
    matched_name, score = fuzzy_match(name, dfB["标准动漫名"].tolist(), score_cutoff=80)
    if matched_name:  # 匹配成功
        matches.append({"原始动漫名": name, "匹配到标准名": matched_name, "相似度": score})
    else:  # 未匹配成功 → 保留原名
        matches.append({"原始动漫名": name, "匹配到标准名": name, "相似度": 0})

# 转换为 DataFrame
df_matches = pd.DataFrame(matches)

# 将匹配结果加到A表
dfA = dfA.merge(df_matches, left_on="动漫名", right_on="原始动漫名", how="left")
dfA["映射动漫名"] = dfA["匹配到标准名"]

# 按映射动漫名聚合（合并不同季的数据）
dfA_grouped = dfA.groupby("映射动漫名", as_index=False).agg({
    "视频数": "sum",
    "总播放量": "sum"
})

# 用表单B做主表，保证所有标准名都在结果里
result = pd.merge(dfB, dfA_grouped, left_on="标准动漫名", right_on="映射动漫名", how="left")

# 只保留需要的列并重命名
result = result[["标准动漫名", "视频数", "总播放量"]]
result = result.rename(columns={"标准动漫名": "动漫名"})

# 填充 NaN 为 0
result[["视频数", "总播放量"]] = result[["视频数", "总播放量"]].fillna(0)

# 输出两个结果文件
result.to_excel("对齐后的结果movie.xlsx", index=False)
df_matches.to_excel("匹配结果记录movie.xlsx", index=False)

print("已生成 对齐后的结果.xlsx 和 匹配结果记录.xlsx")
