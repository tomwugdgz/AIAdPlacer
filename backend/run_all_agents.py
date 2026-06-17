"""
一键启动所有 AIAdPlacer Agent
端口分配：
  - 5002: MCP Server（pdooh MCP 工具）
  - 5003: Tom Agent（户外广告投放专家）
  - 5004: ROI Agent（广告投放 ROI 计算专家）
  - 5005: 竞品监测 Agent

使用方式：
  python run_all_agents.py
"""

import os
import sys
import time
import subprocess
import signal
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("run_all")

# ── 配置 ────────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = os.path.join(BASE_DIR, "venv", "Scripts", "python.exe")

# 如果 venv 不存在，使用系统 Python
if not os.path.exists(VENV_PYTHON):
    VENV_PYTHON = sys.executable

PORTS = {
    "mcp": 5002,
    "tom": 5003,
    "roi": 5004,
    "competitor": 5005,
}

PROCESSES = {}

# ── 信号处理 ─────────────────────────────────────────────────────────────────────
def signal_handler(sig, frame):
    logger.info("收到停止信号，正在关闭所有 Agent...")
    for name, proc in PROCESSES.items():
        if proc and proc.poll() is None:
            logger.info(f"停止 {name} Agent (PID={proc.pid})...")
            proc.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ── 启动函数 ─────────────────────────────────────────────────────────────────────
def start_agent(name: str, script: str, port: int, env_vars: dict = None):
    """启动一个 Agent 进程"""
    cmd = [VENV_PYTHON, script, "--port", str(port)]
    env = os.environ.copy()
    if env_vars:
        env.update(env_vars)

    logger.info(f"启动 {name} Agent (端口 {port})...")
    proc = subprocess.Popen(
        cmd,
        cwd=BASE_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    PROCESSES[name] = proc
    logger.info(f"{name} Agent 已启动 (PID={proc.pid})")
    return proc

def wait_for_health(agent_name: str, port: int, timeout: int = 30):
    """等待 Agent 健康检查通过"""
    import httpx
    url = f"http://127.0.0.1:{port}/health"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = httpx.get(url, timeout=2.0)
            if resp.status_code == 200:
                logger.info(f"{agent_name} Agent 健康检查通过 (http://127.0.0.1:{port}/health)")
                return True
        except Exception:
            pass
        time.sleep(1.0)
    logger.warning(f"{agent_name} Agent 健康检查超时 (端口 {port})")
    return False

# ── 主函数 ─────────────────────────────────────────────────────────────────────
def main():
    logger.info("=" * 60)
    logger.info("AIAdPlacer 多 Agent 启动器")
    logger.info("=" * 60)

    # 1. 启动 MCP Server（端口 5002）
    start_agent("MCP", "app/pdooh_mcp.py", PORTS["mcp"])

    # 2. 启动 Tom Agent（端口 5003）
    start_agent("Tom", "app/tom_agent.py", PORTS["tom"])

    # 3. 启动 ROI Agent（端口 5004）
    start_agent("ROI", "app/roi_agent.py", PORTS["roi"])

    # 4. 启动竞品监测 Agent（端口 5005）
    competitor_script = os.path.join(BASE_DIR, "competitor_agent.py")
    if os.path.exists(competitor_script):
        start_agent("Competitor", "competitor_agent.py", PORTS["competitor"])
    else:
        logger.warning("竞品监测 Agent 脚本未找到，跳过")

    # 等待所有 Agent 健康检查通过
    logger.info("-" * 60)
    logger.info("等待所有 Agent 健康检查通过...")
    for name, port in PORTS.items():
        wait_for_health(name, port)

    # 打印访问地址
    logger.info("-" * 60)
    logger.info("所有 Agent 已启动！访问地址：")
    logger.info(f"  - MCP Server:      http://127.0.0.1:{PORTS['mcp']}/health")
    logger.info(f"  - Tom Agent:      http://127.0.0.1:{PORTS['tom']}/health")
    logger.info(f"  - ROI Agent:      http://127.0.0.1:{PORTS['roi']}/health")
    logger.info(f"  - Competitor Agent: http://127.0.0.1:{PORTS['competitor']}/health")
    logger.info("-" * 60)
    logger.info("按 Ctrl+C 停止所有 Agent")
    logger.info("=" * 60)

    # 保持主进程运行，等待子进程
    try:
        while True:
            # 检查子进程是否退出
            for name, proc in PROCESSES.items():
                if proc.poll() is not None:
                    logger.warning(f"{name} Agent 已退出 (返回码 {proc.returncode})")
            time.sleep(5.0)
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()
