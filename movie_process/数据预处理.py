import pandas as pd
import numpy as np
import os
from pathlib import Path
from functools import reduce


def log1p_transform(column):
    """
    log(1+X)变换 - 用于平滑极端值
    """
    return np.log1p(column)


def min_max_normalize(column):
    """
    Min-Max归一化 - 将数据缩放到[0,1]区间
    """
    min_val = column.min()
    max_val = column.max()

    if max_val == min_val:
        return pd.Series([0.5] * len(column), index=column.index)

    return (column - min_val) / (max_val - min_val)


def z_score_standardize(column):
    """
    Z-score标准化 - 使数据符合标准正态分布
    """
    mean_val = column.mean()
    std_val = column.std()

    if std_val == 0:
        return pd.Series([0] * len(column), index=column.index)

    return (column - mean_val) / std_val


# 预处理方法映射字典
PREPROCESSING_METHODS = {
    'log': log1p_transform,
    'minmax': min_max_normalize,
    'zscore': z_score_standardize
}


def process_single_dataframe(df, file_name, sheet_name):
    """
    处理单个数据框：根据配置应用多种预处理方法

    参数：
    df: 要处理的数据框
    file_name: 文件名
    sheet_name: 工作表名
    """
    # 复制数据，但只保留 movie 列和需要处理的列
    processed_df = pd.DataFrame()
    processed_df['movie'] = df['movie'].copy()

    # =================================================================
    # 预处理配置部分 - 请根据您的实际需求修改这部分
    # =================================================================

    # 配置格式: '列名': ['预处理方法1', '预处理方法2', ...]
    preprocessing_config = {
        # industry_movie.xlsx - 所有计数类数据先log变换减轻偏度，再minmax归一化
        'movie_post_count_movie_帖子数': ['log', 'minmax'],
      
        # tieba_movie.xlsx - 贴吧数据先log变换，再minmax归一化
        'tieba_stats_from_excelmovie_new_followers': ['log', 'minmax'],
        'tieba_stats_from_excelmovie_new_posts': ['log', 'minmax'],

        # baidu_movie_index_summary_filled.csv 列配置
        'baidu_movie_index_summary_filled_sum': ['log', 'minmax'],
        'baidu_movie_index_summary_filled_mean': ['log', 'minmax'],
        
        #imdb
        'movie_imdb_final_new_rating_votes': ['log', 'minmax'],  # 投票数先log再minmax
        'movie_imdb_final_new_rating_score': ['minmax'],  # 评分直接minmax归一化

        # douban
        'douban_movie_final_score_x': ['minmax'],
        'douban_movie_final_votes_douban': ['log', 'minmax'],
        'douban_movie_final_comment_count': ['log', 'minmax'],
        'ouban_movie_final_review_count': ['log', 'minmax'],

        # douyin
        'douyin_movie_final_num': ['log', 'minmax'],
        'douyin_movie_final_likes': ['log', 'minmax'],
        'douyin_movie_final_comments': ['log', 'minmax'],
        'douyin_movie_final_shares': ['log', 'minmax'],


        # 
        'bilibili_movie_dataall_play_count_plays': ['log', 'minmax'],
        'bilibili_movie_dataall_followers_followers': ['log', 'minmax'],
        'bilibili_movie_dataall_likes_interactions': ['log', 'minmax'],
        'bilibili_movie_dataall_coins_interactions': ['log', 'minmax'],
        'bilibili_movie_dataall_total_favorite': ['log', 'minmax'],
        'bilibili_movie_dataall_shares_interations': ['log', 'minmax'],
        'bilibili_movie_dataall_danmu_interactions': ['log','minmax'],
        'bilibili_movie_dataall_score_ratings': ['log', 'minmax'],

        # 
        'bilibili_movie_creations_creations': ['log', 'minmax'],
        'bilibili_movie_creations_videos': ['log', 'minmax'],

        # 
        'bilibili_movie_comments_comment_count': ['log', 'minmax'],
    }

    # =================================================================
    # 配置结束
    # =================================================================

    # 应用预处理
    for col, methods in preprocessing_config.items():
        if col in df.columns:
            temp_data = df[col].copy()  # 从原始数据框复制数据
            method_names = []  # 记录使用的方法名

            for method in methods:
                if method in PREPROCESSING_METHODS:
                    # 在上一步结果基础上继续处理
                    temp_data = PREPROCESSING_METHODS[method](temp_data)
                    method_names.append(method)
                    print(f"    - 对列 '{col}' 应用了 {method} 预处理")
                else:
                    print(f"    - 警告: 未知的预处理方法 '{method}'，跳过")

            # 生成最终列名（包含所有方法名）
            new_col_name = f"{col}_{'_'.join(method_names)}"
            processed_df[new_col_name] = temp_data

    return processed_df


