#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
基于提示词"rawdata提示词.md"生成的代码逻辑
晶圆厂CP测试数据分析工具主程序
支持多批次分析功能
"""

import os
import sys
import argparse
from log_parser import CPLogParser
from data_cleaner import CPDataCleanerFactory, SmartParameterCleanerStrategy, RemoveOutliersStrategy
from data_analyzer import CPDataAnalyzer
from chart_generator import CPChartGenerator
from html_report import CPHTMLReport
import pandas as pd
from datetime import datetime

def parse_args():
    """
    解析命令行参数
    
    Returns:
        Namespace: 参数命名空间
    """
    parser = argparse.ArgumentParser(description='晶圆厂CP测试数据分析工具')
    
    # 外部数据目录
    external_data_dir = "E:\\data\\rawdata"
    
    parser.add_argument('--data-dir', type=str, default=external_data_dir,
                        help='数据目录路径 (默认: E:\\data\\rawdata)')
    
    parser.add_argument('--output-dir', type=str, default='./output',
                        help='输出目录路径 (默认: ./output)')
    
    parser.add_argument('--params', type=str, nargs='+',
                        default=["BVDSS1", "BVDSS2", "DELTABV", "IDSS1", "VTH", 
                                "RDSON1", "VFSDS", "IGSS2", "IGSSR2", "IDSS2"],
                        help='要分析的参数列表')
                        
    parser.add_argument('--export-json', action='store_true', default=True,
                        help='是否导出JSON格式数据 (默认: True)')
                        
    parser.add_argument('--cleaner-strategy', type=str, default='standard',
                        choices=['standard', 'smart', 'remove_outliers'],
                        help='数据清洗策略 (默认: standard)')
    
    return parser.parse_args()

def process_batch(batch_dir, output_dir, args):
    """
    处理单个批次的数据
    
    Args:
        batch_dir (str): 批次数据目录
        output_dir (str): 输出目录
        args (Namespace): 命令行参数
        
    Returns:
        bool: 处理是否成功
    """
    batch_name = os.path.basename(batch_dir)
    print(f"\n处理批次: {batch_name}")
    
    # 创建批次特定的输出目录
    batch_output_dir = os.path.join(output_dir, batch_name)
    json_output_dir = os.path.join(batch_output_dir, 'json')
    
    # 确保输出目录存在
    if not os.path.exists(batch_output_dir):
        os.makedirs(batch_output_dir)
    
    # 确保JSON输出目录存在
    if not os.path.exists(json_output_dir):
        os.makedirs(json_output_dir)
    
    # 步骤1: 创建数据清洗器并加载数据
    print("\n步骤1: 加载CP测试数据...")
    cleaner = CPDataCleanerFactory.create_cleaner('cp_log', args.params, batch_output_dir)
    
    if not cleaner.load_data(batch_dir):
        print(f"错误: 未能成功加载批次 {batch_name} 的CP测试数据")
        return False
        
    # 步骤2: 选择清洗策略并执行数据清洗
    print("\n步骤2: 数据清洗...")
    
    if args.cleaner_strategy == 'smart':
        print("使用智能参数清洗策略")
        strategy = SmartParameterCleanerStrategy()
        df_clean = cleaner.apply_cleaner_strategy(strategy)
        cleaner.clean_data = df_clean
    elif args.cleaner_strategy == 'remove_outliers':
        print("使用移除异常值清洗策略")
        strategy = RemoveOutliersStrategy(std_threshold=3.0)
        df_clean = cleaner.apply_cleaner_strategy(strategy)
        cleaner.clean_data = df_clean
    else:
        print("使用标准清洗策略")
        df_clean = cleaner.clean()
    
    if df_clean is None:
        print(f"错误: 批次 {batch_name} 数据清洗失败")
        return False
        
    print(f"清洗后的数据记录数: {len(df_clean)}")
    
    # 步骤3: 导出JSON数据（如果需要）
    if args.export_json:
        print("\n步骤3: 导出JSON数据...")
        # 设置JSON输出目录
        cleaner.output_dir = json_output_dir
        export_paths = cleaner.export_json(export_by_param=True)
        if export_paths:
            print(f"JSON数据已导出到: {json_output_dir}")
            print(f"导出的参数: {', '.join(export_paths.keys())}")
    
    # 步骤4: 数据分析
    print("\n步骤4: 数据分析...")
    analyzer = CPDataAnalyzer(None, args.params, cleaner.get_limits())
    analyzer.df_clean = df_clean
    
    # 步骤5: 生成图表
    print("\n步骤5: 生成图表...")
    chart_generator = CPChartGenerator(analyzer)
    chart_generator.output_dir = batch_output_dir
    
    # 步骤6: 生成HTML报告
    print("\n步骤6: 生成HTML报告...")
    report_generator = CPHTMLReport(chart_generator)
    report_generator.output_dir = batch_output_dir  # 设置批次特定的输出目录
    
    # 生成所有报告
    index_path = report_generator.generate_all_reports()
    
    if index_path is None:
        print(f"错误: 生成批次 {batch_name} 的HTML报告失败")
        return False
        
    print(f"\n批次 {batch_name} 分析完成!")
    print(f"HTML报告已生成: {index_path}")
    
    return True

def main():
    """
    主函数
    """
    # 解析命令行参数
    args = parse_args()
    
    # 获取数据目录的绝对路径
    data_dir = os.path.abspath(args.data_dir)
    
    # 获取输出目录的绝对路径
    output_dir = os.path.abspath(args.output_dir)
    
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print(f"数据目录: {data_dir}")
    print(f"输出目录: {output_dir}")
    print(f"目标参数: {args.params}")
    print(f"清洗策略: {args.cleaner_strategy}")
    
    # 获取所有批次目录
    try:
        batch_dirs = [d for d in os.listdir(data_dir) 
                    if os.path.isdir(os.path.join(data_dir, d))]
    except Exception as e:
        print(f"错误: 读取数据目录 {data_dir} 时出错: {str(e)}")
        print("尝试使用备用方法...")
        try:
            # 尝试直接列出指定目录
            batch_dirs = []
            for item in ["NCEHSM650PBA_C127251.00@CP", "NCEHSM700TCB_C146419.00@CP", 
                          "NCESF600RAA_FA51-3283@203", "NCESM650QAA_FA49-2230@203"]:
                full_path = os.path.join(data_dir, item)
                if os.path.isdir(full_path):
                    batch_dirs.append(item)
        except Exception as e2:
            print(f"备用方法也失败: {str(e2)}")
            return 1
    
    if not batch_dirs:
        print(f"错误: 在 {data_dir} 中没有找到批次目录")
        return 1
    
    print(f"\n找到 {len(batch_dirs)} 个批次目录:")
    for batch_dir in batch_dirs:
        print(f"- {batch_dir}")
    
    # 处理每个批次
    success_count = 0
    batch_info = {}  # 收集批次信息
    
    for batch_dir in batch_dirs:
        batch_path = os.path.join(data_dir, batch_dir)
        
        # 记录处理时间
        process_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 收集批次基本信息
        batch_info[batch_dir] = {
            'process_time': process_time,
            'lot_number': '未知',  # 将在处理过程中更新
            'wafer_count': 0,
            'record_count': 0,
            'param_count': len(args.params)
        }
        
        if process_batch(batch_path, output_dir, args):
            success_count += 1
            
            # 更新批次信息
            try:
                # 尝试从JSON文件中读取批次信息
                json_dir = os.path.join(output_dir, batch_dir, 'json')
                if os.path.exists(json_dir):
                    json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]
                    if json_files:
                        # 读取第一个JSON文件获取批次号和晶圆数量
                        import json
                        with open(os.path.join(json_dir, json_files[0]), 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if data and isinstance(data, list) and len(data) > 0:
                                # 获取记录数
                                batch_info[batch_dir]['record_count'] = len(data)
                                
                                # 获取批次号
                                if 'Lot' in data[0]:
                                    batch_info[batch_dir]['lot_number'] = data[0]['Lot']
                                
                                # 获取晶圆数量 (独特的晶圆编号数量)
                                if 'Wafer' in data[0]:
                                    wafers = set(record['Wafer'] for record in data if 'Wafer' in record)
                                    batch_info[batch_dir]['wafer_count'] = len(wafers)
            except Exception as e:
                print(f"警告: 收集批次 {batch_dir} 信息时出错: {str(e)}")
    
    # 生成批次索引页面
    try:
        # 创建一个空的图表生成器用于生成索引页面
        empty_analyzer = CPDataAnalyzer(None, args.params, {})
        # 设置必要的属性，避免NoneType错误
        empty_analyzer.df_clean = pd.DataFrame()
        empty_analyzer.df_clean['dummy'] = []  # 添加一个空列
        empty_analyzer.target_params = args.params
        
        empty_chart_generator = CPChartGenerator(empty_analyzer)
        empty_chart_generator.output_dir = output_dir
        report_generator = CPHTMLReport(empty_chart_generator)
        report_generator.output_dir = output_dir
        
        # 生成批次索引页面
        index_path = report_generator.generate_batch_index(batch_dirs, batch_info)
        if index_path:
            print(f"\n批次索引页面已生成: {index_path}")
            import webbrowser
            webbrowser.open(f"file://{index_path}")
    except Exception as e:
        print(f"警告: 生成批次索引页面时出错: {str(e)}")
        print(f"错误详情: {e.__class__.__name__}")
        import traceback
        traceback.print_exc()
    
    print(f"\n分析完成! 成功处理 {success_count}/{len(batch_dirs)} 个批次")
    return 0 if success_count > 0 else 1

if __name__ == '__main__':
    sys.exit(main())