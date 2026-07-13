# AGENTS.md

此文件为 Codex (Codex.ai/code) 在此仓库中工作时提供指导。

## 项目概览

StructQuest（结构探求）—— 一个 AI 驱动的学习平台，专注于使用中文教授**数据结构**。全栈：Python FastAPI 后端 + Vue 3 前端，具备 LLM 多服务商故障切换、RAG 知识库、TTS/数字人、以及 8 章知识图谱。

实际项目路径：
- **后端：** `learn/learn/learn/struct-quest-backend/`
- **前端：** `learn/learn/learn/struct-quest-frontend/`
- **Docker/根配置：** `learn/learn/learn/`

## 文件结构总览

> 图例：⭐ = 核心文件（入口/配置/关键基础设施） | 🤖 = 智能体相关文件（多智能体学习系统）

### 根目录 `learn/learn/learn/`

| 文件 | 说明 |
|------|------|
| ⭐ `.env` | 环境变量配置（LLM API Key、数据库地址、RAG 配置等） |
| ⭐ `start.bat` | Windows 一键启动脚本（交互菜单选择启动后端/前端/同时启动） |
| ⭐ `docker-compose.yml` | Docker 编排（MySQL + Redis + 后端 + 前端） |
| `DID_GUIDE.md` | D-ID 数字人配置使用指南 |
| `DIGITAL_TEACHER_README.md` | 数字人老师系统说明文档 |

---

### 后端 `struct-quest-backend/app/` — 完整文件清单

#### ⭐ 入口 & 基础设施

| 文件 | 说明 |
|------|------|
| ⭐ [`main.py`](learn/learn/learn/struct-quest-backend/app/main.py) | **FastAPI 应用入口**：CORS 配置、静态文件挂载、14 个路由注册、WebSocket `/ws/chat` 端点、启动自动建表 + 种子数据填充 |
| ⭐ [`auth.py`](learn/learn/learn/struct-quest-backend/app/auth.py) | **认证模块**：JWT 令牌生成/验证（HS256，7 天）、PBKDF2-SHA256 密码哈希、`get_current_user`/`get_required_user` 依赖注入 |
| ⭐ [`seed.py`](learn/learn/learn/struct-quest-backend/app/seed.py) | **数据种子**：首次启动时向 `knowledge_nodes` 表填充约 50 条知识点（8 章数据结构课程体系） |
| ⭐ [`db/session.py`](learn/learn/learn/struct-quest-backend/app/db/session.py) | **数据库层**：SQLAlchemy 异步引擎（SQLite/MySQL）、会话工厂、Redis 单例客户端、自动迁移缺失列 |

#### 🤖 多智能体系统 `agents/` — 基于 LangGraph 的智能学习引擎

这是 StructQuest 最核心的差异化功能——7 个专业 Agent 协作完成个性化学习路径规划和资源生成。

| 文件 | 说明 |
|------|------|
| 🤖⭐ [`agents/__init__.py`](learn/learn/learn/struct-quest-backend/app/agents/__init__.py) | **智能体包入口**：导出 `MultiAgentGraph`、`build_graph`、`run_learning_session`、`LearningState` |
| 🤖⭐ [`agents/base.py`](learn/learn/learn/struct-quest-backend/app/agents/base.py) | **Agent 抽象基类**：统一 LLM 调用（含同步兜底）、JSON 解析（中文标点清洗)、RAG 检索集成、日志记录、安全执行包装器。所有业务 Agent 继承此类 |
| 🤖⭐ [`agents/state.py`](learn/learn/learn/struct-quest-backend/app/agents/state.py) | **全局共享状态定义**：`LearningState`(顶层)、`StudentProfile`(学习画像)、`PathStep`(路径步骤)、`ResourceItem`/`ResourceBundle`(资源)、`AssessmentResult`(测评结果)、`BehaviorFeatures`(行为特征)、`KnowledgeMastery`(知识追踪)、`SessionSnapshot`(断点续学) 等 TypedDict |
| 🤖⭐ [`agents/graph.py`](learn/learn/learn/struct-quest-backend/app/agents/graph.py) | **LangGraph 编排引擎**：定义 7 节点状态图（profile → behavior → profile_update → path → resource → review → assessment），含条件路由（测评 ≥80 继续、<40 回退重规划）、循环迭代控制。提供 `run_learning_session()` 便捷入口 |
| 🤖 [`agents/profile_agent.py`](learn/learn/learn/struct-quest-backend/app/agents/profile_agent.py) | **学习画像 Agent**：分析学生能力等级、强弱项、学习风格（视觉/听觉/阅读/动手）、认知特征（MBTI 简化风格、费曼法适配度、抽象推理能力）、短板诊断 |
| 🤖 [`agents/behavior_agent.py`](learn/learn/learn/struct-quest-backend/app/agents/behavior_agent.py) | **行为分析 Agent**：从聊天记录、答题模式、学习时长中提取行为特征（专注度、参与度、节奏信号、资源偏好） |
| 🤖 [`agents/profile_update_agent.py`](learn/learn/learn/struct-quest-backend/app/agents/profile_update_agent.py) | **画像动态更新 Agent**：根据学习事件和测评结果持续更新用户画像，预测成绩趋势，调整学习策略 |
| 🤖 [`agents/path_agent.py`](learn/learn/learn/struct-quest-backend/app/agents/path_agent.py) | **学习路径规划 Agent**：基于依赖图谱和布鲁姆认知层级（记忆→理解→应用→分析→评估→创造）规划自适应难度螺旋路径 |
| 🤖 [`agents/resource_agent.py`](learn/learn/learn/struct-quest-backend/app/agents/resource_agent.py) | **资源生成 Agent**：生成 6 种学习资源——讲义（Markdown）、思维导图（Mermaid/Markmap）、练习题（结构化 JSON）、代码案例（Python）、PPT 大纲、Manim 动画 |
| 🤖 [`agents/review_agent.py`](learn/learn/learn/struct-quest-backend/app/agents/review_agent.py) | **审核推荐 Agent**：对生成的资源进行质量审查、相关性评分、推荐排序，提供管理员治理入口 |
| 🤖 [`agents/assessment_agent.py`](learn/learn/learn/struct-quest-backend/app/agents/assessment_agent.py) | **测评 Agent**：布鲁姆六维评估（记忆/理解/应用/分析/评估/创造）、错误模式识别、知识掌握追踪（知识追踪图谱） |

**智能体系统架构图（状态流转）：**

