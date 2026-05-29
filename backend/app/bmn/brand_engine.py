"""
BMN L1 品牌逻辑引擎
"""
from app.bmn.models import BmnBrandConfig
from app.models import SessionLocal
from datetime import datetime


class BrandEngine:
    """
    品牌逻辑引擎 — 生成并管理"母指令"(master_prompt)
    所有后续 AI 生成任务都以 master_prompt 作为 system prompt 的基础
    """

    def get_brand_config(self, brand_name: str = "XX传媒") -> dict:
        """读取品牌配置"""
        db = SessionLocal()
        try:
            cfg = db.query(BmnBrandConfig).filter_by(brand_name=brand_name).first()
            if not cfg:
                return {"error": f"未找到品牌配置: {brand_name}"}
            return {
                "id": str(cfg.id),
                "brand_name": cfg.brand_name,
                "identity": cfg.identity or "",
                "value_proposition": cfg.value_proposition or "",
                "trust_proof": cfg.trust_proof or [],
                "differentiation": cfg.differentiation or "",
                "master_prompt": cfg.master_prompt or "",
            }
        finally:
            db.close()

    def upsert_brand_config(self, data: dict) -> dict:
        """
        创建或更新品牌配置，同时自动生成 master_prompt
        data 字段: brand_name, identity, value_proposition, trust_proof, differentiation
        """
        db = SessionLocal()
        try:
            cfg = db.query(BmnBrandConfig).filter_by(brand_name=data["brand_name"]).first()
            now = datetime.utcnow()

            master_prompt = self._build_master_prompt(data)

            if cfg:
                cfg.identity = data.get("identity", cfg.identity)
                cfg.value_proposition = data.get("value_proposition", cfg.value_proposition)
                cfg.trust_proof = data.get("trust_proof", cfg.trust_proof)
                cfg.differentiation = data.get("differentiation", cfg.differentiation)
                cfg.master_prompt = master_prompt
                cfg.updated_at = now
            else:
                cfg = BmnBrandConfig(
                    brand_name=data["brand_name"],
                    identity=data.get("identity", ""),
                    value_proposition=data.get("value_proposition", ""),
                    trust_proof=data.get("trust_proof", []),
                    differentiation=data.get("differentiation", ""),
                    master_prompt=master_prompt,
                    created_at=now,
                    updated_at=now,
                )
                db.add(cfg)

            db.commit()
            db.refresh(cfg)
            return {"ok": True, "id": str(cfg.id), "master_prompt": master_prompt}
        except Exception as e:
            db.rollback()
            return {"error": str(e)}
        finally:
            db.close()

    def _build_master_prompt(self, data: dict) -> str:
        """
        根据四大输入模块生成母指令（master_prompt）
        这是所有 AI 生成任务的 system prompt 核心
        """
        identity = data.get("identity", "")
        value_prop = data.get("value_proposition", "")
        trust_proof = data.get("trust_proof", [])
        differentiation = data.get("differentiation", "")

        trust_str = "、".join(trust_proof) if trust_proof else "（待补充）"

        return f"""你是 {data.get("brand_name", "本品牌")} 的 AI 品牌助手。

## 品牌身份
{identity}

## 核心价值
{value_prop}

## 信任背书
{trust_str}

## 差异化定位
{differentiation}

---
## 输出要求
- 以上述品牌定位为唯一准则，所有输出不得偏离上述定位
- 语气专业、有说服力，面向商务决策者（CMO/COO 级别）
- 数据引用须真实可查，不得捏造
- 输出内容自动适配受众语言体系（用户/客户/渠道/投资人）
- 每次输出后在末尾注明"品牌主张匹配度"自评（1-10分）
""".strip()

    def get_master_prompt(self, brand_name: str = "XX传媒") -> str:
        """直接获取 master_prompt 字符串，供其他服务注入 LLM"""
        cfg = self.get_brand_config(brand_name)
        return cfg.get("master_prompt", "")


brand_engine = BrandEngine()
