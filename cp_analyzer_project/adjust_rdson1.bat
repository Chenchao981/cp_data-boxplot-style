@echo off
echo ==========================================
echo   晶圆CP测试数据RDSON1单位调整工具
echo ==========================================
echo.

cd /d %~dp0

echo 开始执行单位调整 - %date% %time% > rdson1_adjust_log.txt
echo 命令: python scripts/adjust_units.py --output-dir ./output --params RDSON1 %* >> rdson1_adjust_log.txt
echo. >> rdson1_adjust_log.txt

python scripts/adjust_units.py --output-dir ./output --params RDSON1 %* >> rdson1_adjust_log.txt 2>&1

set ERRORLEVEL_VAL=%ERRORLEVEL%

echo. >> rdson1_adjust_log.txt
echo 执行完成 - %date% %time% >> rdson1_adjust_log.txt
echo 退出代码: %ERRORLEVEL_VAL% >> rdson1_adjust_log.txt

echo.
if %ERRORLEVEL_VAL% EQU 0 (
    echo RDSON1单位调整成功完成！
    echo 请检查output目录下的报告文件。
    echo 详细日志已保存到 rdson1_adjust_log.txt
) else (
    echo 单位调整过程中出现错误，请检查日志文件 rdson1_adjust_log.txt
)

pause 