```
START
  → 🤖 profile_agent (学习画像分析：能力/风格/认知)
    → 🤖 behavior_agent (行为特征提取：专注度/资源偏好)
      → 🤖 profile_update_agent (动态画像更新：预测/策略)
        → 🤖 path_agent (学习路径规划：依赖图谱/布鲁姆层级)
          → 🤖 resource_agent (6种资源生成：讲义/导图/题/代码/PPT/动画)
            → 🤖 review_agent (资源审核推荐)
              → 🤖 assessment_agent (布鲁姆六维测评)
                ├─ 优秀(≥80) + 有后续 → resource_agent (继续下一步)
                ├─ 不及格(<40) → path_agent (回退重规划)
                └─ 全部完成/迭代上限 → END
```

#### 📡 API 路由层 `api/`

每个文件对应一组 REST 端点，由 `main.py` 统一注册。

| 文件 | 说明 |
|------|------|
| ⭐ [`api/auth_api.py`](learn/learn/learn/struct-quest-backend/app/api/auth_api.py) | **认证 API**：注册、登录、Token 刷新、密码修改 |
| [`api/knowledge_api.py`](learn/learn/learn/struct-quest-backend/app/api/knowledge_api.py) | **知识图谱 API**：知识点 CRUD、章节结构、知识节点查询 |
| [`api/knowledge_doc_api.py`](learn/learn/learn/struct-quest-backend/app/api/knowledge_doc_api.py) | **知识库文档 API**：PDF/PPTX 上传、文档管理（管理员） |
| [`api/profile_api.py`](learn/learn/learn/struct-quest-backend/app/api/profile_api.py) | **用户画像 API**：画像保存/查询、学习模式设置 |
| [`api/learning.py`](learn/learn/learn/struct-quest-backend/app/api/learning.py) | **学习 API**：节点学习、资源获取、Manim 视频生成、学习进度更新 |
| [`api/study_api.py`](learn/learn/learn/struct-quest-backend/app/api/study_api.py) | **学习会话 API**：计时、专注度记录 |
| [`api/exam_api.py`](learn/learn/learn/struct-quest-backend/app/api/exam_api.py) | **考试 API**：章节考试、题目生成、成绩提交 |
| [`api/chat_api.py`](learn/learn/learn/struct-quest-backend/app/api/chat_api.py) | **聊天 API**：聊天历史保存/查询、会话管理 |
| [`api/admin_api.py`](learn/learn/learn/struct-quest-backend/app/api/admin_api.py) | **管理后台 API**：用户管理、数据统计、系统配置 |
| [`api/ability_api.py`](learn/learn/learn/struct-quest-backend/app/api/ability_api.py) | **能力评估 API**：用户能力维度 CRUD、雷达图数据 |
| [`api/task_api.py`](learn/learn/learn/struct-quest-backend/app/api/task_api.py) | **学习任务 API**：任务记录、完成状态 |
| [`api/daily_task_api.py`](learn/learn/learn/struct-quest-backend/app/api/daily_task_api.py) | **每日任务 API**：每日任务分配、打卡 |
| [`api/daily_learning_api.py`](learn/learn/learn/struct-quest-backend/app/api/daily_learning_api.py) | **每日学习 API**：每日学习进度追踪 |
| [`api/ppt_generator.py`](learn/learn/learn/struct-quest-backend/app/api/ppt_generator.py) | **PPT 生成 API**：解析思维导图 + 渲染 PPT（三阶段流程） |
| [`api/recommendation_api.py`](learn/learn/learn/struct-quest-backend/app/api/recommendation_api.py) | **推荐 API**：AI 推荐外部学习资源（网页/视频/文章） |

#### 🔧 业务服务层 `services/`

| 文件 | 说明 |
|------|------|
| ⭐ [`services/llm.py`](learn/learn/learn/struct-quest-backend/app/services/llm.py) | **LLM 多服务商故障切换**：`LLMProvider` 抽象基类 → `OpenAIProvider`/`AnthropicProvider`。`chat_with_failover()` 流式 + `chat_completion()` 非流式。自动按序切换服务商 |
| ⭐ [`services/rag.py`](learn/learn/learn/struct-quest-backend/app/services/rag.py) | **RAG 知识库**：PDF/PPTX 解析 → 文本分割 → 嵌入向量（SiliconFlow BGE）→ ChromaDB 存储检索 |
| [`services/tts.py`](learn/learn/learn/struct-quest-backend/app/services/tts.py) | **Edge TTS 语音合成**：微软 Edge TTS → MP3 base64 编码，支持多音色 |
| [`services/did.py`](learn/learn/learn/struct-quest-backend/app/services/did.py) | **D-ID 数字人**：生成真人数字人说话视频，基于内容哈希的磁盘缓存（相同文本不重复计费） |
| [`services/manim_renderer.py`](learn/learn/learn/struct-quest-backend/app/services/manim_renderer.py) | **Manim 动画渲染**：LLM 生成 Manim 代码 → 安全注入配置 → subprocess 渲染 → 返回视频 URL |
| [`services/pptx_generator.py`](learn/learn/learn/struct-quest-backend/app/services/pptx_generator.py) | **PPTX 文件生成**：从大纲 JSON 生成 .pptx 文件（python-pptx） |
| [`services/html_renderer.py`](learn/learn/learn/struct-quest-backend/app/services/html_renderer.py) | **HTML 预览渲染**：从大纲 JSON 生成 HTML 预览页面 |
| [`services/slide_templates.py`](learn/learn/learn/struct-quest-backend/app/services/slide_templates.py) | **PPT 幻灯片模板**：10 种布局模板（title/section/content/summary/chart/comparison/timeline/quote/two_column/cards_grid） |
| [`services/mindmap_extractor.py`](learn/learn/learn/struct-quest-backend/app/services/mindmap_extractor.py) | **思维导图解析器**：解析 Markmap/Markdown 格式思维导图 → LLM 生成 PPT 大纲 → 规则引擎 fallback |
| [`services/recommendation_engine.py`](learn/learn/learn/struct-quest-backend/app/services/recommendation_engine.py) | **推荐引擎**：基于用户画像和知识图谱推荐外部学习资源 |
| [`services/web_crawler.py`](learn/learn/learn/struct-quest-backend/app/services/web_crawler.py) | **网页爬虫**：抓取和解析外部学习资源 |
| [`services/learning_mode_service.py`](learn/learn/learn/struct-quest-backend/app/services/learning_mode_service.py) | **学习模式服务**：管理多种学习模式（自由探索/路径引导/考试冲刺等） |
| [`services/learning_record_service.py`](learn/learn/learn/struct-quest-backend/app/services/learning_record_service.py) | **学习记录服务**：学习事件追踪、进度统计 |
| [`services/ability_service.py`](learn/learn/learn/struct-quest-backend/app/services/ability_service.py) | **能力评估服务**：用户多维度能力计算与更新 |
| [`services/cache_service.py`](learn/learn/learn/struct-quest-backend/app/services/cache_service.py) | **缓存服务**：Redis 缓存封装 |
| [`services/task_service.py`](learn/learn/learn/struct-quest-backend/app/services/task_service.py) | **任务服务**：学习任务生成与分配 |
| [`services/user_profile.py`](learn/learn/learn/struct-quest-backend/app/services/user_profile.py) | **用户画像服务**：画像数据持久化和查询 |

