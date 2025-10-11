import pandas as pd
import os


def rename_columns_in_excel(file_path):
    """
    重命名Excel文件中所有工作表的列名
    格式：文件名_Sheet名_原列名
    """
    # 获取文件名（不含扩展名）
    file_name = os.path.splitext(os.path.basename(file_path))[0]

    # 读取Excel文件的所有工作表
    excel_file = pd.ExcelFile(file_path)

    # 创建一个空的字典来存储处理后的DataFrame
    processed_dfs = {}

    # 遍历每个工作表
    for sheet_name in excel_file.sheet_names:
        # 读取工作表
        df = pd.read_excel(file_path, sheet_name=sheet_name)

        # 创建新的列名映射
        new_columns = {}
        for old_col in df.columns:
            new_col_name = f"{file_name}_{sheet_name}_{old_col}"
            new_columns[old_col] = new_col_name

        # 重命名列
        df.rename(columns=new_columns, inplace=True)

        # 将处理后的DataFrame存储到字典中
        processed_dfs[sheet_name] = df

        print(f"工作表 '{sheet_name}' 的列名已重命名完成")

    # 将修改后的数据写回原文件（覆盖）
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        for sheet_name, df in processed_dfs.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"文件 '{file_path}' 的列名重命名完成并已保存")


# 使用示例
if __name__ == "__main__":
    # 替换为你的文件路径
    file_path = "douban_anime_final2.xlsx"
    rename_columns_in_excel(file_path)