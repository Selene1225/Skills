@echo off
chcp 65001 >nul
echo ========================================
echo    基金数据获取工具 - 启动器
echo ========================================
echo.

cd /d "%~dp0fund_scraper_mcp"

REM 检查 Python 是否安装（支持 conda 环境）
python --version >nul 2>&1
if not errorlevel 1 (
    echo [检测] Python 已安装 ^(系统Python^)
    python --version
    set PYTHON_CMD=python
    goto :check_deps
)

REM 尝试使用 python3
python3 --version >nul 2>&1
if not errorlevel 1 (
    echo [检测] Python 已安装 ^(python3^)
    python3 --version
    set PYTHON_CMD=python3
    goto :check_deps
)

REM 尝试激活 conda base 环境
where conda >nul 2>&1
if not errorlevel 1 (
    echo [检测] 发现 Conda，正在激活 base 环境...
    call conda activate base >nul 2>&1
    python --version >nul 2>&1
    if not errorlevel 1 (
        echo [检测] Python 已安装 ^(Conda环境^)
        python --version
        set PYTHON_CMD=python
        goto :check_deps
    )
)

REM 如果都找不到，报错
echo [错误] 未检测到 Python
echo.
echo 您可以：
echo 1. 安装 Python: https://www.python.org/downloads/
echo 2. 如果使用 Conda，请先运行: conda activate base
echo 3. 然后手动运行: python fund_scraper_gui.py
echo.
pause
exit /b 1

:check_deps
REM 检查依赖是否安装
echo.
echo [检测] 正在检查依赖...
%PYTHON_CMD% -c "import playwright; import mcp; import aiohttp" >nul 2>&1
if errorlevel 1 (
    echo [警告] 缺少依赖，正在自动安装...
    %PYTHON_CMD% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        echo.
        echo 请手动运行: pip install -r requirements.txt
        echo 或者使用 conda: conda install --file requirements.txt
        pause
        exit /b 1
    )
)

echo [检测] 依赖检查完毕
echo.
echo [启动] 正在启动图形界面...
echo.

REM 运行图形界面
%PYTHON_CMD% fund_scraper_gui.py

if errorlevel 1 (
    echo.
    echo [错误] 程序运行出错
    pause
)
