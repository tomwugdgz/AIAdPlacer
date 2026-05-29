#!/usr/bin/env python3
"""BMN LLM 客户端 Demo 测试"""
import sys
sys.path.insert(0, '.')

from app.bmn.llm_client import call_llm, get_llm_config

# 显示配置
config = get_llm_config()
print("=" * 60)
print("BMN LLM 客户端测试")
print("=" * 60)
print(f"提供商: {config['provider']}")
print(f"模型: {config['model']}")
print(f"启用状态: {config['enabled']}")
print(f"可用性: {config['available']}")
print()

# 测试调用
if config['available']:
    print("测试调用中...")
    try:
        response = call_llm("请用一句话介绍XX传媒", timeout=30)
        print(f"响应: {response[:200]}...")
        print()
        print("✅ LLM 调用成功!")
    except Exception as e:
        print(f"❌ 调用失败: {e}")
else:
    print("⚠️ LLM 不可用，请检查配置")

print("=" * 60)
