# 晶圆厂CP测试数据分析工具

一个用于分析晶圆厂CP测试数据的工具，支持数据清洗、统计分析、图表生成和HTML报告生成。

## 功能特点

- 解析CP测试日志文件
- 灵活的数据清洗策略
- 参数统计分析
- 交互式图表生成
- HTML格式报告
- 数据单位智能调整

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本用法

```bash
python scripts/main.py --data-dir "data/data2/rawdata" --output-dir "./output"
```

### 指定参数和清洗策略

```bash
python scripts/main.py --data-dir "data/data2/rawdata" --params BVDSS1 BVDSS2 VTH --cleaner-strategy smart
```

### 导出JSON格式数据

```bash
python scripts/main.py --data-dir "data/data2/rawdata" --export-json
```

### 调整数据单位

在Windows系统下，可以直接运行批处理文件调整数据单位：

```bash
adjust_units.bat
```

或使用Python脚本：

```bash
python scripts/adjust_units.py --output-dir "./output"
```

指定批次和参数：

```bash
python scripts/adjust_units.py --output-dir "./output" --batch "C141321.02-CPTSTE12-250213-185303@CP_014" --params RDSON1 IDSS1
```

## 数据清洗功能

本工具提供了灵活的数据清洗功能，支持多种清洗策略：

1. **标准清洗策略**：基本的数据清洗，识别并标记异常值
2. **智能参数清洗策略**：根据参数特性自动选择最合适的清洗方法
3. **移除异常值策略**：检测并标记数据中的异常值

### 数据清洗模块使用示例

```python
from data_cleaner import CPDataCleanerFactory, SmartParameterCleanerStrategy

# 创建数据清洗器
cleaner = CPDataCleanerFactory.create_cleaner('cp_log', target_params=["BVDSS1", "VTH"], 
                                             output_dir="./output")

# 加载数据
cleaner.load_data("data/data2/rawdata")

# 执行数据清洗
df_clean = cleaner.clean()

# 导出JSON数据
cleaner.export_json(export_by_param=True)

# 应用智能清洗策略
smart_strategy = SmartParameterCleanerStrategy()
df_smart = cleaner.apply_cleaner_strategy(smart_strategy)
```

## 数据单位调整功能

工具提供了数据单位调整功能，确保数据的单位与LimitU保持一致：

- **RDSON1**：欧姆(Ω)转换为毫欧(mΩ)，乘以1000
- **IDSS1, IDSS2, IGSS2, IGSSR2**：安培(A)转换为纳安(nA)，乘以10^9
- **IDSS3**：安培(A)转换为微安(μA)，乘以10^6

### 单位调整工具使用示例

```python
from unit_adjuster import adjust_batch_directory

# 调整批次目录下所有JSON文件的数据单位
adjust_batch_directory('./output/C141321.02-CPTSTE12-250213-185303@CP_014')
```

## 命令行参数

### main.py参数

- `--data-dir`: 数据目录路径
- `--output-dir`: 输出目录路径
- `--params`: 要分析的参数列表
- `--export-json`: 是否导出JSON格式数据
- `--cleaner-strategy`: 数据清洗策略 (standard, smart, remove_outliers)

### adjust_units.py参数

- `--output-dir`: 输出目录路径
- `--batch`: 指定批次名称，为空则处理所有批次
- `--params`: 要处理的参数列表，默认处理电流和电阻参数
- `--regenerate`: 是否在调整单位后重新生成HTML报告

## 安装依赖

```bash
pip install -r requirements.txt