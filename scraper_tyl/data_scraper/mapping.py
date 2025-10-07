import pandas as pd
import ast # Used for safely evaluating string representations of lists

# --- 配置区 ---
# 请确保这两个文件名与您本地的文件名完全一致
cleaned_file = 'cleaned_anime_list.csv'
original_file = 'originalist.csv'
output_filename = 'anime_mapping_grouped.csv'
# --- 配置结束 ---

try:
    print(f"步骤 1: 正在读取文件 '{cleaned_file}' 和 '{original_file}'...")
    cleaned_df = pd.read_csv(cleaned_file)
    original_df = pd.read_csv(original_file)
    print("文件读取成功！")

    # --- 数据清洗与准备 ---
    cleaned_df.dropna(subset=['anime'], inplace=True)
    original_df.dropna(subset=['series_name', 'season_id'], inplace=True)
    original_df['season_id'] = pd.to_numeric(original_df['season_id'], errors='coerce')
    original_df.dropna(subset=['season_id'], inplace=True)
    original_df['season_id'] = original_df['season_id'].astype(int)

    # --- 核心匹配逻辑 (与之前相同) ---
    print("步骤 2: 正在建立一对多映射关系...")
    mapping_list = []
    for cleaned_name in cleaned_df['anime']:
        matches = original_df[original_df['series_name'].str.contains(cleaned_name, na=False)]
        if not matches.empty:
            for _, row in matches.iterrows():
                mapping_list.append({
                    'cleaned_name': cleaned_name,
                    'original_name': row['series_name'],
                    'season_id': row['season_id']
                })

    mapping_df = pd.DataFrame(mapping_list)
    print("初步映射完成！")

    # --- 按要求聚合数据 ---
    print("步骤 3: 正在将分季数据聚合为列表...")
    
    # 创建一个包含分季名称和ID的元组，方便聚合
    mapping_df['season_info'] = mapping_df.apply(lambda row: (row['original_name'], row['season_id']), axis=1)
    
    # 按 'cleaned_name' 分组，并将每个组的 'season_info' 聚合到一个列表中
    grouped_df = mapping_df.groupby('cleaned_name')['season_info'].apply(list).reset_index()
    
    # 重命名列以符合要求
    grouped_df.columns = ['series_name', 'seasons_list']
    
    print("数据聚合成功！")

    # --- 保存结果 ---
    grouped_df.to_csv(output_filename, index=False, encoding='utf-8-sig')
    print(f"步骤 4: 最终结果已成功保存到文件 '{output_filename}' 中。")
    '''
    # --- 打印示例 ---
    print("\n--- 运行结果示例 ---")
    # 为了清晰展示，我们只打印'斗破苍穹'的结果
    doupo_example = grouped_df[grouped_df['series_name'] == '斗破苍穹']
    if not doupo_example.empty:
        series_name = doupo_example.iloc[0]['series_name']
        seasons_list_str = doupo_example.iloc[0]['seasons_list']
        
        # 将字符串格式的列表转换回真实的列表对象，以便逐行打印
        seasons_list = ast.literal_eval(str(seasons_list_str)) # Safely evaluate the string
        
        print(f"\n系列名称: {series_name}")
        print("对应的分季列表:")
        for season_name, season_id in seasons_list:
            print(f"  - {season_name} (season_id: {season_id})")
    '''
except FileNotFoundError as e:
    print(f"错误：文件未找到。请确保 '{cleaned_file}' 和 '{original_file}' 与此脚本在同一个文件夹中。")
except Exception as e:
    print(f"处理过程中发生了一个意外错误: {e}")