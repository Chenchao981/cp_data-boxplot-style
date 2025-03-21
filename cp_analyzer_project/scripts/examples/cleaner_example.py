#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据清洗模块使用示例

展示如何使用数据清洗模块对CP测试数据进行清洗
"""

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt

# 添加项目路径，以便导入项目模块
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(project_root, 'scripts'))

from data_cleaner import (
    CPDataCleanerFactory, 
    SmartParameterCleanerStrategy, 
    RemoveOutliersStrategy
)

def simple_example():
    """
    简单使用示例
    """
    # 数据目录路径
    data_dir = os.path.join(project_root, 'data', 'data2', 'rawdata')
    
    # 输出目录路径
    output_dir = os.path.join(project_root, 'output', 'cleaner_example')
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 目标参数
    target_params = ["BVDSS1", "BVDSS2", "IDSS1", "VTH"]
    
    # 创建数据清洗器
    print(f"创建数据清洗器: CPLogCleaner")
    cleaner = CPDataCleanerFactory.create_cleaner('cp_log', target_params, output_dir)
    
    # 加载数据
    print(f"加载数据: {data_dir}")
    cleaner.load_data(data_dir)
    
    # 执行数据清洗
    print("执行数据清洗...")
    df_clean = cleaner.clean()
    
    # 导出JSON数据
    print("导出JSON数据...")
    export_paths = cleaner.export_json(export_by_param=True)
    
    # 打印导出路径
    for param, path in export_paths.items():
        print(f"参数 {param} 的JSON数据已导出到: {path}")
    
    # 打印清洗结果
    print(f"\n清洗后的数据记录数: {len(df_clean)}")
    print(f"数据字段: {df_clean.columns.tolist()}")
    
    return df_clean

def advanced_example():
    """
    高级使用示例，展示不同清洗策略
    """
    # 数据目录路径
    data_dir = os.path.join(project_root, 'data', 'data2', 'rawdata')
    
    # 输出目录路径
    output_dir = os.path.join(project_root, 'output', 'cleaner_advanced_example')
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 目标参数
    target_params = ["BVDSS1", "IDSS1"]
    
    # 创建数据清洗器
    print(f"创建数据清洗器: CPLogCleaner")
    cleaner = CPDataCleanerFactory.create_cleaner('cp_log', target_params, output_dir)
    
    # 加载数据
    print(f"加载数据: {data_dir}")
    cleaner.load_data(data_dir)
    
    # 1. 标准清洗策略
    print("\n1. 使用标准清洗策略")
    df_standard = cleaner.clean()
    print(f"标准清洗后的数据记录数: {len(df_standard)}")
    
    # 2. 使用移除异常值策略
    print("\n2. 使用移除异常值策略")
    outlier_strategy = RemoveOutliersStrategy(std_threshold=2.5)
    df_outlier = cleaner.apply_cleaner_strategy(outlier_strategy)
    print(f"异常值清洗后的数据记录数: {len(df_outlier)}")
    
    # 3. 使用智能参数清洗策略
    print("\n3. 使用智能参数清洗策略")
    smart_strategy = SmartParameterCleanerStrategy()
    df_smart = cleaner.apply_cleaner_strategy(smart_strategy)
    print(f"智能清洗后的数据记录数: {len(df_smart)}")
    
    # 对比不同策略的结果
    compare_strategies(df_standard, df_outlier, df_smart, output_dir)
    
    return {
        'standard': df_standard,
        'outlier': df_outlier,
        'smart': df_smart
    }

def compare_strategies(df_standard, df_outlier, df_smart, output_dir):
    """
    对比不同清洗策略的结果
    
    Args:
        df_standard: 标准清洗策略结果
        df_outlier: 异常值清洗策略结果
        df_smart: 智能参数清洗策略结果
        output_dir: 输出目录
    """
    # 确保每个DataFrame都有BVDSS1列
    if 'BVDSS1' not in df_standard.columns or 'BVDSS1' not in df_outlier.columns or 'BVDSS1' not in df_smart.columns:
        print("错误: 缺少BVDSS1列，无法进行对比")
        return
    
    # 设置图表大小
    plt.figure(figsize=(15, 10))
    
    # 绘制直方图
    plt.subplot(2, 1, 1)
    plt.hist(df_standard['BVDSS1'].dropna(), bins=50, alpha=0.5, label='标准清洗')
    plt.hist(df_outlier['BVDSS1'].dropna(), bins=50, alpha=0.5, label='异常值清洗')
    plt.hist(df_smart['BVDSS1'].dropna(), bins=50, alpha=0.5, label='智能清洗')
    plt.title('BVDSS1参数分布对比')
    plt.xlabel('BVDSS1')
    plt.ylabel('频数')
    plt.legend()
    
    # 绘制箱型图
    plt.subplot(2, 1, 2)
    data = [
        df_standard['BVDSS1'].dropna(),
        df_outlier['BVDSS1'].dropna(),
        df_smart['BVDSS1'].dropna()
    ]
    plt.boxplot(data, labels=['标准清洗', '异常值清洗', '智能清洗'])
    plt.title('BVDSS1参数箱型图对比')
    plt.ylabel('BVDSS1')
    
    # 保存图表
    output_path = os.path.join(output_dir, 'strategy_comparison.png')
    plt.tight_layout()
    plt.savefig(output_path)
    
    print(f"策略对比图已保存到: {output_path}")
    
    # 统计异常值标记
    outlier_columns = [col for col in df_smart.columns if 'outlier' in col or 'spec' in col]
    
    print("\n异常值标记统计:")
    for col in outlier_columns:
        if col in df_smart.columns:
            count = df_smart[col].sum()
            print(f"{col}: {count}个异常值")

if __name__ == '__main__':
    # 简单示例
    print("="*50)
    print("简单清洗示例")
    print("="*50)
    df = simple_example()
    
    # 高级示例
    print("\n"+"="*50)
    print("高级清洗示例")
    print("="*50)
    results = advanced_example()
    
    print("\n清洗示例运行完成！") 