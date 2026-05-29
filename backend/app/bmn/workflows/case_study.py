"""
BMN L3 客户案例生成工作流
LangGraph 状态机：
素材录入 → 卖点提炼 → 品牌对齐 → 多渠道生成 → 合规校验 → 资产回写 → END
"""
from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END
from app.bmn.asset_vault import asset_vault
from app.bmn.brand_engine import brand_engine
from app.models import SessionLocal
from app.bmn.models import BmnAsset, AssetType, BmnWorkflowRun
from datetime import datetime
import json

# ── 导入 LLM 客户端 ──────────────────────────────────
try:
    from app.bmn.llm_client import call_llm, is_llm_available
    LLM_AVAILABLE = is_llm_available()
except Exception as e:
    print(f"⚠️ LLM 客户端导入失败：{e}")
    LLM_AVAILABLE = False


class CaseStudyState(TypedDict):
    """案例生成工作流状态"""
    raw_material: str          # 客户原始素材
    client_name: str            # 客户名称
    industry: str              # 行业
    product_info: str          # 产品信息（可选）

    selling_points: List[str]   # 提炼的卖点
    brand_prompt: str         # 品牌母指令
    copies: dict              # 生成结果：{xhs, moments, ppt_outline}
    compliance_issues: List[str]  # 合规问题列表
    output: dict              # 最终输出

    workflow_run_id: str      # 运行记录 ID


def build_case_study_graph():
    """构建案例生成 LangGraph 工作流"""
    workflow = StateGraph(CaseStudyState)

    # 节点
    workflow.add_node("extract_selling", _extract_selling_points)
    workflow.add_node("load_brand", _load_brand_prompt)
    workflow.add_node("generate_copies", _generate_multi_channel)
    workflow.add_node("compliance_check", _compliance_check)
    workflow.add_node("save_asset", _save_to_asset_vault)
    workflow.add_node("finalize", _finalize_output)

    # 边
    workflow.set_entry_point("extract_selling")
    workflow.add_edge("extract_selling", "load_brand")
    workflow.add_edge("load_brand", "generate_copies")
    workflow.add_edge("generate_copies", "compliance_check")
    workflow.add_edge("compliance_check", "save_asset")
    workflow.add_edge("save_asset", "finalize")
    workflow.add_edge("finalize", END)

    return workflow.compile()


# ── 工作流节点函数 ────────────────────────────────────────

def _extract_selling_points(state: CaseStudyState) -> CaseStudyState:
    """
    节点1：从原始素材中提炼卖点
    检索资产金库中的产品卖点库做参考
    """
    # 从资产金库检索相关卖点
    search_result = asset_vault.search(
        query=state["raw_material"][:200],
        asset_type="product_selling",
        top_k=3,
    )

    reference = ""
    if search_result.get("results"):
        reference = "\n".join(
            r["content"][:300] for r in search_result["results"]
        )

    # 用 LLM 提炼卖点（降级：规则提取）
    raw = state["raw_material"]
    client = state.get("client_name", "")
    industry = state.get("industry", "")

    # 尝试调用 LLM（使用统一接口，支持 Ollama/OpenAI）
    if LLM_AVAILABLE:
        try:
            prompt = f"""请从以下客户素材中提炼 3-5 个核心卖点，每条卖点不超过 30 字。
客户：{client}
行业：{industry}
素材：
{raw[:1000]}

参考卖点库：
{reference[:500]}

输出格式：每行一个卖点，以"- "开头。"""

            response = call_llm(prompt, timeout=30)
            lines = [l.strip() for l in response.strip().split("\n") if l.strip()]
            selling = [l.lstrip("- ").strip() for l in lines if l.startswith("-")]
            if selling:
                state["selling_points"] = selling
                return state
        except Exception as e:
            print(f"⚠️ LLM 调用失败（将使用降级方案）：{e}")

    # 降级：从原始素材中提取关键句（简单规则）
    sentences = [s.strip() for s in raw.split("。") if len(s.strip()) > 5]
    state["selling_points"] = sentences[:5] if sentences else ["（待补充卖点）"]
    return state


