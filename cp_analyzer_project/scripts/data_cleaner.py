#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
晶圆厂CP测试数据清洗模块

提供灵活、可扩展的数据清洗功能，支持不同格式的log文件处理
"""

import os
import re
import json
import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple, Union

class BaseDataCleaner(ABC):
    """
    数据清洗基类
    
    定义数据清洗的通用接口和基本功能
    """
    
    def __init__(self, target_params: List[str] = None, output_dir: str = "./output"):
        """
        初始化数据清洗器
        
        Args:
            target_params (List[str]): 目标参数列表
            output_dir (str): 输出目录
        """
        self.target_params = target_params or ["BVDSS1", "BVDSS2", "DELTABV", "IDSS1", 
                                              "VTH", "RDSON1", "VFSDS", "IGSS2", 
                                              "IGSSR2", "IDSS2"]
        self.output_dir = output_dir
        self.raw_data = None
        self.clean_data = None
        self.limits = {}
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
    
    @abstractmethod
    def load_data(self, data_source: Union[str, pd.DataFrame]) -> bool:
        """
        加载数据
        
        Args:
            data_source: 数据源，可以是DataFrame或文件路径
            
        Returns:
            bool: 加载是否成功
        """
        pass
    
    @abstractmethod
    def clean(self) -> pd.DataFrame:
        """
        执行数据清洗
        
        Returns:
            pd.DataFrame: 清洗后的数据
        """
        pass
    
    def export_json(self, export_by_param: bool = True) -> Dict[str, str]:
        """
        导出JSON格式数据
        
        Args:
            export_by_param (bool): 是否按参数分别导出
            
        Returns:
            dict: 导出文件路径字典
        """
        if self.clean_data is None or self.clean_data.empty:
            print("错误: 无清洗数据可供导出")
            return {}
            
        export_paths = {}
        
        # 导入单位转换模块
        try:
            from unit_adjuster import adjust_unit, parse_limit_value
            unit_adjuster_available = True
        except ImportError:
            print("警告: 单位转换模块不可用，将使用内置的简单转换逻辑")
            unit_adjuster_available = False
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 检查批次信息
        batch_info = None
        if 'Lot' in self.clean_data.columns and not self.clean_data['Lot'].empty:
            batch_info = self.clean_data['Lot'].iloc[0]
        
        if not batch_info:
            batch_info = 'unknown_batch'
            
        # 创建批次目录
        batch_dir = os.path.join(self.output_dir, batch_info.replace('/', '_').replace('\\', '_'))
        os.makedirs(batch_dir, exist_ok=True)
        
        # 创建json子目录
        json_dir = os.path.join(batch_dir, 'json')
        os.makedirs(json_dir, exist_ok=True)
        
        if export_by_param:
            # 按参数分别导出
            for param in self.target_params:
                if param not in self.clean_data.columns:
                    continue
                
                # 提取该参数的数据
                param_data = self.clean_data[~self.clean_data[param].isna()].copy()
                if param_data.empty:
                    print(f"跳过参数 {param}，无有效数据")
                    continue
                
                # 获取参数的上下限
                limit_upper = None
                limit_lower = None
                limit_unit = None
                
                if self.limits and param in self.limits:
                    if 'upper' in self.limits[param]:
                        limit_upper = self.limits[param]['upper']
                    if 'lower' in self.limits[param]:
                        limit_lower = self.limits[param]['lower']
                        
                # 尝试解析上限值的单位
                if limit_upper is not None:
                    try:
                        # 使用单位转换模块的函数解析单位
                        if unit_adjuster_available:
                            _, limit_unit = parse_limit_value(limit_upper)
                        else:
                            # 简单的单位解析逻辑
                            match = re.search(r"([-+]?\d*\.?\d+)([a-zA-Z]+)?", str(limit_upper))
                            if match and match.group(2):
                                limit_unit = match.group(2).lower()
                    except Exception as e:
                        print(f"解析参数 {param} 的限制单位时出错: {str(e)}")
                
                # 导出文件路径
                json_path = os.path.join(json_dir, f"{param}_data.json")
                export_paths[param] = json_path
                
                # 准备JSON数据
                json_records = []
                
                for _, row in param_data.iterrows():
                    # 提取原始值
                    value = row[param]
                    
                    # 使用单位转换模块进行转换
                    if unit_adjuster_available and limit_upper is not None:
                        value = adjust_unit(value, param, limit_upper)
                    else:
                        # 根据参数进行特殊处理，确保单位一致性 (内置的简单转换逻辑)
                        # 处理RDSON1：RDSON1需要以毫欧姆(mohm)为单位
                        if param == 'RDSON1' and limit_unit and limit_unit.lower() in ['mohm', 'mω', 'mω', 'mΩ']:
                            # 判断值大小，小于1的值可能是欧姆值，需要转换为毫欧姆
                            if value < 1:  # 可能是欧姆值
                                original_value = value
                                value = value * 1000  # 欧姆转毫欧姆
                                print(f"JSON导出时转换RDSON1值：原值={original_value}欧姆 -> 新值={value}毫欧")
                        
                        # 处理电流单位：根据LimitU单位进行转换
                        if param in ['IDSS1', 'IDSS2', 'IGSS2', 'IGSSR2']:
                            if limit_unit and limit_unit.lower() in ['na', 'na']:  # 如果限制单位是纳安(nA)
                                if value < 1e-6:  # 如果值很小，可能是安培(A)
                                    original_value = value
                                    value = value * 1e9  # 安培转纳安
                                    print(f"JSON导出时转换{param}值：原值={original_value}A -> 新值={value}nA")
                                elif value < 1e-3:  # 如果值小于1e-3，可能是微安(uA)
                                    original_value = value
                                    value = value * 1000  # 微安转纳安
                                    print(f"JSON导出时转换{param}值：原值={original_value}uA -> 新值={value}nA")
                            elif limit_unit and limit_unit.lower() in ['ua', 'μa', 'ua']:  # 如果限制单位是微安(uA)
                                if value < 1e-3:  # 如果值很小，可能是安培(A)
                                    original_value = value
                                    value = value * 1e6  # 安培转微安
                                    print(f"JSON导出时转换{param}值：原值={original_value}A -> 新值={value}uA")
                        
                        # 处理IDSS3：特殊处理微安单位
                        if param == 'IDSS3' and limit_unit and limit_unit.lower() in ['ua', 'μa', 'ua'] and value < 1e-3:
                            original_value = value
                            value = value * 1e6  # 安培转微安
                            print(f"JSON导出时转换IDSS3值：原值={original_value}A -> 新值={value}uA")
                    
                    # 创建记录，确保值匹配单位
                    record = {
                        'Lot': row.get('Lot', ''),
                        'Wafer': row.get('Wafer', ''),
                        'No.U': row.get('No.U', 0),
                        param: value
                    }
                    
                    # 添加限制值，不做转换，保持原始值
                    if limit_upper is not None:
                        record['LimitU'] = limit_upper
                    if limit_lower is not None:
                        record['LimitL'] = limit_lower
                    if limit_unit:
                        record['Unit'] = limit_unit
                        
                    json_records.append(record)
                
                # 导出JSON
                try:
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(json_records, f, indent=2)
                    print(f"已导出参数 {param} 的JSON数据: {json_path}")
                except Exception as e:
                    print(f"导出参数 {param} 的JSON数据时出错: {str(e)}")
            
            return export_paths
        else:
            # 一次性导出所有参数数据
            json_path = os.path.join(json_dir, "all_data.json")
            export_paths['all'] = json_path
            
            # 准备JSON数据
            json_records = []
            
            for _, row in self.clean_data.iterrows():
                record = {
                    'Lot': row.get('Lot', ''),
                    'Wafer': row.get('Wafer', ''),
                    'No.U': row.get('No.U', 0)
                }
                
                # 添加参数值
                for param in self.target_params:
                    if param in row and not pd.isna(row[param]):
                        value = row[param]
                        
                        # 获取参数的上限值
                        limit_upper = None
                        if self.limits and param in self.limits and 'upper' in self.limits[param]:
                            limit_upper = self.limits[param]['upper']
                        
                        # 使用单位转换模块进行转换
                        if unit_adjuster_available and limit_upper is not None:
                            value = adjust_unit(value, param, limit_upper)
                        
                        record[param] = value
                
                json_records.append(record)
            
            # 导出JSON
            try:
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(json_records, f, indent=2)
                print(f"已导出所有参数的JSON数据: {json_path}")
            except Exception as e:
                print(f"导出所有参数的JSON数据时出错: {str(e)}")
            
            return export_paths
    
    def get_limits(self) -> Dict[str, Dict[str, float]]:
        """
        获取参数限制
        
        Returns:
            Dict[str, Dict[str, float]]: 参数限制字典
        """
        return self.limits
    
    def set_limits(self, limits: Dict[str, Dict[str, float]]) -> None:
        """
        设置参数限制
        
        Args:
            limits: 参数限制字典 {参数名: {'upper': 上限值, 'lower': 下限值}}
        """
        self.limits = limits
    
    def apply_cleaner_strategy(self, strategy: 'DataCleanerStrategy') -> pd.DataFrame:
        """
        应用清洗策略
        
        Args:
            strategy: 清洗策略对象
            
        Returns:
            pd.DataFrame: 应用策略后的数据
        """
        if self.raw_data is None:
            print("错误: 原始数据为空，无法应用清洗策略")
            return None
        
        return strategy.clean(self.raw_data, self.limits)


class DataCleanerStrategy(ABC):
    """
    数据清洗策略接口
    
    定义数据清洗策略的接口
    """
    
    @abstractmethod
    def clean(self, data: pd.DataFrame, limits: Dict[str, Dict[str, float]] = None) -> pd.DataFrame:
        """
        执行数据清洗
        
        Args:
            data: 待清洗的数据
            limits: 参数限制字典
            
        Returns:
            pd.DataFrame: 清洗后的数据
        """
        pass


class CPLogCleaner(BaseDataCleaner):
    """
    CP测试日志数据清洗器
    
    专门用于清洗CP测试日志数据的实现
    """
    
    def __init__(self, target_params: List[str] = None, output_dir: str = "./output"):
        """
        初始化CP测试日志数据清洗器
        
        Args:
            target_params: 目标参数列表
            output_dir: 输出目录
        """
        super().__init__(target_params, output_dir)
        self.log_files = []
        
        # 检查并添加IDSS3参数（如果不存在）
        if target_params and "IDSS3" not in target_params:
            self.target_params.append("IDSS3")
    
    def load_data(self, data_source: Union[str, pd.DataFrame]) -> bool:
        """
        加载CP测试日志数据
        
        Args:
            data_source: 数据源，可以是DataFrame或数据目录路径
            
        Returns:
            bool: 加载是否成功
        """
        if isinstance(data_source, pd.DataFrame):
            self.raw_data = data_source
            return True
        
        elif isinstance(data_source, str) and os.path.isdir(data_source):
            # 从日志解析器中解析数据
            from log_parser import CPLogParser
            parser = CPLogParser(data_source)
            parser.target_params = self.target_params
            
            print(f"开始解析目录 {data_source} 中的数据文件...")
            df, limits = parser.parse_all_files()
            
            if df is None or df.empty:
                print(f"错误: 未能从目录 {data_source} 中提取有效数据")
                return False
            
            # 检查是否包含必要的列
            for param in self.target_params:
                if param not in df.columns or df[param].count() == 0:
                    print(f"警告: 参数 {param} 没有有效数据，将以空值填充")
                    df[param] = np.nan
            
            # 确保包含必要的基础列
            if 'Lot' not in df.columns:
                print("警告: 数据中缺少Lot列，添加默认值'LOT01'")
                df['Lot'] = 'LOT01'
                
            if 'Wafer' not in df.columns:
                print("警告: 数据中缺少Wafer列，添加默认值'01'")
                df['Wafer'] = '01'
                
            if 'No.U' not in df.columns:
                print("警告: 数据中缺少No.U列，添加默认值(行索引+1)")
                df['No.U'] = range(1, len(df) + 1)
            
            # 转换数据类型
            for param in self.target_params:
                if param in df.columns:
                    df[param] = pd.to_numeric(df[param], errors='coerce')
            
            self.raw_data = df
            self.limits = limits
            
            valid_count = df.count().min()
            print(f"成功加载 {len(self.raw_data)} 条数据记录，其中至少 {valid_count} 条包含完整数据")
            return True
        
        else:
            print("错误: 不支持的数据源类型，请提供有效的DataFrame或数据目录路径")
            return False
    
    def clean(self) -> pd.DataFrame:
        """
        执行CP测试日志数据清洗
        
        Returns:
            pd.DataFrame: 清洗后的数据
        """
        if self.raw_data is None or self.raw_data.empty:
            print("错误: 原始数据为空，无法进行清洗")
            return None
        
        # 应用默认的清洗策略
        default_strategy = StandardCPDataCleanerStrategy()
        self.clean_data = self.apply_cleaner_strategy(default_strategy)
        
        # 应用单位转换
        try:
            print("开始应用数据单位转换...")
            from unit_adjuster import adjust_unit, parse_limit_value
            
            # 为每个参数进行单位转换
            supported_params = [
                "RDSON1", "IDSS1", "IDSS2", "IGSS2", "IGSSR2", "IDSS3",
                "VFSDS", "BVDSS1", "BVDSS2", "DELTABV"
            ]
            
            for param in self.target_params:
                if param not in supported_params or param not in self.clean_data.columns:
                    continue
                
                # 获取该参数的限制值
                limit_upper = None
                if param in self.limits and 'upper' in self.limits[param]:
                    limit_upper = self.limits[param]['upper']
                
                if limit_upper is None:
                    # 如果没有找到限制值，跳过此参数
                    print(f"警告: 无法找到参数 {param} 的上限，跳过单位转换")
                    continue
                
                print(f"应用参数 {param} 的单位转换，上限值: {limit_upper}")
                
                # 对每个数值应用单位转换
                converted_count = 0
                for idx in self.clean_data.index:
                    value = self.clean_data.at[idx, param]
                    if pd.notna(value):
                        adjusted_value = adjust_unit(value, param, limit_upper)
                        if adjusted_value != value:
                            self.clean_data.at[idx, param] = adjusted_value
                            converted_count += 1
                
                if converted_count > 0:
                    print(f"已转换参数 {param} 的 {converted_count} 个数值")
            
            print("数据单位转换完成")
            
        except Exception as e:
            print(f"数据单位转换时出错: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return self.clean_data


class StandardCPDataCleanerStrategy(DataCleanerStrategy):
    """
    标准CP数据清洗策略
    
    实现标准的CP数据清洗流程
    """
    
    def clean(self, data: pd.DataFrame, limits: Dict[str, Dict[str, float]] = None) -> pd.DataFrame:
        """
        执行标准CP数据清洗
        
        Args:
            data: 待清洗的数据
            limits: 参数限制字典
            
        Returns:
            pd.DataFrame: 清洗后的数据
        """
        # 复制数据，避免修改原始数据
        df_clean = data.copy()
        
        # 确保必要的列存在
        required_columns = ['Lot', 'Wafer', 'No.U']
        for col in required_columns:
            if col not in df_clean.columns:
                if col == 'Lot':
                    df_clean['Lot'] = 'LOT01'
                elif col == 'Wafer':
                    df_clean['Wafer'] = '01'
                elif col == 'No.U':
                    df_clean['No.U'] = range(1, len(df_clean) + 1)
        
        # 处理参数数据
        for param in df_clean.columns:
            if param in ['Lot', 'Wafer', 'No.U']:
                continue
            
            # 将参数列转换为数值类型
            df_clean[param] = pd.to_numeric(df_clean[param], errors='coerce')
            
            # 获取参数限制
            param_limits = limits.get(param, {})
            upper_limit = param_limits.get('upper')
            lower_limit = param_limits.get('lower')
            
            # 标记异常值
            if upper_limit is not None:
                mask_high = df_clean[param] > upper_limit * 1.5
                df_clean.loc[mask_high, f"{param}_outlier_high"] = True
                
                # 标记超出规格的值（但不是异常值）
                mask_spec = (df_clean[param] > upper_limit) & (~mask_high)
                df_clean.loc[mask_spec, f"{param}_spec_high"] = True
            
            if lower_limit is not None:
                mask_low = df_clean[param] < lower_limit * 0.5
                df_clean.loc[mask_low, f"{param}_outlier_low"] = True
                
                # 标记超出规格的值（但不是异常值）
                mask_spec = (df_clean[param] < lower_limit) & (~mask_low)
                df_clean.loc[mask_spec, f"{param}_spec_low"] = True
        
        return df_clean


class CPDataCleanerFactory:
    """
    CP数据清洗器工厂
    
    用于创建不同类型的数据清洗器
    """
    
    @staticmethod
    def create_cleaner(cleaner_type: str, target_params: List[str] = None, output_dir: str = "./output") -> BaseDataCleaner:
        """
        创建数据清洗器
        
        Args:
            cleaner_type: 清洗器类型
            target_params: 目标参数列表
            output_dir: 输出目录
            
        Returns:
            BaseDataCleaner: 数据清洗器对象
        """
        if cleaner_type.lower() == 'cp_log':
            return CPLogCleaner(target_params, output_dir)
        else:
            raise ValueError(f"不支持的清洗器类型: {cleaner_type}")


# 自定义清洗策略示例：去除异常值的策略
class RemoveOutliersStrategy(DataCleanerStrategy):
    """
    移除异常值的清洗策略
    
    检测并移除数据中的异常值
    """
    
    def __init__(self, std_threshold: float = 3.0):
        """
        初始化异常值清洗策略
        
        Args:
            std_threshold: 标准差阈值，用于确定异常值
        """
        self.std_threshold = std_threshold
    
    def clean(self, data: pd.DataFrame, limits: Dict[str, Dict[str, float]] = None) -> pd.DataFrame:
        """
        执行异常值清洗
        
        Args:
            data: 待清洗的数据
            limits: 参数限制字典
            
        Returns:
            pd.DataFrame: 清洗后的数据
        """
        # 复制数据，避免修改原始数据
        df_clean = data.copy()
        
        # 获取数值型列
        numeric_cols = df_clean.select_dtypes(include=['number']).columns
        
        for col in numeric_cols:
            if col in ['Lot', 'Wafer', 'No.U'] or col.endswith(('_outlier_high', '_outlier_low', '_spec_high', '_spec_low')):
                continue
            
            # 利用z分数检测异常值
            z_scores = np.abs((df_clean[col] - df_clean[col].mean()) / df_clean[col].std())
            outliers = z_scores > self.std_threshold
            
            # 标记异常值
            df_clean.loc[outliers, f"{col}_z_outlier"] = True
            
            # 如果需要从数据中移除异常值，可以取消下面的注释
            # df_clean = df_clean[~outliers]
        
        return df_clean


# 智能参数清洗策略：根据参数特性自动选择清洗方法
class SmartParameterCleanerStrategy(DataCleanerStrategy):
    """
    智能参数清洗策略
    
    根据参数特性自动选择最合适的清洗方法
    """
    
    def clean(self, data: pd.DataFrame, limits: Dict[str, Dict[str, float]] = None) -> pd.DataFrame:
        """
        执行智能参数清洗
        
        Args:
            data: 待清洗的数据
            limits: 参数限制字典
            
        Returns:
            pd.DataFrame: 清洗后的数据
        """
        # 复制数据，避免修改原始数据
        df_clean = data.copy()
        
        # 参数特性字典
        param_features = {
            'BVDSS1': {'method': 'spec_limit', 'skew_sensitive': True},
            'BVDSS2': {'method': 'spec_limit', 'skew_sensitive': True},
            'DELTABV': {'method': 'statistical', 'skew_sensitive': False},
            'IDSS1': {'method': 'log_transform', 'skew_sensitive': True},
            'VTH': {'method': 'spec_limit', 'skew_sensitive': False},
            'RDSON1': {'method': 'statistical', 'skew_sensitive': True},
            'VFSDS': {'method': 'spec_limit', 'skew_sensitive': False},
            'IGSS2': {'method': 'log_transform', 'skew_sensitive': True},
            'IGSSR2': {'method': 'log_transform', 'skew_sensitive': True},
            'IDSS2': {'method': 'log_transform', 'skew_sensitive': True}
        }
        
        for param in df_clean.columns:
            if param in ['Lot', 'Wafer', 'No.U'] or not param in param_features:
                continue
                
            # 将参数列转换为数值类型
            df_clean[param] = pd.to_numeric(df_clean[param], errors='coerce')
            
            # 获取参数特性
            features = param_features.get(param, {'method': 'statistical', 'skew_sensitive': False})
            
            # 根据参数特性选择清洗方法
            if features['method'] == 'spec_limit' and limits and param in limits:
                # 基于规格限制的清洗
                upper_limit = limits[param].get('upper')
                lower_limit = limits[param].get('lower')
                
                if upper_limit is not None:
                    # 使用3倍IQR或1.5倍规格上限作为异常值阈值
                    q3 = df_clean[param].quantile(0.75)
                    iqr = df_clean[param].quantile(0.75) - df_clean[param].quantile(0.25)
                    threshold = min(q3 + 3 * iqr, upper_limit * 1.5)
                    
                    mask = df_clean[param] > threshold
                    df_clean.loc[mask, f"{param}_smart_outlier_high"] = True
                
                if lower_limit is not None:
                    # 使用3倍IQR或0.5倍规格下限作为异常值阈值
                    q1 = df_clean[param].quantile(0.25)
                    iqr = df_clean[param].quantile(0.75) - df_clean[param].quantile(0.25)
                    threshold = max(q1 - 3 * iqr, lower_limit * 0.5)
                    
                    mask = df_clean[param] < threshold
                    df_clean.loc[mask, f"{param}_smart_outlier_low"] = True
            
            elif features['method'] == 'log_transform':
                # 对于偏斜分布，尝试对数变换后检测异常值
                log_values = np.log1p(df_clean[param].abs())
                z_scores = np.abs((log_values - log_values.mean()) / log_values.std())
                
                mask = z_scores > 3.0
                df_clean.loc[mask, f"{param}_smart_log_outlier"] = True
            
            elif features['method'] == 'statistical':
                # 统计方法检测异常值
                z_scores = np.abs((df_clean[param] - df_clean[param].mean()) / df_clean[param].std())
                
                mask = z_scores > 3.0
                df_clean.loc[mask, f"{param}_smart_stat_outlier"] = True
        
        return df_clean 