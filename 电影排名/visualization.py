# -*- coding: utf-8 -*-
"""
Created on Tue Oct  7 12:16:02 2025

@author: HP
"""

"""
可视化模块
绘制雷达图和生成最终评分报告
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
from matplotlib.font_manager import FontProperties
import config

# 设置中文字体
try:
    # 尝试使用系统中文字体
    font = FontProperties(fname='/System/Library/Fonts/PingFang.ttc')  # macOS
except:
    try:
        font = FontProperties(fname='C:/Windows/Fonts/simhei.ttf')  # Windows
    except:
        font = FontProperties()  # 使用默认字体


def create_radar_chart(final_scores, first_level_scores, first_weights, top_n=10):
    """
    为前N名动漫创建雷达图

    参数:
    final_scores: 最终得分DataFrame
    first_level_scores: 一级指标得分DataFrame
    first_weights: 一级指标权重字典
    top_n: 显示前多少名动漫
    """
    # 确保输出目录存在
    os.makedirs('output', exist_ok=True)

    # 获取前N名动漫
    top_animes = final_scores.nlargest(top_n, 'final_score')

    # 准备雷达图数据 - 使用一级指标名称
    categories = list(config.FIRST_LEVEL_NAMES.values())
    N = len(categories)

    # 计算角度
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]  # 闭合图形

    # 创建雷达图
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))

    # 为每个动漫绘制雷达图
    colors = plt.cm.tab10(np.linspace(0, 1, min(top_n, 10)))

    for i, (idx, row) in enumerate(top_animes.iterrows()):
        anime_name = row['anime']
        values = []

        for first_code in config.FIRST_LEVEL_NAMES.keys():
            # 获取该动漫在该一级指标上的得分
            anime_row = first_level_scores[first_level_scores['anime'] == anime_name]
            if not anime_row.empty:
                # 使用原始得分，不应用权重（权重已经在计算final_score时应用）
                score = anime_row[first_code].iloc[0]
                values.append(score)
            else:
                values.append(0)

        # 闭合图形
        values += values[:1]

        # 绘制线条
        ax.plot(angles, values, 'o-', linewidth=2,
                label=f'{anime_name} ({row["final_score"]:.3f})',
                color=colors[i % len(colors)])
        ax.fill(angles, values, alpha=0.1, color=colors[i % len(colors)])

    # 设置类别标签
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontproperties=font)

    # 设置y轴标签
    ax.set_ylim(0, 1)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'])

    # 添加标题和图例
    plt.title(f'前{top_n}名动漫指标雷达图', size=16, fontproperties=font, pad=20)
    plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0), prop=font)

    # 保存图片
    plt.tight_layout()
    plt.savefig('output/top_movies_radar.png', dpi=300, bbox_inches='tight')
    plt.savefig('output/top_movies_radar.pdf', bbox_inches='tight')
    plt.show()

    print(f"雷达图已保存到 output/top_movies_radar.png 和 output/top_movies_radar.pdf")


def generate_detailed_report(final_scores, first_level_scores, second_level_scores,
                             first_weights, second_weights, third_weights, top_n=20):
    """
    生成详细的评分报告 - 修复版
    """
    # 确保输出目录存在
    os.makedirs('output', exist_ok=True)

    # 创建详细报告
    report_data = []

    # 获取前N名动漫的名单
    top_animes = final_scores.head(top_n)['anime'].tolist()

    # 预先筛选一级指标得分数据
    first_scores_filtered = first_level_scores[first_level_scores['anime'].isin(top_animes)]

    for i, anime_name in enumerate(top_animes, 1):
        # 获取该动漫的最终得分
        final_score = final_scores[final_scores['anime'] == anime_name]['final_score'].values[0]

        # 获取一级指标得分
        first_scores = {}
        anime_scores = first_scores_filtered[first_scores_filtered['anime'] == anime_name]

        if not anime_scores.empty:
            for first_code in config.FIRST_LEVEL_NAMES.keys():
                score = anime_scores[first_code].values[0]
                first_scores[config.FIRST_LEVEL_NAMES[first_code]] = score
        else:
            for first_code in config.FIRST_LEVEL_NAMES.keys():
                first_scores[config.FIRST_LEVEL_NAMES[first_code]] = 0

        report_data.append({
            '排名': i,
            '动漫名称': anime_name,
            '综合得分': final_score,
            **first_scores
        })

    # 创建DataFrame并保存 - 现在在循环外部
    report_df = pd.DataFrame(report_data)

    # 确保列顺序一致
    columns_order = ['排名', '动漫名称', '综合得分'] + sorted(
        [config.FIRST_LEVEL_NAMES[code] for code in config.FIRST_LEVEL_NAMES.keys()])
    report_df = report_df[columns_order]

    report_df.to_csv('output/detailed_ranking_report.csv', index=False, encoding='utf-8-sig')

    # 保存权重信息
    weights_data = []
    for level, weights in [('一级指标权重', first_weights),
                          ('二级指标权重', second_weights),
                          ('三级指标权重', third_weights)]:
        for code, weight in weights.items():
            weights_data.append({
                '层级': level,
                '指标代码': code,
                '权重': weight
            })

    weights_df = pd.DataFrame(weights_data)
    weights_df.to_csv('output/weights_report.csv', index=False, encoding='utf-8-sig')

    print(f"\n详细排名报告已生成，包含 {len(report_df)} 条记录")
    print(f"文件已保存到 output/detailed_ranking_report.csv")

    # 在控制台输出前10名
    print(f"\n前{min(10, top_n)}名动漫排名:")
    print("=" * 80)
    for i, row in report_df.head(10).iterrows():
        print(f"{row['排名']:2d}. {row['动漫名称']:20} 综合得分: {row['综合得分']:.4f}")

    return report_df, weights_df

if __name__ == "__main__":
    print("可视化模块")