#### 📊 数据模型层 `models/`

| 文件 | 对应数据表 |
|------|-----------|
| [`models/user.py`](learn/learn/learn/struct-quest-backend/app/models/user.py) | `users` — 用户账户、密码哈希、学习模式 |
| [`models/knowledge.py`](learn/learn/learn/struct-quest-backend/app/models/knowledge.py) | `knowledge_documents` — 上传的知识文档 |
| [`models/knowledge_graph.py`](learn/learn/learn/struct-quest-backend/app/models/knowledge_graph.py) | `knowledge_nodes` — 知识图谱节点（8 章 50+ 知识点） |
| [`models/learning_progress.py`](learn/learn/learn/struct-quest-backend/app/models/learning_progress.py) | `learning_progress` — 用户学习进度 |
| [`models/study_session.py`](learn/learn/learn/struct-quest-backend/app/models/study_session.py) | `study_sessions` — 学习会话记录 |
| [`models/exam_result.py`](learn/learn/learn/struct-quest-backend/app/models/exam_result.py) | `exam_results` — 考试结果 |
| [`models/chat.py`](learn/learn/learn/struct-quest-backend/app/models/chat.py) | `chat_sessions` + `chat_messages` — 聊天记录 |
| [`models/resource.py`](learn/learn/learn/struct-quest-backend/app/models/resource.py) | `external_resources` — 外部学习资源 |
| [`models/user_ability.py`](learn/learn/learn/struct-quest-backend/app/models/user_ability.py) | `user_abilities` — 用户能力维度评估 |
| [`models/user_task.py`](learn/learn/learn/struct-quest-backend/app/models/user_task.py) | `user_task_records` — 用户任务记录 |
| [`models/wrong_question.py`](learn/learn/learn/struct-quest-backend/app/models/wrong_question.py) | `wrong_questions` — 错题本 |
| [`models/daily_task.py`](learn/learn/learn/struct-quest-backend/app/models/daily_task.py) | `daily_tasks` — 每日学习任务 |
| [`models/daily_learning_progress.py`](learn/learn/learn/struct-quest-backend/app/models/daily_learning_progress.py) | `daily_learning_progress` — 每日学习进度 |
| [`models/learning_ecosystem.py`](learn/learn/learn/struct-quest-backend/app/models/learning_ecosystem.py) | `learning_events`、`profile_snapshots`、`learning_plans`、`learning_plan_steps`、`resource_assets`、`resource_reviews` — 学习生态系统（事件溯源/计划/资源管理） |
| [`models/generated_content.py`](learn/learn/learn/struct-quest-backend/app/models/generated_content.py) | `generated_content` — AI 生成内容缓存 |

#### 🧪 实验性模块 `minimal_langgraph/`

| 文件 | 说明 |
|------|------|
| [`minimal_langgraph/__init__.py`](learn/learn/learn/struct-quest-backend/app/minimal_langgraph/__init__.py) | 极简 LangGraph 实现（实验性），不依赖 langgraph 包的轻量替代 |
| [`minimal_langgraph/state.py`](learn/learn/learn/struct-quest-backend/app/minimal_langgraph/state.py) | 简化版状态定义 |
| [`minimal_langgraph/graph.py`](learn/learn/learn/struct-quest-backend/app/minimal_langgraph/graph.py) | 简化版图编排 |
| [`minimal_langgraph/api.py`](learn/learn/learn/struct-quest-backend/app/minimal_langgraph/api.py) | 简化版 API 端点 |
| [`minimal_langgraph/planner_agent.py`](learn/learn/learn/struct-quest-backend/app/minimal_langgraph/planner_agent.py) | 简化版规划 Agent |
| [`minimal_langgraph/profile_agent.py`](learn/learn/learn/struct-quest-backend/app/minimal_langgraph/profile_agent.py) | 简化版画像 Agent |

#### 🛠 工具层 `utils/`

| 文件 | 说明 |
|------|------|
| [`utils/logger.py`](learn/learn/learn/struct-quest-backend/app/utils/logger.py) | 统一日志系统（格式、级别、输出目标） |

---

### 前端 `struct-quest-frontend/src/` — 完整文件清单

#### ⭐ 入口 & 配置

| 文件 | 说明 |
|------|------|
| ⭐ [`main.js`](learn/learn/learn/struct-quest-frontend/src/main.js) | **Vue 应用入口**：创建 app → 安装 Pinia/Router/Element Plus → 注册全部图标 → 全局错误处理 → 挂载 `#app` → 后台同步认证状态 |
| ⭐ [`App.vue`](learn/learn/learn/struct-quest-frontend/src/App.vue) | **根组件**：全局布局容器、路由视图 `<router-view>` |
| ⭐ [`router/index.js`](learn/learn/learn/struct-quest-frontend/src/router/index.js) | **Vue Router**：15 条路由定义 + 路由守卫（登录检测 → 引导检测 → 模式选择 → 管理员保护），支持 localStorage 降级恢复 |
| ⭐ [`vite.config.js`](learn/learn/learn/struct-quest-frontend/vite.config.js) | **Vite 配置**：`@` 别名、Vue 模板编译模式、开发代理（`/api` → 8008、`/ws` → 8008、`/static` → 8008） |

#### 🗄 状态管理 `store/` — Pinia

