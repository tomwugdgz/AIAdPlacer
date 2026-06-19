@echo off
chcp 65001 >nul
REM ═══════════════════════════════════════════════════════════════
REM pDOOH 服务端一键启动脚本 (Windows)
REM 版本: 2.0
REM 说明: 激活虚拟环境并启动所有 Agent（MCP/Tom/ROI/Competitor）
REM ═══════════════════════════════════════════════════════════════

title pDOOH 服务端 - 所有 Agent

echo.
echo ═══════════════════════════════════════════════════════════════
echo    pDOOH 服务端启动器
echo ═══════════════════════════════════════════════════════════════
echo.

REM ── 检查虚拟环境是否存在 ───────────────────────────────────────────
if not exist venv (
    echo [错误] 虚拟环境不存在，请先运行 install.bat 安装
    echo.
    pause
    exit /b 1
)

REM ── 激活虚拟环境 ─────────────────────────────────────────────────────
echo [1/3] 激活虚拟环境...
call venv\Scripts\activate.bat
echo [成功] 虚拟环境已激活

REM ── 检查 .env 文件 ──────────────────────────────────────────────────
echo.
echo [2/3] 检查环境配置...
if not exist .env (
    echo [警告] .env 文件不存在，将使用默认配置
    echo         建议先运行 install.bat 创建配置文件
)

REM ── 启动所有 Agent ──────────────────────────────────────────────────
echo.
echo [3/3] 启动所有 Agent...
echo.
echo ═══════════════════════════════════════════════════════════════
echo    启动的 Agent 和服务端口：
echo    - MCP Server (pDOOH MCP 工具):      端口 5002
echo    - Tom Agent (户外广告投放专家):       端口 5003
echo    - ROI Agent (ROI 计算专家):          端口 5004
echo    - Competitor Agent (竞品监测):       端口 5005
echo ═══════════════════════════════════════════════════════════════
echo.
echo 提示: 按 Ctrl+C 停止所有 Agent
echo.

python run_all_agents.py

REM ── 如果程序退出，等待用户按键 ────────────────────────────────────
echo.
echo [信息] 所有 Agent 已停止
pause
