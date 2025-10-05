import pandas as pd


def compare_and_clean_anime_data(sheetA_path, sheetB_path, output_path=None):
    """
    对比两个表单的anime列并清理数据

    参数:
    sheetA_path: 表单A文件路径
    sheetB_path: 表单B文件路径
    output_path: 清理后保存路径(可选)
    """

    # 读取数据
    try:
        df_A = pd.read_excel(sheetA_path)  # 如果是Excel文件
        df_B = pd.read_excel(sheetB_path)
    except:
        # 如果是CSV文件
        df_A = pd.read_csv(sheetA_path)
        df_B = pd.read_csv(sheetB_path)

    # 确保列名正确
    anime_col_A = 'anime'
    anime_col_B = 'anime'  # 根据实际情况调整列名

    print(f"表单A原始数据量: {len(df_A)}")
    print(f"表单B原始数据量: {len(df_B)}")

    # 获取两个表单的anime集合
    anime_set_A = set(df_A[anime_col_A].dropna().astype(str))
    anime_set_B = set(df_B[anime_col_B].dropna().astype(str))

    print(f"表单A中anime数量: {len(anime_set_A)}")
    print(f"表单B中anime数量: {len(anime_set_B)}")

    # 找出A中有但B中没有的anime
    anime_only_in_A = anime_set_A - anime_set_B
    print(f"\n表单A中有但表单B中没有的anime数量: {len(anime_only_in_A)}")

    if anime_only_in_A:
        print("具体内容:")
        for anime in sorted(anime_only_in_A):
            print(f"  - {anime}")

    # 删除A中有但B中没有的行
    df_A_cleaned = df_A[~df_A[anime_col_A].astype(str).isin(anime_only_in_A)]

    print(f"\n清理后表单A数据量: {len(df_A_cleaned)}")
    print(f"删除的行数: {len(df_A) - len(df_A_cleaned)}")

    # 找出B中有但A中没有的anime
    anime_only_in_B = anime_set_B - anime_set_A
    print(f"\n表单B中有但表单A中没有的anime数量: {len(anime_only_in_B)}")

    if anime_only_in_B:
        print("具体内容:")
        for anime in sorted(anime_only_in_B):
            print(f"  - {anime}")

    # 保存清理后的数据
    if output_path:
        if output_path.endswith('.xlsx'):
            df_A_cleaned.to_excel(output_path, index=False)
        else:
            df_A_cleaned.to_csv(output_path, index=False)
        print(f"\n清理后的数据已保存到: {output_path}")

    return df_A_cleaned, anime_only_in_B


# 使用示例
if __name__ == "__main__":
    # 请修改为您的实际文件路径
    sheetB_path = "newall_cleaned.xlsx"  # 或 "表单A.csv"
    sheetA_path = "final_anime_data.xlsx"  # 或 "表单B.csv"
    output_path = "final.xlsx"

    # 执行对比和清理
    cleaned_data, missing_in_A = compare_and_clean_anime_data(
        sheetA_path, sheetB_path, output_path
    )

    # 如果需要将B中有A中没有的内容保存到文件
    if missing_in_A:
        missing_df = pd.DataFrame(list(missing_in_A), columns=['missing_anime'])
        missing_df.to_excel("B中有A中没有的anime列表.xlsx", index=False)
        print("B中有A中没有的anime列表已保存到文件")