def _load_brand_prompt(state: CaseStudyState) -> CaseStudyState:
    """
    节点2：注入品牌母指令
    确保所有输出符合品牌调性
    """
    prompt = brand_engine.get_master_prompt("XX传媒")
    state["brand_prompt"] = prompt or ""
    return state


def _generate_multi_channel(state: CaseStudyState) -> CaseStudyState:
    """
    节点3：生成三个版本
    - 小红书版：种草风格，带 emoji，500 字内
    - 朋友圈版：简洁有力，一句话卖点 + 联系方式
    - PPT 大纲：提案用，3-5 页结构
    """
    brand = state.get("brand_prompt", "")
    client = state.get("client_name", "")
    industry = state.get("industry", "")
    selling = "\n".join(state.get("selling_points", []))
    raw = state.get("raw_material", "")[:500]

    copies = {}

    # ── 小红书版 ─────────────────────────────
    try:
        import subprocess
        xhs_prompt = f"""{brand}

请为【{client}】（{industry}）写一则小红书推广文案。
卖点：
{selling}
原始素材：{raw}

要求：
- 种草风格，亲切有说服力
- 500 字以内
- 带合适的话题标签
- 末尾自评"品牌主张匹配度"（1-10 分）"""

        result = subprocess.run(
            ["ollama", "run", "llama3", xhs_prompt],
            capture_output=True, text=True, timeout=30
        )
        copies["xhs"] = result.stdout.strip() if result.returncode == 0 else _fallback_xhs(client, industry, selling)
    except Exception:
        copies["xhs"] = _fallback_xhs(client, industry, selling)

    # ── 朋友圈版 ─────────────────────────────
    try:
        import subprocess
        moments_prompt = f"""{brand}

请为【{client}】写一则朋友圈推广文案。
卖点：{selling}
要求：简洁有力，3-5 行，带联系引导。"""

        result = subprocess.run(
            ["ollama", "run", "llama3", moments_prompt],
            capture_output=True, text=True, timeout=30
        )
        copies["moments"] = result.stdout.strip() if result.returncode == 0 else _fallback_moments(client, selling)
    except Exception:
        copies["moments"] = _fallback_moments(client, selling)

    # ── PPT 大纲 ─────────────────────────────
    copies["ppt_outline"] = _generate_ppt_outline(client, industry, selling, raw[:300])

    state["copies"] = copies
    return state


def _compliance_check(state: CaseStudyState) -> CaseStudyState:
    """
    节点4：合规校验
    检索风险边界库，检查生成内容是否触碰风险
    """
    # 检索风险边界库
    risk_result = asset_vault.search(
        query="广告法 绝对化用语 合规风险",
        asset_type="risk_boundary",
        top_k=2,
    )

    risk_rules = ""
    if risk_result.get("results"):
        risk_rules = risk_result["results"][0]["content"][:500]

    issues = []
    copies = state.get("copies", {})
    all_text = json.dumps(copies, ensure_ascii=False)

    # 规则检查：绝对化用语
    forbidden = ["最", "第一", "唯一", "国家级", "最高级"]
    for word in forbidden:
        if word in all_text:
            issues.append(f"🟡 中风险：包含绝对化用语「{word}」，违反广告法第9条")

    # 检查是否有数据来源标注
    if "87%" in all_text and "来源" not in all_text:
        issues.append("🟡 中风险：到达率数据未注明来源，需补充「来源：XX传媒+第三方调研」")

    # 高风险：未触发则通过
    if not issues:
        issues.append("🟢 合规通过：未发现明显风险项，建议人工复审")

    state["compliance_issues"] = issues
    return state


def _save_to_asset_vault(state: CaseStudyState) -> CaseStudyState:
    """
    节点5：将生成的案例回写到资产金库（客户案例库）
    """
    client = state.get("client_name", "未知客户")
    copies = state.get("copies", {})
    compliance = state.get("compliance_issues", [])

    content = f"""客户案例：{client}
生成时间：{datetime.now().strftime("%Y-%m-%d")}

## 小红书文案
{copies.get('xhs', '')}

## 朋友圈文案
{copies.get('moments', '')}

## PPT 大纲
{copies.get('ppt_outline', '')}

## 合规检查
{chr(10).join(compliance)}
"""

    result = asset_vault.add_asset(
        asset_type="customer_case",
        title=f"{client}社区营销案例_{datetime.now().strftime('%m%d')}",
        content=content,
        tags=[client, state.get("industry", ""), "AI生成"],
        source="BMN案例工作流",
    )

    state["output"] = {
        "copies": copies,
        "compliance": compliance,
        "asset_saved": "id" in result,
        "asset_id": result.get("id", ""),
    }
    return state