| 文件 | 说明 |
|------|------|
| ⭐ [`store/session.js`](learn/learn/learn/struct-quest-frontend/src/store/session.js) | **会话 Store**（核心）：认证状态、用户信息、学习模式、引导进度、疲劳度。`login()`/`logout()`/`syncFromServer()`/`completeOnboarding()`。持久化到 localStorage 作为服务端降级方案 |
| [`store/learning.js`](learn/learn/learn/struct-quest-frontend/src/store/learning.js) | **学习 Store**：当前学习节点、进度、资源包 |
| [`store/chat.js`](learn/learn/learn/struct-quest-frontend/src/store/chat.js) | **聊天 Store**：消息列表、WebSocket 连接状态 |
| [`store/task.js`](learn/learn/learn/struct-quest-frontend/src/store/task.js) | **任务 Store**：每日任务、学习任务状态 |
| [`store/persona.js`](learn/learn/learn/struct-quest-frontend/src/store/persona.js) | **数字人 Store**：Live2D/数字人老师状态 |
| [`store/ability.js`](learn/learn/learn/struct-quest-frontend/src/store/ability.js) | **能力 Store**：用户能力维度数据 |
| [`store/theme.js`](learn/learn/learn/struct-quest-frontend/src/store/theme.js) | **主题 Store**：亮色/暗色主题切换 |

#### 📡 API 客户端 `api/`

| 文件 | 说明 |
|------|------|
| ⭐ [`utils/request.js`](learn/learn/learn/struct-quest-frontend/src/utils/request.js) | **Axios 实例**：baseURL、拦截器（401 → 跳转登录页）、token 注入 |
| [`api/auth.js`](learn/learn/learn/struct-quest-frontend/src/api/auth.js) | 认证 API：登录、注册、获取当前用户 |
| [`api/knowledge.js`](learn/learn/learn/struct-quest-frontend/src/api/knowledge.js) | 知识图谱 API：知识点、章节结构 |
| [`api/learning.js`](learn/learn/learn/struct-quest-frontend/src/api/learning.js) | 学习 API：节点内容、资源、Manim 视频 |
| [`api/learningWs.js`](learn/learn/learn/struct-quest-frontend/src/api/learningWs.js) | **WebSocket 客户端**：`/ws/chat` 连接，接收 `chunk`/`done`/`tts_audio`/`tts_start`/`tts_error`/`did_video` 消息 |
| [`api/exam.js`](learn/learn/learn/struct-quest-frontend/src/api/exam.js) | 考试 API：题目、提交、成绩 |
| [`api/profile.js`](learn/learn/learn/struct-quest-frontend/src/api/profile.js) | 画像 API：保存/查询画像、学习模式 |
| [`api/study.js`](learn/learn/learn/struct-quest-frontend/src/api/study.js) | 学习会话 API：计时、记录 |
| [`api/admin.js`](learn/learn/learn/struct-quest-frontend/src/api/admin.js) | 管理后台 API |
| [`api/dailyLearning.js`](learn/learn/learn/struct-quest-frontend/src/api/dailyLearning.js) | 每日学习 API |
| [`api/dailyTask.js`](learn/learn/learn/struct-quest-frontend/src/api/dailyTask.js) | 每日任务 API |
| [`api/resource.js`](learn/learn/learn/struct-quest-frontend/src/api/resource.js) | 资源 API：外部资源、推荐 |

#### 📄 视图页面 `views/`

| 文件 | 路由 | 说明 |
|------|------|------|
| ⭐ [`views/Login/index.vue`](learn/learn/learn/struct-quest-frontend/src/views/Login/index.vue) | `/login` | **登录页**：账户密码登录、注册切换 |
| ⭐ [`views/Onboarding/index.vue`](learn/learn/learn/struct-quest-frontend/src/views/Onboarding/index.vue) | `/onboarding` | **新手引导页**：多步骤画像采集（学习风格/目标/基础水平/MBTI 简易测试） |
| ⭐ [`views/ModeChoice/index.vue`](learn/learn/learn/struct-quest-frontend/src/views/ModeChoice/index.vue) | `/mode-choice` | **学习模式选择页**：自由探索/路径引导/考试冲刺 等模式 |
| [`views/Dashboard/index.vue`](learn/learn/learn/struct-quest-frontend/src/views/Dashboard/index.vue) | `/dashboard` | **仪表盘首页**：学习概览、进度统计、每日任务、热门知识点、推荐资源 |
| [`views/Dashboard/HotTopicDetail.vue`](learn/learn/learn/struct-quest-frontend/src/views/Dashboard/HotTopicDetail.vue) | `/hot/:topicId` | 热门知识点详情页 |
| [`views/Dashboard/ExternalResources.vue`](learn/learn/learn/struct-quest-frontend/src/views/Dashboard/ExternalResources.vue) | (仪表盘子组件) | 外部推荐资源面板 |
| [`views/Map/index.vue`](learn/learn/learn/struct-quest-frontend/src/views/Map/index.vue) | `/map` | **知识图谱可视化页**：ECharts 图形化展示 8 章知识结构 |
| [`views/Quest/index.vue`](learn/learn/learn/struct-quest-frontend/src/views/Quest/index.vue) | `/quest` | **知识点探索页**：任务式关卡推进 |
| [`views/NodeLearning/index.vue`](learn/learn/learn/struct-quest-frontend/src/views/NodeLearning/index.vue) | `/learn/:nodeId` | **单节点学习页**（核心学习页）：讲义/思维导图/代码/动画 + AI 对话面板 |
| [`views/ChapterExam/index.vue`](learn/learn/learn/struct-quest-frontend/src/views/ChapterExam/index.vue) | `/exam/:nodeId` | **章节考试页**：答题 + 自动评分 + 错题收集 |
| [`views/Chat/index.vue`](learn/learn/learn/struct-quest-frontend/src/views/Chat/index.vue) | `/chat` | **AI 聊天页**：与 AI 老师自由对话，支持语音合成 + 数字人 |
| [`views/Review/index.vue`](learn/learn/learn/struct-quest-frontend/src/views/Review/index.vue) | `/review` | **复习页**：错题回顾、知识点巩固 |
| [`views/Analysis/index.vue`](learn/learn/learn/struct-quest-frontend/src/views/Analysis/index.vue) | `/analysis` | **学习分析页**：能力雷达图、进度趋势、知识掌握热力图 |
| [`views/Profile/index.vue`](learn/learn/learn/struct-quest-frontend/src/views/Profile/index.vue) | `/profile` | **个人中心**：画像查看/编辑、学习统计、设置 |
| [`views/Admin/index.vue`](learn/learn/learn/struct-quest-frontend/src/views/Admin/index.vue) | `/admin` | **管理后台**：用户管理、数据统计（需管理员权限） |
| [`views/KnowledgeBase/index.vue`](learn/learn/learn/struct-quest-frontend/src/views/KnowledgeBase/index.vue) | (内嵌页面) | **知识库管理**：PDF/PPTX 上传、文档浏览 |
| [`views/DailyPractice/index.vue`](learn/learn/learn/struct-quest-frontend/src/views/DailyPractice/index.vue) | `/daily-practice` | **每日练习页**：每日任务、打卡 |

