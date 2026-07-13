# Requirements Document

## Introduction

StructQuest 是一个面向大学《数据结构》课程的 AI 个性化学习辅助平台。本项目旨在设计并实现完整的前端 UI 系统，采用类似 ChatGPT 的现代 AI 产品风格，强调简洁、高级感、交互流畅和专业学习氛围。系统融合学习画像、动态学习路径、多智能体协同和智能资源生成，帮助学生实现个性化学习体验。

## Glossary

- **StructQuest**: 本项目名称，面向数据结构课程的 AI 个性化学习平台
- **学习人格**: 基于 MBTI 式测试得出的学生学习风格画像
- **学习地图**: 以技能树结构展示的数据结构课程知识图谱
- **AI 伙伴**: 系统中的多智能体协同助手，提供学习建议和资源推荐
- **费曼学习法**: 一种通过向他人解释概念来加深理解的学习方法
- **学习画像**: 根据用户学习行为和偏好构建的用户模型
- **技能树**: 以节点和连线形式展示的课程知识结构图
- **流式输出**: AI 响应以逐字符或逐块方式渐进显示
- **SSE (Server-Sent Events)**: 服务器推送事件技术，用于实现流式响应
- **学习热力图**: 以热力图形式展示学习活动分布的可视化图表

## Requirements

### Requirement 1

**User Story:** 作为学生用户，我希望通过登录页面安全进入系统，以便开始我的个性化学习之旅。

#### Acceptance Criteria

1. WHEN 用户访问系统 THEN 系统 SHALL 展示左右分栏式登录页面，左侧为品牌介绍区，右侧为登录表单区
2. WHEN 用户输入学号/邮箱和密码 THEN 系统 SHALL 验证输入格式并提示错误信息
3. WHEN 用户点击登录按钮 THEN 系统 SHALL 执行身份验证并显示加载状态
4. WHEN 身份验证成功 AND 用户已完成学习人格测试 THEN 系统 SHALL 跳转至首页 Dashboard
5. WHEN 身份验证成功 AND 用户未完成学习人格测试 THEN 系统 SHALL 跳转至学习人格测试页
6. WHEN 用户点击游客体验 THEN 系统 SHALL 以游客身份进入系统并跳转至学习人格测试页
7. WHEN 用户勾选"记住我"选项 THEN 系统 SHALL 在本地存储登录状态
8. WHEN 用户点击"忘记密码"链接 THEN 系统 SHALL 展示密码找回流程入口
9. WHEN 用户点击"立即注册"链接 THEN 系统 SHALL 展示注册表单

### Requirement 2

**User Story:** 作为新用户，我希望通过学习人格测试了解自己的学习风格，以便获得个性化的学习建议。

#### Acceptance Criteria

1. WHEN 用户进入学习人格测试页 THEN 系统 SHALL 展示测试引导页，说明测试目的和流程
2. WHEN 测试开始 THEN 系统 SHALL 以卡片切换方式逐题展示问题
3. WHEN 用户回答问题 THEN 系统 SHALL 实时更新进度条显示答题进度
4. WHEN 用户完成所有问题 THEN 系统 SHALL 分析答案并生成学习人格标签卡片
5. WHEN 系统生成学习人格结果 THEN 系统 SHALL 展示人格类型描述和建议学习方式
6. WHILE 测试进行中 THEN 系统 SHALL 显示当前进度百分比和剩余题目数量

### Requirement 3

**User Story:** 作为已登录用户，我希望在首页看到个性化的学习概览，以便快速了解今日学习重点。

#### Acceptance Criteria

1. WHEN 用户进入首页 THEN 系统 SHALL 展示欢迎区域，包含用户名称和时间相关的问候语
2. WHEN 首页加载完成 THEN 系统 SHALL 展示 AI 学习建议卡片，包含个性化分析和推荐
3. WHEN 首页加载完成 THEN 系统 SHALL 展示今日学习任务列表，按优先级排序
4. WHEN 首页加载完成 THEN 系统 SHALL 展示学习进度概览，显示各模块完成百分比
5. WHEN 首页加载完成 THEN 系统 SHALL 展示最近学习记录时间线
6. WHEN 用户点击"继续学习"按钮 THEN 系统 SHALL 跳转至上次学习的资源页面
7. WHEN 用户点击任务卡片 THEN 系统 SHALL 跳转至对应的学习资源页

