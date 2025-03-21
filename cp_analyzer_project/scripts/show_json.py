#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
显示JSON文件内容

用于查看JSON文件中的数据和单位信息
"""

import os
import sys
import json
import argparse
import numpy as np

def show_json_content(json_file):
    """
    显示JSON文件内容
    
    Args:
        json_file (str): JSON文件路径
    """
    if not os.path.exists(json_file):
        print(f"错误: 文件 {json_file} 不存在")
        return
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        param = os.path.basename(json_file).split('_')[0]
        print(f"参数: {param}")
        print(f"记录数: {len(data)}")
        
        if len(data) > 0:
            # 显示第一条记录
            first_record = data[0]
            print("\n第一条记录:")
            for key, value in first_record.items():
                print(f"  {key}: {value}")
            
            # 分析LimitU/LimitL
            if "LimitU" in first_record and "LimitL" in first_record:
                print(f"\n参数限制:")
                print(f"  上限(LimitU): {first_record['LimitU']}")
                print(f"  下限(LimitL): {first_record['LimitL']}")
            
            # 分析单位信息
            if "Unit" in first_record:
                print(f"\n单位信息: {first_record['Unit']}")
            
            # 分析数值范围
            values = [item.get(param) for item in data 
                     if item.get(param) is not None and not np.isnan(item.get(param))]
            
            if values:
                print(f"\n数值统计:")
                print(f"  最小值: {min(values)}")
                print(f"  最大值: {max(values)}")
                print(f"  平均值: {sum(values)/len(values)}")
                print(f"  样本数: {len(values)}")
                
                # 数值分布
                print("\n数值分布:")
                
                # RDSON1参数的分布分析
                if param == "RDSON1":
                    # 欧姆范围
                    ohm_values = [v for v in values if v < 1]
                    if ohm_values:
                        print(f"  欧姆范围 (<1): {len(ohm_values)} 条记录 ({len(ohm_values)/len(values)*100:.1f}%)")
                    
                    # 毫欧姆范围
                    mohm_values = [v for v in values if 1 <= v < 1000]
                    if mohm_values:
                        print(f"  毫欧姆范围 (1-1000): {len(mohm_values)} 条记录 ({len(mohm_values)/len(values)*100:.1f}%)")
                    
                    # 微欧姆范围
                    uohm_values = [v for v in values if v >= 1000]
                    if uohm_values:
                        print(f"  微欧姆范围 (>=1000): {len(uohm_values)} 条记录 ({len(uohm_values)/len(values)*100:.1f}%)")
                
                # 电流参数的分布分析
                elif param in ["IDSS1", "IDSS2", "IGSS2", "IGSSR2", "IDSS3"]:
                    # 安培范围
                    a_values = [v for v in values if v < 1e-6]
                    if a_values:
                        print(f"  安培范围 (<1e-6): {len(a_values)} 条记录 ({len(a_values)/len(values)*100:.1f}%)")
                    
                    # 微安/毫安范围
                    ua_values = [v for v in values if 1e-6 <= v < 1e-3]
                    if ua_values:
                        print(f"  微安/毫安范围 (1e-6 - 1e-3): {len(ua_values)} 条记录 ({len(ua_values)/len(values)*100:.1f}%)")
                    
                    # 纳安范围
                    na_values = [v for v in values if v >= 1e-3]
                    if na_values:
                        print(f"  纳安范围 (>=1e-3): {len(na_values)} 条记录 ({len(na_values)/len(values)*100:.1f}%)")
            
    except Exception as e:
        print(f"读取文件 {json_file} 时出错: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description="显示JSON文件内容")
    parser.add_argument("json_file", type=str, help="JSON文件路径")
    
    args = parser.parse_args()
    
    show_json_content(args.json_file)

if __name__ == "__main__":
    main() 