#### 🧩 组件 `components/`

| 文件 | 说明 |
|------|------|
| ⭐ [`layout/index.vue`](learn/learn/learn/struct-quest-frontend/src/layout/index.vue) | **主布局**：侧边栏 + 顶栏 + `<router-view>` 的内容区 |
| [`common/AppHeader.vue`](learn/learn/learn/struct-quest-frontend/src/components/common/AppHeader.vue) | **顶栏**：Logo、导航、用户菜单、通知 |
| [`common/AppSidebar.vue`](learn/learn/learn/struct-quest-frontend/src/components/common/AppSidebar.vue) | **侧边栏**：功能导航菜单 |
| [`common/Breadcrumb.vue`](learn/learn/learn/struct-quest-frontend/src/components/common/Breadcrumb.vue) | 面包屑导航 |
| [`common/Card.vue`](learn/learn/learn/struct-quest-frontend/src/components/common/Card.vue) | 通用卡片组件 |
| [`common/Tag.vue`](learn/learn/learn/struct-quest-frontend/src/components/common/Tag.vue) | 通用标签组件 |
| [`common/Progress.vue`](learn/learn/learn/struct-quest-frontend/src/components/common/Progress.vue) | 通用进度条组件 |
| [`common/Skeleton.vue`](learn/learn/learn/struct-quest-frontend/src/components/common/Skeleton.vue) | 骨架屏加载组件 |
| [`common/Modal.vue`](learn/learn/learn/struct-quest-frontend/src/components/common/Modal.vue) | 通用弹窗组件 |
| [`common/AIStatus.vue`](learn/learn/learn/struct-quest-frontend/src/components/common/AIStatus.vue) | AI 思考状态指示器 |
| [`common/StreamMessage.vue`](learn/learn/learn/struct-quest-frontend/src/components/common/StreamMessage.vue) | 流式消息渲染（Markdown + 代码高亮） |
| [`common/ResourceCard.vue`](learn/learn/learn/struct-quest-frontend/src/components/common/ResourceCard.vue) | 学习资源卡片 |
| [`common/PdfUploadDialog.vue`](learn/learn/learn/struct-quest-frontend/src/components/common/PdfUploadDialog.vue) | PDF 上传弹窗 |
| [`AICompanion/index.vue`](learn/learn/learn/struct-quest-frontend/src/components/AICompanion/index.vue) | **AI 陪伴面板**：右侧可折叠的 AI 对话 + TTS/数字人切换 |
| [`DigitalTeacher/index.vue`](learn/learn/learn/struct-quest-frontend/src/components/DigitalTeacher/index.vue) | **数字人老师组件**：Live2D 模型渲染 + 语音同步 |
| [`PPTGenerator/index.vue`](learn/learn/learn/struct-quest-frontend/src/components/PPTGenerator/index.vue) | **PPT 智能生成器**（容器）：三阶段流程编排 |
| [`PPTGenerator/Step1Input.vue`](learn/learn/learn/struct-quest-frontend/src/components/PPTGenerator/Step1Input.vue) | PPT 生成器 **第一步**：输入/粘贴思维导图 Markdown |
| [`PPTGenerator/Step2Editor.vue`](learn/learn/learn/struct-quest-frontend/src/components/PPTGenerator/Step2Editor.vue) | PPT 生成器 **第二步**：编辑 LLM 生成的大纲（拖拽排序、增删页） |
| [`PPTGenerator/Step3Render.vue`](learn/learn/learn/struct-quest-frontend/src/components/PPTGenerator/Step3Render.vue) | PPT 生成器 **第三步**：预览 HTML + 下载 PPTX |
| [`QuizDisplay/index.vue`](learn/learn/learn/struct-quest-frontend/src/components/QuizDisplay/index.vue) | 练习题展示组件（选择题/填空题/判断题） |
| [`LearningCalendar.vue`](learn/learn/learn/struct-quest-frontend/src/components/LearningCalendar.vue) | 学习日历热力图 |
| [`ModeTag.vue`](learn/learn/learn/struct-quest-frontend/src/components/ModeTag.vue) | 学习模式标签 |

#### 🔌 组合式函数 `composables/`（Composition API Hooks）

| 文件 | 说明 |
|------|------|
| [`composables/useAuth.js`](learn/learn/learn/struct-quest-frontend/src/composables/useAuth.js) | 认证相关逻辑封装 |
| [`composables/useStudyTimer.js`](learn/learn/learn/struct-quest-frontend/src/composables/useStudyTimer.js) | 学习计时器（开始/暂停/统计） |
| [`composables/useGlobalTimer.js`](learn/learn/learn/struct-quest-frontend/src/composables/useGlobalTimer.js) | 全局计时器（跨页面学习时长追踪） |
| [`composables/useTheme.js`](learn/learn/learn/struct-quest-frontend/src/composables/useTheme.js) | 主题切换逻辑 |
| [`composables/usePPTGenerator.js`](learn/learn/learn/struct-quest-frontend/src/composables/usePPTGenerator.js) | PPT 生成器逻辑封装（API 调用 + 状态管理） |

#### 🛠 工具 & 静态数据

| 文件 | 说明 |
|------|------|
| ⭐ [`utils/request.js`](learn/learn/learn/struct-quest-frontend/src/utils/request.js) | **Axios 请求封装**：baseURL、401 拦截自动跳转登录 |
| [`utils/storage.js`](learn/learn/learn/struct-quest-frontend/src/utils/storage.js) | **localStorage 工具**：带命名空间的存取、`STORAGE_KEYS` 常量 |
| [`utils/mindmapParser.js`](learn/learn/learn/struct-quest-frontend/src/utils/mindmapParser.js) | **思维导图解析器**：前端 Markdown/Markmap 解析 |
| [`data/knowledgeMap.js`](learn/learn/learn/struct-quest-frontend/src/data/knowledgeMap.js) | **知识图谱静态数据**：8 章章节定义、知识点列表 |
| [`data/knowledgeModes.js`](learn/learn/learn/struct-quest-frontend/src/data/knowledgeModes.js) | **学习模式定义**：各模式的名称、描述、图标、推荐场景 |

---

### 文件角色速查

**🔴 核心文件（必须确保稳定）：**

