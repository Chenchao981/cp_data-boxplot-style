import os
import json
import numpy as np

class ReportGenerator:
    def __init__(self, data, limits_data, output_dir):
        self.data = data
        self.limits_data = limits_data
        self.output_dir = output_dir

    def export_json_data(self, param_name):
        """
        导出参数数据为JSON格式
        :param param_name: 参数名称
        """
        try:
            # 创建输出目录
            os.makedirs(os.path.join(self.output_dir, 'json'), exist_ok=True)
            
            # 获取该参数对应的限值
            limit_u, limit_l, unit = None, None, None
            if param_name in self.limits_data:
                limit_info = self.limits_data[param_name]
                limit_u = limit_info['upper']
                limit_l = limit_info['lower']
                unit = limit_info['unit']
            
            # 准备JSON数据
            json_data = []
            for item in self.data:
                value = item.get(param_name)
                if value is not None:
                    # 对于RDSON1参数，如果单位是mohm，则将值转换为毫欧姆
                    if param_name == 'RDSON1' and unit == 'mohm' and value is not None and not np.isnan(value):
                        # 存储原始值用于展示
                        orig_value = value
                        # 将欧姆转换为毫欧姆（乘以1000）
                        value = value * 1000
                        print(f"JSON导出时转换RDSON1值：原值={orig_value}ohm -> 新值={value}mohm")
                    # 对于电流参数，根据单位进行转换
                    elif param_name in ['IDSS1', 'IDSS2', 'IDSS3', 'IGSS2', 'IGSSR2'] and unit in ['na', 'nA', 'ua', 'uA'] and value is not None and not np.isnan(value):
                        orig_value = value
                        if unit.lower() == 'na':
                            value = value * 1e9  # 从A转换为nA
                            print(f"JSON导出时转换{param_name}值：原值={orig_value}A -> 新值={value}nA")
                        elif unit.lower() == 'ua':
                            value = value * 1e6  # 从A转换为uA
                            print(f"JSON导出时转换{param_name}值：原值={orig_value}A -> 新值={value}uA")
                        
                    json_item = {
                        'Lot': item.get('Lot', ''),
                        'Wafer': item.get('Wafer', ''),
                        'No.U': item.get('No.U', ''),
                        param_name: value,
                        'LimitU': limit_u,
                        'LimitL': limit_l,
                        'Unit': unit
                    }
                    json_data.append(json_item)
            
            # 导出JSON数据 - 注意这部分移到了循环外面
            json_file_path = os.path.join(self.output_dir, 'json', f'{param_name}_data.json')
            os.makedirs(os.path.dirname(json_file_path), exist_ok=True)
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            print(f"已导出参数 {param_name} 的JSON数据: {json_file_path}")
            return len(json_data) > 0
        except Exception as e:
            print(f"导出参数 {param_name} 的JSON数据时出错: {str(e)}")
            return False