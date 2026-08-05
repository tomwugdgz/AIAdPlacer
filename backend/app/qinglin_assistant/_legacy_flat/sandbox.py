"""
青柠智能助手 — 命令沙箱（骨架，T05 实现）。

规划能力
--------
- 命令黑名单拦截（删除 / 提权 / 网络外联 / 磁盘格式化等）
- 资源限制（超时、输出大小上限、工作目录白名单）
- 仅 ``developer`` 角色可调用（见 ``rbac.TOOL_SANDBOX_EXEC``）

本轮只提供可 import 的签名与黑名单常量，不含执行逻辑。
**安全要求**：T05 实现时默认拒绝，白名单放行；绝不允许 shell=True 拼接用户输入。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

#: 命令黑名单关键词（命中即拒绝）
COMMAND_BLACKLIST: List[str] = [
    "rm", "rmdir", "del", "format", "mkfs", "fdisk",
    "shutdown", "reboot", "halt", "poweroff",
    "sudo", "su", "chmod", "chown", "passwd",
    "dd", "kill", "killall", "taskkill",
    "curl", "wget", "nc", "netcat", "ssh", "scp", "ftp",
    "reg", "regedit", "schtasks", "net",
    "eval", "exec", "pickle", "os.system", "subprocess",
    ">", ">>", "|", "&&", ";", "`", "$(",
]

#: 允许执行的命令白名单（T05 按需扩充）
COMMAND_WHITELIST: List[str] = ["python", "pip", "git", "ls", "dir", "cat", "type", "echo"]

#: 单次执行超时（秒）
DEFAULT_TIMEOUT: int = 10
#: 输出截断上限（字符）
MAX_OUTPUT_CHARS: int = 8000


@dataclass
class SandboxResult:
    """沙箱执行结果。"""

    command: str = ""
    allowed: bool = False
    exit_code: int = -1
    stdout: str = ""
    stderr: str = ""
    elapsed_ms: int = 0
    blocked_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


def is_command_allowed(command: str) -> bool:
    """
    判断命令是否允许执行。

    Parameters
    ----------
    command : str
        待执行命令原文。

    Returns
    -------
    bool
        允许返回 True。

    Notes
    -----
    TODO(T05): 先切 token，命中 COMMAND_BLACKLIST 直接拒绝；
    首 token 必须在 COMMAND_WHITELIST 中才放行。
    """
    raise NotImplementedError("sandbox.is_command_allowed 将在 T05 实现")


def check_command(command: str) -> Optional[str]:
    """
    检查命令并返回拒绝原因。

    Parameters
    ----------
    command : str
        待执行命令。

    Returns
    -------
    str | None
        允许时返回 None，拒绝时返回原因文案。

    Notes
    -----
    TODO(T05): 实现细粒度原因回传，便于前端提示。
    """
    raise NotImplementedError("sandbox.check_command 将在 T05 实现")


async def run_command(
    command: str,
    timeout: int = DEFAULT_TIMEOUT,
    cwd: Optional[str] = None,
) -> SandboxResult:
    """
    在受限沙箱中执行命令。

    Parameters
    ----------
    command : str
        待执行命令。
    timeout : int
        超时秒数。
    cwd : str | None
        工作目录，必须在白名单目录内。

    Returns
    -------
    SandboxResult
        执行结果。

    Notes
    -----
    TODO(T05): 使用 asyncio.create_subprocess_exec（**不用 shell**），
    超时 kill，输出按 MAX_OUTPUT_CHARS 截断。
    """
    raise NotImplementedError("sandbox.run_command 将在 T05 实现")
