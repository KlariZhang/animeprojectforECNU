# -*- coding: utf-8 -*-
"""
Created on Tue Oct  7 12:16:02 2025

@author: HP
"""

"""
二级指标权重计算模块
使用PCA方法为每个一级指标下的二级指标计算权重
"""

import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import config

def calculate_second_level_weights(second_level_scores):
    """
    计算二级指标权重并计算一级指标综合得分
    
    参数:
    second_level_scores: 包含所有二级指标得分的DataFrame
    
    返回:
    second_weights: 二级指标权重字典
    first_level_scores: 一级指标综合得分DataFrame
    """
    
    # 存储二级指标权重
    second_weights = {}
    # 存储一级指标得分
    first_level_scores = pd.DataFrame()
    first_level_scores['anime'] = second_level_scores['anime']
    
    # 获取所有一级指标
    first_levels = config.get_all_first_levels()
    
    for first_code in first_levels:
        # 获取该一级指标下的所有二级指标
        second_codes = config.get_second_level_by_first(first_code)
        
        if len(second_codes) == 0:
            print(f"警告: 一级指标 {first_code} 下没有二级指标")
            continue
            
        # 检查数据列是否存在
        valid_second_codes = []
        for second_code in second_codes:
            if second_code in second_level_scores.columns:
                valid_second_codes.append(second_code)
            else:
                print(f"警告: 二级指标 {second_code} 得分数据不存在")
        
        if len(valid_second_codes) < 2:
            print(f"警告: 一级指标 {first_code} 下有效指标少于2个，无法进行PCA，使用等权重")
            if len(valid_second_codes) == 1:
                # 只有一个指标，权重为1
                second_weights[valid_second_codes[0]] = 1.0
                # 直接使用该指标作为一级指标得分
                first_level_scores[first_code] = second_level_scores[valid_second_codes[0]]
            continue
        
        # 提取数据
        X = second_level_scores[valid_second_codes].values
        
        # 标准化数据
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # 进行PCA分析
        pca = PCA()
        pca.fit(X_scaled)
        
        # 使用第一主成分的绝对值作为权重
        weights = np.abs(pca.components_[0])
        # 归一化权重
        weights = weights / np.sum(weights)
        
        # 存储权重
        for i, second_code in enumerate(valid_second_codes):
            second_weights[second_code] = weights[i]
        
        # 计算一级指标综合得分
        first_score = np.zeros(len(second_level_scores))
        for i, second_code in enumerate(valid_second_codes):
            first_score += second_level_scores[second_code].values * weights[i]
        
        first_level_scores[first_code] = first_score
        
        print(f"一级指标 {first_code} PCA完成:")
        print(f"  各指标权重: {dict(zip(valid_second_codes, weights))}")
        print(f"  第一主成分方差解释率: {pca.explained_variance_ratio_[0]:.4f}")
    
    return second_weights, first_level_scores

if __name__ == "__main__":
    # 测试代码
    print("二级指标权重计算模块")