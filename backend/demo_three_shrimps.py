"""
"三只虾"系统 Demo — 完整流程演示
运行：python demo_three_shrimps.py
"""

import sys
import json
import time

# 添加项目路径
sys.path.insert(0, r'D:\Mirofish\AIAdPlacer\backend')

from app.bmn.llm_client import call_llm, get_llm_config


def print_section(title):
    """打印章节标题"""
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)
    print()


def print_json(data):
    """漂亮地打印 JSON"""
    print(json.dumps(data, indent=2, ensure_ascii=False))


def clean_json_response(response_text):
    """清理 LLM 返回的 JSON（去除 markdown、修复换行符、提取 JSON 对象）"""
    import re
    import json5
    
    text = response_text.strip()
    
    # 去除 ```json ... ``` 或 ``` ... ``` 包裹
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        parts = text.split("```")
        if len(parts) >= 3:
            text = parts[1].strip()
    
    # 提取 JSON 对象（从第一个 { 到最后一个 }）
    start = text.find("{")
    end = text.rfind("}")
    
    if start != -1 and end != -1 and start < end:
        json_str = text[start:end+1]
        
        # 修复 JSON 中字符串内的未转义换行符
        def fix_json_newlines(s):
            """将字符串内的真实换行转为 \n 转义序列"""
            result = []
            in_string = False
            escape_next = False
            
            i = 0
            while i < len(s):
                char = s[i]
                
                if escape_next:
                    result.append(char)
                    escape_next = False
                    i += 1
                    continue
                    
                if char == '\\':
                    escape_next = True
                    result.append(char)
                    i += 1
                    continue
                    
                if char == '"':
                    # 检查前面是否有奇数个反斜杠（表示这个引号被转义）
                    # 简化：检查前一个字符
                    if not escape_next:
                        in_string = not in_string
                    result.append(char)
                    i += 1
                    continue
                    
                if in_string and char == '\n':
                    result.append('\\n')  # 转义换行符
                    i += 1
                    continue
                    
                if in_string and char == '\r':
                    result.append('\\r')  # 转义回车符
                    i += 1
                    continue
                    
                result.append(char)
                i += 1
            
            return ''.join(result)
        
        json_str_fixed = fix_json_newlines(json_str)
        
        try:
            # 使用 json5 解析（更宽容：允许 trailing commas 等）
            parsed = json5.loads(json_str_fixed)
            return json.dumps(parsed)  # 转回标准 JSON 字符串
        except Exception as e:
            print(f"   ⚠️  JSON5 解析失败：{e}")
            # 降级：返回修复后的字符串，让调用者决定如何处理
            return json_str_fixed
    
    return text


# ───────────────────────────────────────────────────────────
# 1. 选题虾 (TopicBot)
# ───────────────────────────────────────────────────────────
def topic_bot(industry, product, target_audience, campaign_goal, num_topics=3):
    """
    选题虾：生成广告选题
    """
    prompt = f"""你是一位资深广告策划。请根据以下信息生成 {num_topics} 个广告选题：

行业：{industry}
产品：{product}
目标人群：{target_audience}
营销目标：{campaign_goal}

要求：
1. 每个选题包含：标题、切入角度、核心信息、适用场景
2. 突出社区媒体特性（家庭场景、高频触达、精准定向）
3. 符合品牌调性，具有差异化
4. 严格要求：JSON 字符串值中不要包含换行符，所有内容放在一行内

输出严格 JSON 格式（不要有 markdown 代码块包裹）：
{{
  "topics": [
    {{
      "title": "选题标题",
      "angle": "切入角度",
      "key_message": "核心信息",
      "scenario": "适用场景"
    }}
  ]
}}"""

    print("📡 正在调用 LLM（选题虾）...")
    start = time.time()
    response = call_llm(prompt, timeout=120)
    elapsed = time.time() - start
    print(f"   ✅ 响应时间：{elapsed:.1f}秒\n")
    
    # 解析 JSON
    try:
        cleaned = clean_json_response(response)
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"   ⚠️  JSON 解析失败：{e}")
        print(f"   原始响应：{response[:200]}...")
        return {"topics": []}


