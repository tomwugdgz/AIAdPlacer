#!/usr/bin/env python3
"""
ROI Agent 独立启动脚本
端口: 5004
功能: 广告投放 ROI 计算专家
"""
import uvicorn
import os
import sys

# 将 backend 目录加入 sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("📈 ROI Agent 启动中...")
    print("   端口: 5004")
    print("   文档: http://127.0.0.1:5004/docs")
    print()
    uvicorn.run(
        "app.roi_agent:router",
        host="0.0.0.0",
        port=5004,
        reload=True,
        log_level="info",
    )
