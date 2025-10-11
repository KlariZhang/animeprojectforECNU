import pandas as pd
import os


def compare_anime_columns(sheetA_path, sheetB_path, sheetB_sheet_name='anime',sheetA_sheet_name='comments'):
    """
    对比两个表单的anime列是否相同
    sheetA_path: baidu_anime.xlsx 文件路径
    sheetB_path: newall_cleaned.xlsx 文件路径
    sheetB_sheet_name: newall_cleaned.xlsx 中的sheet名称
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(sheetA_path):
            print(f"❌ 文件 {sheetA_path} 不存在")
            return False
        if not os.path.exists(sheetB_path):
            print(f"❌ 文件 {sheetB_path} 不存在")
            return False

        # 读取数据 - 正确的方式传递参数
        df_A = pd.read_excel(sheetA_path,sheet_name=sheetA_sheet_name)
        df_B = pd.read_excel(sheetB_path, sheet_name=sheetB_sheet_name)

        print(f"文件A列名: {df_A.columns.tolist()}")
        print(f"文件B列名: {df_B.columns.tolist()}")

        # 检查所需的列是否存在
        if 'anime' not in df_A.columns:
            print("❌ 文件A中找不到 'anime' 列")
            return False
        if 'anime' not in df_B.columns:
            print("❌ 文件B中找不到 'anime' 列")
            return False

        # 获取anime列数据并转换为集合
        anime_A = set(df_A['anime'].dropna().astype(str))
        anime_B = set(df_B['anime'].dropna().astype(str))

        print(f"文件A的anime数量: {len(anime_A)}")
        print(f"文件B的anime数量: {len(anime_B)}")

        # 比较是否相同
        if anime_A == anime_B:
            print("✅ 两个表的anime列完全相同")
            return True
        else:
            print("❌ 两个表的anime列不相同")

            # 显示差异详情
            only_in_A = anime_A - anime_B
            only_in_B = anime_B - anime_A

            if only_in_A:
                print(f"仅在文件A中存在: {list(only_in_A)[:5]}")  # 只显示前5个
            if only_in_B:
                print(f"仅在文件B中存在: {list(only_in_B)[:5]}")  # 只显示前5个

            return False

    except Exception as e:
        print(f"❌ 读取文件时出错: {e}")
        return False


# 使用示例 - 修正文件路径和参数传递
sheetA_path = "bilibili_anime.xlsx"  # 确保这个文件存在
sheetB_path = "newall_cleaned.xlsx"  # 确保这个文件存在

# 调用函数，正确传递参数
compare_anime_columns(sheetA_path, sheetB_path, 'anime')