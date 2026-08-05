"""
青柠智能助手 — 文档生成技能（骨架，T02/T03 实现）。

规划能力（**真实链路**，产出真实可下载文件，``demo: false``）
------------------------------------------------------------
- ``generate_docx``  投放方案 / 巡检报告（python-docx）
- ``generate_xlsx``  点位清单 / 排期表（openpyxl，已在 requirements 中）
- ``generate_pptx``  提案 PPT（python-pptx）
- ``generate_pdf``   对外报告（reportlab）

本轮只提供可 import 的签名与输出目录约定，不含实现逻辑。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

# backend/app/qinglin_assistant/skills.py -> qinglin_assistant -> app -> backend
_BACKEND_DIR: Path = Path(__file__).resolve().parent.parent.parent
#: 生成文件的输出目录
OUTPUT_DIR: Path = _BACKEND_DIR / "data" / "qinglin_outputs"


@dataclass
class DocumentResult:
    """文档生成结果。"""

    file_path: str = ""
    file_name: str = ""
    file_type: str = ""
    size_bytes: int = 0
    download_url: str = ""


def ensure_output_dir() -> Path:
    """
    确保输出目录存在。

    Returns
    -------
    Path
        输出目录路径。
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


async def generate_docx(
    title: str,
    sections: List[Dict[str, Any]],
    file_name: Optional[str] = None,
) -> DocumentResult:
    """
    生成 Word 文档。

    Notes
    -----
    TODO(T03): 使用 python-docx 渲染标题 / 段落 / 表格。
    """
    raise NotImplementedError("skills.generate_docx 将在 T03 实现")


async def generate_xlsx(
    sheet_name: str,
    headers: List[str],
    rows: List[List[Any]],
    file_name: Optional[str] = None,
) -> DocumentResult:
    """
    生成 Excel 文档。

    Notes
    -----
    TODO(T03): 使用 openpyxl 写入表头与数据行，设置列宽与冻结首行。
    """
    raise NotImplementedError("skills.generate_xlsx 将在 T03 实现")


async def generate_pptx(
    title: str,
    slides: List[Dict[str, Any]],
    file_name: Optional[str] = None,
) -> DocumentResult:
    """
    生成 PPT 提案。

    Notes
    -----
    TODO(T03): 使用 python-pptx 渲染封面页 + 内容页。
    """
    raise NotImplementedError("skills.generate_pptx 将在 T03 实现")


async def generate_pdf(
    title: str,
    sections: List[Dict[str, Any]],
    file_name: Optional[str] = None,
) -> DocumentResult:
    """
    生成 PDF 报告。

    Notes
    -----
    TODO(T03): 使用 reportlab 渲染，需注册中文字体避免乱码。
    """
    raise NotImplementedError("skills.generate_pdf 将在 T03 实现")
