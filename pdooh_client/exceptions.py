"""
pDOOH Python 客户端库 - 自定义异常模块

定义所有自定义异常类，提供清晰的错误信息。
"""

from typing import Any, Dict, Optional


class PDOOHError(Exception):
    """pDOOH 客户端基础异常类。

    所有 pDOOH 客户端异常的父类。

    Attributes:
        message: 错误消息。
        details: 详细错误信息，可选。
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """初始化基础异常。

        Args:
            message: 错误消息。
            details: 详细错误信息，可选。
        """
        self.message = message
        self.details = details if details is not None else {}
        super().__init__(message)

    def __str__(self) -> str:
        """返回异常的字符串表示。

        Returns:
            格式化的错误消息。
        """
        if self.details:
            return f"{self.message} (详情: {self.details})"
        return self.message


class APIError(PDOOHError):
    """API 调用错误异常。

    当 API 调用返回错误状态码或响应时抛出。

    Attributes:
        message: 错误消息。
        status_code: HTTP 状态码。
        response: 响应数据，可选。
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
    ) -> None:
        """初始化 API 错误异常。

        Args:
            message: 错误消息。
            status_code: HTTP 状态码，可选。
            response: 响应数据，可选。
        """
        details: Dict[str, Any] = {}
        if status_code is not None:
            details["status_code"] = status_code
        if response is not None:
            details["response"] = response
        super().__init__(message, details)
        self.status_code = status_code
        self.response = response


class ConnectionError(PDOOHError):
    """连接错误异常。

    当无法连接到 API 服务器时抛出。

    Attributes:
        message: 错误消息。
    """

    def __init__(self, message: str) -> None:
        """初始化连接错误异常。

        Args:
            message: 错误消息。
        """
        super().__init__(message)


class TimeoutError(PDOOHError):
    """超时错误异常。

    当 API 请求超时时抛出。

    Attributes:
        message: 错误消息。
        timeout: 超时时间（秒），可选。
    """

    def __init__(self, message: str, timeout: Optional[int] = None) -> None:
        """初始化超时错误异常。

        Args:
            message: 错误消息。
            timeout: 超时时间（秒），可选。
        """
        details: Dict[str, Any] = {}
        if timeout is not None:
            details["timeout"] = timeout
        super().__init__(message, details)
        self.timeout = timeout


class ValidationError(PDOOHError):
    """参数验证错误异常。

    当传入的参数不符合要求时抛出。

    Attributes:
        message: 错误消息。
        field: 出错的字段名，可选。
    """

    def __init__(self, message: str, field: Optional[str] = None) -> None:
        """初始化验证错误异常。

        Args:
            message: 错误消息。
            field: 出错的字段名，可选。
        """
        details: Dict[str, Any] = {}
        if field is not None:
            details["field"] = field
        super().__init__(message, details)
        self.field = field


class ConfigurationError(PDOOHError):
    """配置错误异常。

    当客户端配置参数无效时抛出。

    Attributes:
        message: 错误消息。
        parameter: 出错的配置参数名，可选。
    """

    def __init__(self, message: str, parameter: Optional[str] = None) -> None:
        """初始化配置错误异常。

        Args:
            message: 错误消息。
            parameter: 出错的配置参数名，可选。
        """
        details: Dict[str, Any] = {}
        if parameter is not None:
            details["parameter"] = parameter
        super().__init__(message, details)
        self.parameter = parameter
