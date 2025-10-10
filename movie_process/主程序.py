# -*- coding: utf-8 -*-
"""
Created on Tue Oct  7 12:16:00 2025

@author: HP
"""

"""
主程序 - 动漫指标体系权重计算
协调三级、二级、一级指标权重的计算流程，并生成可视化结果
"""

import pandas as pd
import numpy as np
from calculate_third_level import calculate_third_level_weights
from calculate_second_level import calculate_second_level_weights
from calculate_first_level import calculate_first_level_weights
from visualization import create_radar_chart, generate_detailed_report
import config

def main():
    """
    主函数：执行完整的权重计算流程
    """
    
    print("开始动漫指标体系权重计算...")
    
    # 1. 读取数据
    # 请根据实际数据路径修改
    try:
        # 这里假设您的数据文件名为 'anime_data.csv'
        df = pd.read_csv('anime_data.csv')
        print(f"数据读取成功，共 {len(df)} 条记录")
        
        # 显示数据基本信息
        print(f"数据列: {list(df.columns)}")
        print(f"前3行数据预览:")
        print(df.head(3))
        
    except FileNotFoundError:
        print("数据文件未找到，请确保 'anime_data.csv' 文件存在")
        print("正在创建示例数据文件以供测试...")
        create_sample_data()
        df = pd.read_csv('anime_data.csv')
    
    # 检查必要的列是否存在
    if 'anime' not in df.columns:
        print("错误: 数据中缺少 'anime' 列")
        return
    
    # 2. 计算三级指标权重和二级指标得分
    print("\n" + "="*50)
    print("开始计算三级指标权重")
    print("="*50)
    third_weights, second_scores = calculate_third_level_weights(df)
    
    # 保存三级指标权重
    pd.Series(third_weights).to_csv('output/third_level_weights.csv', header=True)
    print("三级指标权重已保存到 'output/third_level_weights.csv'")
    
    # 保存二级指标得分
    second_scores.to_csv('output/second_level_scores.csv', index=False)
    print("二级指标得分已保存到 'output/second_level_scores.csv'")
    
    # 3. 计算二级指标权重和一级指标得分
    print("\n" + "="*50)
    print("开始计算二级指标权重")
    print("="*50)
    second_weights, first_scores = calculate_second_level_weights(second_scores)
    
    # 保存二级指标权重
    pd.Series(second_weights).to_csv('output/second_level_weights.csv', header=True)
    print("二级指标权重已保存到 'output/second_level_weights.csv'")
    
    # 保存一级指标得分
    first_scores.to_csv('output/first_level_scores.csv', index=False)
    print("一级指标得分已保存到 'output/first_level_scores.csv'")
    
    # 4. 计算一级指标权重
    print("\n" + "="*50)
    print("开始计算一级指标权重")
    print("="*50)
    first_weights = calculate_first_level_weights(first_scores)
    
    # 保存一级指标权重
    pd.Series(first_weights).to_csv('output/first_level_weights.csv', header=True)
    print("一级指标权重已保存到 'output/first_level_weights.csv'")
    
    # 5. 计算最终综合得分
    print("\n" + "="*50)
    print("计算最终综合得分")
    print("="*50)
    final_scores = pd.DataFrame()
    final_scores['anime'] = first_scores['anime']
    
    # 使用一级指标权重计算最终综合得分
    final_score = np.zeros(len(first_scores))
    for first_code, weight in first_weights.items():
        final_score += first_scores[first_code].values * weight
    
    final_scores['final_score'] = final_score
    final_scores = final_scores.sort_values('final_score', ascending=False)
    
    # 保存最终得分
    final_scores.to_csv('output/final_scores.csv', index=False)
    print("最终综合得分已保存到 'output/final_scores.csv'")
    
    # 6. 生成可视化结果和详细报告
    print("\n" + "="*50)
    print("生成可视化结果和报告")
    print("="*50)
    
    # 绘制雷达图
    create_radar_chart(first_scores, first_weights, top_n=10)
    
    # 生成详细报告
    report_df, weights_df = generate_detailed_report(
        final_scores, first_scores, second_scores,
        first_weights, second_weights, third_weights,
        top_n=20
    )
    
    # 7. 输出最终结果摘要
    print("\n" + "="*50)
    print("权重计算完成 - 结果摘要")
    print("="*50)
    
    print("\n一级指标权重:")
    for first_code, weight in first_weights.items():
        name = config.FIRST_LEVEL_NAMES.get(first_code, first_code)
        print(f"  {name}: {weight:.4f}")
    
    print(f"\n所有输出文件已保存到 'output' 目录")
    print("包括: 各级权重、得分文件、雷达图、详细排名报告")

def create_sample_data():
    """
    创建示例数据文件用于测试
    """
    import numpy as np
    import pandas as pd
    
    # 创建示例动漫数据
    np.random.seed(42)  # 确保可重复性
    n_animes = 50
    
    # 动漫名称列表
    anime_names = [f"动漫{i:02d}" for i in range(1, n_animes + 1)]
    
    # 创建DataFrame
    df = pd.DataFrame()
    df['anime'] = anime_names
    
    # 为每个三级指标生成随机数据（0-1之间）
    for third_code, col_name in config.THIRD_LEVEL_COLUMNS.items():
        # 处理复合指标（如追番人数/播放比）
        if '/' in col_name or '+' in col_name:
            # 对于比率或求和指标，确保数值合理
            if 'followers' in col_name and 'play_count' in col_name:
                # 追番人数/播放比，应该是较小的值
                df[col_name] = np.random.uniform(0.01, 0.2, n_animes)
            elif 'comment_count' in col_name and 'review_count' in col_name:
                # 评论数，可以稍大一些
                df[col_name] = np.random.uniform(0.1, 0.8, n_animes)
        else:
            # 普通指标
            df[col_name] = np.random.uniform(0, 1, n_animes)
    
    # 保存示例数据
    df.to_csv('anime_data.csv', index=False)
    print("示例数据文件 'anime_data.csv' 已创建")

if __name__ == "__main__":
    main()