| 优先级 | 后端 | 前端 |
|--------|------|------|
| P0 - 入口 | `app/main.py` | `src/main.js` |
| P0 - 配置 | `.env`、`db/session.py` | `vite.config.js` |
| P0 - 认证 | `app/auth.py` | `src/store/session.js`、`src/router/index.js` |
| P0 - 数据 | `models/` (全部 15 个文件) | `src/utils/request.js` |
| P1 - LLM | `services/llm.py` | `src/api/learningWs.js` |
| P1 - RAG | `services/rag.py` | `src/api/knowledge.js` |
| P1 - 智能体 | `agents/` (全部 10 个文件) | — |

**🤖 全部智能体相关文件：**

| 文件 | 角色 |
|------|------|
| `agents/base.py` | 基类 — 所有 Agent 的父类 |
| `agents/state.py` | 状态 — 数据模型定义 |
| `agents/graph.py` | 编排 — LangGraph 图 + 路由 |
| `agents/profile_agent.py` | 画像分析 |
| `agents/behavior_agent.py` | 行为分析 |
| `agents/profile_update_agent.py` | 画像更新 |
| `agents/path_agent.py` | 路径规划 |
| `agents/resource_agent.py` | 资源生成 |
| `agents/review_agent.py` | 审核推荐 |
| `agents/assessment_agent.py` | 测评反馈 |
| `minimal_langgraph/*` (6 个文件) | 实验性轻量替代（不依赖 langgraph 包） |

## 常用命令

### 后端（FastAPI + Uvicorn，默认端口 8008）

```bash
# 启动后端（在 struct-quest-backend/ 下执行）
cd learn/learn/learn/struct-quest-backend
.\venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8008 --reload

# 安装依赖
cd learn/learn/learn/struct-quest-backend
.\venv\Scripts\pip install -r requirements.txt
```

### 前端（Vue 3 + Vite，默认端口 5173）

```bash
# 启动开发服务器（在 struct-quest-frontend/ 下执行）
cd learn/learn/learn/struct-quest-frontend
npm run dev          # 将 /api、/ws、/static 代理到 localhost:8008

# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

### Docker（完整技术栈：MySQL + Redis）

```bash
cd learn/learn/learn
docker-compose up --build
```

### Windows 一键启动

```bash
cd learn/learn/learn
start.bat    # 交互菜单：选择启动后端、前端或同时启动
```

## 架构

### 后端（`struct-quest-backend/app/`）

**入口：** [`main.py`](learn/learn/learn/struct-quest-backend/app/main.py) — FastAPI 应用，配置 CORS（允许全部来源），静态文件挂载于 `/static`，注册所有路由。启动时自动建表，并在 `knowledge_nodes` 表为空时填充约 50 条知识点记录（8 章数据结构课程体系）。

**核心架构模式：**

- **多服务商 LLM 故障切换**（[`services/llm.py`](learn/learn/learn/struct-quest-backend/app/services/llm.py)）：`LLMProvider` 抽象基类 → `OpenAIProvider` 和 `AnthropicProvider` 实现。`LLMService.chat_with_failover()` 按顺序尝试各服务商，出错时自动切换。通过 `.env` 配置：`OPENAI_API_KEY`、`OPENAI_BASE_URL`、`ANTHROPIC_API_KEY`。
- **RAG 流水线**（[`services/rag.py`](learn/learn/learn/struct-quest-backend/app/services/rag.py)）：PDF/PPTX 上传 → LangChain `PyPDFLoader`/python-pptx → `RecursiveCharacterTextSplitter` → SiliconFlow 嵌入模型（`BAAI/bge-large-zh-v1.5`）→ ChromaDB 存储和相似度检索。通过 `.env` 配置：`EMBEDDING_API_KEY`、`EMBEDDING_BASE_URL`。
- **数据库**（[`db/session.py`](learn/learn/learn/struct-quest-backend/app/db/session.py)）：SQLAlchemy 异步，默认使用 SQLite（`sqlite+aiosqlite`）。可通过 Docker 切换为 MySQL（`mysql+aiomysql`）。启动时自动迁移缺失的列。Redis 客户端（单例模式）用于可选缓存。
- **认证**（[`auth.py`](learn/learn/learn/struct-quest-backend/app/auth.py)）：JWT（HS256，7 天有效期）+ PBKDF2-SHA256 密码哈希（不依赖 bcrypt）。`get_current_user` 在 token 无效/过期时静默返回 `None`；`get_required_user` 会抛出 401。
- **WebSocket 聊天**（[`main.py` L349-434](learn/learn/learn/struct-quest-backend/app/main.py#L349-L434)）：`/ws/chat` — 接收 JSON `{messages, provider, voice, enable_tts, tts_mode, system_prompt}`。流式返回 LLM 分块 `{"type":"chunk","content":"..."}`，然后返回 TTS 音频 `{"type":"tts_audio","audio_url":"..."}`。

**目录结构：**
- `app/api/` — REST 路由模块（auth、knowledge、profile、study、exam、chat、admin、ability、task、daily_task、daily_learning、ppt_generator、recommendation、learning）
- `app/agents/` — 基于 LangGraph 的多智能体系统：`profile_agent`、`path_agent`、`assessment_agent`、`review_agent`、`resource_agent`、`behavior_agent`、`profile_update_agent`；通过 `graph.py` 编排，共享 `state.py` 状态
- `app/services/` — 业务逻辑：`llm.py`、`rag.py`、`tts.py`（Edge TTS）、`did.py`（D-ID 数字人）、`pptx_generator.py`、`manim_renderer.py`、`recommendation_engine.py`、`web_crawler.py`、`learning_mode_service.py`、`learning_record_service.py`、`ability_service.py`、`cache_service.py`、`task_service.py`、`user_profile.py`
- `app/models/` — SQLAlchemy ORM 模型：`User`、`KnowledgeNode`、`LearningProgress`、`StudySession`、`ExamResult`、`ChatSession`/`ChatMessage`、`KnowledgeDocument`、`ExternalResource`、`UserAbility`、`UserTaskRecord`、`WrongQuestion`、`DailyTask`、`LearningEvent`、`LearningPlan` 等
- `app/db/session.py` — 异步引擎、会话工厂、Redis 客户端、初始化/种子数据逻辑

### 前端（`struct-quest-frontend/src/`）

**入口：** [`main.js`](learn/learn/learn/struct-quest-frontend/src/main.js) — 创建 Vue 应用 → 安装 Pinia、Router、Element Plus（含全部图标），挂载到 `#app`，然后后台同步服务器认证状态。