# ───────────────────────────────────────────────────────────
# 2. 文案虾 (CopyBot)
# ───────────────────────────────────────────────────────────
def copy_bot(topic_title, topic_key_message, style="专业", length="中", platform="开门广告", num_versions=2):
    """
    文案虾：根据选题生成广告文案
    """
    topic_full = f"{topic_title}：{topic_key_message}"
    
    prompt = f"""你是一位资深文案。请根据以下选题写 {num_versions} 个版本的广告文案：

选题：{topic_full}
风格：{style}
长度：{length}（短=50字内，中=50-100字，长=100-150字）
平台：{platform}

要求：
1. 开门见山，3秒内抓住注意力
2. 突出产品核心利益点
3. 有明确的行动号召（扫码/到店/下单）
4. 社区场景化表达，接地气
5. 不同版本要有明显差异（角度/语气/CTA）
6. 严格要求：JSON 字符串值中不要包含换行符

输出严格 JSON 格式（不要有 markdown 代码块包裹）：
{{
  "copies": [
    {{
      "version": "A版",
      "content": "文案内容",
      "hook": "吸引点",
      "cta": "行动号召"
    }},
    {{
      "version": "B版",
      "content": "文案内容",
      "hook": "吸引点",
      "cta": "行动号召"
    }}
  ]
}}"""

    print("📡 正在调用 LLM（文案虾）...")
    start = time.time()
    response = call_llm(prompt, timeout=120)
    elapsed = time.time() - start
    print(f"   ✅ 响应时间：{elapsed:.1f}秒\n")
    
    # 解析 JSON
    try:
        cleaned = clean_json_response(response)
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"   ⚠️  JSON 解析失败：{e}")
        print(f"   原始响应：{response[:200]}...")
        return {"copies": []}


# ───────────────────────────────────────────────────────────
# 3. 审核虾 (ReviewBot)
# ───────────────────────────────────────────────────────────
def review_bot(copy_content, brand_guidelines="", compliance_rules="广告法、社区媒体规范、不实宣传禁用"):
    """
    审核虾：审核文案质量
    """
    prompt = f"""你是一位广告合规审核专家。请审核以下文案：

文案内容：
{copy_content}

品牌规范：{brand_guidelines if brand_guidelines else "无特殊要求"}
合规要求：{compliance_rules}

审核维度（满分100分）：
1. 合规性（30分）：是否违反广告法、是否有虚假宣传
2. 品牌一致性（20分）：是否符合品牌调性
3. 吸引力（20分）：是否能3秒内抓住注意力
4. 清晰度（15分）：信息是否明确、利益点是否突出
5. 行动号召（15分）：是否有明确的CTA、是否容易执行

要求：
1. 严格要求：JSON 字符串值中不要包含换行符
2. 如果文案有问题，在 optimized_copy 字段提供优化后的版本

输出严格 JSON 格式（不要有 markdown 代码块包裹）：
{{
  "score": 85,
  "passed": true,
  "issues": [],
  "suggestions": ["建议1", "建议2"],
  "optimized_copy": "优化后的文案（如果原始文案有问题）"
}}"""

    print("📡 正在调用 LLM（审核虾）...")
    start = time.time()
    response = call_llm(prompt, timeout=120)
    elapsed = time.time() - start
    print(f"   ✅ 响应时间：{elapsed:.1f}秒\n")
    
    # 解析 JSON
    try:
        cleaned = clean_json_response(response)
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"   ⚠️  JSON 解析失败：{e}")
        print(f"   原始响应：{response[:200]}...")
        return {"score": 0, "passed": False, "issues": ["JSON解析失败"], "suggestions": []}


