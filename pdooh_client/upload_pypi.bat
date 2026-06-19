@echo off
echo ==========================================
echo  pDOOH Client - PyPI 安全上传脚本
echo ==========================================
echo.
echo 使用方法：
echo   1. 双击运行此脚本
echo   2. 输入 PyPI 用户名（默认：dukcowlf）
echo   3. 输入 PyPI 密码（Karen2tom）
echo.
echo 注意：密码会通过环境变量传递，不会出现在命令历史中
echo.

set /p PYPI_USER="PyPI 用户名 [%PYPI_USER%]: "

if not defined PYPI_USER set PYPI_USER=dukcowlf

echo.
echo 正在上传到 PyPI...
echo.

set TWINE_USERNAME=%PYPI_USER%
set TWINE_PASSWORD=Karen2tom

python -m twine upload dist/*

echo.
echo 上传完成！
pause
