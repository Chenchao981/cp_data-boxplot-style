#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
晶圆厂CP测试数据HTML报告生成模块
生成交互式HTML报告
支持多批次分析
"""

import os
import shutil
import jinja2
import plotly.io as pio
from datetime import datetime

class CPHTMLReport:
    """
    CP测试数据HTML报告生成类
    """
    def __init__(self, chart_generator):
        """
        初始化HTML报告生成器
        
        Args:
            chart_generator (CPChartGenerator): 图表生成器对象
        """
        self.chart_generator = chart_generator
        self.analyzer = chart_generator.analyzer
        # 默认输出目录
        self.output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
        self.template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates')
        self.static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static')
        
        # 确保模板目录存在
        if not os.path.exists(self.template_dir):
            os.makedirs(self.template_dir)
            
        # 确保静态资源目录存在
        if not os.path.exists(self.static_dir):
            os.makedirs(self.static_dir)
            
        # 确保CSS目录存在
        css_dir = os.path.join(self.static_dir, 'css')
        if not os.path.exists(css_dir):
            os.makedirs(css_dir)
            
        # 确保JS目录存在
        js_dir = os.path.join(self.static_dir, 'js')
        if not os.path.exists(js_dir):
            os.makedirs(js_dir)
            
        # 确保输出目录存在
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        # 复制静态资源文件到输出目录
        self._copy_static_files()
        
    def _copy_static_files(self):
        """
        复制静态资源文件到输出目录
        """
        # 创建输出目录中的静态资源目录
        output_static_dir = os.path.join(self.output_dir, 'static')
        if not os.path.exists(output_static_dir):
            os.makedirs(output_static_dir)
            
        # 创建输出目录中的CSS目录
        output_css_dir = os.path.join(output_static_dir, 'css')
        if not os.path.exists(output_css_dir):
            os.makedirs(output_css_dir)
            
        # 创建输出目录中的JS目录
        output_js_dir = os.path.join(output_static_dir, 'js')
        if not os.path.exists(output_js_dir):
            os.makedirs(output_js_dir)
            
        # 确保项目的静态资源目录存在
        css_dir = os.path.join(self.static_dir, 'css')
        if not os.path.exists(css_dir):
            os.makedirs(css_dir)
            
        js_dir = os.path.join(self.static_dir, 'js')
        if not os.path.exists(js_dir):
            os.makedirs(js_dir)
        
        # 确保至少有一个默认的CSS文件
        default_css_path = os.path.join(css_dir, 'style.css')
        if not os.path.exists(default_css_path):
            with open(default_css_path, 'w', encoding='utf-8') as f:
                f.write("""
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
    background-color: #f5f5f5;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

h1, h2, h3 {
    color: #333;
}

.parameter-selector {
    margin-bottom: 20px;
}

.chart-container {
    background-color: white;
    padding: 20px;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}

.stats-container {
    background-color: white;
    padding: 20px;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}

.stats-table {
    width: 100%;
    border-collapse: collapse;
}

.stats-table th, .stats-table td {
    padding: 8px;
    border: 1px solid #ddd;
    text-align: center;
}

.stats-table th {
    background-color: #f2f2f2;
}

.blue-text {
    color: blue;
}

.brown-text {
    color: brown;
}

.footer {
    margin-top: 40px;
    padding-top: 20px;
    border-top: 1px solid #ddd;
    color: #777;
    font-size: 0.9em;
}

.batch-list ul {
    list-style-type: none;
    padding: 0;
}