### Requirement 4

**User Story:** 作为学习者，我希望通过学习地图查看课程知识结构，以便了解学习路径和进度。

#### Acceptance Criteria

1. WHEN 用户进入学习地图页 THEN 系统 SHALL 以技能树结构展示数据结构课程模块
2. WHEN 学习地图渲染完成 THEN 系统 SHALL 显示节点连线表示章节关系
3. WHEN 学习地图渲染完成 THEN 系统 SHALL 通过视觉样式区分已掌握、学习中、推荐学习、未开始四种节点状态
4. WHEN 用户点击任意节点 THEN 系统 SHALL 展示节点详情并支持跳转至学习资源页
5. WHEN 用户查看学习地图 THEN 系统 SHALL 高亮显示当前推荐学习路径
6. WHILE 用户浏览学习地图 THEN 系统 SHALL 支持缩放和平移操作

### Requirement 5

**User Story:** 作为学习者，我希望查看今日推荐的学习任务，以便有计划地进行学习。

#### Acceptance Criteria

1. WHEN 用户进入今日学习任务页 THEN 系统 SHALL 展示今日推荐学习内容列表
2. WHEN 任务列表加载完成 THEN 系统 SHALL 显示每个任务的优先级排序
3. WHEN 任务列表加载完成 THEN 系统 SHALL 显示每个任务的建议学习时间
4. WHEN 任务列表加载完成 THEN 系统 SHALL 显示 AI 推荐原因
5. WHEN 用户开始任务 THEN 系统 SHALL 更新任务完成状态
6. WHEN 用户点击"开始学习"按钮 THEN 系统 SHALL 进入专注模式或跳转至学习资源页
7. WHILE 任务进行中 THEN 系统 SHALL 提供学习倒计时功能

### Requirement 6

**User Story:** 作为学习者，我希望在学习资源页查看多种类型的学习材料，以便全面理解知识点。

#### Acceptance Criteria

1. WHEN 用户进入学习资源页 THEN 系统 SHALL 以卡片形式展示学习资源列表
2. WHEN 资源卡片渲染完成 THEN 系统 SHALL 显示资源标题、类型标签、难度等级
3. WHEN 资源卡片渲染完成 THEN 系统 SHALL 显示 AI 推荐原因和 AI 生成标记（如适用）
4. WHEN 用户展开资源卡片 THEN 系统 SHALL 显示完整的学习内容
5. WHEN 用户点击收藏按钮 THEN 系统 SHALL 将资源添加至个人收藏
6. WHEN 用户点击下载按钮 THEN 系统 SHALL 下载资源文件（如适用）
7. WHEN 用户点击"再生成"按钮 THEN 系统 SHALL 请求 AI 重新生成该资源
8. WHERE 资源类型为视频/动画 THEN 系统 SHALL 内嵌播放器支持在线播放

### Requirement 7

**User Story:** 作为学习者，我希望通过 AI 聊天页面与 AI 伙伴互动，以便获得答疑和学习指导。

#### Acceptance Criteria

1. WHEN 用户进入 AI 聊天页 THEN 系统 SHALL 展示左侧历史会话列表、中间聊天窗口、底部输入区域
2. WHEN 用户发送消息 THEN 系统 SHALL 以流式输出方式显示 AI 响应
3. WHEN AI 响应包含代码 THEN 系统 SHALL 应用语法高亮显示
4. WHEN AI 响应包含 Markdown THEN 系统 SHALL 正确渲染 Markdown 格式
5. WHILE AI 处理中 THEN 系统 SHALL 显示思考中/分析中/推荐中等状态提示
6. WHEN 用户上传 PDF 文件 THEN 系统 SHALL 解析文件内容作为对话上下文
7. WHEN 用户上传图片 THEN 系统 SHALL 显示图片预览并作为对话上下文
8. WHEN 用户上传代码文件 THEN 系统 SHALL 解析代码作为对话上下文
9. WHEN 用户切换历史会话 THEN 系统 SHALL 加载对应会话的完整聊天记录