**核心模式：**
- Pinia 状态存储在 `store/`：`session`（认证和引导状态）、`learning`、`task`、`chat`、`persona`、`ability`、`theme`
- `session` store 将引导状态和学习模式持久化到 `localStorage` 作为降级方案；`syncFromServer()` 在页面加载时恢复认证状态（8 秒超时）
- `router/index.js` 路由守卫强制流程：登录 → 新手引导（新用户）→ 模式选择 → 主应用。守卫同时检查服务端状态和 `localStorage` 降级
- `utils/request.js` — Axios 实例，401 时通过拦截器调用 `router.push('/login')`（router 通过 `main.js` 的 `initRequestRouter()` 注入）
- API 模块在 `api/` 目录：镜像后端 REST 端点（`auth.js`、`knowledge.js`、`learning.js`、`exam.js`、`profile.js`、`study.js`、`admin.js`、`dailyLearning.js`、`dailyTask.js`）
- `learningWs.js` — WebSocket 客户端，用于实时聊天和 TTS；监听 `chunk`、`done`、`tts_audio`、`tts_start`、`tts_error`、`did_video` 消息类型

**视图页面：** Login（登录）、Onboarding（用户画像设置）、ModeChoice（学习模式选择）、Dashboard（仪表盘）、Map（知识图谱可视化）、Quest（知识点探索）、NodeLearning（单节点学习页，含 AI 对话）、ChapterExam（章节考试）、Chat（聊天）、Review（复习）、Analysis（分析）、KnowledgeBase（知识库）、Profile（个人中心）、Admin（管理后台）、DailyPractice（每日练习）

**核心依赖：** Vue 3（Composition API、`<script setup>`）、Pinia、Vue Router 5、Element Plus、ECharts + vue-echarts、marked + highlight.js（Markdown 渲染）、DOMPurify、pixi.js + pixi-live2d-display（Live2D 数字人）

### Vite 开发代理

[`vite.config.js`](learn/learn/learn/struct-quest-frontend/vite.config.js) 代理配置：
- `/api` → `http://localhost:8008`
- `/ws` → `http://localhost:8008`（WebSocket）
- `/static` → `http://localhost:8008`

别名 `@` → `src/`。Vue 解析为 `vue/dist/vue.esm-bundler.js` 以支持运行时模板编译。

### 环境变量（位于 `learn/learn/learn/.env` 和 `struct-quest-backend/.env`）

- `OPENAI_API_KEY` / `OPENAI_BASE_URL` — LLM 服务商（当前使用 DeepSeek API）
- `ANTHROPIC_API_KEY` — 可选的备用 LLM 服务商，用于故障切换
- `DID_API_KEY` — D-ID 数字人视频生成（可选；未配置时降级为 Edge TTS）
- `EMBEDDING_API_KEY` / `EMBEDDING_BASE_URL` / `EMBEDDING_MODEL` — RAG 嵌入配置（默认 SiliconFlow `BAAI/bge-large-zh-v1.5`）
- `DATABASE_URL` — 默认 SQLite；MySQL 使用 `mysql+aiomysql://...` 格式
- `REDIS_URL` — 可选的 Redis 缓存
- `CHROMA_DB_PATH`、`RAG_CHUNK_SIZE`、`RAG_CHUNK_OVERLAP` — RAG 配置项

### 数字人老师 / TTS 系统

两种模式，可在 AI 陪伴面板中切换：
1. **Edge TTS**（默认，免费）：通过 `edge-tts` Python 库使用微软 Edge TTS → WebSocket 传输 base64 MP3 → 浏览器播放
2. **D-ID**（付费）：生成真人数字人说话视频。基于内容哈希缓存（相同文本 + 相同音色 = 磁盘缓存命中，不计费）。使用指南见 [`DID_GUIDE.md`](learn/learn/learn/DID_GUIDE.md) 和 [`DIGITAL_TEACHER_README.md`](learn/learn/learn/DIGITAL_TEACHER_README.md)

## 已知问题与解决方案

### Manim 视频渲染失败

**环境背景：** Manim 通过系统 conda（`/d/Program/anaconda3/Scripts/manim`）安装，版本 **0.20.1**。项目 venv 中未安装 manim，LLM prompt 中原本引用 v0.18.x 语法，与实例版本不匹配。

#### 错误 1：`ValueError: media_width must be str or falsy value`