.batch-list li {
    margin: 10px 0;
    padding: 10px;
    background-color: white;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.batch-list a {
    color: #0066cc;
    text-decoration: none;
    font-weight: bold;
}

.batch-list a:hover {
    text-decoration: underline;
}

.param-list {
    list-style-type: none;
    padding: 0;
    display: flex;
    flex-wrap: wrap;
}

.param-list li {
    margin: 10px;
    padding: 10px;
    background-color: white;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.param-list a {
    color: #0066cc;
    text-decoration: none;
    font-weight: bold;
}

.param-list a:hover {
    text-decoration: underline;
}
                """)
            
        # 确保至少有一个默认的JS文件
        default_js_path = os.path.join(js_dir, 'script.js')
        if not os.path.exists(default_js_path):
            with open(default_js_path, 'w', encoding='utf-8') as f:
                f.write("""
document.addEventListener('DOMContentLoaded', function() {
    const paramSelect = document.getElementById('param-select');
    if (paramSelect) {
        paramSelect.addEventListener('change', function() {
            const selectedParam = this.value;
            window.location.href = selectedParam + '_report.html';
        });
    }
});
                """)
            
        # 复制CSS文件
        css_files = [f for f in os.listdir(css_dir) if f.endswith('.css')]
        for css_file in css_files:
            src = os.path.join(css_dir, css_file)
            dst = os.path.join(output_css_dir, css_file)
            shutil.copy2(src, dst)
            
        # 复制JS文件
        js_files = [f for f in os.listdir(js_dir) if f.endswith('.js')]
        for js_file in js_files:
            src = os.path.join(js_dir, js_file)
            dst = os.path.join(output_js_dir, js_file)
            shutil.copy2(src, dst)
            
    def create_template(self):
        """
        创建HTML模板
        
        Returns:
            str: 模板文件路径
        """
        # 创建模板文件路径
        template_path = os.path.join(self.template_dir, 'report_template.html')
        
        # 创建模板内容
        template_content = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>晶圆厂CP测试数据分析报告 - {{ param }}</title>
    <link rel="stylesheet" href="static/css/style.css">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="static/js/script.js"></script>
</head>
<body>
    <div class="container">
        <h1>晶圆厂CP测试数据分析报告</h1>
        
        <div class="parameter-selector">
            <label for="param-select">选择参数：</label>
            <select id="param-select">
                {% for p in params %}
                <option value="{{ p }}" {% if p == param %}selected{% endif %}>{{ p }}</option>
                {% endfor %}
            </select>
        </div>
        
        <h2>参数：{{ param }}</h2>
        
        <div class="chart-container">
            {{ chart_html|safe }}
        </div>
        
        <div class="stats-container">
            <h3>统计信息</h3>
            <table class="stats-table">
                <tr>
                    <th>批次</th>
                    <th>平均值</th>
                    <th>标准差</th>
                    <th>中位数</th>
                    <th>最小值</th>
                    <th>最大值</th>
                    <th>数据点数</th>
                </tr>
                {% for lot, stat in stats.by_lot.items() %}
                <tr>
                    <td>{{ lot }}</td>
                    <td class="blue-text">{{ "%.4f"|format(stat.mean) }}</td>
                    <td class="brown-text">{{ "%.4f"|format(stat.std) }}</td>
                    <td>{{ "%.4f"|format(stat.median) }}</td>
                    <td>{{ "%.4f"|format(stat.min) }}</td>
                    <td>{{ "%.4f"|format(stat.max) }}</td>
                    <td>{{ stat.count }}</td>
                </tr>
                {% endfor %}
                <tr>
                    <td><strong>总体</strong></td>
                    <td class="blue-text"><strong>{{ "%.4f"|format(stats.overall.mean) }}</strong></td>
                    <td class="brown-text"><strong>{{ "%.4f"|format(stats.overall.std) }}</strong></td>
                    <td><strong>{{ "%.4f"|format(stats.overall.median) }}</strong></td>
                    <td><strong>{{ "%.4f"|format(stats.overall.min) }}</strong></td>
                    <td><strong>{{ "%.4f"|format(stats.overall.max) }}</strong></td>
                    <td><strong>{{ stats.overall.count }}</strong></td>
                </tr>
            </table>
        </div>
        
        <div class="footer">
            <p>生成时间：{{ timestamp }}</p>
            <p>晶圆厂CP测试数据分析工具</p>
        </div>
    </div>
</body>
</html>
"""
        
        # 确保模板目录存在
        os.makedirs(os.path.dirname(template_path), exist_ok=True)
        
        # 写入模板文件
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
            
        return template_path
    
    def generate_report(self, param):
        """
        生成HTML报告
        
        Args:
            param (str): 参数名称
            
        Returns:
            str: HTML报告文件路径
        """
        # 确保静态资源已复制到输出目录
        self._copy_static_files()
        
        # 创建模板
        template_path = self.create_template()
        
        # 检查analyzer是否为None
        if self.analyzer is None:
            print(f"错误: analyzer对象为None，无法生成参数 {param} 的图表")
            return None
            
        # 检查chart_generator是否为None
        if self.chart_generator is None:
            print(f"错误: chart_generator对象为None，无法生成参数 {param} 的图表")
            return None
        
        # 生成图表
        try:
            fig = self.chart_generator.generate_boxplot_with_scatter(param)
            if fig is None:
                print(f"错误: 无法生成参数 {param} 的图表")
                return None
        except Exception as e:
            print(f"错误: 生成参数 {param} 的图表时出错: {str(e)}")
            return None
            
        # 获取图表HTML
        try:
            chart_html = pio.to_html(fig, include_plotlyjs=False, full_html=False)
        except Exception as e:
            print(f"错误: 转换参数 {param} 的图表为HTML时出错: {str(e)}")
            return None
        
        # 获取统计信息
        try:
            stats = self.analyzer.calculate_statistics(param)
            if stats is None:
                print(f"错误: 无法获取参数 {param} 的统计信息")
                return None
        except Exception as e:
            print(f"错误: 计算参数 {param} 的统计信息时出错: {str(e)}")
            return None
            
        # 获取所有参数
        try:
            params = [p for p in self.analyzer.target_params if p in self.analyzer.df_clean.columns]
        except Exception as e:
            print(f"错误: 获取参数列表时出错: {str(e)}")
            params = [param]  # 至少包含当前参数
        
        # 创建模板环境
        try:
            env = jinja2.Environment(loader=jinja2.FileSystemLoader(self.template_dir))
            template = env.get_template('report_template.html')
        except Exception as e:
            print(f"错误: 加载模板时出错: {str(e)}")
            # 尝试使用字符串模板
            env = jinja2.Environment(loader=jinja2.BaseLoader())
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            template = env.from_string(template_content)
        
        # 渲染模板
        try:
            html_content = template.render(
                param=param,
                params=params,
                chart_html=chart_html,
                stats=stats,
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
        except Exception as e:
            print(f"错误: 渲染模板时出错: {str(e)}")
            return None
        
        # 创建HTML报告文件路径
        report_path = os.path.join(self.output_dir, f"{param}_report.html")
        
        # 写入HTML报告文件
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
        except Exception as e:
            print(f"错误: 写入HTML报告文件时出错: {str(e)}")
            return None
            
        print(f"HTML报告已生成: {report_path}")
        
        return report_path
    
    def generate_index(self, report_files):
        """
        生成索引页面
        
        Args:
            report_files (list): HTML报告文件路径列表
            
        Returns:
            str: 索引页面文件路径
        """
        # 创建索引页面文件路径
        index_path = os.path.join(self.output_dir, "index.html")
        
        # 创建索引页面内容
        index_content = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>晶圆厂CP测试数据分析报告</title>
    <link rel="stylesheet" href="static/css/style.css">
</head>
<body>
    <div class="container">
        <h1>晶圆厂CP测试数据分析报告</h1>
        
        <h2>参数列表</h2>
        
        <ul class="param-list">
            {% for file in report_files %}
            <li><a href="{{ file }}">{{ file|replace('_report.html', '') }}</a></li>
            {% endfor %}
        </ul>
        
        <div class="footer">
            <p>生成时间：{{ timestamp }}</p>
            <p>晶圆厂CP测试数据分析工具</p>
        </div>
    </div>
</body>
</html>
"""
        
        # 创建模板环境
        env = jinja2.Environment(loader=jinja2.BaseLoader())
        template = env.from_string(index_content)
        
        # 获取报告文件名
        report_file_names = [os.path.basename(f) for f in report_files]
        
        # 渲染模板
        html_content = template.render(
            report_files=report_file_names,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        # 写入索引页面文件
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print(f"索引页面已生成: {index_path}")
        
        return index_path
    
    def generate_batch_index(self, batch_dirs, batch_info=None):
        """
        生成批次索引页面
        
        Args:
            batch_dirs (list): 批次目录列表
            batch_info (dict, optional): 批次信息字典，包含批次的统计数据
            
        Returns:
            str: 批次索引页面文件路径
        """
        # 创建批次索引页面文件路径
        index_path = os.path.join(self.output_dir, "index.html")
        
        # 复制静态资源到输出目录
        self._copy_static_files()
        
        # 如果没有提供批次信息，创建一个空字典
        if batch_info is None:
            batch_info = {}
        
        # 创建批次索引页面内容
        index_content = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>晶圆厂CP测试数据分析报告 - 批次索引</title>
    <link rel="stylesheet" href="static/css/style.css">
    <style>
        .batch-container {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .batch-card {
            flex: 1 1 300px;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
            transition: transform 0.2s;
        }
        
        .batch-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .batch-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #0066cc;
        }
        
        .batch-info {
            font-size: 14px;
            color: #666;
            margin-bottom: 15px;
        }
        
        .batch-stats {
            display: flex;
            justify-content: space-between;
            margin-bottom: 15px;
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-value {
            font-size: 18px;
            font-weight: bold;
            color: #333;
        }
        
        .stat-label {
            font-size: 12px;
            color: #777;
        }
        
        .batch-link {
            display: block;
            text-align: center;
            background-color: #0066cc;
            color: white;
            padding: 8px 0;
            border-radius: 4px;
            text-decoration: none;
            font-weight: bold;
            transition: background-color 0.2s;
        }
        
        .batch-link:hover {
            background-color: #0055aa;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>晶圆厂CP测试数据分析报告</h1>
        <h2>批次索引</h2>
        
        <div class="batch-container">
            {% for batch_dir in batch_dirs %}
            <div class="batch-card">
                <div class="batch-title">{{ batch_dir }}</div>
                <div class="batch-info">
                    批次号: {{ batch_info.get(batch_dir, {}).get('lot_number', '未知') }}<br>
                    处理时间: {{ batch_info.get(batch_dir, {}).get('process_time', '未知') }}
                </div>
                <div class="batch-stats">
                    <div class="stat-item">
                        <div class="stat-value">{{ batch_info.get(batch_dir, {}).get('wafer_count', '?') }}</div>
                        <div class="stat-label">晶圆数量</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{{ batch_info.get(batch_dir, {}).get('record_count', '?') }}</div>
                        <div class="stat-label">记录数</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{{ batch_info.get(batch_dir, {}).get('param_count', '?') }}</div>
                        <div class="stat-label">参数数</div>
                    </div>
                </div>
                <a href="{{ batch_dir }}/index.html" class="batch-link">查看详情</a>
            </div>
            {% endfor %}
        </div>
        
        <div class="footer">
            <p>生成时间：{{ timestamp }}</p>
            <p>晶圆厂CP测试数据分析工具</p>
        </div>
    </div>
</body>
</html>
"""
        
        # 创建模板环境
        env = jinja2.Environment(loader=jinja2.BaseLoader())
        template = env.from_string(index_content)
        
        # 渲染模板
        html_content = template.render(
            batch_dirs=batch_dirs,
            batch_info=batch_info,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        # 写入批次索引页面文件
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print(f"批次索引页面已生成: {index_path}")
        
        return index_path
    
    def generate_all_reports(self):
        """
        生成所有参数的HTML报告
        
        Returns:
            str: 索引页面文件路径
        """
        report_files = []
        
        # 生成每个参数的报告
        for param in self.analyzer.target_params:
            if param in self.analyzer.df_clean.columns:
                report_path = self.generate_report(param)
                if report_path:
                    report_files.append(report_path)
        
        if not report_files:
            print("错误: 没有生成任何报告")
            return None
            
        # 生成索引页面
        index_path = self.generate_index(report_files)
        
        return index_path