def read_and_process_all_files(folder_path):
    """
    读取并处理文件夹中的所有Excel文件
    """
    all_processed_data = []
    folder_path = Path(folder_path)

    # 获取所有Excel文件
    excel_files = list(folder_path.glob("*.xlsx"))

    if not excel_files:
        print(f"在文件夹 '{folder_path}' 中未找到任何Excel文件(.xlsx)")
        return all_processed_data

    print(f"找到 {len(excel_files)} 个Excel文件")

    # 处理每个Excel文件
    for excel_file in excel_files:
        print(f"处理文件: {excel_file.name}")

        try:
            # 读取Excel文件的所有工作表
            excel_data = pd.read_excel(excel_file, sheet_name=None)
            print(f"  找到 {len(excel_data)} 个工作表")

            # 处理每个工作表
            for sheet_name, df in excel_data.items():
                print(f"  处理工作表: '{sheet_name}' ({len(df)} 行数据)")

                # 检查是否包含movie列
                if 'movie' not in df.columns:
                    print(f"    警告: 工作表 '{sheet_name}' 中未找到 'movie' 列，跳过处理")
                    continue

                # 处理该工作表的数据
                processed_df = process_single_dataframe(df, excel_file.name, sheet_name)
                all_processed_data.append(processed_df)

        except Exception as e:
            print(f"  处理文件 '{excel_file.name}' 时出错: {str(e)}")

    return all_processed_data


def merge_movie_data(processed_dataframes):
    """
    基于movie列合并所有处理后的数据框
    """
    if not processed_dataframes:
        print("没有可合并的数据框")
        return pd.DataFrame()

    print(f"开始合并 {len(processed_dataframes)} 个数据源")

    # 使用reduce函数逐步合并所有数据框
    def merge_two_dfs(df1, df2):
        """
        合并两个数据框的辅助函数
        """
        # 基于movie列进行外连接，确保所有movie都被保留
        return pd.merge(df1, df2, on='movie', how='outer')

    # 从第一个数据框开始逐步合并
    final_data = reduce(merge_two_dfs, processed_dataframes)

    print(f"合并完成，共 {len(final_data)} 个电影")
    return final_data


def process_movie_data(folder_path, output_file="processed_movie_data.csv"):
    """
    主处理函数：处理所有动漫数据并输出结果
    """
    print("=" * 50)
    print("动漫数据处理开始")
    print("=" * 50)

    # 步骤1: 读取和处理所有文件
    print("\n步骤1: 读取和处理所有Excel文件...")
    processed_dfs = read_and_process_all_files(folder_path)

    if not processed_dfs:
        print("未找到任何可处理的数据文件！程序结束。")
        return None

    print(f"成功处理 {len(processed_dfs)} 个数据源")

    # 步骤2: 合并所有处理后的数据
    print("\n步骤2: 基于'movie'列合并所有数据源...")
    final_data = merge_movie_data(processed_dfs)

    if final_data.empty:
        print("合并后的数据为空！程序结束。")
        return None

    # 步骤3: 数据后处理
    print("\n步骤3: 数据后处理...")

    # 按movie名称排序
    final_data = final_data.sort_values('movie').reset_index(drop=True)

    # 处理可能的重复movie记录（取第一个出现的值）
    movie_count_before = len(final_data)
    final_data = final_data.groupby('movie').first().reset_index()
    movie_count_after = len(final_data)

    if movie_count_before != movie_count_after:
        print(f"  处理了 {movie_count_before - movie_count_after} 个重复的动漫记录")

    # 步骤4: 保存结果
    print("\n步骤4: 保存结果...")
    final_data.to_csv(output_file, index=False, encoding='utf-8-sig')

    # 输出摘要信息
    print("\n" + "=" * 50)
    print("处理完成！")
    print("=" * 50)
    print(f"输出文件: {output_file}")
    print(f"唯一动漫数量: {len(final_data)}")
    print(f"总列数: {len(final_data.columns)}")
    print(f"数据形状: {final_data.shape}")

    # 显示列名示例
    print(f"\n列名示例 (前15个):")
    for i, col in enumerate(final_data.columns[:15]):
        print(f"  {i + 1}. {col}")

    if len(final_data.columns) > 15:
        print(f"  ... 还有 {len(final_data.columns) - 15} 个列")

    return final_data


# 使用示例
if __name__ == "__main__":
    # 设置包含Excel文件的文件夹路径
    data_folder = "D:/2025.10_animeproject\movie_process"  # 请修改为您的Excel文件所在文件夹路径

    # 设置输出文件名
    output_filename = "final_movie_data.csv"

    # 执行处理
    result = process_movie_data(data_folder, output_filename)

    # 显示结果摘要
    if result is not None:
        print("\n结果摘要:")
        print(result.head())