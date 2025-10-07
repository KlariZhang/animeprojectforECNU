# -*- coding: utf-8 -*-
"""
Created on Tue Oct  7 12:16:02 2025

@author: HP
"""

"""
一级指标权重计算模块
使用熵权法为一级指标计算权重
"""

import pandas as pd
import numpy as np
import config

def entropy_weight_method(data):
    """
    熵权法计算权重
    
    参数:
    data: 二维数组，每行代表一个样本，每列代表一个指标
    
    返回:
    weights: 各指标的权重
    """
    
    # 数据标准化（确保没有负值和零值）
    data = np.array(data)
    # 避免除零错误，给一个很小的偏移量
    data = data - np.min(data, axis=0) + 1e-10
    
    # 计算每个样本在每个指标下的比重
    p = data / np.sum(data, axis=0)
    
    # 计算每个指标的熵值
    e = -np.sum(p * np.log(p), axis=0) / np.log(len(data))
    
    # 计算差异系数
    d = 1 - e
    
    # 计算权重
    weights = d / np.sum(d)
    
    return weights

def calculate_first_level_weights(first_level_scores):
    """
    使用熵权法计算一级指标权重
    
    参数:
    first_level_scores: 包含所有一级指标得分的DataFrame
    
    返回:
    first_weights: 一级指标权重字典
    """
    
    # 获取一级指标列（排除'anime'列）
    first_columns = [col for col in first_level_scores.columns if col != 'anime']
    
    if len(first_columns) < 2:
        print("警告: 一级指标数量少于2个，无法进行熵权法计算")
        if len(first_columns) == 1:
            return {first_columns[0]: 1.0}
        else:
            return {}
    
    # 提取数据
    data = first_level_scores[first_columns].values
    
    # 使用熵权法计算权重
    weights = entropy_weight_method(data)
    
    # 创建权重字典
    first_weights = dict(zip(first_columns, weights))
    
    print("一级指标熵权法计算完成:")
    for first_code, weight in first_weights.items():
        print(f"  指标 {first_code} 权重: {weight:.4f}")
    
    return first_weights

if __name__ == "__main__":
    # 测试代码
    print("一级指标权重计算模块")