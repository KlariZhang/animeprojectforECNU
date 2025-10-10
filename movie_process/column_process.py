import pandas as pd
import os
import re
import sys

def clean_filename(filepath):
    """
    根据文件路径清理文件名，为列名创建一个干净的前缀。
    """
    # 从路径中获取文件名 (e.g., 'data/my_file.csv' -> 'my_file.csv')
    filename = os.path.basename(filepath)
    # 获取不含 .csv 扩展名的文件名
    base_name = os.path.splitext(filename)[0]
    # 替换特殊字符和空格
    clean_name = re.sub(r'[\s\.\-:]+', '_', base_name)
    return clean_name

def rename_columns_for_single_file(filepath):
    """
    读取指定的CSV文件，将其除第一列外的所有列重命名，
    并原地覆盖保存文件。

    列名格式: '文件名_原列名'
    """
    # 检查文件是否存在
    if not os.path.exists(filepath):
        print(f"错误：文件 '{filepath}' 不存在。请检查文件名和路径。")
        return

    try:
        # 1. 读取CSV文件
        df = pd.read_csv(filepath)
        
        # 检查DataFrame是否为空或只有一列
        if df.empty:
            print(f"警告：文件 '{filepath}' 为空，无需处理。")
            return
        if len(df.columns) <= 1:
            print(f"警告：文件 '{filepath}' 只有一列或没有其他列，无需重命名。")
            return

        # 2. 从文件名获取前缀
        prefix = clean_filename(filepath)

        # 3. 获取第一列的名称，确保它不被修改
        first_column_name = df.columns[0]
        
        # 4. 创建新的列名映射，跳过第一列
        rename_mapper = {
            col: f"{prefix}_{col}" 
            for col in df.columns 
            if col != first_column_name
        }

        # 5. 应用新的列名
        df.rename(columns=rename_mapper, inplace=True)

        # 6. 直接覆盖保存回原文件
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        print(f"成功处理文件: '{filepath}'")
        print("第一列 '{}' 未被修改。".format(first_column_name))
        print("其他列已添加前缀 '{}_'".format(prefix))

    except Exception as e:
        print(f"处理文件 '{filepath}' 时发生错误: {e}")

# --- 如何使用 ---
if __name__ == "__main__":
    # 警告用户此操作的风险
    print("="*50)
    print("警告：此脚本将直接修改并覆盖您指定的原始CSV文件。")
    print("这个操作是不可逆的。强烈建议您在运行前备份数据。")
    print("="*50)
    
    # ----------------------------------------------------------------------
    # 使用说明：请在这里修改您要处理的文件名
    # ----------------------------------------------------------------------
    # 示例: 
    # file_to_process = 'anime_post_count_movie.csv'
    # file_to_process = 'baidu_movie_index_summary_filled.csv'
    
    file_to_process = "movie_process\douyin_movie_final.csv"  # <--- 在这里替换成您想处理的CSV文件名

    # ----------------------------------------------------------------------

    rename_columns_for_single_file(file_to_process)