- **原因：** Manim 0.20+ 要求 `config.media_width` 和 `config.media_height` 必须是**字符串**（如 `"1920"`），而代码中多处传入了整数 `1920`。
- **涉及位置（3 处）：**
  - [`manim_renderer.py` L60-61](learn/learn/learn/struct-quest-backend/app/services/manim_renderer.py#L60-L61) — `MANIM_HEADER` 模板
  - [`learning.py` L796-797](learn/learn/learn/struct-quest-backend/app/api/learning.py#L796-L797) — `MANIM_HEADER_PREFIX`
  - LLM 生成的代码中也可能自行设置（整数）config 值
- **修复：** 将所有 `config.media_width = 1920` 改为 `= "1920"`，`config.media_height` 同理。

#### 错误 2：渲染完成但未找到输出视频（HTTP 500）

- **原因：** 此错误意味着 Manim 进程退出码为 0，但 `rglob("*.mp4")` 未搜到文件。可能原因：
  1. **LLM 代码绕过 header：** 当 LLM 生成的代码带有 `from manim import *` 时，旧逻辑直接跳过 `MANIM_HEADER`（含安全配置），LLM 代码可能用整数设置了 config 导致 Manim 静默失败。
  2. **partial_movie_files 干扰：** 搜索到的 MP4 中包含 `partial_movie_files/` 下的中间文件，旧代码取最新文件时可能拿到不完整的片段。
  3. **Manim 0.20.1 输出结构：** 文件位于 `<media_dir>/videos/<script>/480p30/<Scene>.mp4`，需要确保搜索根路径正确。
- **修复（[`manim_renderer.py`](learn/learn/learn/struct-quest-backend/app/services/manim_renderer.py)）：**
  - **始终注入安全配置**：无论 LLM 代码是否包含 import，都在第一个 `import manim` 行后注入 `config_patch`（含字符串类型的 media_width/height）。
  - **过滤 partial 文件**：优先选择不含 `partial_movie_files` 的完整视频；仅当无完整视频时才回退到 partial 文件。
  - **增强搜索诊断**：记录所有搜索目录的存在性和内容，搜索失败时在 error 消息中附带 stdout/stderr 尾部。
  - **新增搜索位置**：将 `self.output_dir`（static/videos 根目录）也加入搜索列表。
  - **更新 LLM Prompt**：在 3 个文件中（[`manim_renderer.py`](learn/learn/learn/struct-quest-backend/app/services/manim_renderer.py)、[`learning.py`](learn/learn/learn/struct-quest-backend/app/api/learning.py)、[`resource_agent.py`](learn/learn/learn/struct-quest-backend/app/agents/resource_agent.py)）明确告知 LLM **不要设置** `config.media_width` / `config.media_height`，由系统自动注入。

#### 排查步骤（若仍失败）

1. 查看后端控制台日志，搜索 `🎬 开始渲染` / `🎬 在.*找到` / `⚠️ 未找到MP4` 等关键字。
2. 确认 manim 可执行：`manim --version`（应在系统 PATH 中，conda 环境）。
3. 确认输出目录存在：检查 `D:\app\static\videos\` 下是否有渲染产物。
4. 手动测试：用 [`manim_renderer.py`](learn/learn/learn/struct-quest-backend/app/services/manim_renderer.py) 中 `MANIM_HEADER` + 简单 Scene 代码，执行 `manim -ql --media_dir <路径> test.py SceneName`。

### PPT 智能生成器：大纲不跟随思维导图 + 结构太简单

**背景：** PPT 生成有两个入口：
1. ~~`resource_agent.py` 直接生成~~（已删除）—— 学习资源包中直接调 LLM 生成 PPT，不走思维导图
2. **PPT 智能生成器（三阶段流程）**（保留）—— 前端 `PPTGenerator` 组件 → `/api/ppt/parse-mindmap` → `MindmapExtractor` 解析 → LLM 生成大纲 → `/api/ppt/render` 渲染

#### 错误 1：思维导图层级全部丢失（解析器 Bug）

- **现象：** AI 生成的思维导图（`#` / `##` / `###` 标题层级）传入 PPT 生成器后，生成的 PPT 完全不跟随思维导图结构，内容无关。
- **原因：** [`mindmap_extractor.py`](learn/learn/learn/struct-quest-backend/app/services/mindmap_extractor.py) 的 `_parse_markmap()` 用**空格缩进**而非 `#` 数量判断层级。AI 生成的标题都在行首（缩进为 0），全部被当作平级节点，树结构完全丢失。
- **修复（3 处）：**
  - `_parse_markmap()`：重写为自动检测 `#` 标题格式，按 `#` 数量 = 层级深度，`-` 列表项作为叶子节点挂在最近的标题下。
  - `_parse_existing_mindmap()`：修复 markdown 字符串被 `json.loads()` 成功解析后，整个文本变成一个节点名的 bug。增加类型检查，字符串结果回退到 markdown 解析。
  - 压缩算法：`max_depth` 4→6，`max_chars` 4000→8000，节点名限制放宽，输出改为 Markdown `#` 格式（LLM 更易理解）。

#### 错误 2：LLM 从未被真正调用（`chat_completion` 方法缺失）

- **现象：** PPT 内容与思维导图完全无关，都是「核心内容N」式占位符。
- **原因：** [`mindmap_extractor.py`](learn/learn/learn/struct-quest-backend/app/services/mindmap_extractor.py) 的 `_call_llm_generate_outline()` 调用 `self.llm_service.chat_completion(...)`，但 [`llm.py`](learn/learn/learn/struct-quest-backend/app/services/llm.py) 的 `LLMService` **根本没有** `chat_completion` 方法——它只有流式 `chat_with_failover()`。每次调用抛 `AttributeError`，静默降级到 fallback，fallback 用空字符串生成无关内容。
- **修复（2 处）：**
  - [`llm.py`](learn/learn/learn/struct-quest-backend/app/services/llm.py)：新增 `chat_completion()` 异步方法，内部调用 `chat_with_failover()` 收集全部 chunk 后返回完整文本。
  - [`mindmap_extractor.py`](learn/learn/learn/struct-quest-backend/app/services/mindmap_extractor.py)：`get_mindmap_extractor()` 单例改为每次调用时更新 `llm_service`（防止首次创建时 service 为 None 的僵死状态）。
  - 异常处理链路改进：LLM 失败时优先用已解析的树结构做规则引擎 fallback，而非丢弃树直接降级到纯文本 fallback。

#### 错误 3：启动失败 `NameError: name 'Any' is not defined`

- **现象：** `uvicorn` 启动后端时崩溃，`import app.main` 失败。
- **原因：** [`llm.py`](learn/learn/learn/struct-quest-backend/app/services/llm.py) 新增的 `chat_completion()` 返回类型标注用了 `Dict[str, Any]`，但文件头部 `from typing import ...` 未导入 `Any`。
- **修复：** 在 `llm.py` 第 5 行 `typing` 导入中加入 `Any`：
  ```python
  from typing import Any, AsyncGenerator, Optional, List, Dict, Tuple
  ```

#### 错误 4：Step3Render.vue `computed is not defined`

- **现象：** 前端生成 PPT 第三步时白屏，控制台报 `ReferenceError: computed is not defined`。
- **原因：** [`Step3Render.vue`](learn/learn/learn/struct-quest-frontend/src/components/PPTGenerator/Step3Render.vue) 的 `<script setup>` 中使用了 `computed()` 但未从 Vue 导入。
- **修复：** 在 `<script setup>` 顶部添加 `import { computed } from 'vue'`。

#### PPT 生成器架构总结

```
用户思维导图 (#/##/### Markdown)
  → PPTGenerator (前端三阶段弹窗)
    → POST /api/ppt/parse-mindmap  (MindmapExtractor 解析 → LLM 生成大纲JSON)
    → 用户编辑大纲 (Step2Editor)
    → POST /api/ppt/render          (HTML/PPTX 渲染)
  → 下载/预览 PPT
```

**LLM Prompt 优化要点（[`mindmap_extractor.py`](learn/learn/learn/struct-quest-backend/app/services/mindmap_extractor.py)）：**
- 思维导图 `##` 一级分支 → PPT section 或 content 页标题
- 思维导图 `###` 二级分支 → content 页标题，其下 `-` 列表项展开为 bullet_points（40-120 字）
- 强制 layout 多样化：10 种类型（title/section/content/summary/chart/comparison/timeline/quote/two_column/cards_grid），相邻页禁止同 layout
- 禁止编造思维导图中不存在的主题
