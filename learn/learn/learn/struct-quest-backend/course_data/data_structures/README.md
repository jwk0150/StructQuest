# 数据结构初始课程知识库

这套文档是 StructQuest 的内置课程语料，用于满足“至少一门完整高校专业课程的初始知识库/文档集作为系统输入”的要求。

系统定位：

- 课程：数据结构
- 章节：8 章，对应数据库中的知识图谱章节
- 用途：启动或部署前通过 `scripts/build_knowledge_base.py` 写入 ChromaDB
- 下游：AI 问答智能体、资源生成智能体、考试生成逻辑、独立知识库检索接口

构建命令：

```bash
cd struct-quest-backend
python scripts/build_knowledge_base.py
```

构建后，向量库条目会带上 `course_id=data_structures`、`document_type=initial_course`、`chapter`、`source`、`version` 等元数据，便于和用户上传文档、AI 生成缓存区分。
