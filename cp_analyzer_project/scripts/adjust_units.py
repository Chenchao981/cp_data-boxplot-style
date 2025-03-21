#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
单位调整工具

调整JSON数据单位，然后重新生成HTML报告
"""

import os
import sys
import argparse
from unit_adjuster import adjust_batch_directory, adjust_json_file
from regenerate_reports import regenerate_batch_reports

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description="调整数据单位并重新生成HTML报告")
    parser.add_argument("--output-dir", type=str, default="../output",
                        help="输出目录路径 (默认: ../output)")
    parser.add_argument("--batch", type=str, default=None,
                        help="指定批次名称，为空则处理所有批次")
    parser.add_argument("--params", type=str, nargs='+',
                        default=["RDSON1", "IDSS1", "IDSS2", "IGSS2", "IGSSR2", "IDSS3", 
                                "VFSDS", "BVDSS1", "BVDSS2", "DELTABV"],
                        help="要处理的参数列表，默认处理所有支持的参数")
    parser.add_argument("--regenerate", action="store_true", default=True,
                        help="是否在调整单位后重新生成HTML报告 (默认: True)")
    
    args = parser.parse_args()
    
    # 获取输出目录的绝对路径
    output_dir = os.path.abspath(args.output_dir)
    
    if not os.path.exists(output_dir):
        print(f"错误: 输出目录 {output_dir} 不存在")
        return
    
    # 处理指定批次
    if args.batch:
        batch_dir = os.path.join(output_dir, args.batch)
        if not os.path.exists(batch_dir):
            print(f"错误: 批次目录 {batch_dir} 不存在")
            return
        
        print(f"\n调整批次 {args.batch} 的单位...")
        adjust_batch_directory(batch_dir)
        
        if args.regenerate:
            print(f"\n重新生成批次 {args.batch} 的报告...")
            regenerate_batch_reports(batch_dir, args.params)
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
            print(f"\n调整批次 {batch} 的单位...")
            adjust_batch_directory(batch_dir)
            
            if args.regenerate:
                print(f"\n重新生成批次 {batch} 的报告...")
                regenerate_batch_reports(batch_dir, args.params)
    
    print("\n单位调整和报告重新生成完成!")

if __name__ == "__main__":
    main() 