### Requirement 8

**User Story:** 作为学习者，我希望在学习分析页查看我的学习数据，以便了解学习效果和改进方向。

#### Acceptance Criteria

1. WHEN 用户进入学习分析页 THEN 系统 SHALL 展示学习时长统计图表
2. WHEN 学习分析页加载完成 THEN 系统 SHALL 展示知识掌握度雷达图
3. WHEN 学习分析页加载完成 THEN 系统 SHALL 展示学习热力图
4. WHEN 学习分析页加载完成 THEN 系统 SHALL 展示弱项分析列表
5. WHEN 学习分析页加载完成 THEN 系统 SHALL 展示 AI 生成的学习总结报告
6. WHEN 学习分析页加载完成 THEN 系统 SHALL 展示学习趋势折线图
7. WHEN 学习分析页加载完成 THEN 系统 SHALL 展示个性化学习建议

### Requirement 9

**User Story:** 作为系统用户，我希望系统提供统一的公共组件，以便获得一致的交互体验。

#### Acceptance Criteria

1. WHEN 页面需要导航 THEN 系统 SHALL 提供统一的顶部导航栏组件
2. WHEN 页面需要侧边导航 THEN 系统 SHALL 提供统一的左侧菜单栏组件
3. WHEN 页面需要路径指示 THEN 系统 SHALL 提供面包屑导航组件
4. WHEN 页面需要展示信息块 THEN 系统 SHALL 提供统一样式的卡片组件，支持圆角（12px~20px）和柔和阴影
5. WHEN 页面需要分类标记 THEN 系统 SHALL 提供标签组件
6. WHEN 页面需要显示 AI 状态 THEN 系统 SHALL 提供 AI 状态组件，显示思考中/分析中/推荐中等状态
7. WHEN 页面需要展示学习进度 THEN 系统 SHALL 提供学习进度组件
8. WHEN 内容加载中 THEN 系统 SHALL 显示骨架屏组件
9. WHEN 需要用户确认操作 THEN 系统 SHALL 提供弹窗组件
10. WHEN AI 响应流式输出 THEN 系统 SHALL 提供流式消息组件

### Requirement 10

**User Story:** 作为系统用户，我希望系统支持深色模式，以便在不同光线环境下舒适使用。

#### Acceptance Criteria

1. WHEN 用户切换深色模式 THEN 系统 SHALL 立即应用深色主题样式
2. WHILE 深色模式启用 THEN 系统 SHALL 保持所有页面的可读性和视觉一致性
3. WHEN 用户重新登录 THEN 系统 SHALL 记住用户上次选择的主题模式
4. WHEN 系统检测到系统级深色模式设置 THEN 系统 SHALL 提供自动跟随选项

### Requirement 11

**User Story:** 作为开发者，我希望前端系统采用模块化架构，以便于维护和扩展。

#### Acceptance Criteria

1. WHEN 开发新功能 THEN 系统 SHALL 采用 Vue3 Composition API 编写组件
2. WHEN 管理应用状态 THEN 系统 SHALL 使用 Pinia 进行状态管理
3. WHEN 实现页面路由 THEN 系统 SHALL 使用 Vue Router 管理路由
4. WHEN 构建 UI 组件 THEN 系统 SHALL 使用 Element Plus 组件库
5. WHEN 需要数据可视化 THEN 系统 SHALL 使用 ECharts 库
6. WHEN 与后端通信 THEN 系统 SHALL 使用 Axios 进行 HTTP 请求
7. WHEN 需要 AI 流式响应 THEN 系统 SHALL 使用 SSE 技术实现
