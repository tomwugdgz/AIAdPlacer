"""
pDOOH Python 客户端库 - 配置管理模块

提供客户端配置管理功能，支持自定义 base_url、超时时间等参数。
"""

from typing import Optional
from .exceptions import ConfigurationError


class PDOOHConfig:
    """pDOOH 客户端配置类。

    管理所有客户端的通用配置参数，包括服务器地址、超时时间、重试次数等。

    Attributes:
        base_url: API 服务器基础 URL。
        timeout: HTTP 请求超时时间（秒）。
        max_retries: 请求失败后的最大重试次数。
        verify_ssl: 是否验证 SSL 证书。
    """

    DEFAULT_BASE_URL: str = "http://47.253.159.62"
    DEFAULT_TIMEOUT: int = 30
    DEFAULT_MAX_RETRIES: int = 3
    DEFAULT_VERIFY_SSL: bool = True

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        verify_ssl: Optional[bool] = None,
    ) -> None:
        """初始化配置对象。

        Args:
            base_url: API 服务器基础 URL，默认 http://47.253.159.62。
            timeout: HTTP 请求超时时间（秒），默认 30 秒。
            max_retries: 请求失败后的最大重试次数，默认 3 次。
            verify_ssl: 是否验证 SSL 证书，默认 True。

        Raises:
            ConfigurationError: 当配置参数无效时抛出。
        """
        self.base_url = base_url if base_url is not None else self.DEFAULT_BASE_URL
        self.timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT
        self.max_retries = (
            max_retries if max_retries is not None else self.DEFAULT_MAX_RETRIES
        )
        self.verify_ssl = (
            verify_ssl if verify_ssl is not None else self.DEFAULT_VERIFY_SSL
        )

        self._validate()

    def _validate(self) -> None:
        """验证配置参数的有效性。

        Raises:
            ConfigurationError: 当配置参数无效时抛出。
        """
        if not self.base_url:
            raise ConfigurationError("base_url 不能为空")

        if self.timeout <= 0:
            raise ConfigurationError("timeout 必须大于 0")

        if self.max_retries < 0:
            raise ConfigurationError("max_retries 不能为负数")

    def get_service_url(self, port: int, path: str = "") -> str:
        """构建完整服务 URL。

        Args:
            port: 服务端口号。
            path: API 路径，可选。

        Returns:
            完整的服务 URL。
        """
        base = self.base_url.rstrip("/")
        return f"{base}:{port}/{path.lstrip('/')}" if path else f"{base}:{port}"

    def to_dict(self) -> dict:
        """将配置转换为字典格式。

        Returns:
            包含所有配置参数的字典。
        """
        return {
            "base_url": self.base_url,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "verify_ssl": self.verify_ssl,
        }

    @classmethod
    def from_dict(cls, config_dict: dict) -> "PDOOHConfig":
        """从字典创建配置对象。

        Args:
            config_dict: 包含配置参数的字典。

        Returns:
            新的 PDOOHConfig 实例。
        """
        return cls(
            base_url=config_dict.get("base_url"),
            timeout=config_dict.get("timeout"),
            max_retries=config_dict.get("max_retries"),
            verify_ssl=config_dict.get("verify_ssl"),
        )

    def __repr__(self) -> str:
        """返回配置的字符串表示。

        Returns:
            配置信息的字符串表示。
        """
        return (
            f"PDOOHConfig(base_url='{self.base_url}', "
            f"timeout={self.timeout}, "
            f"max_retries={self.max_retries}, "
            f"verify_ssl={self.verify_ssl})"
        )
