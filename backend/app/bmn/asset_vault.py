"""
BMN L2 数字资产金库服务
- 八大资产子库：品牌诉求/产品卖点/用户场景/客户案例/行业知识/视觉资产/问答口径/风险边界
- 同时写入 PostgreSQL（结构化）+ ChromaDB（语义检索）
"""
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.bmn.models import BmnAsset, AssetType
from app.models import SessionLocal
from app.config import settings


# ── ChromaDB 集成 ──────────────────────────────────────────────
# 复用 AIAdPlacer 已有的 ChromaDB 客户端模式
# BMN 资产统一存放在 "bmn_assets" collection

class AssetVault:
    """
    数字资产金库
    - add_asset()   ：写入 PG + ChromaDB
    - search()      ：ChromaDB 语义检索，返回结构化结果
    - list_assets() ：结构化列表（分页）
    - get_asset()   ：单条详情
    - delete_asset()：同时从 PG 和 ChromaDB 删除
    - increment_usage()：使用计数 +1（用于资产热度排序）
    """

    COLLECTION_NAME = "bmn_assets"

    def __init__(self):
        self.chroma_collection = None
        self.embedding_model = None
        self._init_chromadb()

    def _init_chromadb(self):
        # 确保环境变量已设置（Windows 兼容性）
        import os
        os.environ["USERNAME"] = os.environ.get("USERNAME", "user")
        os.environ["USER"] = os.environ.get("USER", "user")
        
        try:
            import chromadb
            client = chromadb.Client()
            self.chroma_collection = client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            # 延迟加载 embedding 模型
            try:
                from sentence_transformers import SentenceTransformer
                self.embedding_model = SentenceTransformer("shibing624/text2vec-base-chinese")
                print(f"[OK] BMN 资产金库 ChromaDB 初始化成功，当前文档数: {self.chroma_collection.count()}")
            except Exception as e:
                print(f"[WARN] Embedding 模型加载失败（将使用模拟模式）: {e}")
                self.embedding_model = None
        except Exception as e:
            print(f"[WARN] BMN ChromaDB 初始化失败（将使用模拟模式）: {e}")
            self.chroma_collection = None

    def _encode(self, text: str) -> list:
        if self.embedding_model:
            return self.embedding_model.encode(text).tolist()
        # 模拟嵌入（降级方案）
        import hashlib
        h = hashlib.md5(text.encode("utf-8")).hexdigest()
        return [int(h[i:i + 2], 16) / 255.0 for i in range(0, 32, 2)]

    # ── CRUD ────────────────────────────────────────────────────

    def add_asset(
        self,
        asset_type: str,
        title: str,
        content: str,
        tags: List[str] = None,
        source: str = None,
        extra_data: dict = None,
    ) -> Dict:
        """新增资产，同时写入 PG 和 ChromaDB"""
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            asset = BmnAsset(
                asset_type=AssetType(asset_type),
                title=title,
                content=content,
                tags=tags or [],
                source=source,
                extra_data=extra_data or {},
                created_at=now,
                updated_at=now,
            )
            db.add(asset)
            db.commit()
            db.refresh(asset)

            # 写入 ChromaDB
            chroma_id = f"bmn_asset_{str(asset.id)}"
            if self.chroma_collection:
                embedding = self._encode(title + "\n" + content)
                self.chroma_collection.add(
                    embeddings=[embedding],
                    documents=[content],
                    metadatas=[{
                        "asset_id": str(asset.id),
                        "asset_type": asset_type,
                        "title": title,
                        "tags": ",".join(tags or []),
                        "source": source or "",
                    }],
                    ids=[chroma_id],
                )
                asset.chroma_doc_id = chroma_id
                db.commit()

            return {"ok": True, "id": str(asset.id), "chroma_id": chroma_id}

        except Exception as e:
            db.rollback()
            return {"error": str(e)}
        finally:
            db.close()

    def get_asset(self, asset_id: str) -> Dict:
        db = SessionLocal()
        try:
            from uuid import UUID
            asset = db.query(BmnAsset).filter_by(id=UUID(asset_id)).first()
            if not asset:
                return {"error": "资产不存在"}
            return self._serialize(asset)
        except Exception as e:
            return {"error": str(e)}
        finally:
            db.close()

    def list_assets(
        self,
        asset_type: str = None,
        keyword: str = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict:
        db = SessionLocal()
        try:
            q = db.query(BmnAsset)
            if asset_type:
                q = q.filter_by(asset_type=AssetType(asset_type))
            if keyword:
                q = q.filter(BmnAsset.title.contains(keyword) | BmnAsset.content.contains(keyword))
            total = q.count()
            items = q.order_by(BmnAsset.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
            return {
                "items": [self._serialize(a) for a in items],
                "total": total,
                "page": page,
                "page_size": page_size,
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            db.close()

    def search(self, query: str, asset_type: str = None, top_k: int = 5) -> Dict:
        """
        语义检索资产金库
        返回 ChromaDB 检索结果 + PG 详情
        """
        if not self.chroma_collection:
            # 降级：PG 模糊搜索
            return self._fallback_search(query, asset_type, top_k)

        try:
            embedding = self._encode(query)
            where = {"asset_type": asset_type} if asset_type else None
            results = self.chroma_collection.query(
                query_embeddings=[embedding],
                n_results=min(top_k * 2, max(1, self.chroma_collection.count())),
                where=where,
                include=["documents", "metadatas", "distances"],
            )

            # 格式化结果
            formatted = []
            db = SessionLocal()
            try:
                docs = results.get("documents", [[]])[0]
                metas = results.get("metadatas", [[]])[0]
                dists = results.get("distances", [[]])[0]
                for doc, meta, dist in zip(docs, metas, dists):
                    asset_id = meta.get("asset_id")
                    pg_asset = None
                    if asset_id:
                        from uuid import UUID
                        a = db.query(BmnAsset).filter_by(id=UUID(asset_id)).first()
                        if a:
                            pg_asset = self._serialize(a, short=True)
                            # 使用计数 +1
                            a.usage_count = (a.usage_count or 0) + 1
                    db.commit()
                    formatted.append({
                        "content": doc[:300],
                        "metadata": meta,
                        "relevance_score": round(1.0 / (1.0 + dist), 4),
                        "asset": pg_asset,
                    })
            finally:
                db.close()

            formatted.sort(key=lambda x: x["relevance_score"], reverse=True)
            return {"results": formatted[:top_k], "total": len(formatted)}

        except Exception as e:
            print(f"语义检索失败，降级到 PG 搜索: {e}")
            return self._fallback_search(query, asset_type, top_k)

    def _fallback_search(self, query: str, asset_type: str = None, top_k: int = 5) -> Dict:
        """ChromaDB 不可用时的降级搜索"""
        db = SessionLocal()
        try:
            q = db.query(BmnAsset)
            if asset_type:
                q = q.filter_by(asset_type=AssetType(asset_type))
            q = q.filter(BmnAsset.title.contains(query) | BmnAsset.content.contains(query))
            items = q.order_by(BmnAsset.usage_count.desc()).limit(top_k).all()
            return {
                "results": [{
                    "content": a.content[:300],
                    "metadata": {"title": a.title, "asset_type": a.asset_type.value},
                    "relevance_score": 0.5,
                    "asset": self._serialize(a, short=True),
                } for a in items],
                "total": len(items),
                "note": "降级模式（PG 模糊搜索）",
            }
        finally:
            db.close()

    def delete_asset(self, asset_id: str) -> Dict:
        db = SessionLocal()
        try:
            from uuid import UUID
            asset = db.query(BmnAsset).filter_by(id=UUID(asset_id)).first()
            if not asset:
                return {"error": "资产不存在"}
            chroma_id = asset.chroma_doc_id
            db.delete(asset)
            db.commit()
            # 从 ChromaDB 删除
            if self.chroma_collection and chroma_id:
                try:
                    self.chroma_collection.delete(ids=[chroma_id])
                except Exception:
                    pass
            return {"ok": True}
        except Exception as e:
            db.rollback()
            return {"error": str(e)}
        finally:
            db.close()

    def _serialize(self, asset: BmnAsset, short: bool = False) -> Dict:
        d = {
            "id": str(asset.id),
            "asset_type": asset.asset_type.value,
            "title": asset.title,
            "tags": asset.tags or [],
            "usage_count": asset.usage_count or 0,
            "source": asset.source,
            "created_at": asset.created_at.isoformat() if asset.created_at else None,
            "updated_at": asset.updated_at.isoformat() if asset.updated_at else None,
        }
        if not short:
            d["content"] = asset.content
            d["extra_data"] = asset.extra_data or {}
        return d


# 全局实例
asset_vault = AssetVault()
