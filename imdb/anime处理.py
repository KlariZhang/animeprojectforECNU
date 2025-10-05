import pandas as pd
from rapidfuzz import process, fuzz
import re


def clean_anime_name(name):
    """
    清理动漫名称，去除季数等非主要IP名信息
    """
    if pd.isna(name):
        return ""

    # 去除季数信息
    patterns = [
        r'第[一二三四五六七八九十\d]+季',
        r'Season\s*\d+',
        r'S\d+',
        r'\(\d{4}\)',
        r'第[一二三四五六七八九十\d]+期',
        r'Part\s*\d+',
        r'-\s*Season\s*\d+',
        r'\s*动态漫',
        r'\s*动态漫画',
        r'\s*日语版',
        r'\s*粤语版',
        r'\s*中配版'
    ]

    cleaned_name = str(name)
    for pattern in patterns:
        cleaned_name = re.sub(pattern, '', cleaned_name, flags=re.IGNORECASE)

    # 去除多余空格和特殊字符
    cleaned_name = re.sub(r'\s+', ' ', cleaned_name).strip()
    cleaned_name = cleaned_name.strip(' -')

    return cleaned_name


def fuzzy_match(name, choices, score_cutoff=80):
    """
    模糊匹配函数
    """
    match = process.extractOne(
        name, choices, scorer=fuzz.token_set_ratio
    )
    if match:
        matched_name, score, _ = match
        if score >= score_cutoff:
            return matched_name, score
    return None, 0


def process_anime_imdb_data():
    """
    处理动漫IMDb数据的主要函数
    """
    # 1. 读取数据
    dfA = pd.read_csv("anime_imdb_results.csv")  # 表单A
    dfB = pd.read_excel("newall_cleaned.xlsx", sheet_name="anime")  # 表单B

    # 重命名列以便清晰
    dfB = dfB.rename(columns={"anime": "标准动漫名"})

    # 2. 清理表单A的动漫名称用于分组
    dfA_clean = dfA.copy()
    dfA_clean['cleaned_name'] = dfA_clean['original_name'].apply(clean_anime_name)

    # 处理votes列（去除逗号并转换为数值）
    def clean_votes(vote_str):
        if pd.isna(vote_str) or vote_str == '':
            return 0
        try:
            # 处理带逗号的数字字符串
            if isinstance(vote_str, str):
                vote_str = vote_str.replace(',', '')
            return float(vote_str)
        except:
            return 0

    dfA_clean['votes_clean'] = dfA_clean['votes'].apply(clean_votes)
    dfA_clean['rating_clean'] = pd.to_numeric(dfA_clean['rating'], errors='coerce').fillna(0)

    # 3. 按清理后的名称分组，合并相同IP的数据
    merged_a = dfA_clean.groupby('cleaned_name').agg({
        'original_name': 'first',  # 保留第一个原始名称
        'imdb_name': 'first',  # 保留第一个imdb名称
        'rating_clean': 'sum',  # 评分相加
        'votes_clean': 'sum',  # 投票数相加
        'imdbid': 'first'  # 保留第一个imdbid
    }).reset_index()

    # 4. 清理表单B的动漫名称用于匹配
    dfB_clean = dfB.copy()
    dfB_clean['cleaned_name'] = dfB_clean['标准动漫名'].apply(clean_anime_name)

    # 5. 存储匹配结果
    matches = []
    for name in dfB_clean["标准动漫名"]:
        cleaned_name = clean_anime_name(name)
        matched_name, score = fuzzy_match(cleaned_name, merged_a['cleaned_name'].tolist(), score_cutoff=80)

        if matched_name:  # 匹配成功
            # 获取匹配的数据
            matched_data = merged_a[merged_a['cleaned_name'] == matched_name].iloc[0]
            matches.append({
                '标准动漫名': name,
                '匹配到的清理名': matched_name,
                '相似度': score,
                'original_name': matched_data['original_name'],
                'imdb_name': matched_data['imdb_name'],
                'rating': matched_data['rating_clean'],
                'votes': matched_data['votes_clean'],
                'imdbid': matched_data['imdbid']
            })
        else:  # 未匹配成功
            matches.append({
                '标准动漫名': name,
                '匹配到的清理名': None,
                '相似度': 0,
                'original_name': name,  # 使用表单B的名称
                'imdb_name': None,
                'rating': None,
                'votes': None,
                'imdbid': None
            })

    # 6. 转换为结果DataFrame
    df_matches = pd.DataFrame(matches)

    # 7. 创建最终结果（以表单B为主表）
    result = dfB_clean[['标准动漫名']].merge(
        df_matches[['标准动漫名', 'original_name', 'imdb_name', 'rating', 'votes', 'imdbid']],
        on='标准动漫名',
        how='left'
    )

    # 重命名列以符合输出格式
    result = result.rename(columns={'标准动漫名': 'original_name'})

    # 8. 输出结果
    result.to_excel("对齐后的动漫IMDb结果.xlsx", index=False)
    pd.DataFrame(matches).to_excel("匹配结果记录_动漫IMDb.xlsx", index=False)

    print("处理完成！")
    print(f"总处理条目数: {len(result)}")
    print(f"成功匹配数: {len([m for m in matches if m['相似度'] >= 80])}")

    return result, pd.DataFrame(matches)


# 执行处理
if __name__ == "__main__":
    final_result, match_records = process_anime_imdb_data()

    # 显示前几行结果
    print("\n前10行处理结果:")
    print(final_result.head(10))

    # 显示匹配统计
    match_stats = match_records['相似度'].value_counts().sort_index(ascending=False)
    print("\n匹配相似度统计:")
    for score, count in match_stats.items():
        if score > 0:
            print(f"相似度 {score}%: {count} 条")