def _finalize_output(state: CaseStudyState) -> CaseStudyState:
    """节点6：整理最终输出"""
    state["output"] = state.get("output", {})
    return state


# ── 降级方案（无 LLM 时）────────────────────────────────

def _fallback_xhs(client: str, industry: str, selling: str) -> str:
    return f"""【{client}】社区营销案例分享 📍

家门口的广告真的有效！我们帮 {client} 做了社区精准投放：
{chr(10).join(f"✅ {s}" for s in selling.split(chr(10)) if s)}

📍 覆盖中高端小区，居民每天进出都看到
📞 扫码领券，到店核销率 40%+

#社区营销 #{industry} #XX传媒 #精准投放"""


def _fallback_moments(client: str, selling: str) -> str:
    s = selling.split("\n")[0] if selling else "精准社区投放"
    return f"""{client}社区推广案例 ✅
{s}
📍 单元门灯箱 + 开门App 双端联动
📞 咨询请私信"""


def _generate_ppt_outline(client: str, industry: str, selling: str, raw: str) -> str:
    return f"""【{client}社区营销提案大纲】

第1页：封面
- 标题：{client} × XX传媒 社区精准营销方案
- 副标题：让品牌在居民每天必经之路上高频触达

第2页：客户背景 & 营销目标
- {client} 品牌介绍
- 本次推广目标（认知/转化/新品上市）
- 预算范围与预期 ROI

第3页：社区媒体价值
- 社区场景 vs 写字楼/商场：更高频、更精准
- XX核心数据：70,000+ 小区、600 万+ DAU
- 单元门灯箱到达率 87%

第4页：投放方案
- 产品组合：单元门灯箱 + 开门App 联动
- 选点策略：（根据 {industry} 目标人群定向）
- 核心卖点：
{selling}

第5页：效果预期
- 预计曝光量、扫码率、到店转化率
- ROI 测算（参考同行业案例）
- 效果追踪方案：扫码数据 → 到店核销 → 效果报告"""


# ── 对外接口 ──────────────────────────────────────

_workflow_graph = None

def get_case_study_graph():
    global _workflow_graph
    if _workflow_graph is None:
        _workflow_graph = build_case_study_graph()
    return _workflow_graph


async def run_case_study_workflow(
    raw_material: str,
    client_name: str,
    industry: str = "",
    product_info: str = "",
) -> dict:
    """执行客户案例生成工作流"""
    db = SessionLocal()
    run_id = None
    try:
        # 创建运行记录
        from uuid import uuid4
        run = BmnWorkflowRun(
            id=uuid4(),
            workflow_name="case_study",
            status="running",
            input_data={
                "client_name": client_name,
                "industry": industry,
                "raw_material_len": len(raw_material),
            },
            created_at=datetime.utcnow(),
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        run_id = str(run.id)

        # 执行工作流
        graph = get_case_study_graph()
        initial_state = {
            "raw_material": raw_material,
            "client_name": client_name,
            "industry": industry,
            "product_info": product_info,
            "selling_points": [],
            "brand_prompt": "",
            "copies": {},
            "compliance_issues": [],
            "output": {},
            "workflow_run_id": run_id,
        }

        result = await graph.ainvoke(initial_state)

        # 更新运行记录
        run.status = "success"
        run.output_data = result.get("output", {})
        run.finished_at = datetime.utcnow()
        db.commit()

        return {
            "ok": True,
            "workflow_run_id": run_id,
            "result": result.get("output", {}),
            "compliance": result.get("compliance_issues", []),
        }

    except Exception as e:
        if run_id:
            run = db.query(BmnWorkflowRun).filter_by(id=run_id).first()
            if run:
                run.status = "failed"
                run.error_msg = str(e)
                run.finished_at = datetime.utcnow()
                db.commit()
        return {"ok": False, "error": str(e)}
    finally:
        db.close()
