@echo off
echo ==========================================
echo   晶圆CP测试数据处理工具
echo ==========================================
echo.

cd /d %~dp0

:: 设置数据目录和输出目录
set DATA_DIR=E:\data\rawdata
set OUTPUT_DIR=./output

:: 创建输出目录
if not exist %OUTPUT_DIR% mkdir %OUTPUT_DIR%

:: 处理每个批次
for /d %%b in ("%DATA_DIR%\*") do (
    echo.
    echo 处理批次: %%b
    echo.
    
    :: 获取批次名称
    for %%f in ("%%b") do set BATCH_NAME=%%~nxf
    
    :: 运行数据处理脚本
    python scripts/main.py --data-dir "%%b" --output-dir "%OUTPUT_DIR%/%BATCH_NAME%"
    
    :: 调整数据单位
    python scripts/adjust_units.py --output-dir "%OUTPUT_DIR%" --batch "%BATCH_NAME%"
    
    echo.
    echo 批次 %BATCH_NAME% 处理完成
    echo.
)

echo.
echo 所有批次处理完成！
echo 请检查 %OUTPUT_DIR% 目录下的报告文件。
echo.

pause 