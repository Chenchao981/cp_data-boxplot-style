#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
晶圆厂CP测试数据图表生成模块
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
import os
import json

class CPChartGenerator:
    """
    CP测试数据图表生成类
    
    用于生成各种数据可视化图表
    """
    
    def __init__(self, analyzer=None):
        """
        初始化图表生成器
        
        Args:
            analyzer (CPDataAnalyzer): 数据分析器对象
        """
        self.analyzer = analyzer
        self.charts = {}
        self.output_dir = "./output"
    
    def generate_boxplot_with_scatter(self, param):
        """
        生成带散点图的箱线图
        
        Args:
            param (str): 参数名称
            
        Returns:
            Figure: Plotly图表对象
        """
        # 获取分析器中的数据
        if not self.analyzer:
            print(f"错误: 分析器对象未设置")
            return None
            
        # 确保df_clean字段已设置
        if self.analyzer.df_clean is None or self.analyzer.df_clean.empty:
            print(f"错误: 分析器的df_clean字段为空或未设置")
            return None
            
        # 确保参数在数据中存在
        if param not in self.analyzer.df_clean.columns:
            print(f"错误: 参数 {param} 不在清洗后的数据中")
            return None
            
        # 获取统计信息
        stats = self.analyzer.calculate_statistics(param)
        if not stats:
            print(f"错误: 无法计算参数 {param} 的统计信息")
            return None
            
        # 获取所有晶圆片并排序
        wafers = sorted(stats['by_lot'].keys())
        
        # 创建子图，为表格预留空间
        fig = make_subplots(
            rows=2, 
            cols=1,
            row_heights=[0.85, 0.15],  # 图表占85%，表格占15%
            vertical_spacing=0.03,  # 减小垂直间距
            specs=[[{"type": "scatter"}], [{"type": "table"}]]
        )
        
        # 获取参数信息
        param_info = self.analyzer.get_parameter_info(param)
        
        # 获取箱型图数据
        boxplot_data = self.analyzer.get_data_for_boxplot(param)
        if boxplot_data is None or len(boxplot_data['y']) == 0:
            print(f"错误: 无法获取参数 {param} 的箱型图数据或数据为空")
            return None
        
        # 获取散点图数据
        scatter_data = self.analyzer.get_data_for_scatter(param)
        if scatter_data is None or len(scatter_data['y']) == 0:
            print(f"错误: 无法获取参数 {param} 的散点图数据或数据为空")
            return None
            
        # 获取统计信息
        stats = self.analyzer.calculate_statistics(param)
        if stats is None:
            print(f"错误: 无法获取参数 {param} 的统计信息")
            return None
            
        # 获取参数限制
        limits = param_info['limits']
        
        # 获取晶圆片列表并排序
        wafers = sorted(set(boxplot_data['x']))
        
        # 设置Y轴范围
        y_min = min(boxplot_data['y']) * 0.95 if boxplot_data['y'] else 0
        y_max = max(boxplot_data['y']) * 1.05 if boxplot_data['y'] else 1000
        
        # 如果有上下限，则考虑上下限
        if limits.get('upper') is not None:
            y_max = max(y_max, limits['upper'] * 1.1)
        if limits.get('lower') is not None:
            y_min = min(y_min, limits['lower'] * 0.9)
        
        # 确保Y轴范围包含600，用于显示标签
        y_min = min(y_min, 550)  # 确保Y轴下限低于最低标签位置
        
        # 添加箱型图
        fig.add_trace(go.Box(
            x=[float(wafers.index(x)) + 0.5 for x in boxplot_data['x']],  # 将x坐标转换为数值并向右平移0.5格
            y=boxplot_data['y'],
            name='VALUE',
            boxpoints='all',  # 显示所有点
            jitter=0.3,  # 点的抖动程度
            pointpos=0,  # 点的位置
            marker=dict(
                color='#1f77b4',  # D3 Category10 蓝色
                size=1,  # 进一步减小散点大小
                opacity=0.7  # 提高不透明度以增加可见性
            ),
            line=dict(
                color='#1f77b4',  # D3 Category10 蓝色
                width=0.75  # 进一步减小线条宽度
            ),
            fillcolor='rgba(31, 119, 180, 0.1)',  # D3 蓝色半透明
            whiskerwidth=0.3,  # 胡须宽度进一步变细
            boxmean=True,  # 显示均值
            showlegend=False
        ))
        
        # 计算每个晶圆片的平均值，用于添加平均值标记
        wafer_means = {}
        wafer_stds = {}
        for wafer in wafers:
            if wafer in stats['by_lot']:
                wafer_means[wafer] = stats['by_lot'][wafer]['mean']
                wafer_stds[wafer] = stats['by_lot'][wafer]['std']
        
        # 添加平均值标记
        avg_x = []
        avg_y = []
        
        for wafer in wafers:
            if wafer in wafer_means and wafer_means[wafer] is not None:
                avg_x.append(wafer)
                avg_y.append(wafer_means[wafer])
        
        fig.add_trace(go.Scatter(
            x=[float(wafers.index(x)) + 0.5 for x in avg_x],  # 将平均值标记的x坐标转换为数值并向右平移0.5格
            y=avg_y,
            mode='markers',
            name='Average',
            marker=dict(
                symbol='triangle-up',
                color='red',
                size=10,
                line=dict(
                    color='darkred',
                    width=1
                )
            ),
            showlegend=False
        ))
        
        # 添加交替的背景色带，使数据更容易阅读
        for i in range(len(wafers)):
            x_pos = i + 0.5  # 将垂直网格线向右平移0.5格
            fig.add_shape(
                type="line",
                x0=x_pos,
                y0=y_min,
                x1=x_pos,
                y1=y_max,
                line=dict(
                    color="rgba(180, 180, 180, 0.5)",  # 调整颜色为更柔和的灰色，增加不透明度
                    width=1,
                    dash="dash"  # 使用虚线样式
                ),
                row=1,  # 指定添加到第一行（图表）
                col=1
            )
            
            # 添加交替的背景色带，使数据更容易阅读
            if i % 2 == 0:  # 偶数列添加浅色背景
                fig.add_shape(
                    type="rect",
                    x0=i,
                    y0=y_min,
                    x1=i+1,
                    y1=y_max,
                    fillcolor="rgba(240, 240, 240, 0.3)",  # 非常浅的灰色
                    line=dict(width=0),
                    layer="below",
                    row=1,
                    col=1
                )
        
        # 设置图表布局
        fig.update_layout(
            title=dict(
                text=f"Box Plot: {param}",
                font=dict(size=14),
                x=0.5,
                y=0.95,
                xanchor='center',
                yanchor='top'
            ),
            xaxis=dict(
                title=dict(text=''),
                tickmode='array',
                tickvals=list(range(len(wafers))),
                ticktext=[''] * len(wafers),  # 隐藏X轴标签，使用表格的标签
                gridcolor='rgba(200, 200, 200, 0.2)',  # 淡化X轴网格线
                showgrid=False,  # 不显示默认网格线，我们已经添加了自定义的垂直线
                zeroline=False,
                showticklabels=False,
                range=[0, len(wafers)]  # 保持x轴范围不变，因为我们已经调整了数据点的位置
            ),
            yaxis=dict(
                title=dict(
                    text='VALUE',
                    standoff=30  # 增加标题与轴的距离
                ),
                zeroline=False,
                range=[y_min, y_max],  # 设置Y轴范围
                gridcolor='rgba(200, 200, 200, 0.3)',  # 调整Y轴网格线颜色
                showgrid=True,
                gridwidth=1,
                griddash='dot',  # 使用点线样式
                side="left",  # 确保Y轴在左侧
                automargin=True  # 自动调整Y轴标签的边距
            ),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=-0.35 + (3 * 0.031),  # 向上移动3个单元格距离，每个单元格高度约为0.031
                xanchor='center',
                x=0.5
            ),
            margin=dict(
                l=120,  # 增加左侧边距，为标签列和Y轴留出足够空间
                r=50,
                t=100,
                b=100  # 减小底部边距，因为表格现在是子图
            ),
            height=900,  # 增加图表高度
            width=1200,
            hovermode='closest',
            showlegend=True,
            plot_bgcolor='rgba(250, 250, 250, 0.5)'  # 使用非常浅的灰色作为图表背景
        )
        
        # 如果有上限，则添加水平红色虚线
        if limits.get('upper') is not None:
            fig.add_shape(
                type="line",
                x0=0,  # 调整起始位置
                y0=limits['upper'],
                x1=len(wafers),  # 调整结束位置
                y1=limits['upper'],
                line=dict(
                    color="red",
                    width=2,
                    dash="dash",
                ),
                name="USL"
            )
            # 添加USL标签
            fig.add_annotation(
                x=0,  # 调整标签位置
                y=limits['upper'],
                text=f"USL:{limits['upper']}",
                showarrow=False,
                font=dict(
                    color="red",
                    size=12
                ),
                xanchor="left"
            )
        
        # 如果有下限，则添加水平红色虚线
        if limits.get('lower') is not None:
            fig.add_shape(
                type="line",
                x0=0,  # 调整起始位置
                y0=limits['lower'],
                x1=len(wafers),  # 调整结束位置
                y1=limits['lower'],
                line=dict(
                    color="red",
                    width=2,
                    dash="dash",
                ),
                name="LSL"
            )
            # 添加LSL标签
            fig.add_annotation(
                x=0,  # 调整标签位置
                y=limits['lower'],
                text=f"LSL:{limits['lower']}",
                showarrow=False,
                font=dict(
                    color="red",
                    size=12
                ),
                xanchor="left"
            )
        
        # 保存图表
        self.charts[param] = fig
        
        # 添加数据表格，显示每个Wafer的平均值和标准差
        self._add_wafer_stats_table(fig, param, stats)
        
        return fig
        
    def _add_wafer_stats_table(self, fig, param, stats):
        """
        向图表添加Wafer统计信息表格
        
        Args:
            fig (Figure): Plotly图表对象
            param (str): 参数名称
            stats (dict): 统计信息字典
        """
        # 获取所有晶圆片并排序
        wafers = sorted(stats['by_lot'].keys())
        
        # 定义nA单位的参数列表
        na_unit_params = ['IDSS1', 'IGSS2', 'IGSSR2', 'IDSS2']  # 纳安培单位的参数
        
        # 提取每个晶圆片的平均值和标准差
        avg_values = []
        std_values = []
        
        for wafer in wafers:
            wafer_stats = stats['by_lot'][wafer]
            mean_value = wafer_stats['mean']
            std_value = wafer_stats['std']
            
            # 根据参数类型选择不同的格式化方式
            if param in na_unit_params:
                # 纳安培单位参数，将安培转换为纳安培，1nA=1e-9A
                mean_value_na = mean_value * 1e9
                std_value_na = std_value * 1e9
                # 保留两位小数
                avg_values.append(f"{mean_value_na:.2f}")
                std_values.append(f"{std_value_na:.2f}")
            else:
                # 其他参数保持原来的精度
                if abs(mean_value) >= 100:
                    # 大数值保留1位小数
                    avg_values.append(f"{mean_value:.1f}")
                elif abs(mean_value) >= 10:
                    # 中等数值保留2位小数
                    avg_values.append(f"{mean_value:.2f}")
                else:
                    # 小数值保留3位小数
                    avg_values.append(f"{mean_value:.3f}")
                
                # 标准差通常需要更多精度
                if abs(std_value) >= 10:
                    std_values.append(f"{std_value:.2f}")
                else:
                    std_values.append(f"{std_value:.3f}")
        
        # 获取批次号
        lot_number = ""
        if not self.analyzer.df_clean.empty:
            lot_number = self.analyzer.df_clean['Lot'].iloc[0]
        
        # 在Plotly中，表格的values参数是按列组织的，每个列表代表一列数据
        columns = []
        
        # 添加数据列
        for i in range(len(wafers)):
            columns.append([avg_values[i], std_values[i], wafers[i]])
        
        # 添加表格到图表的第二行
        fig.add_trace(
            go.Table(
                columnwidth=[0.035] * len(wafers),  # 所有列宽度一致
                cells=dict(
                    values=columns,
                    line_color='darkslategray',
                    fill_color=[
                        ['white', 'white', 'white'] if i % 2 == 1 else ['rgba(240, 240, 240, 0.5)', 'rgba(240, 240, 240, 0.5)', 'rgba(240, 240, 240, 0.5)'] 
                        for i in range(len(wafers))  # 数据列背景色，偶数列使用浅色背景
                    ],
                    align=['center'] * len(wafers),  # 数据列居中
                    font=dict(
                        color=[
                            ['blue', 'brown', 'black'] for _ in range(len(wafers))  # 数据列颜色
                        ],
                        size=11
                    ),
                    height=25
                )
            ),
            row=2,  # 指定添加到第二行（表格）
            col=1
        )
        
        # 添加标签文字，放置在Y轴坐标下方
        labels = ["Average", "StdDev", "WAFER_LOT"]
        
        # 在Y轴左侧添加标签，精确对齐表格行
        # 使用表格单元格的高度(25)来计算间隔，表格在paper坐标系中大约占据0.15的高度(从0.11到0.172差约0.062)
        # 对应3行，每行的高度约为0.031，与原来设置的高度基本一致
        # 向左移动0.2个单元格距离，每个单元格宽度为0.035，所以向左移动约0.007
        # 下移2个单元格距离，每个单元格高度约为0.031，所以下移约0.062
        # 再下移0.2个单元格距离，0.2*0.031=0.0062
        positions = [
            {"y": 0.104, "label": "Average"},     # 对应再下移0.2个单元格后的位置（原来是0.11）
            {"y": 0.073, "label": "StdDev"},      # 对应再下移0.2个单元格后的位置（原来是0.079）
            {"y": 0.042, "label": "WAFER_LOT"}    # 对应再下移0.2个单元格后的位置（原来是0.048）
        ]
        
        for pos in positions:
            fig.add_annotation(
                x=-0.002,  # 放置在Y轴左侧，向左移动0.2个单元格(原来是0.005，移动0.007)
                y=pos["y"],  # 使用预定义位置
                text=pos["label"],
                showarrow=False,
                font=dict(
                    color="black",
                    size=11,
                    family="Arial"
                ),
                xref="paper",
                yref="paper",
                xanchor="right",  # 右对齐
                yanchor="middle",
                align="right"
            )
        
        # 增加下方空间，添加批次信息在表格下方居中
        fig.add_annotation(
            x=0.5,
            y=-0.15 + (3 * 0.031),  # 向上移动3个单元格距离，每个单元格高度约为0.031
            xref="paper",
            yref="paper",
            text=f"{lot_number}",
            showarrow=False,
            font=dict(
                color="black",
                size=12
            ),
            align="center"
        )
        
    def save_chart(self, param, output_dir=None):
        """
        保存图表到HTML文件
        
        Args:
            param (str): 参数名称
            output_dir (str): 输出目录
            
        Returns:
            str: 保存的文件路径
        """
        if param not in self.charts:
            # 尝试生成图表
            fig = self.generate_boxplot_with_scatter(param)
            if fig is None:
                print(f"错误: 无法生成参数 {param} 的图表")
                return None
        
        # 使用指定的输出目录或默认输出目录
        output_dir = output_dir or self.output_dir
        
        # 确保输出目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # 保存图表
        filename = os.path.join(output_dir, f"{param}_chart.html")
        self.charts[param].write_html(filename)
        
        return filename
        
    def generate_all_charts(self, params=None):
        """
        生成所有参数的图表
        
        Args:
            params (list): 参数列表
            
        Returns:
            dict: 图表字典 {参数名: 图表对象}
        """
        if not self.analyzer:
            print("错误: 分析器对象未设置")
            return {}
            
        # 使用指定的参数列表或分析器中的目标参数
        params = params or self.analyzer.target_params
        
        charts = {}
        for param in params:
            fig = self.generate_boxplot_with_scatter(param)
            if fig:
                charts[param] = fig
                
        return charts