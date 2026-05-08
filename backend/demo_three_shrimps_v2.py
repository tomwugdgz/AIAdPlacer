"""
"三只虾"系统 Demo — 简化版（文本输出，更可靠）
运行：python demo_three_shrimps_v2.py
"""

import sys
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
    import json
    print(json.dumps(data, indent=2, ensure_ascii=False))


# ───────────────────────────────────────────────────────────
# 1. 选题虾 (TopicBot) — 文本输出版
# ───────────────────────────────────────────────────────────
def topic_bot(industry, product, target_audience, campaign_goal, num_topics=3):
    """
    选题虾：生成广告选题（文本输出，更可靠）
    """
    prompt = f"""你是资深广告策划，请生成 {num_topics} 个「{product}」的广告选题。

背景：
- 行业：{industry}
- 目标人群：{target_audience}
- 营销目标：{campaign_goal}
- 投放场景：社区媒体（开门广告/灯箱）

要求：
1. 每个选题包含：标题、切入角度、核心信息
2. 突出社区场景（家庭、高频、精准）
3. 格式：
选题1：[标题]
角度：[切入角度]
核心：[核心信息]

选题2：...
"""

    print("📡 正在调用 LLM（选题虾）...")
    start = time.time()
    response = call_llm(prompt, timeout=180)
    elapsed = time.time() - start
    print(f"   ✅ 响应时间：{elapsed:.1f}秒\n")
    
    # 解析文本输出为结构化数据
    topics = parse_topics_text(response)
    return {"raw_text": response, "topics": topics}


def parse_topics_text(text):
    """解析选题文本为结构化数据"""
    topics = []
    
    # 按"选题X："分割
    import re
    pattern = r'选题\d+[：:]\s*(.+?)(?=选题\d+[：:]|$)'
    matches = re.findall(pattern, text, re.DOTALL)
    
    if not matches:
        # 尝试按行解析
        lines = text.strip().split("\n")
        current_topic = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if "标题" in line or "题目" in line:
                if current_topic:
                    topics.append(current_topic)
                current_topic = {"title": line.split("：")[-1].split(":")[-1].strip()}
            elif "角度" in line:
                current_topic["angle"] = line.split("：")[-1].split(":")[-1].strip()
            elif "核心" in line or "信息" in line:
                current_topic["key_message"] = line.split("：")[-1].split(":")[-1].strip()
        
        if current_topic:
            topics.append(current_topic)
    else:
        for match in matches:
            lines = match.strip().split("\n")
            topic = {"title": lines[0].strip()}
            for line in lines[1:]:
                if "角度" in line:
                    topic["angle"] = line.split("：")[-1].split(":")[-1].strip()
                elif "核心" in line or "信息" in line:
                    topic["key_message"] = line.split("：")[-1].split(":")[-1].strip()
            topics.append(topic)
    
    # 补充默认值
    for topic in topics:
        if "title" not in topic:
            topic["title"] = "未命名选题"
        if "angle" not in topic:
            topic["angle"] = "待补充"
        if "key_message" not in topic:
            topic["key_message"] = "待补充"
        topic["scenario"] = "社区开门场景"
    
    return topics


# ───────────────────────────────────────────────────────────
# 2. 文案虾 (CopyBot) — 文本输出版
# ───────────────────────────────────────────────────────────
def copy_bot(topic_title, topic_key_message, style="专业", length="中", platform="开门广告", num_versions=2):
    """
    文案虾：生成广告文案（文本输出）
    """
    length_map = {"短": "50字以内", "中": "50-100字", "长": "100-150字"}
    length_desc = length_map.get(length, "50-100字")
    
    prompt = f"""你是资深文案，请写 {num_versions} 个版本的「{topic_title}」广告文案。

要求：
1. 风格：{style}
2. 长度：{length_desc}
3. 平台：{platform}（社区开门广告）
4. 要包含：吸引点 + 产品利益 + 行动号召
5. 格式：
版本A：
[文案内容]
吸引点：[吸引点]
CTA：[行动号召]

版本B：
...
"""

    print("📡 正在调用 LLM（文案虾）...")
    start = time.time()
    response = call_llm(prompt, timeout=180)
    elapsed = time.time() - start
    print(f"   ✅ 响应时间：{elapsed:.1f}秒\n")
    
    # 解析文本输出
    copies = parse_copies_text(response, num_versions)
    return {"raw_text": response, "copies": copies}


