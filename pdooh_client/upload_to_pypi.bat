@echo off
chcp 65001 >nul
echo ==========================================
echo  pDOOH Client - PyPI 上传脚本
echo ==========================================
echo.

REM 检查是否已构建
if not exist "dist" (
    echo [错误] dist 目录不存在，请先运行构建命令：
    echo   python -m build
    pause
    exit /b 1
)

echo 检查 dist 目录中的文件...
dir dist\
echo.

echo 请手动执行以下命令上传到 PyPI：
echo.
echo     python -m twine upload dist/*
echo.
echo 执行后会提示输入：
echo   Username: dukcowlf
echo   Password: [你的 PyPI 密码]
echo.
echo 注意：密码输入时不会显示，直接输入后按回车即可
echo.
pause

REM 启动交互式上传
python -m twine upload dist/*

echo.
echo 上传完成！
echo.
echo 验证安装：
echo   pip install pdooh-client
echo.
pause
