@echo off
chcp 65001 >nul
echo ========================================
echo    基金数据获取工具 - 启动器
echo ========================================
echo.

REM 进入 fund_scraper_mcp 目录并运行主程序
cd /d "%~dp0fund_scraper_mcp"

REM 调用实际的启动脚本
call "启动基金数据获取工具.bat"

REM 返回原目录
cd /d "%~dp0"