def parse_copies_text(text, num_versions=2):
    """解析文案文本为结构化数据"""
    copies = []
    
    # 按"版本X："分割
    import re
    pattern = r'版本[AB\d]+[：:]\s*(.+?)(?=版本[AB\d]+[：:]|$)'
    matches = re.findall(pattern, text, re.DOTALL)
    
    if not matches:
        # 尝试简单分割
        copies.append({
            "version": "A版",
            "content": text[:100].strip(),
            "hook": "待提取",
            "cta": "待提取"
        })
    else:
        for i, match in enumerate(matches[:num_versions]):
            lines = match.strip().split("\n")
            content = lines[0].strip()
            hook = ""
            cta = ""
            
            for line in lines:
                if "吸引" in line:
                    hook = line.split("：")[-1].split(":")[-1].strip()
                elif "CTA" in line or "行动" in line or "号召" in line:
                    cta = line.split("：")[-1].split(":")[-1].strip()
            
            copies.append({
                "version": f"{chr(65+i)}版",  # A版, B版, ...
                "content": content,
                "hook": hook or "吸引点待补充",
                "cta": cta or "扫码/到店"
            })
    
    return copies


# ───────────────────────────────────────────────────────────
# 3. 审核虾 (ReviewBot) — 文本输出版
# ───────────────────────────────────────────────────────────
def review_bot(copy_content, brand_guidelines="", compliance_rules="广告法、社区媒体规范"):
    """
    审核虾：审核文案质量（文本输出）
    """
    prompt = f"""你是广告合规审核专家，请审核以下文案：

文案：
{copy_content}

审核维度（满分100）：
1. 合规性（30分）：是否违反广告法
2. 品牌一致性（20分）：是否符合品牌调性
3. 吸引力（20分）：能否抓住注意力
4. 清晰度（15分）：信息是否明确
5. 行动号召（15分）：是否有明确CTA

请输出：
总分：[X/100]
是否通过：[是/否]
问题：
1. [问题1]
2. [问题2]
...
建议：
1. [建议1]
2. [建议2]
"""

    print("📡 正在调用 LLM（审核虾）...")
    start = time.time()
    response = call_llm(prompt, timeout=180)
    elapsed = time.time() - start
    print(f"   ✅ 响应时间：{elapsed:.1f}秒\n")
    
    # 解析审核结果
    review = parse_review_text(response)
    return {"raw_text": response, "review": review}


def parse_review_text(text):
    """解析审核文本为结构化数据"""
    import re
    
    # 提取总分
    score_match = re.search(r'总分[：:]\s*(\d+)', text)
    score = int(score_match.group(1)) if score_match else 0
    
    # 是否通过
    passed = "是" in text and "否" not in text[:text.find("是否通过")+10] if "是否通过" in text else score >= 70
    
    # 提取问题和建议
    issues = []
    suggestions = []
    
    # 简单提取
    lines = text.split("\n")
    in_issues = False
    in_suggestions = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if "问题" in line:
            in_issues = True
            in_suggestions = False
            continue
        elif "建议" in line:
            in_issues = False
            in_suggestions = True
            continue
        
        if in_issues and (line[0].isdigit() or line[0] in ['-', '•']):
            issues.append(line.lstrip("0123456789.-• "))
        elif in_suggestions and (line[0].isdigit() or line[0] in ['-', '•']):
            suggestions.append(line.lstrip("0123456789.-• "))
    
    return {
        "score": score,
        "passed": passed,
        "issues": issues,
        "suggestions": suggestions,
        "optimized_copy": ""
    }


# ───────────────────────────────────────────────────────────
# 主流程
# ───────────────────────────────────────────────────────────
def run_demo():
    """运行完整 Demo"""
    
    print()
    print("  🦐" * 15)
    print("  「三只虾」内容生产系统 — 简化版 Demo")
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
    
    # 预热模型
    print("  ⏳ 正在预热模型...")
    try:
        warmup_response = call_llm("你好", timeout=60)
        print(f"  ✅ 模型预热完成\n")
    except Exception as e:
        print(f"  ⚠️  预热失败：{e}")
        print("     继续演示，但响应可能较慢...\n")
    
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
        print(f"   原始输出：{topic_result.get('raw_text', '')[:200]}...")
        return
    
    print("  ✅ 生成选题成功！\n")
    for i, topic in enumerate(topics, 1):
        print(f"  选题 {i}：")
        print(f"    标题：{topic.get('title', 'N/A')}")
        print(f"    角度：{topic.get('angle', 'N/A')}")
        print(f"    核心信息：{topic.get('key_message', 'N/A')}")
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
        print(f"   原始输出：{copy_result.get('raw_text', '')[:200]}...")
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
    
    review = review_result.get("review", {})
    score = review.get('score', 0)
    passed = review.get('passed', False)
    issues = review.get('issues', [])
    suggestions = review.get('suggestions', [])
    
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
