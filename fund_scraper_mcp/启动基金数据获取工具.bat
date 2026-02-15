@echo off
chcp 65001 >nul
echo ========================================
echo    基金数据获取工具 - 启动器
echo ========================================
echo.

cd /d "%~dp0"

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [检测] Python 已安装
python --version

REM 检查依赖是否安装
echo.
echo [检测] 正在检查依赖...
python -c "import playwright; import mcp; import aiohttp" >nul 2>&1
if errorlevel 1 (
    echo [警告] 缺少依赖，正在自动安装...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)

echo [检测] 依赖检查完毕
echo.
echo [启动] 正在启动图形界面...
echo.

REM 运行图形界面
python fund_scraper_gui.py

if errorlevel 1 (
    echo.
    echo [错误] 程序运行出错
    pause
)
