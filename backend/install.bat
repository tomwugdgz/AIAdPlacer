@echo off
chcp 65001 >nul
REM ═══════════════════════════════════════════════════════════════
REM pDOOH 服务端一键安装脚本 (Windows)
REM 版本: 2.0
REM 说明: 自动检查环境、创建虚拟环境、安装依赖、初始化配置
REM ═══════════════════════════════════════════════════════════════

title pDOOH 服务端安装器

echo.
echo ═══════════════════════════════════════════════════════════════
echo    pDOOH 服务端一键安装脚本
echo ═══════════════════════════════════════════════════════════════
echo.

REM ── 检查 Python 版本 ─────────────────────────────────────────────────
echo [1/6] 检查 Python 版本...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8 或更高版本
    echo        下载地址: https://www.python.org/downloads/
    echo        安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)

REM 获取 Python 版本号
for /f "tokens=2 delims= " %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [成功] 检测到 Python %PYTHON_VERSION%

REM 检查版本是否 >= 3.8
python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"
if errorlevel 1 (
    echo [错误] Python 版本过低，需要 3.8 或更高版本
    echo        当前版本: %PYTHON_VERSION%
    pause
    exit /b 1
)
echo [成功] Python 版本检查通过

REM ── 创建虚拟环境 ─────────────────────────────────────────────────────
echo.
echo [2/6] 创建 Python 虚拟环境...
if exist venv (
    echo [提示] 虚拟环境已存在，跳过创建
) else (
    python -m venv venv
    if errorlevel 1 (
        echo [错误] 虚拟环境创建失败
        pause
        exit /b 1
    )
    echo [成功] 虚拟环境创建完成
)

REM ── 激活虚拟环境并升级 pip ──────────────────────────────────────────
echo.
echo [3/6] 升级 pip...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo [警告] pip 升级失败，尝试使用默认源...
    python -m pip install --upgrade pip
)
echo [成功] pip 已升级

REM ── 安装依赖 ─────────────────────────────────────────────────────────
echo.
echo [4/6] 安装 Python 依赖包（这可能需要几分钟）...
echo [提示] 使用清华大学镜像源加速下载
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo [警告] 使用镜像源安装失败，尝试使用默认源...
    pip install -r requirements.txt
)
if errorlevel 1 (
    echo [错误] 依赖安装失败，请检查 requirements.txt
    pause
    exit /b 1
)
echo [成功] 依赖安装完成

REM ── 创建 .env 配置文件 ─────────────────────────────────────────────
echo.
echo [5/6] 创建环境配置文件...
if exist .env (
    echo [提示] .env 文件已存在，跳过创建
) else (
    if exist .env.example (
        copy .env.example .env >nul
        echo [成功] 已根据 .env.example 创建 .env 文件
        echo [重要] 请编辑 .env 文件，填入正确的配置值
    ) else (
        echo # pDOOH 环境变量配置 > .env
        echo # 请参考以下说明编辑此文件 >> .env
        echo. >> .env
        echo # 数据库配置 >> .env
        echo DATABASE_URL=sqlite:///./pdooh.db >> .env
        echo. >> .env
        echo # Redis 配置（可选） >> .env
        echo REDIS_URL=redis://127.0.0.1:6379/0 >> .env
        echo. >> .env
        echo # 腾讯地图 API Key（可选，用于地理位置查询） >> .env
        echo TENCENT_MAP_KEY=your_tencent_map_key_here >> .env
        echo. >> .env
        echo # 调试模式 >> .env
        echo DEBUG=true >> .env
        echo. >> .env
        echo # LLM 配置 >> .env
        echo LLM_PROVIDER=ollama >> .env
        echo OLLAMA_BASE_URL=http://127.0.0.1:11434 >> .env
        echo OLLAMA_MODEL=qwen2.5:latest >> .env
        echo LLM_ENABLED=false >> .env
        echo. >> .env
        echo [成功] 已创建默认 .env 文件
        echo [重要] 请编辑 .env 文件，填入正确的配置值
    )
)

REM ── 检查数据库文件 ───────────────────────────────────────────────────
echo.
echo [6/6] 检查数据库文件...
set DB_COUNT=0
if exist "亲邻单元门智能框架.db" set /a DB_COUNT+=1
if exist "亲邻门禁全国点位.db" set /a DB_COUNT+=1
if exist "亲邻广州道闸.db" set /a DB_COUNT+=1
if exist "亲邻商场LED.db" set /a DB_COUNT+=1

if %DB_COUNT% EQU 0 (
    echo [提示] 未找到媒体资源数据库文件（.db）
    echo        请将以下数据库文件放到 backend/ 目录：
    echo          - 亲邻单元门智能框架.db
    echo          - 亲邻门禁全国点位.db
    echo          - 亲邻广州道闸.db
    echo          - 亲邻商场LED.db
) else (
    echo [成功] 找到 %DB_COUNT% 个数据库文件
)

REM ── 安装完成 ─────────────────────────────────────────────────────────
echo.
echo ═══════════════════════════════════════════════════════════════
echo    安装完成！
echo ═══════════════════════════════════════════════════════════════
echo.
echo 接下来的步骤：
echo.
echo 1. 编辑 .env 文件，配置环境变量
echo    记事本打开: notepad .env
echo.
echo 2. 启动所有 Agent：
echo    双击运行: start_all.bat
echo    或命令行: python run_all_agents.py
echo.
echo 3. 访问服务：
echo    - MCP Server:      http://127.0.0.1:5002/health
echo    - Tom Agent:      http://127.0.0.1:5003/health
echo    - ROI Agent:      http://127.0.0.1:5004/health
echo    - Competitor Agent: http://127.0.0.1:5005/health
echo.
echo 4. 查看完整文档：
echo    打开 README.md 查看详细使用说明
echo.
pause
