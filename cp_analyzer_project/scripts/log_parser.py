import re
import os
import pandas as pd
import glob
import traceback

# 调整类定义顺序，将函数放入类内部
class CPLogParser:
    def __init__(self, data_dir):
        """
        初始化日志解析器
        
        Args:
            data_dir (str): 数据目录
        """
        self.data_dir = data_dir
        self.target_params = ["BVDSS1", "BVDSS2", "DELTABV", "IDSS1", "VTH", 
                            "RDSON1", "VFSDS", "IGSS2", "IGSSR2", "IDSS2"]

    def _parse_limit_value(self, limit_str, param_name=None):
        """
        解析限制值
        
        Args:
            limit_str (str): 限制值字符串，如 "900.0V"
            param_name (str, optional): 参数名称，用于特殊处理某些参数
            
        Returns:
            tuple: (解析后的数值, 单位)
        """
        if not limit_str or limit_str.strip() == '':
            return None, None
            
        # 单位转换字典
        unit_multipliers = {
            'V': 1,
            'mV': 1e-3,
            'uV': 1e-6,
            'nV': 1e-9,
            'A': 1,
            'mA': 1e-3,
            'uA': 1e-6,
            'nA': 1e-9,
            'OHM': 1,
            'mOHM': 1, # 对于RDSON1参数，我们保持毫欧姆的原始单位
            'Ω': 1,    # 希腊字母欧姆
            'mΩ': 1,   # 毫欧姆
            'μA': 1e-6, # 微安培，希腊字母
            'μΩ': 1,   # 微欧姆，希腊字母
            '-': 1     # 对于无单位的情况
        }

        try:
            # 对于RDSON1的限制值，特殊处理
            if param_name == "RDSON1":
                # 提取数值和单位
                match = re.search(r"([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)([a-zA-Z-Ωμ]*)", limit_str)
                if match:
                    value_part, unit_part = match.groups()
                    
                    # 标准化单位
                    unit_lower = unit_part.lower() if unit_part else ""
                    
                    # 如果单位包含mohm(不区分大小写)或mΩ，保持毫欧姆单位
                    if 'mohm' in unit_lower or 'mω' in unit_lower or 'mΩ' in unit_lower:
                        return float(value_part), "mohm"
                    elif 'ohm' in unit_lower or 'ω' in unit_lower or 'Ω' in unit_lower:
                        # 如果单位是欧姆，将值转换为毫欧姆
                        return float(value_part), "mohm"  # 保持单位为mohm，值不变
                    else:
                        # 如果没有明确单位，假设为毫欧姆
                        return float(value_part), "mohm"
                else:
                    try:
                        # 如果没有单位，假设单位为毫欧姆
                        return float(limit_str), "mohm"
                    except ValueError:
                        print(f"无法解析RDSON1限制值: {limit_str}")
                        return None, None
            
            # 对于电流参数的限制值，特殊处理
            if param_name in ["IDSS1", "IDSS2", "IGSS2", "IGSSR2", "IDSS3"]:
                # 提取数值和单位
                match = re.search(r"([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)([a-zA-Z-Ωμ]*)", limit_str)
                if match:
                    value_part, unit_part = match.groups()
                    
                    # 标准化单位
                    unit_lower = unit_part.lower() if unit_part else ""
                    
                    # 根据单位返回适当的值和单位标识
                    if 'na' in unit_lower:
                        return float(value_part), "na"
                    elif 'ua' in unit_lower or 'μa' in unit_lower:
                        return float(value_part), "ua"
                    elif 'ma' in unit_lower:
                        return float(value_part), "ma"
                    elif 'a' in unit_lower:
                        return float(value_part), "a"
                    else:
                        # 如果没有明确单位，根据参数选择默认单位
                        if param_name in ["IDSS1", "IDSS2", "IGSS2", "IGSSR2"]:
                            return float(value_part), "na"  # 默认为纳安
                        elif param_name == "IDSS3":
                            return float(value_part), "ua"  # 默认为微安
                else:
                    try:
                        # 尝试直接转换
                        return float(limit_str), "na" if param_name in ["IDSS1", "IDSS2", "IGSS2", "IGSSR2"] else "ua"
                    except ValueError:
                        print(f"无法解析{param_name}限制值: {limit_str}")
                        return None, None
            
            # 对科学计数法的特殊处理
            if 'E' in limit_str or 'e' in limit_str:
                # 例如："1.20E-08"
                try:
                    return float(limit_str), None
                except ValueError:
                    pass
            
            # 提取数值部分
            match = re.search(r"([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)([a-zA-Z-Ωμ]*)", limit_str)
            if not match:
                try:
                    # 尝试直接转换
                    return float(limit_str), None
                except ValueError:
                    print(f"无法解析限制值: {limit_str}")
                    return None, None
                    
            value_part, unit_part = match.groups()
            
            # 处理特殊格式，例如 "50.00-"
            if unit_part == '-' and limit_str.endswith('-'):
                # 格式如 "50.00-"，表示正值
                return float(value_part), unit_part
            
            # 记录原始单位
            original_unit = unit_part
            
            # 转换为标准单位格式以便使用字典查找
            std_unit = unit_part.upper()
            
            # 如果单位中包含希腊字母，需要特殊处理
            if 'Ω' in unit_part or 'μ' in unit_part:
                if 'μ' in unit_part and 'A' in unit_part:
                    std_unit = 'μA'
                elif 'μ' in unit_part and 'Ω' in unit_part:
                    std_unit = 'μΩ'
                elif 'mΩ' in unit_part:
                    std_unit = 'mΩ'
                elif 'Ω' in unit_part:
                    std_unit = 'Ω'
            
            # 转换数值
            value = float(value_part)
            
            # 返回解析后的值和原始单位
            return value, original_unit
                
        except Exception as e:
            print(f"解析限制值错误: {limit_str} - {str(e)}")
            return None, None

    def _parse_file(self, file_path):
        """
        解析单个CP测试文件
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            tuple: (数据字典列表, 参数限制字典)
        """
        try:
            # 尝试不同的编码方式打开文件
            encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
            lines = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                        lines = f.readlines()
                    break
                except Exception as e:
                    continue
            
            if lines is None:
                print(f"错误: 无法读取文件 {file_path} 内容")
                return [], {}
            
            # 提取文件头信息
            lot_number = None
            wafer_number = None
            
            # 寻找批次号和晶圆号
            for i, line in enumerate(lines[:20]):  # 扩大搜索范围到前20行
                if 'Lot number' in line or 'LOT' in line.upper():
                    parts = line.strip().split('\t')
                    if len(parts) > 1:
                        lot_number = parts[1].strip()
                elif 'Wafer number' in line or 'WAFER' in line.upper():
                    parts = line.strip().split('\t')
                    if len(parts) > 1:
                        try:
                            wafer_number = int(parts[1].strip())
                        except ValueError:
                            wafer_number = parts[1].strip()
            
            # 如果从文件名中提取批次号和晶圆号
            if lot_number is None or wafer_number is None:
                filename = os.path.basename(file_path)
                
                # 尝试从文件名提取批次号
                lot_matches = re.search(r'([A-Z0-9]+-\d+)', filename)
                if lot_matches and lot_number is None:
                    lot_number = lot_matches.group(1)
                
                # 尝试从文件名提取晶圆号
                wafer_matches = re.search(r'_(\d+)\.', filename)
                if wafer_matches and wafer_number is None:
                    try:
                        wafer_number = int(wafer_matches.group(1))
                    except ValueError:
                        wafer_number = wafer_matches.group(1)
            
            # 仍然找不到，使用默认值        
            if lot_number is None:
                # 从目录名中提取批次号
                lot_number = os.path.basename(self.data_dir)
            
            if wafer_number is None:
                # 默认晶圆号为1
                wafer_number = 1
                
            # 提取参数名称行
            params_line_idx = None
            for i, line in enumerate(lines):
                if 'No.U' in line or ('X' in line and 'Y' in line and 'Bin' in line):
                    params_line_idx = i
                    break
                    
            if params_line_idx is None:
                # 尝试查找包含多个目标参数的行
                for i, line in enumerate(lines):
                    param_count = sum(1 for param in self.target_params if param in line)
                    if param_count >= 3:  # 如果行中包含至少3个目标参数
                        params_line_idx = i
                        break
            
            if params_line_idx is None:
                print(f"警告: 无法从文件 {file_path} 提取参数名称行")
                return [], {}
                
            # 解析参数名称
            param_names = lines[params_line_idx].strip().split('\t')
            param_names = [p.strip() for p in param_names if p.strip()]
            
            # 查找LimitU和LimitL行
            limit_u_idx = None
            limit_l_idx = None
            
            for i in range(params_line_idx + 1, min(params_line_idx + 10, len(lines))):
                if i < len(lines):
                    line = lines[i].strip()
                    if 'LimitU' in line or 'USL' in line:
                        limit_u_idx = i
                    elif 'LimitL' in line or 'LSL' in line:
                        limit_l_idx = i
            
            # 解析参数限制
            limits = {}
            
            # 记录每个参数的单位信息，用于后续的单位转换
            param_units = {}
            
            if limit_u_idx is not None and limit_l_idx is not None:
                limit_u = lines[limit_u_idx].strip().split('\t')
                limit_l = lines[limit_l_idx].strip().split('\t')
                
                # 创建参数限制字典
                for i, param in enumerate(param_names):
                    if param in self.target_params or param == "IDSS3":  # 增加对IDSS3的支持
                        upper_idx = min(i, len(limit_u) - 1) if limit_u else None
                        lower_idx = min(i, len(limit_l) - 1) if limit_l else None
                        
                        # 提取上限和下限的值和单位，同时传递参数名称以便特殊处理
                        upper_value, upper_unit = self._parse_limit_value(limit_u[upper_idx] if upper_idx is not None else None, param)
                        lower_value, lower_unit = self._parse_limit_value(limit_l[lower_idx] if lower_idx is not None else None, param)
                        
                        # 使用上限的单位作为参数单位
                        if upper_unit:
                            param_units[param] = upper_unit.lower()
                        
                        limits[param] = {
                            'upper': upper_value,
                            'lower': lower_value,
                            'unit': upper_unit
                        }
            
            # 查找数据起始行
            data_start_idx = None
            for i in range(params_line_idx + 1, len(lines)):
                line = lines[i].strip()
                if line and line[0].isdigit() and not ('LimitU' in line or 'LimitL' in line or 'Bias' in line):
                    # 确认这是数据行而不是设置行
                    if '\t' in line:  # 确保是制表符分隔的数据行
                        values = line.split('\t')
                        if len(values) >= 3 and values[0].isdigit():  # 至少有3列且第一列是数字
                            data_start_idx = i
                            break
                    
            if data_start_idx is None:
                print(f"警告: 无法从文件 {file_path} 提取数据起始行")
                return [], {}
                
            # 解析数据
            data_records = []
            record_count = 0

            # 检查批次号以便进行特定参数的单位转换
            is_c141321_batch = "C141321" in lot_number
            is_c127251_batch = "C127251" in lot_number
            
            for i in range(data_start_idx, len(lines)):
                line = lines[i].strip()
                if not line:
                    continue
                    
                values = line.split('\t')
                
                # 确保行以数字开头且有足够的值
                if not values[0].isdigit() or len(values) < 3:
                    continue
                
                # 确保有足够的值来匹配参数
                if len(values) < len(param_names):
                    # 补充空值
                    values.extend([''] * (len(param_names) - len(values)))
                    
                record = {
                    'Lot': lot_number,
                    'Wafer': f"{wafer_number:02d}" if isinstance(wafer_number, int) else wafer_number,
                    'No.U': int(values[0]) if values[0].isdigit() else record_count + 1
                }
                
                record_count += 1
                
                # 添加目标参数的值
                valid_params = 0
                target_params = self.target_params + ["IDSS3"]  # 增加对IDSS3的支持
                
                for param in target_params:
                    if param in param_names:
                        param_idx = param_names.index(param)
                        if param_idx < len(values) and values[param_idx]:
                            try:
                                # 尝试将科学计数法转换为浮点数
                                value_str = values[param_idx].strip()
                                if value_str and value_str.lower() != '999.9':  # 跳过特殊的无效值标记
                                    value = float(value_str)
                                    
                                    # 根据不同批次和参数进行单位转换
                                    # RDSON1参数: 科学记数法处理和单位转换
                                    if param == "RDSON1":
                                        # 判断当前单位
                                        unit = param_units.get(param, "").lower()
                                        if unit in ["ohm", "ohm", ""]:  # 如果是欧姆或未指定单位，转换为毫欧姆
                                            # 科学记数法处理: 例如 3.35782E-002 = 0.0335782 欧姆
                                            # 转换为毫欧姆: 0.0335782 * 1000 = 33.5782 毫欧姆
                                            orig_value = value
                                            value = value * 1000  # 欧姆转毫欧姆
                                            print(f"转换RDSON1值：原值={orig_value}欧姆 -> 新值={value}毫欧")
                                            param_units[param] = "mohm"  # 更新单位为毫欧姆
                                        elif unit in ["mohm", "mohm"]:  # 如果已经是毫欧姆，保持不变
                                            print(f"RDSON1值保持毫欧单位：值={value}毫欧")
                                    
                                    # IDSS1, IGSS2, IGSSR2, IDSS2参数：需要将安培转为纳安(乘以1e9)
                                    elif param in ["IDSS1", "IGSS2", "IGSSR2", "IDSS2"] and param_units.get(param) == "a":
                                        print(f"转换{param}值：原值={value}安培 -> 新值={value*1e9}纳安")
                                        value = value * 1e9  # 安培转纳安
                                        param_units[param] = "na"  # 更新单位为纳安
                                        
                                    # IDSS3参数：需要将安培转为微安(乘以1e6)
                                    elif param == "IDSS3" and param_units.get(param) == "a":
                                        print(f"转换IDSS3值：原值={value}安培 -> 新值={value*1e6}微安")
                                        value = value * 1e6  # 安培转微安
                                    
                                    record[param] = value
                                    valid_params += 1
                            except ValueError:
                                # 无效值跳过
                                continue
                
                # 只有包含至少一个有效目标参数的记录才添加
                if valid_params > 0:
                    data_records.append(record)
            
            # 如果这是一个需要特殊处理的批次，打印一条确认信息
            if is_c141321_batch:
                print(f"注意: 检测到C141321批次，已对RDSON1参数进行单位转换")
            if is_c127251_batch:
                print(f"注意: 检测到C127251批次，已对IDSS3参数进行单位转换")
                
            return data_records, limits
            
        except Exception as e:
            print(f"解析文件 {file_path} 出错: {str(e)}")
            traceback.print_exc()
            return [], {}
            
    def parse_all_files(self):
        """
        解析所有CP测试文件
        
        Returns:
            tuple: (DataFrame, limits_dict)
        """
        # 确保IDSS3参数在需要时被处理
        if "IDSS3" not in self.target_params:
            extended_params = self.target_params + ["IDSS3"]
        else:
            extended_params = self.target_params
            
        # 获取所有可能的CP测试文件
        file_patterns = [
            os.path.join(self.data_dir, "*.TXT"),
            os.path.join(self.data_dir, "*.txt"),
            os.path.join(self.data_dir, "*.LOG"),
            os.path.join(self.data_dir, "*.log"),
            # 添加更多可能的扩展名
            os.path.join(self.data_dir, "*.CSV"),
            os.path.join(self.data_dir, "*.csv"),
            os.path.join(self.data_dir, "*.DAT"),
            os.path.join(self.data_dir, "*.dat")
        ]
        
        # 收集所有匹配的文件
        file_paths = []
        for pattern in file_patterns:
            try:
                matches = glob.glob(pattern)
                print(f"使用模式 {pattern} 找到文件: {len(matches)} 个")
                file_paths.extend(matches)
            except Exception as e:
                print(f"搜索模式 {pattern} 时出错: {str(e)}")
        
        # 移除重复文件（忽略大小写）
        unique_files = {}
        for file_path in file_paths:
            base_name = os.path.basename(file_path).lower()
            if base_name not in unique_files:
                unique_files[base_name] = file_path
        
        file_paths = list(unique_files.values())
        
        # 如果没有找到文件，尝试备用方法
        if not file_paths:
            print("使用备用方法查找文件...")
            try:
                all_files = os.listdir(self.data_dir)
                for file_name in all_files:
                    full_path = os.path.join(self.data_dir, file_name)
                    if os.path.isfile(full_path) and os.path.getsize(full_path) > 0:
                        # 不基于扩展名，而是尝试读取文件内容的前几行来判断是否是数据文件
                        try:
                            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                                content = f.read(1000)  # 读取前1000个字符
                                if any(param in content for param in extended_params):
                                    print(f"找到可能的数据文件: {file_name}")
                                    file_paths.append(full_path)
                        except:
                            pass
            except Exception as e:
                print(f"使用备用方法查找文件时出错: {str(e)}")
        
        if not file_paths:
            print(f"错误: 在目录 {self.data_dir} 中未找到任何文件")
            # 如果真的找不到文件，手动查看目录内容
            try:
                print(f"查看目录 {self.data_dir} 中的所有内容:")
                all_items = os.listdir(self.data_dir)
                for item in all_items:
                    item_path = os.path.join(self.data_dir, item)
                    if os.path.isdir(item_path):
                        print(f"  [目录] {item}")
                    else:
                        print(f"  [文件] {item} ({os.path.getsize(item_path)} 字节)")
            except Exception as e:
                print(f"查看目录内容时出错: {str(e)}")
            return None, None
        
        print(f"找到 {len(file_paths)} 个可能的数据文件")
            
        all_records = []
        all_limits = {}
        
        # 首先从所有文件中提取限制值信息
        for file_path in file_paths:
            print(f"解析文件: {os.path.basename(file_path)}")
            try:
                _, limits = self._parse_file(file_path)
                
                # 合并参数限制，优先使用非空的限制值
                for param, limit_values in limits.items():
                    if param not in all_limits:
                        all_limits[param] = limit_values
                    else:
                        if limit_values.get('upper') is not None and all_limits[param].get('upper') is None:
                            all_limits[param]['upper'] = limit_values['upper']
                        if limit_values.get('lower') is not None and all_limits[param].get('lower') is None:
                            all_limits[param]['lower'] = limit_values['lower']
                        if limit_values.get('unit') is not None and all_limits[param].get('unit') is None:
                            all_limits[param]['unit'] = limit_values['unit']
            except Exception as e:
                print(f"解析文件 {os.path.basename(file_path)} 的限制值信息时出错: {str(e)}")
        
        # 如果还是没有找到目标参数的限制值，则手动设置
        for param in extended_params:
            if param not in all_limits:
                # 根据参数名称设置默认限制值
                if param == 'BVDSS1' or param == 'BVDSS2':
                    all_limits[param] = {'upper': 900.0, 'lower': 660.0, 'unit': 'v'}
                elif param == 'DELTABV':
                    all_limits[param] = {'upper': 50.0, 'lower': -10.0, 'unit': 'v'}
                elif param == 'IDSS1' or param == 'IDSS2':
                    all_limits[param] = {'upper': 250.0e-9, 'lower': 0.0, 'unit': 'a'}
                elif param == 'IDSS3':
                    all_limits[param] = {'upper': 250.0e-6, 'lower': 0.0, 'unit': 'ua'}  # 以微安为单位
                elif param == 'VTH':
                    all_limits[param] = {'upper': 4.0, 'lower': 3.0, 'unit': 'v'}
                elif param == 'RDSON1':
                    all_limits[param] = {'upper': 365.0e-3, 'lower': 100.0e-3, 'unit': 'ohm'}
                elif param == 'VFSDS':
                    all_limits[param] = {'upper': 1.0, 'lower': 0.0, 'unit': 'v'}
                elif param == 'IGSS2' or param == 'IGSSR2':
                    all_limits[param] = {'upper': 300.0e-9, 'lower': 0.0, 'unit': 'a'}
                else:
                    # 默认限制值
                    all_limits[param] = {'upper': None, 'lower': None, 'unit': None}
            else:
                # 如果存在限制值但有缺失，设置默认值
                if all_limits[param].get('upper') is None:
                    if param == 'BVDSS1' or param == 'BVDSS2':
                        all_limits[param]['upper'] = 900.0
                    elif param == 'DELTABV':
                        all_limits[param]['upper'] = 50.0
                    elif param == 'IDSS1' or param == 'IDSS2':
                        all_limits[param]['upper'] = 250.0e-9
                    elif param == 'IDSS3':
                        all_limits[param]['upper'] = 250.0e-6  # 以微安为单位
                    elif param == 'VTH':
                        all_limits[param]['upper'] = 4.0
                    elif param == 'RDSON1':
                        all_limits[param]['upper'] = 365.0e-3
                    elif param == 'VFSDS':
                        all_limits[param]['upper'] = 1.0
                    elif param == 'IGSS2' or param == 'IGSSR2':
                        all_limits[param]['upper'] = 300.0e-9
                        
                if all_limits[param].get('lower') is None:
                    if param == 'BVDSS1' or param == 'BVDSS2':
                        all_limits[param]['lower'] = 660.0
                    elif param == 'DELTABV':
                        all_limits[param]['lower'] = -10.0
                    elif param == 'IDSS1' or param == 'IDSS2' or param == 'IDSS3':
                        all_limits[param]['lower'] = 0.0
                    elif param == 'VTH':
                        all_limits[param]['lower'] = 3.0
                    elif param == 'RDSON1':
                        all_limits[param]['lower'] = 100.0e-3
                    elif param == 'VFSDS':
                        all_limits[param]['lower'] = 0.0
                    elif param == 'IGSS2' or param == 'IGSSR2':
                        all_limits[param]['lower'] = 0.0
        
        # 打印所有参数的限制值
        print("参数限制值信息:")
        for param, limits in all_limits.items():
            unit_info = f", 单位={limits.get('unit')}" if limits.get('unit') else ""
            print(f"  {param}: 上限={limits.get('upper')}, 下限={limits.get('lower')}{unit_info}")
            
        # 然后解析数据记录
        success_count = 0
        for file_path in file_paths:
            try:
                records, _ = self._parse_file(file_path)
                if records:
                    success_count += 1
                    all_records.extend(records)
            except Exception as e:
                print(f"解析文件 {os.path.basename(file_path)} 的数据记录时出错: {str(e)}")
            
        if not all_records:
            print("错误: 未能从任何文件中提取有效数据")
            return None, None
        
        print(f"成功从 {success_count}/{len(file_paths)} 个文件中提取了 {len(all_records)} 条记录")
            
        # 转换为DataFrame
        df = pd.DataFrame(all_records)
        
        # 确保DataFrame包含所有目标参数的列，包括IDSS3（如果需要）
        for param in extended_params:
            if param not in df.columns:
                df[param] = None
        
        return df, all_limits

# 确保没有外部函数定义