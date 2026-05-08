"""
BMN L3 工作流 API
POST /api/v2/bmn/workflows/case_study/run  执行客户案例生成工作流
GET  /api/v2/bmn/workflows/runs               查询运行记录
GET  /api/v2/bmn/workflows/runs/{id}       查询单条运行记录
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.bmn.workflows.case_study import run_case_study_workflow

router = APIRouter()


class CaseStudyRunReq(BaseModel):
    raw_material: str
    client_name: str
    industry: Optional[str] = ""
    product_info: Optional[str] = ""


@router.post("/api/v2/bmn/workflows/case_study/run")
async def run_case_study(req: CaseStudyRunReq):
    """
    执行客户案例生成工作流
    返回：
    - copies: {xhs, moments, ppt_outline}
    - compliance: 合规检查结果
    """
    result = await run_case_study_workflow(
        raw_material=req.raw_material,
        client_name=req.client_name,
        industry=req.industry,
        product_info=req.product_info,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=500, detail=result.get("error", "工作流执行失败"))
    return {
        "ok": True,
        "workflow_run_id": result["workflow_run_id"],
        "result": result["result"],
        "compliance": result["compliance"],
    }


@router.get("/api/v2/bmn/workflows/runs")
async def list_workflow_runs(
    workflow_name: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
):
    """查询工作流运行记录"""
    from app.bmn.models import BmnWorkflowRun
    from app.models import SessionLocal

    db = SessionLocal()
    try:
        q = db.query(BmnWorkflowRun)
        if workflow_name:
            q = q.filter_by(workflow_name=workflow_name)
        if status:
            q = q.filter_by(status=status)
        rows = q.order_by(BmnWorkflowRun.created_at.desc()).limit(limit).all()
        return {
            "items": [{
                "id": str(r.id),
                "workflow_name": r.workflow_name,
                "status": r.status,
                "input_data": r.input_data,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            } for r in rows]
        }
    finally:
        db.close()


@router.get("/api/v2/bmn/workflows/runs/{run_id}")
async def get_workflow_run(run_id: str):
    """查询单条运行记录详情"""
    from app.bmn.models import BmnWorkflowRun
    from app.models import SessionLocal
    from uuid import UUID

    db = SessionLocal()
    try:
        row = db.query(BmnWorkflowRun).filter_by(id=UUID(run_id)).first()
        if not row:
            raise HTTPException(status_code=404, detail="运行记录不存在")
        return {
            "id": str(row.id),
            "workflow_name": row.workflow_name,
            "status": row.status,
            "input_data": row.input_data,
            "output_data": row.output_data,
            "error_msg": row.error_msg,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "finished_at": row.finished_at.isoformat() if row.finished_at else None,
        }
    finally:
        db.close()
