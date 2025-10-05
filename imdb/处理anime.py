import pandas as pd
from rapidfuzz import process, fuzz

# 读取两个表单
dfA = pd.read_excel("anime_imdb_results.xlsx")  # 表单A：动漫名和IMDB数据
dfB = pd.read_excel("newall_cleaned.xlsx", sheet_name="anime")  # 表单B：标准动漫名

# 重命名表单B的列为标准名
dfB = dfB.rename(columns={"anime": "标准动漫名"})


# 定义模糊匹配函数
def fuzzy_match(name, choices, score_cutoff=80):
    match = process.extractOne(
        name, choices, scorer=fuzz.token_set_ratio, score_cutoff=score_cutoff
    )
    if match:
        matched_name, score, _ = match
        return matched_name, score
    return None, 0


# 为表单A的动漫名找到对应的标准IP名
matches = []
for name in dfA["original_name"]:
    matched_name, score = fuzzy_match(name, dfB["标准动漫名"].tolist(), score_cutoff=80)
    if matched_name:  # 匹配成功
        matches.append({"原始动漫名": name, "映射动漫名": matched_name, "相似度": score})
    else:  # 未匹配成功 → 保留原名
        matches.append({"原始动漫名": name, "映射动漫名": name, "相似度": 0})

# 将匹配结果转换为DataFrame并合并到表单A
df_matches = pd.DataFrame(matches)
dfA = dfA.merge(df_matches, left_on="original_name", right_on="原始动漫名", how="left")

# 检查dfA的列名
print("dfA的列名:", dfA.columns.tolist())

# 根据您的列名设置聚合规则
# 数值型数据求和，评分求平均
aggregation_dict = {
    'votes': 'sum',  # 投票数求和
    'imdbid': 'first'  # 取第一个imdbid
}

# 如果有rating列，则求平均
if 'rating' in dfA.columns:
    aggregation_dict['rating'] = 'mean'

# 添加您可能需要保留的其他列（取第一个值）
other_columns_to_keep = ['imdb_name']  # 可以添加其他需要保留的列
for col in other_columns_to_keep:
    if col in dfA.columns:
        aggregation_dict[col] = 'first'

print("使用的聚合规则:", aggregation_dict)

# 按照映射后的动漫名聚合（合并不同季的数据）
dfA_grouped = dfA.groupby("映射动漫名", as_index=False).agg(aggregation_dict)

# 将表单B作为主表，保证所有标准IP都在结果里
result = pd.merge(
    dfB,
    dfA_grouped,
    left_on="标准动漫名",
    right_on="映射动漫名",
    how="left"
)

# 保留所有需要的列
columns_to_keep = ["标准动漫名"]
for col in aggregation_dict.keys():
    if col in result.columns:
        columns_to_keep.append(col)

# 添加其他保留的列
for col in other_columns_to_keep:
    if col in result.columns and col not in columns_to_keep:
        columns_to_keep.append(col)

result = result[columns_to_keep]

# 重命名列
rename_dict = {"标准动漫名": "动漫名"}
result = result.rename(columns=rename_dict)

# 填充NaN为0（只对数值列）
numeric_columns = ['votes']
if 'rating' in result.columns:
    numeric_columns.append('rating')

result[numeric_columns] = result[numeric_columns].fillna(0)

# 输出结果
result.to_excel("对齐后的结果.xlsx", index=False)
df_matches.to_excel("匹配过程记录.xlsx", index=False)

print("已生成 对齐后的结果.xlsx 和 匹配过程记录.xlsx")
print(f"处理了 {len(dfA)} 条原始数据")
print(f"生成了 {len(result)} 条标准动漫记录")
print(f"结果包含的列: {result.columns.tolist()}")

# 显示匹配统计信息
matched_count = len(df_matches[df_matches['相似度'] >= 80])
print(f"成功匹配: {matched_count} 条记录")
print(f"匹配成功率: {matched_count / len(df_matches) * 100:.2f}%")