#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pdooh-client: Python 客户端库，用于调用 pDOOH API（MCP Server、Tom Agent、ROI Agent、竞品 Agent）。

让用户可以通过 Python 直接调用所有 pDOOH 接口，支持任何电脑安装和使用。
"""

from setuptools import setup, find_packages

setup(
    name="pdooh-client",
    version="1.0.0",
    author="Tom (Qi)",
    author_email="tom@example.com",
    description="Python 客户端库，用于调用 pDOOH API（MCP Server、Tom Agent、ROI Agent、竞品 Agent）",
    long_description=open("README.md", "r", encoding="utf-8").read() if open("README.md", "r").read() else __doc__,
    long_description_content_type="text/markdown",
    url="https://github.com/tomwugdgz/AIAdPlacer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.8",
    install_requires=[
        "httpx>=0.27.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "flake8>=6.0.0",
            "black>=23.0.0",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
