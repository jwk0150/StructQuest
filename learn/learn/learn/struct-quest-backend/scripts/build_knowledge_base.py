"""
Build the StructQuest initial course knowledge base.

Inputs:
- course_data/data_structures/chapters/*.md
- knowledge_nodes seeded by app.db.session
- hardcoded chapter exam bank from app.api.exam_api

Output:
- Chroma collection used by app.services.rag.rag_service

Run:
    cd struct-quest-backend
    python scripts/build_knowledge_base.py
"""

from __future__ import annotations

import asyncio
import hashlib
import sys
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))
load_dotenv(BACKEND_ROOT / ".env")

COURSE_ID = "data_structures"
COURSE_NAME = "\u6570\u636e\u7ed3\u6784"
COURSE_VERSION = "2026.07"
COURSE_DIR = BACKEND_ROOT / "course_data" / COURSE_ID
CHAPTERS = [
    ("ch01_intro", "\u7eea\u8bba\u4e0e\u7b97\u6cd5\u5206\u6790", "chapters/01_intro.md"),
    ("ch02_linear_list", "\u7ebf\u6027\u8868", "chapters/02_linear_list.md"),
    ("ch03_stack_queue", "\u6808\u548c\u961f\u5217", "chapters/03_stack_queue.md"),
    ("ch04_string_array", "\u4e32\u3001\u6570\u7ec4\u548c\u5e7f\u4e49\u8868", "chapters/04_string_array.md"),
    ("ch05_tree", "\u6811\u548c\u4e8c\u53c9\u6811", "chapters/05_tree.md"),
    ("ch06_graph", "\u56fe", "chapters/06_graph.md"),
    ("ch07_search", "\u67e5\u627e", "chapters/07_search.md"),
    ("ch08_sort", "\u6392\u5e8f", "chapters/08_sort.md"),
]


def _stable_id(*parts: str) -> str:
    raw = "::".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _base_meta(document_type: str) -> Dict[str, str]:
    return {
        "course_id": COURSE_ID,
        "course_name": COURSE_NAME,
        "version": COURSE_VERSION,
        "document_type": document_type,
    }


def _load_course_docs() -> List[Dict[str, str]]:
    docs: List[Dict[str, str]] = []
    for chapter, title, rel_path in CHAPTERS:
        path = COURSE_DIR / rel_path
        if not path.exists():
            raise FileNotFoundError(f"Missing course chapter: {path}")
        content = path.read_text(encoding="utf-8")
        docs.append(
            {
                "doc_id": f"course_{COURSE_ID}_{chapter}",
                "title": title,
                "chapter": chapter,
                "source": str(path.relative_to(BACKEND_ROOT)).replace("\\", "/"),
                "content": content,
            }
        )
    return docs


async def _load_knowledge_nodes() -> List[Dict[str, str]]:
    from app.db.session import AsyncSessionLocal
    from sqlalchemy import text

    rows: List[Dict[str, str]] = []
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text(
                "SELECT id, title, description, full_desc, category, points, ai_suggestion "
                "FROM knowledge_nodes ORDER BY category, order_index"
            )
        )
        for node in result.fetchall():
            node_id, title, desc, full_desc, category, points, ai_suggestion = node
            rows.append(
                {
                    "id": f"node_{node_id}",
                    "title": title or node_id,
                    "chapter": category or "",
                    "source": "database:knowledge_nodes",
                    "content": "\n\n".join(
                        [
                            f"# {title}",
                            f"\u8282\u70b9ID: {node_id}",
                            f"\u7ae0\u8282: {category or ''}",
                            f"\u63cf\u8ff0: {desc or ''}",
                            f"\u8be6\u7ec6\u8bf4\u660e: {full_desc or ''}",
                            f"\u77e5\u8bc6\u70b9: {points or ''}",
                            f"\u5b66\u4e60\u5efa\u8bae: {ai_suggestion or ''}",
                        ]
                    ),
                }
            )
    return rows


