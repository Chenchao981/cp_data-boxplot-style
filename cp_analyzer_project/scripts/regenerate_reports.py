#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
重新生成HTML报告

在调整JSON数据单位后，使用更新后的数据重新生成HTML报告
"""

import os
import sys
import json
import glob
import argparse
import pandas as pd
from chart_generator import CPChartGenerator
from html_report import CPHTMLReport
from data_analyzer import CPDataAnalyzer

def load_params_data(batch_dir, params):
    """
    加载批次目录下指定参数的JSON数据
    
    Args:
        batch_dir (str): 批次目录路径
        params (list): 参数列表
        
    Returns:
        dict: 参数数据字典，键为参数名称，值为数据DataFrame
    """
    params_data = {}
    json_dir = os.path.join(batch_dir, "json")
    
    # 如果json子目录存在，使用它
    if os.path.exists(json_dir) and os.path.isdir(json_dir):
        json_pattern = os.path.join(json_dir, "*_data.json")
    else:
        # 否则在批次目录中寻找json文件
        json_pattern = os.path.join(batch_dir, "*_data.json")
    
    # 查找所有JSON文件
    json_files = glob.glob(json_pattern)
    
    # 加载指定参数的数据
    for json_file in json_files:
        param = os.path.basename(json_file).split('_')[0]
        
        if params and param not in params:
            continue
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 转换为DataFrame
            df = pd.DataFrame(data)
            params_data[param] = df
            print(f"加载参数 {param} 的JSON数据: {len(df)} 条记录")
        except Exception as e:
            print(f"加载参数 {param} 的JSON数据时出错: {str(e)}")
    
    return params_data

def extract_limits(params_data):
    """
    从参数数据中提取限制值
    
    Args:
        params_data (dict): 参数数据字典
        
    Returns:
        dict: 参数限制字典
    """
    limits = {}
    
    for param, df in params_data.items():
        if 'LimitU' in df.columns and 'LimitL' in df.columns:
            # 获取第一行的限制值
            limit_u = df['LimitU'].iloc[0] if not df['LimitU'].empty else None
            limit_l = df['LimitL'].iloc[0] if not df['LimitL'].empty else None
            
            if limit_u is not None and limit_l is not None:
                limits[param] = {
                    'upper': limit_u,
                    'lower': limit_l
                }
    
    return limits

def regenerate_batch_reports(batch_dir, params=None):
    """
    重新生成批次的HTML报告
    
    Args:
        batch_dir (str): 批次目录路径
        params (list, optional): 要重新生成的参数列表，为空则重新生成所有参数
    """
    batch_name = os.path.basename(batch_dir)
    print(f"\n重新生成批次 {batch_name} 的HTML报告...")
    
    # 加载参数数据
    params_data = load_params_data(batch_dir, params)
    
    if not params_data:
        print(f"警告: 批次 {batch_name} 没有找到JSON数据")
        return False
    
    # 提取限制值
    limits = extract_limits(params_data)
    
    # 合并所有参数数据
    df_merged = None
    for param, df in params_data.items():
        # 确保关键字段存在
        required_fields = ['Lot', 'Wafer', 'No.U']
        if not all(field in df.columns for field in required_fields):
            print(f"警告: 参数 {param} 的数据缺少必要字段")
            continue
        
        # 合并数据
        if df_merged is None:
            df_merged = df[required_fields].copy()
        
        # 添加参数列
        if param in df.columns:
            df_merged[param] = df[param]
    
    if df_merged is None or len(df_merged) == 0:
        print(f"错误: 合并后的数据为空")
        return False
    
    # 创建数据分析器
    analyzer = CPDataAnalyzer(None, list(params_data.keys()), limits)
    analyzer.df_clean = df_merged
    
    # 创建图表生成器
    chart_generator = CPChartGenerator(analyzer)
    chart_generator.output_dir = batch_dir
    
    # 创建HTML报告生成器
    report_generator = CPHTMLReport(chart_generator)
    report_generator.output_dir = batch_dir
    
    # 生成所有报告
    index_path = report_generator.generate_all_reports()
    
    if index_path is None:
        print(f"错误: 生成批次 {batch_name} 的HTML报告失败")
        return False
    
    print(f"\n批次 {batch_name} 的HTML报告已重新生成: {index_path}")
    return True

def regenerate_all_reports(output_dir, batch=None, params=None):
    """
    重新生成所有批次的HTML报告
    
    Args:
        output_dir (str): 输出目录路径
        batch (str, optional): 指定批次名称，为空则处理所有批次
        params (list, optional): 要重新生成的参数列表，为空则重新生成所有参数
    """
    if batch:
        # 处理指定批次
        batch_dir = os.path.join(output_dir, batch)
        if not os.path.exists(batch_dir):
            print(f"错误: 批次目录 {batch_dir} 不存在")
            return
        
        regenerate_batch_reports(batch_dir, params)
    else:
        # 处理所有批次
        batch_dirs = [d for d in os.listdir(output_dir) 
                     if os.path.isdir(os.path.join(output_dir, d)) 
                     and not d.startswith('.') 
                     and d != "static"]
        
        if not batch_dirs:
            print(f"在输出目录 {output_dir} 中未找到批次目录")
            return
        
        print(f"找到 {len(batch_dirs)} 个批次目录")
        
        for batch in batch_dirs:
            batch_dir = os.path.join(output_dir, batch)
            print(f"\n处理批次: {batch}")
            regenerate_batch_reports(batch_dir, params)

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description="重新生成HTML报告")
    parser.add_argument("--output-dir", type=str, default="../output",
                        help="输出目录路径 (默认: ../output)")
    parser.add_argument("--batch", type=str, default=None,
                        help="指定批次名称，为空则处理所有批次")
    parser.add_argument("--params", type=str, nargs='+',
                        default=None,
                        help="要重新生成的参数列表，为空则重新生成所有参数")
    
    args = parser.parse_args()
    
    # 获取输出目录的绝对路径
    output_dir = os.path.abspath(args.output_dir)
    
    if not os.path.exists(output_dir):
        print(f"错误: 输出目录 {output_dir} 不存在")
        return
    
    # 重新生成报告
    regenerate_all_reports(output_dir, args.batch, args.params)
    
    print("\nHTML报告重新生成完成!")

if __name__ == "__main__":
    main() 