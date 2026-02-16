@echo off
chcp 65001 >nul
echo ========================================
echo    基金数据快速获取工具
echo    使用天天基金API，速度快100倍
echo ========================================
echo.

cd /d "%~dp0fund_scraper_mcp"

REM 检查 Python 是否安装
python --version >nul 2>&1
if not errorlevel 1 (
    echo [检测] Python 已安装
    python --version
    set PYTHON_CMD=python
    goto :run
)

python3 --version >nul 2>&1
if not errorlevel 1 (
    echo [检测] Python 已安装 ^(python3^)
    python3 --version
    set PYTHON_CMD=python3
    goto :run
)

REM 尝试初始化 Conda (检查多个常见位置)
if exist "%USERPROFILE%\AppData\Local\anaconda3\Scripts\conda.exe" (
    call "%USERPROFILE%\AppData\Local\anaconda3\Scripts\activate.bat" "%USERPROFILE%\AppData\Local\anaconda3"
    goto :check_conda_python
)

if exist "%USERPROFILE%\anaconda3\Scripts\conda.exe" (
    call "%USERPROFILE%\anaconda3\Scripts\activate.bat" "%USERPROFILE%\anaconda3"
    goto :check_conda_python
)

if exist "%USERPROFILE%\AppData\Local\miniconda3\Scripts\conda.exe" (
    call "%USERPROFILE%\AppData\Local\miniconda3\Scripts\activate.bat" "%USERPROFILE%\AppData\Local\miniconda3"
    goto :check_conda_python
)

if exist "%USERPROFILE%\miniconda3\Scripts\conda.exe" (
    call "%USERPROFILE%\miniconda3\Scripts\activate.bat" "%USERPROFILE%\miniconda3"
    goto :check_conda_python
)

if exist "C:\ProgramData\anaconda3\Scripts\conda.exe" (
    call "C:\ProgramData\anaconda3\Scripts\activate.bat" "C:\ProgramData\anaconda3"
    goto :check_conda_python
)

if exist "C:\ProgramData\miniconda3\Scripts\conda.exe" (
    call "C:\ProgramData\miniconda3\Scripts\activate.bat" "C:\ProgramData\miniconda3"
    goto :check_conda_python
)

goto :no_python

:check_conda_python
python --version >nul 2>&1
if not errorlevel 1 (
    echo [检测] Python 已安装 ^(Conda环境^)
    python --version
    set PYTHON_CMD=python
    goto :run
)

:no_python

echo [错误] 未检测到 Python
echo.
echo 请安装 Python: https://www.python.org/downloads/
pause
exit /b 1

:run
echo.
echo [检测] 正在检查依赖...
%PYTHON_CMD% -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo [警告] 缺少 requests 库，正在安装...
    %PYTHON_CMD% -m pip install requests
)

echo [检测] 依赖检查完毕
echo.
echo [启动] 正在快速获取基金数据...
echo.

REM 运行快速获取脚本
%PYTHON_CMD% fetch_funds_fast.py

if errorlevel 1 (
    echo.
    echo [错误] 程序运行出错
    pause
    exit /b 1
)

echo.
echo [完成] 按任意键退出...
pause >nul