def _load_exam_docs() -> List[Dict[str, str]]:
    try:
        from app.api.exam_api import NODE_EXAMS
    except Exception as exc:
        print(f"[warn] skip exam bank: {exc}")
        return []

    docs: List[Dict[str, str]] = []
    for node_id, exam_data in NODE_EXAMS.items():
        for index, q in enumerate(exam_data.get("questions", []), start=1):
            question = q.get("question", "")
            options = "\n".join(q.get("options", []))
            explanation = q.get("explanation", "")
            answer = q.get("answer", q.get("correct", ""))
            docs.append(
                {
                    "id": f"exam_{_stable_id(node_id, str(index), question)}",
                    "title": f"{node_id} \u7ec3\u4e60\u9898 {index}",
                    "chapter": node_id.split("_")[0] if "_" in node_id else "",
                    "source": "app.api.exam_api:NODE_EXAMS",
                    "content": (
                        f"# {node_id} \u7ec3\u4e60\u9898 {index}\n\n"
                        f"\u9898\u76ee: {question}\n\n"
                        f"\u9009\u9879:\n{options}\n\n"
                        f"\u7b54\u6848: {answer}\n\n"
                        f"\u89e3\u6790: {explanation}"
                    ),
                }
            )
    return docs


async def _sync_db_document_records(course_docs: List[Dict[str, str]], chunks_by_doc: Dict[str, int]) -> None:
    from app.db.session import AsyncSessionLocal
    from app.models.knowledge import KnowledgeDocument
    from sqlalchemy.future import select

    async with AsyncSessionLocal() as db:
        for doc in course_docs:
            result = await db.execute(
                select(KnowledgeDocument).where(KnowledgeDocument.doc_id == doc["doc_id"])
            )
            record = result.scalar_one_or_none()
            if record:
                record.filename = doc["source"]
                record.chunks = chunks_by_doc.get(doc["doc_id"], record.chunks or 0)
                record.status = "active"
            else:
                db.add(
                    KnowledgeDocument(
                        doc_id=doc["doc_id"],
                        filename=doc["source"],
                        file_size=round(len(doc["content"].encode("utf-8")) / 1024, 2),
                        chunks=chunks_by_doc.get(doc["doc_id"], 0),
                        status="active",
                    )
                )
        await db.commit()


async def build_knowledge_base() -> None:
    from app.db.session import init_database
    from app.services.rag import rag_service

    print("=" * 72)
    print("StructQuest initial course knowledge-base builder")
    print("=" * 72)

    print("[1/5] Ensure database schema and seed knowledge graph")
    await init_database()

    print("[2/5] Ingest course chapter documents")
    course_docs = _load_course_docs()
    chunks_by_doc: Dict[str, int] = {}
    for doc in course_docs:
        result = rag_service.ingest_texts(
            [doc["content"]],
            doc_id=doc["doc_id"],
            source=doc["source"],
            metadata={
                **_base_meta("initial_course"),
                "chapter": doc["chapter"],
                "chapter_name": doc["title"],
            },
        )
        chunks_by_doc[doc["doc_id"]] = result["chunks"]
        print(f"  {doc['chapter']}: {result['chunks']} chunks")

    print("[3/5] Sync course document records")
    await _sync_db_document_records(course_docs, chunks_by_doc)

    print("[4/5] Upsert knowledge graph nodes")
    nodes = await _load_knowledge_nodes()
    rag_service.add_documents(
        texts=[n["content"] for n in nodes],
        ids=[n["id"] for n in nodes],
        metadatas=[
            {
                **_base_meta("knowledge_graph_node"),
                "doc_id": n["id"],
                "title": n["title"],
                "chapter": n["chapter"],
                "source": n["source"],
            }
            for n in nodes
        ],
    )
    print(f"  {len(nodes)} nodes")

    print("[5/5] Upsert exam bank")
    exams = _load_exam_docs()
    rag_service.add_documents(
        texts=[e["content"] for e in exams],
        ids=[e["id"] for e in exams],
        metadatas=[
            {
                **_base_meta("exam_question"),
                "doc_id": e["id"],
                "title": e["title"],
                "chapter": e["chapter"],
                "source": e["source"],
            }
            for e in exams
        ],
    )
    print(f"  {len(exams)} questions")

    stats = rag_service.get_stats()
    print("Done.")
    print(f"  Chroma path: {stats.get('chroma_path')}")
    print(f"  Total chunks: {stats.get('total_chunks')}")
    print(f"  Distinct docs: {stats.get('document_count')}")


if __name__ == "__main__":
    asyncio.run(build_knowledge_base())
