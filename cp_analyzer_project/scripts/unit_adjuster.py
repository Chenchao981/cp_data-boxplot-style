#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据单位调整工具

用于调整JSON文件中的数据单位，确保与LimitU的单位保持一致
"""

import os
import json
import glob
import re
import numpy as np
from typing import Dict, List, Any, Tuple

def parse_limit_value(limit_str: str) -> Tuple[float, str]:
    """
    解析限制值字符串，提取数值和单位
    
    Args:
        limit_str (str): 限制值字符串，如 "900.0V" 或 "365.0mOHM"
        
    Returns:
        tuple: (解析后的数值, 单位)
    """
    # 提取数值和单位
    match = re.search(r"([-+]?\d*\.?\d+)([a-zA-Z]+)?", str(limit_str))
    if not match:
        return float(limit_str), ""
    
    value_part, unit_part = match.groups()
    value = float(value_part)
    unit = unit_part.lower() if unit_part else ""
    
    # 标准化单位名称
    # 电阻单位
    if unit in ('ohm', 'Ω', 'ω', 'Ω', 'ohms'):
        unit = 'ohm'
    elif unit in ('mohm', 'mΩ', 'mω', 'mΩ', 'mohms', 'milliohm', 'milliohms'):
        unit = 'mohm'
    # 电压单位
    elif unit in ('v', 'volt', 'volts'):
        unit = 'v'
    elif unit in ('mv', 'mvolt', 'mvolts', 'millivolt', 'millivolts'):
        unit = 'mv'
    # 电流单位
    elif unit in ('a', 'amp', 'amps', 'ampere', 'amperes'):
        unit = 'a'
    elif unit in ('ma', 'mamp', 'mamps', 'milliamp', 'milliamps', 'milliampere', 'milliamperes'):
        unit = 'ma'
    elif unit in ('ua', 'uamp', 'uamps', 'microamp', 'microamps', 'microampere', 'microamperes'):
        unit = 'ua'
    elif unit in ('na', 'namp', 'namps', 'nanoamp', 'nanoamps', 'nanoampere', 'nanoamperes'):
        unit = 'na'
    
    print(f"  解析限制值: {limit_str} -> 值={value}, 单位={unit}")
    return value, unit

def adjust_unit(value: float, param: str, limit_u: Any) -> float:
    """
    根据参数和LimitU调整数据单位
    
    Args:
        value (float): 原始数值
        param (str): 参数名称
        limit_u (Any): 上限值
        
    Returns:
        float: 调整后的数值
    """
    if not value or np.isnan(value):
        return value
        
    limit_value, limit_unit = parse_limit_value(limit_u)
    
    # 电阻参数 - RDSON1
    if param == "RDSON1":
        # 判断LimitU的单位和值：确定目标单位
        # 1. 如果LimitU值大于10，通常是毫欧姆单位
        is_mohm_scale = limit_value > 10 or (limit_unit and 'mohm' in limit_unit.lower())
        
        # 2. 根据value本身进行智能判断
        # 欧姆单位的值通常很小（0.01~1范围内）
        if value < 1.0:
            # 如果目标是毫欧姆，需要转换
            if is_mohm_scale:
                converted_value = value * 1000  # 欧姆转毫欧姆
                print(f"  - RDSON1转换: {value:.6f} 欧姆 -> {converted_value:.2f} 毫欧姆")
                return converted_value
            # 否则保持欧姆单位
            return value
        # 毫欧姆单位的值通常在10~1000范围内
        elif 1.0 <= value < 1000:
            # 如果目标是欧姆，需要转换回欧姆
            if not is_mohm_scale:
                converted_value = value / 1000  # 毫欧姆转欧姆
                print(f"  - RDSON1转换: {value:.2f} 毫欧姆 -> {converted_value:.6f} 欧姆")
                return converted_value
            # 否则保持毫欧姆单位
            return value
        # 超过1000，可能是微欧姆单位
        else:
            # 转换到目标单位
            if is_mohm_scale:
                converted_value = value / 1000  # 微欧姆转毫欧姆
                print(f"  - RDSON1转换: {value:.2f} 微欧姆 -> {converted_value:.2f} 毫欧姆")
                return converted_value
            else:
                converted_value = value / 1000000  # 微欧姆转欧姆
                print(f"  - RDSON1转换: {value:.2f} 微欧姆 -> {converted_value:.6f} 欧姆")
                return converted_value
    
    # 电流参数转换 - IDSS1, IDSS2, IGSS2, IGSSR2
    if param in ("IDSS1", "IDSS2", "IGSS2", "IGSSR2"):
        # 判断LimitU的单位：确定目标单位
        is_na_scale = limit_unit and 'na' in limit_unit.lower()
        
        # 如果值很小（<1e-6），很可能是安培单位
        if value < 1e-6:
            # 如果目标是纳安，需要转换
            if is_na_scale or not limit_unit:
                converted_value = value * 1e9  # 安培转纳安
                print(f"  - {param}转换: {value:.2e} 安培 -> {converted_value:.2f} 纳安")
                return converted_value
            # 否则保持当前单位
            return value
        # 如果值较小（<1e-3），可能是微安单位  
        elif value < 1e-3:
            # 如果目标是纳安，需要转换
            if is_na_scale or not limit_unit:
                converted_value = value * 1000  # 微安转纳安
                print(f"  - {param}转换: {value:.2e} 微安 -> {converted_value:.2f} 纳安")
                return converted_value
            # 否则保持当前单位
            return value
        # 如果值在合理范围内，可能已经是纳安单位
        elif 0.1 <= value <= 1000:
            # 无需转换
            return value
        else:
            return value
    
    # IDSS3 转换为微安 (uA)
    if param == "IDSS3":
        # 判断LimitU的单位：确定目标单位
        is_ua_scale = limit_unit and 'ua' in limit_unit.lower()
        
        # 如果值很小（<1e-6），很可能是安培单位
        if value < 1e-6:
            # 如果目标是微安，需要转换
            if is_ua_scale or not limit_unit:
                converted_value = value * 1e6  # 安培转微安
                print(f"  - IDSS3转换: {value:.2e} 安培 -> {converted_value:.2f} 微安")
                return converted_value
            # 否则保持当前单位
            return value
        # 如果值较小（<1e-3），可能已经是微安单位
        elif 0.1 <= value <= 1000:
            # 无需转换
            return value
        else:
            return value
    
    # 电压参数转换 - VFSDS, BVDSS1, BVDSS2, DELTABV
    if param in ("VFSDS", "BVDSS1", "BVDSS2", "DELTABV"):
        # 判断LimitU的单位：确定目标单位
        is_mv_scale = limit_unit and 'mv' in limit_unit.lower()
        
        # 如果LimitU单位是毫伏，并且当前值较大（看起来是伏特单位）
        if is_mv_scale and value < 10 and limit_value > 100:
            converted_value = value * 1000  # 伏特转毫伏
            print(f"  - {param}转换: {value:.2f} 伏特 -> {converted_value:.2f} 毫伏")
            return converted_value
            
        # 如果LimitU单位是伏特，并且当前值较大（看起来已经是毫伏单位）
        if not is_mv_scale and value > 100 and limit_value < 10:
            converted_value = value / 1000  # 毫伏转伏特
            print(f"  - {param}转换: {value:.2f} 毫伏 -> {converted_value:.2f} 伏特")
            return converted_value
            
        # 判断值的范围是否符合LimitU的范围，如果相差1000倍，可能需要转换
        if limit_value > 0 and value > 0:
            ratio = limit_value / value
            
            # 如果当前值比LimitU小1000倍左右，可能需要转换为毫伏
            if 500 < ratio < 2000 and not is_mv_scale:
                converted_value = value * 1000  # 伏特转毫伏
                print(f"  - {param}转换: {value:.2f} 伏特 -> {converted_value:.2f} 毫伏")
                return converted_value
                
            # 如果当前值比LimitU大1000倍左右，可能需要转换为伏特
            if 0.0005 < ratio < 0.002 and is_mv_scale:
                converted_value = value / 1000  # 毫伏转伏特
                print(f"  - {param}转换: {value:.2f} 毫伏 -> {converted_value:.2f} 伏特")
                return converted_value
        
    return value

def adjust_json_file(json_file: str) -> None:
    """
    调整JSON文件中的数据单位
    
    Args:
        json_file (str): JSON文件路径
    """
    print(f"处理文件: {json_file}")
    
    try:
        # 读取JSON文件
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 获取参数名称
        param = os.path.basename(json_file).split('_')[0]
        
        # 跳过不需要单位转换的参数
        supported_params = [
            "RDSON1", "IDSS1", "IDSS2", "IGSS2", "IGSSR2", "IDSS3",
            "VFSDS", "BVDSS1", "BVDSS2", "DELTABV"
        ]
        
        if param not in supported_params:
            print(f"跳过参数 {param}，不需要单位转换")
            return
        
        # 调整数据单位
        modified = False
        total_records = len(data)
        converted_records = 0
        
        # 先分析第一条记录的LimitU，确定目标单位
        target_unit = ""
        if len(data) > 0 and "LimitU" in data[0]:
            first_limit_u = data[0]["LimitU"]
            limit_value, limit_unit = parse_limit_value(first_limit_u)
            print(f"参数 {param} 的LimitU值: {first_limit_u}, 解析为: 值={limit_value}, 单位={limit_unit}")
            
            # 根据参数和LimitU确定目标单位
            if param == "RDSON1":
                # 如果LimitU大于5，通常表示单位是毫欧姆
                if limit_value > 5:
                    target_unit = "mohm"
                    print(f"参数 {param} 的目标单位设置为: 毫欧姆(mohm), 因为LimitU值{limit_value}大于5")
                else:
                    target_unit = "ohm"
                    print(f"参数 {param} 的目标单位设置为: 欧姆(ohm), 因为LimitU值{limit_value}不大于5")
            elif param in ("IDSS1", "IDSS2", "IGSS2", "IGSSR2"):
                target_unit = "na"
                print(f"参数 {param} 的目标单位设置为: 纳安(na)")
            elif param == "IDSS3":
                target_unit = "ua"
                print(f"参数 {param} 的目标单位设置为: 微安(ua)")
            elif param in ("VFSDS", "BVDSS1", "BVDSS2", "DELTABV"):
                # 根据LimitU单位确定是伏特还是毫伏
                if limit_unit and 'mv' in limit_unit.lower():
                    target_unit = "mv"
                    print(f"参数 {param} 的目标单位设置为: 毫伏(mv), 因为LimitU单位包含mv")
                else:
                    target_unit = "v"
                    print(f"参数 {param} 的目标单位设置为: 伏特(v)")
        
        # 统计显示值的范围，帮助判断可能的单位
        values = [item.get(param) for item in data if item.get(param) is not None and not np.isnan(item.get(param))]
        if values:
            min_val = min(values)
            max_val = max(values)
            avg_val = sum(values) / len(values)
            print(f"当前值范围: 最小={min_val:.6e}, 最大={max_val:.6e}, 平均={avg_val:.6e}")
            
            # 根据值范围推断可能的单位
            if param == "RDSON1":
                if min_val < 0.1 and max_val < 1:
                    print(f"  推测: 当前值可能是欧姆单位 (值范围较小)")
                elif min_val > 1 and max_val < 1000:
                    print(f"  推测: 当前值可能是毫欧姆单位 (值范围适中)")
                elif min_val > 1000:
                    print(f"  推测: 当前值可能是微欧姆单位 (值范围较大)")
            elif param in ("IDSS1", "IDSS2", "IGSS2", "IGSSR2", "IDSS3"):
                if min_val < 1e-6 and max_val < 1e-4:
                    print(f"  推测: 当前值可能是安培单位 (值较小)")
                elif min_val < 1e-3 and max_val < 1e-1:
                    print(f"  推测: 当前值可能是毫安/微安单位 (值范围适中)")
                elif min_val > 0.1 and max_val < 1000:
                    print(f"  推测: 当前值可能已经是纳安/微安单位 (值范围较大)")
            elif param in ("VFSDS", "BVDSS1", "BVDSS2", "DELTABV"):
                if max_val < 10:
                    print(f"  推测: 当前值可能是伏特单位 (值范围较小)")
                elif min_val > 100:
                    print(f"  推测: 当前值可能是毫伏单位 (值范围较大)")
        
        # 处理每条记录
        for item in data:
            # 确保LimitU存在
            if "LimitU" not in item:
                continue
                
            # 获取原始值
            original_value = item.get(param)
            if original_value is None or np.isnan(original_value):
                continue
            
            # 调整单位
            adjusted_value = adjust_unit(original_value, param, item["LimitU"])
            
            # 如果值发生变化，更新数据
            if adjusted_value != original_value:
                item[param] = adjusted_value
                modified = True
                converted_records += 1
                print(f"  记录 {converted_records}: {original_value:.6e} -> {adjusted_value:.6e}")
            
            # 添加或更新单位字段
            if target_unit and ("Unit" not in item or item["Unit"] != target_unit):
                item["Unit"] = target_unit
                modified = True
        
        # 如果有修改，保存更新后的数据
        if modified:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print(f"已更新文件: {json_file} (转换了 {converted_records}/{total_records} 条记录)")
        else:
            print(f"文件无需更新: {json_file}")
            
    except Exception as e:
        print(f"处理文件 {json_file} 时出错: {str(e)}")
        import traceback
        traceback.print_exc()

def adjust_batch_directory(batch_dir: str) -> None:
    """
    调整批次目录下所有JSON文件的数据单位
    
    Args:
        batch_dir (str): 批次目录路径
    """
    json_dir = os.path.join(batch_dir, "json")
    
    # 如果json子目录存在，使用它
    if os.path.exists(json_dir) and os.path.isdir(json_dir):
        json_files = glob.glob(os.path.join(json_dir, "*_data.json"))
    else:
        # 否则在批次目录中寻找json文件
        json_files = glob.glob(os.path.join(batch_dir, "*_data.json"))
    
    if not json_files:
        print(f"在目录 {batch_dir} 中未找到JSON文件")
        return
    
    print(f"在目录 {batch_dir} 中找到 {len(json_files)} 个JSON文件")
    
    # 处理每个JSON文件
    for json_file in json_files:
        adjust_json_file(json_file)

def main():
    """
    主函数
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="调整JSON文件中的数据单位，确保与LimitU的单位保持一致")
    parser.add_argument("--output-dir", type=str, default="../output",
                        help="输出目录路径 (默认: ../output)")
    parser.add_argument("--batch", type=str, default=None,
                        help="指定批次名称，为空则处理所有批次")
    
    args = parser.parse_args()
    
    # 获取输出目录的绝对路径
    output_dir = os.path.abspath(args.output_dir)
    
    if not os.path.exists(output_dir):
        print(f"错误: 输出目录 {output_dir} 不存在")
        return
    
    if args.batch:
        # 处理指定批次
        batch_dir = os.path.join(output_dir, args.batch)
        if not os.path.exists(batch_dir):
            print(f"错误: 批次目录 {batch_dir} 不存在")
            return
        
        adjust_batch_directory(batch_dir)
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
            adjust_batch_directory(batch_dir)
    
    print("\n单位调整完成!")

if __name__ == "__main__":
    main() 