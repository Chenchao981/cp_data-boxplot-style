@echo off
echo ==========================================
echo   晶圆CP测试数据单位调整工具
echo ==========================================
echo.

cd /d %~dp0
python scripts/adjust_units.py --output-dir ./output %*

echo.
if %ERRORLEVEL% EQU 0 (
    echo 单位调整成功完成！
    echo 请检查output目录下的报告文件。
) else (
    echo 单位调整过程中出现错误，请检查日志。
)

pause 