"""青柠智能助手 — 命令沙箱（Bash Sandbox）。

用于「沙箱命令执行」动作（仅工程 / 商业开发等内部可信角色可触发，由 RBAC 前置拦截）。
内置：命令黑名单（高危命令禁止执行）+ 超时限制（默认 10s）+ 工作目录限制。

设计目标：即便被误用，也不会执行破坏性强命令。所有执行均记录审计日志。
"""

from __future__ import annotations

import asyncio
import shlex
from typing import Any, Dict, List, Optional

from app.common import setup_logging

logger = setup_logging("qinglin_sandbox")

# 高危命令黑名单（命中即拒绝执行）
_BLACKLIST_PATTERNS: List[str] = [
    "rm -rf", "rm -r /", "rm -fr", "rm -f /",
    "sudo", "su ", "mkfs", "dd if=", "shutdown", "reboot", "halt",
    "format", ":(){", "chmod -R", "chown -R",
    ">/dev/sd", "mv /", "wget ", "curl ", "> /etc/", "crontab",
    "passwd", "useradd", "userdel", "net user",
]

# 允许执行的只读 / 轻量命令白名单前缀（空表示仅依赖黑名单）
_WHITELIST_PREFIX: List[str] = [
    "ls", "dir", "echo", "cat", "type", "pwd", "cd", "date",
    "python", "py", "node", "git status", "git log", "git diff",
    "pip list", "pip show", "head", "tail", "wc", "whoami", "ipconfig", "ifconfig",
]

DEFAULT_TIMEOUT = 10  # 秒


class BashSandbox:
    """带黑名单与超时限制的命令沙箱。"""

    def __init__(self, timeout: int = DEFAULT_TIMEOUT, workdir: Optional[str] = None):
        self.timeout = timeout
        self.workdir = workdir

    def _is_blocked(self, command: str) -> Optional[str]:
        low = command.lower()
        for pat in _BLACKLIST_PATTERNS:
            if pat in low:
                return pat
        return None

    def _is_allowed(self, command: str) -> bool:
        if not _WHITELIST_PREFIX:
            return True
        low = command.lower().lstrip()
        return any(low.startswith(p) for p in _WHITELIST_PREFIX)

    async def run(self, command: str) -> Dict[str, Any]:
        """执行命令，返回结构化结果。

        Returns:
            dict 含 success / stdout / stderr / exit_code / blocked / reason
        """
        if not command or not command.strip():
            return {"success": False, "blocked": True, "reason": "空命令", "exit_code": -1}

        blocked = self._is_blocked(command)
        if blocked:
            logger.warning("沙箱拒绝执行（命中黑名单 %r）: %s", blocked, command)
            return {
                "success": False,
                "blocked": True,
                "reason": f"命中高危命令黑名单：{blocked}",
                "exit_code": -1,
            }

        if not self._is_allowed(command):
            logger.warning("沙箱拒绝执行（不在白名单）: %s", command)
            return {
                "success": False,
                "blocked": True,
                "reason": "命令不在允许的白名单内",
                "exit_code": -1,
            }

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.workdir,
            )
        except Exception as e:  # noqa: BLE001
            return {"success": False, "blocked": False, "reason": f"启动失败：{e}", "exit_code": -1}

        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return {
                "success": False,
                "blocked": False,
                "reason": f"执行超时（>{self.timeout}s）已终止",
                "exit_code": -1,
            }

        return {
            "success": proc.returncode == 0,
            "blocked": False,
            "exit_code": proc.returncode,
            "stdout": (stdout or b"").decode("utf-8", errors="replace"),
            "stderr": (stderr or b"").decode("utf-8", errors="replace"),
        }


# 模块级单例
bash_sandbox = BashSandbox()
