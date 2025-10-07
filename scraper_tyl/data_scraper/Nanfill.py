import pandas as pd

# --- 配置区 ---
SOURCE_LIST_FILE = 'cleaned_anime_list.csv'
CURRENT_RESULTS_FILE = 'bilibili_stats.xlsx'
OUTPUT_FILE = 'bilibili_stats_complete.xlsx'
# --- 配置结束 ---

def fill_missing_anime_data():
    """
    对照源列表，补全结果文件中缺失的动漫IP数据。
    """
    print("--- 开始补全缺失的动漫IP数据 ---")

    # 1. 读取两个文件
    try:
        source_df = pd.read_csv(SOURCE_LIST_FILE)
        results_df = pd.read_excel(CURRENT_RESULTS_FILE,sheet_name='anime')
        print("[✓] 成功读取源列表和当前结果文件。")
    except FileNotFoundError as e:
        print(f"[!] 文件未找到错误: {e}")
        print("请确保 'cleaned_anime_list.csv' 和 'bilibili_stats.xlsx - anime.csv' 都在脚本所在的文件夹中。")
        return

    # 2. 找出缺失的动漫IP
    source_names = set(source_df['anime'].dropna())
    result_names = set(results_df['series_name'].dropna())
    missing_names = list(source_names - result_names)

    if not missing_names:
        print("[✓] 数据完整，没有找到需要补全的动漫IP。")
        return
    
    print(f"[*] 共找到 {len(missing_names)} 个未被爬取到的IP，将为其填充5%分位数的数据。")

    # 3. 计算5%分位数
    # 确定哪些是数值列（排除series_name）
    numeric_cols = results_df.select_dtypes(include='number').columns.tolist()
    
    # 计算分位数，并转换为字典格式，方便后续使用
    quantile_values = results_df[numeric_cols].quantile(0.05).to_dict()
    print("\n--- 计算出的5%分位数填充值 ---")
    for col, val in quantile_values.items():
        print(f"  - {col}: {val:.2f}")
    print("---------------------------------")
    
    # 4. 为缺失的IP创建新的数据行
    new_rows = []
    for name in missing_names:
        new_row = {'series_name': name}
        new_row.update(quantile_values)
        new_rows.append(new_row)
        
    # 5. 合并数据并保存
    missing_df = pd.DataFrame(new_rows)
    
    # 确保列顺序一致
    final_df = pd.concat([results_df, missing_df], ignore_index=True)
    
    try:
        final_df.to_excel(OUTPUT_FILE, sheet_name='anime', index=False)
        print(f"\n[🎉] 数据补全成功！最终的完整数据已保存到 '{OUTPUT_FILE}'。")
        print(f"[*] 最终文件包含 {len(final_df)} 行数据。")
    except Exception as e:
        print(f"\n[!] 保存到Excel文件时出错: {e}")
        print("请确保您已安装 'openpyxl' 库 (pip install openpyxl)。")

if __name__ == '__main__':
    fill_missing_anime_data()