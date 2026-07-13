"""
课程知识库构建脚本

将 knowledge_nodes 表中的8章45个知识点 + 考试题库
向量化存入 ChromaDB，供 RAG 服务检索。

运行方式：
    cd struct-quest-backend
    python scripts/build_knowledge_base.py
"""
import os
import sys
import asyncio

# 确保项目路径在 sys.path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv()


async def build_knowledge_base():
    """构建知识库索引"""
    from app.db.session import AsyncSessionLocal, engine
    from sqlalchemy import text

    print("=" * 60)
    print("StructQuest 课程知识库构建工具")
    print("=" * 60)

    # 1. 从知识图谱节点提取内容
    print("\n[1/3] 提取知识图谱节点...")
    documents = []

    async with AsyncSessionLocal() as db:
        result = await db.execute(text(
            "SELECT id, title, description, full_desc, category, points, ai_suggestion "
            "FROM knowledge_nodes ORDER BY category, order_index"
        ))
        nodes = result.fetchall()

        for node in nodes:
            node_id, title, desc, full_desc, category, points, ai_suggestion = node

            # 组合为可检索的文本
            content_parts = [
                f"# {title}",
                f"分类: {category}",
                f"描述: {desc or ''}",
                f"详细说明: {full_desc or ''}",
                f"知识点: {points or ''}",
                f"学习建议: {ai_suggestion or ''}",
            ]
            content = "\n\n".join(content_parts)

            documents.append({
                "id": node_id,
                "title": title,
                "category": category,
                "content": content,
            })

        print(f"  已提取 {len(documents)} 个知识节点")

    # 2. 从考试题库提取题目
    print("\n[2/3] 提取考试题库...")
    try:
        from app.api.exam_api import NODE_EXAMS
        exam_count = 0
        for node_id, exam_data in NODE_EXAMS.items():
            questions = exam_data.get("questions", [])
            for q in questions:
                q_text = q.get("question", "")
                options = "\n".join(q.get("options", []))
                explanation = q.get("explanation", "")
                q_content = f"题目: {q_text}\n选项:\n{options}\n解析: {explanation}"

                documents.append({
                    "id": f"exam_{q.get('id', node_id)}",
                    "title": f"练习题: {q_text[:30]}...",
                    "category": "exam_questions",
                    "content": q_content,
                })
                exam_count += 1
        print(f"  已提取 {exam_count} 道练习题")
    except ImportError:
        print("  跳过：无法导入 NODE_EXAMS")

    # 3. 向量化存入 ChromaDB
    print(f"\n[3/3] 向量化并存入 ChromaDB ({len(documents)} 条文档)...")
    try:
        from app.services.rag import RAGService

        rag = RAGService.get_instance()
        if rag is None:
            print("  RAG 服务未初始化，请检查 EMBEDDING_API_KEY 配置")
            return

        # 分批处理
        batch_size = 10
        stored = 0
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            texts = [d["content"] for d in batch]
            ids = [d["id"] for d in batch]
            metadatas = [
                {"title": d["title"], "category": d["category"], "doc_id": d["id"]}
                for d in batch
            ]

            try:
                rag.add_documents(texts, ids=ids, metadatas=metadatas)
                stored += len(batch)
                print(f"  进度: {stored}/{len(documents)}")
            except Exception as e:
                print(f"  批次 {i//batch_size + 1} 失败: {e}")

        print(f"\n✅ 知识库构建完成！共 {stored} 条文档已索引")
    except Exception as e:
        print(f"\n❌ 向量化失败: {e}")
        print("  请检查:")
        print("  1. .env 文件中 EMBEDDING_API_KEY 是否正确")
        print("  2. EMBEDDING_BASE_URL 是否可访问")
        print("  3. ChromaDB 存储路径是否可写")


if __name__ == "__main__":
    asyncio.run(build_knowledge_base())
