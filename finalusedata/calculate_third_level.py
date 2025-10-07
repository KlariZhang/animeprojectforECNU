# -*- coding: utf-8 -*-
"""
Created on Tue Oct  7 12:16:01 2025

@author: HP
"""

"""
三级指标权重计算模块
使用PCA方法为每个二级指标下的三级指标计算权重
"""

import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import config

def calculate_third_level_weights(df):
    """
    计算三级指标权重并计算二级指标综合得分
    
    参数:
    df: 包含所有三级指标原始数据的DataFrame，数据已归一化到[0,1]
    
    返回:
    third_weights: 三级指标权重字典
    second_level_scores: 二级指标综合得分DataFrame
    """
    
    # 存储三级指标权重
    third_weights = {}
    # 存储二级指标得分
    second_level_scores = pd.DataFrame()
    second_level_scores['anime'] = df['anime']
    
    # 获取所有二级指标
    second_levels = config.get_all_second_levels()
    
    for second_code in second_levels:
        # 获取该二级指标下的所有三级指标
        third_codes = config.get_third_level_by_second(second_code)
        
        if len(third_codes) == 0:
            print(f"警告: 二级指标 {second_code} 下没有三级指标")
            continue
            
        # 提取对应的数据列
        data_columns = []
        valid_third_codes = []
        
        for third_code in third_codes:
            col_name = config.THIRD_LEVEL_COLUMNS[third_code]
            if col_name in df.columns:
                data_columns.append(col_name)
                valid_third_codes.append(third_code)
            else:
                print(f"警告: 数据列 {col_name} 不存在，跳过三级指标 {third_code}")
        
        if len(data_columns) < 2:
            print(f"警告: 二级指标 {second_code} 下有效指标少于2个，无法进行PCA，使用等权重")
            if len(data_columns) == 1:
                # 只有一个指标，权重为1
                third_weights[valid_third_codes[0]] = 1.0
                # 直接使用该指标作为二级指标得分
                second_level_scores[second_code] = df[data_columns[0]]
            continue
        
        # 提取数据并标准化
        X = df[data_columns].values
        # 数据已经归一化到[0,1]，这里使用StandardScaler确保均值为0，方差为1，有利于PCA
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # 进行PCA分析
        pca = PCA()
        pca.fit(X_scaled)
        
        # 使用第一主成分的绝对值作为权重（确保权重为正）
        weights = np.abs(pca.components_[0])
        # 归一化权重
        weights = weights / np.sum(weights)
        
        # 存储权重
        for i, third_code in enumerate(valid_third_codes):
            third_weights[third_code] = weights[i]
        
        # 计算二级指标综合得分（使用原始归一化数据，不是标准化后的数据）
        second_score = np.zeros(len(df))
        for i, col in enumerate(data_columns):
            second_score += df[col].values * weights[i]
        
        second_level_scores[second_code] = second_score
        
        print(f"二级指标 {second_code} PCA完成:")
        print(f"  各指标权重: {dict(zip(valid_third_codes, weights))}")
        print(f"  第一主成分方差解释率: {pca.explained_variance_ratio_[0]:.4f}")
    
    return third_weights, second_level_scores

if __name__ == "__main__":
    # 测试代码
    print("三级指标权重计算模块")