# ───────────────────────────────────────────────────────────
# 主流程
# ───────────────────────────────────────────────────────────
def run_demo():
    """运行完整 Demo"""
    
    print()
    print("  🦐" * 15)
    print("  「三只虾」内容生产系统 — 完整流程 Demo")
    print("  🦐" * 15)
    print()
    print("  演示产品：舒肤佳洗手液")
    print("  目标人群：家庭主妇、年轻妈妈")
    print("  营销目标：品牌曝光 + 促销转化")
    print()
    
    # 检查 LLM 配置
    config = get_llm_config()
    print("  LLM 配置：")
    print(f"    提供商：{config['provider']}")
    print(f"    模型：{config['model']}")
    print(f"    可用性：{'✅ 正常' if config['available'] else '❌ 不可用'}")
    print()
    
    if not config['available']:
        print("  ❌ LLM 不可用，请检查 Ollama 是否运行")
        print("     启动命令：ollama serve")
        return
    
    # 使用轻量模型（如果可用）
    import os
    env_model = os.getenv("DEMO_MODEL", "")
    if env_model:
        print(f"  💡 使用轻量模型：{env_model}")
        print("     （设置 DEMO_MODEL 环境变量可切换模型）")
        print()
    
    # 预热模型（加快后续响应）
    print("  ⏳ 正在预热模型（首次加载可能需 30-60 秒）...")
    try:
        warmup_response = call_llm("你好", timeout=60)
        print(f"  ✅ 模型预热完成")
    except Exception as e:
        print(f"  ⚠️  预热失败：{e}")
        print("     继续演示，但响应可能较慢...")
    print()
    
    # ── 第1步：选题虾 ──────────────────────────────────
    print_section("第1步：选题虾 (TopicBot) — 生成广告选题")
    
    topic_result = topic_bot(
        industry="日化",
        product="舒肤佳洗手液",
        target_audience="家庭主妇、年轻妈妈",
        campaign_goal="品牌曝光 + 促销转化",
        num_topics=3
    )
    
    topics = topic_result.get("topics", [])
    
    if not topics:
        print("  ❌ 选题生成失败")
        return
    
    print("  ✅ 生成选题成功！\n")
    for i, topic in enumerate(topics, 1):
        print(f"  选题 {i}：")
        print(f"    标题：{topic.get('title', 'N/A')}")
        print(f"    角度：{topic.get('angle', 'N/A')}")
        print(f"    核心信息：{topic.get('key_message', 'N/A')}")
        print(f"    场景：{topic.get('scenario', 'N/A')}")
        print()
    
    # ── 第2步：文案虾 ──────────────────────────────────
    print_section("第2步：文案虾 (CopyBot) — 生成广告文案")
    
    # 取第一个选题
    selected_topic = topics[0]
    topic_title = selected_topic.get('title', '')
    topic_key_msg = selected_topic.get('key_message', '')
    
    print(f"  基于选题：「{topic_title}」\n")
    
    copy_result = copy_bot(
        topic_title=topic_title,
        topic_key_message=topic_key_msg,
        style="接地气",
        length="中",
        platform="社区开门广告",
        num_versions=2
    )
    
    copies = copy_result.get("copies", [])
    
    if not copies:
        print("  ❌ 文案生成失败")
        return
    
    print("  ✅ 生成文案成功！\n")
    for copy in copies:
        print(f"  {copy.get('version', '未知版本')}：")
        print(f"    文案：{copy.get('content', 'N/A')}")
        print(f"    吸引点：{copy.get('hook', 'N/A')}")
        print(f"    行动号召：{copy.get('cta', 'N/A')}")
        print()
    
    # ── 第3步：审核虾 ──────────────────────────────────
    print_section("第3步：审核虾 (ReviewBot) — 审核广告文案")
    
    # 取第一个文案进行审核
    selected_copy = copies[0]
    copy_content = selected_copy.get('content', '')
    
    print(f"  审核文案：{copy_content[:50]}...\n")
    
    review_result = review_bot(
        copy_content=copy_content,
        brand_guidelines="舒肤佳：专业、健康、可信赖",
        compliance_rules="广告法、社区媒体规范、不得使用'第一'/'唯一'等绝对化用语"
    )
    
    score = review_result.get('score', 0)
    passed = review_result.get('passed', False)
    issues = review_result.get('issues', [])
    suggestions = review_result.get('suggestions', [])
    optimized = review_result.get('optimized_copy', '')
    
    print("  ✅ 审核完成！\n")
    print(f"  总分：{score}/100 {'✅ 通过' if passed else '❌ 未通过'}")
    
    if issues:
        print(f"\n  问题：")
        for issue in issues:
            print(f"    - {issue}")
    
    if suggestions:
        print(f"\n  建议：")
        for suggestion in suggestions:
            print(f"    - {suggestion}")
    
    if optimized:
        print(f"\n  优化后文案：{optimized}")
    
    # ── 总结 ──────────────────────────────────────────
    print_section("流程总结")
    
    print("  ✅ 三只虾系统运行完成！\n")
    print("  生成结果：")
    print(f"    - 选题数：{len(topics)} 个")
    print(f"    - 文案版本：{len(copies)} 个")
    print(f"    - 审核得分：{score}/100")
    print(f"    - 审核状态：{'通过' if passed else '未通过'}")
    
    print()
    print("  推荐文案：")
    print(f"    {copy_content}")
    
    print()
    print("=" * 70)
    print("  Demo 结束，感谢使用「三只虾」内容生产系统！")
    print("=" * 70)
    print()


if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
    except Exception as e:
        print(f"\n\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()
