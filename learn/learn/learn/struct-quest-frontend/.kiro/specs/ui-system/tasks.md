# Implementation Plan

## Phase 1: 基础架构与公共组件

- [-] 1. 建立项目基础架构



  - 创建 types 目录，定义核心 TypeScript 类型（User, LearningNode, ChatMessage 等）
  - 创建 utils 目录，实现 request.js（Axios 封装）、storage.js（本地存储工具）
  - 创建 composables 目录，实现 useTheme.js（主题切换）、useAuth.js（认证逻辑）
  - 配置 vitest 测试框架
  - _Requirements: 11.1, 11.2, 11.6, 11.7_

- [x] 1.1 实现主题系统


  - 创建 src/assets/styles/variables.scss 定义 CSS 变量（浅色/深色主题）
  - 创建 src/assets/styles/themes.scss 实现主题切换样式
  - 实现 useTheme composable 支持主题切换和持久化
  - 在 App.vue 中集成主题系统
  - _Requirements: 10.1, 10.3, 10.4_

- [ ]* 1.2 编写主题系统属性测试
  - **Property 1: 主题切换一致性**
  - **Validates: Requirements 10.1**

- [x] 1.3 创建公共组件 - 布局类


  - 实现 AppHeader.vue 顶部导航栏组件（Logo、搜索、主题切换、用户菜单）
  - 实现 AppSidebar.vue 左侧菜单栏组件（折叠/展开、菜单项、徽章）
  - 实现 Breadcrumb.vue 面包屑导航组件
  - 实现 MainLayout.vue 主布局组件整合以上组件
  - _Requirements: 9.1, 9.2, 9.3_

- [x] 1.4 创建公共组件 - 展示类


  - 实现 Card.vue 卡片组件（支持 title、shadow、borderRadius、loading、hoverable 属性）
  - 实现 Tag.vue 标签组件（支持不同类型和颜色）
  - 实现 Progress.vue 学习进度组件
  - 实现 Skeleton.vue 骨架屏组件（支持 text、card、list、image 变体）
  - _Requirements: 9.4, 9.5, 9.7, 9.8_

- [ ]* 1.5 编写卡片组件属性测试
  - **Property 1: 卡片圆角范围**
  - **Validates: Requirements 9.4**

- [x] 1.6 创建公共组件 - 交互类


  - 实现 Modal.vue 弹窗组件（确认对话框、信息提示）
  - 实现 AIStatus.vue AI 状态组件（thinking、analyzing、recommending、idle 状态）
  - 实现 StreamMessage.vue 流式消息组件（Markdown 渲染、代码高亮、打字机效果）
  - _Requirements: 9.6, 9.9, 9.10_

- [ ]* 1.7 编写 AI 状态组件属性测试
  - **Property 1: AI 状态类型覆盖**
  - **Validates: Requirements 9.6**

- [ ] 1.8 实现全局状态管理



  - 创建 store/theme.js 主题状态管理
  - 创建 store/learning.js 学习进度状态管理
  - 创建 store/chat.js 聊天状态管理
  - 更新现有 store/session.js 和 store/persona.js
  - _Requirements: 11.2_

## Phase 2: 认证与用户系统

- [ ] 2. 实现登录页面
  - 更新 src/views/Login/index.vue 实现左右分栏布局
  - 实现左侧品牌介绍区（Logo、系统简介、核心亮点、背景装饰）
  - 实现右侧登录表单区（学号/邮箱输入、密码输入、记住我、忘记密码、游客登录、注册链接）
  - 实现表单验证逻辑（必填项、邮箱格式、密码长度）
  - 实现登录加载状态和成功/失败反馈
  - _Requirements: 1.1, 1.2, 1.3, 1.6, 1.7, 1.8, 1.9_

- [ ]* 2.1 编写表单验证属性测试
  - **Property 1: 表单验证完整性**
  - **Validates: Requirements 1.2**

- [ ] 2.2 实现登录流程逻辑
  - 在 useAuth composable 中实现登录逻辑
  - 实现登录成功后根据人格测试状态跳转（已完成→Dashboard，未完成→Onboarding）
  - 实现游客登录逻辑
  - 实现记住我功能（localStorage 持久化）
  - _Requirements: 1.4, 1.5, 1.6, 1.7_

- [ ] 2.3 实现注册页面
  - 创建 src/views/Register/index.vue 注册页面
  - 实现注册表单（学号、邮箱、密码、确认密码）
  - 实现注册验证和提交逻辑
  - 实现注册成功后自动登录并跳转人格测试
  - _Requirements: 1.9_

- [ ] 2.4 配置路由守卫
  - 在 router/index.js 中添加路由守卫
  - 未登录用户访问受保护页面时重定向到登录页
  - 已登录未完成人格测试的用户重定向到 Onboarding
  - _Requirements: 1.4, 1.5_

## Phase 3: 学习人格测试系统

- [ ] 3. 实现学习人格测试页面
  - 更新 src/views/Onboarding/index.vue 实现完整测试流程
  - 实现测试引导页（说明测试目的和流程）
  - 实现问题展示区（卡片切换动画）
  - 实现进度条组件（实时更新进度百分比和剩余题目）
  - 实现答题逻辑和答案存储
  - _Requirements: 2.1, 2.2, 2.3, 2.6_

- [ ]* 3.1 编写问题展示属性测试
  - **Property 1: 问题卡片展示一致性**
  - **Validates: Requirements 2.2**

- [ ]* 3.2 编写进度更新属性测试
  - **Property 1: 进度条同步性**
  - **Validates: Requirements 2.3, 2.6**

- [ ] 3.3 实现测试结果生成
  - 实现测试完成后的答案分析算法
  - 生成学习人格类型和分数
  - 实现结果展示页面（人格标签卡片、类型描述、建议学习方式）
  - 更新 store/persona.js 存储人格结果
  - _Requirements: 2.4, 2.5_

## Phase 4: 首页 Dashboard

- [ ] 4. 实现首页布局
  - 更新 src/views/Dashboard/index.vue 实现三栏布局
  - 左侧导航栏（复用 AppSidebar）
  - 中间主内容区
  - 右侧辅助面板
  - _Requirements: 3.1_

- [ ] 4.1 实现欢迎区域组件
  - 根据当前时间显示问候语（早安/下午好/晚上好）
  - 显示用户名称
  - 显示今日概览信息
  - _Requirements: 3.1_

- [ ]* 4.2 编写问候语属性测试
  - **Property 1: 问候语时间正确性**
  - **Validates: Requirements 3.1**

- [ ] 4.3 实现 AI 学习建议卡片
  - 显示 AI 分析结果和个性化推荐
  - 支持查看详细报告和快速操作按钮
  - 实现骨架屏加载状态
  - _Requirements: 3.2_

- [ ] 4.4 实现今日任务列表
  - 创建任务卡片组件（任务图标、标题、建议时长、开始按钮）
  - 实现任务按优先级排序显示
  - 实现点击任务跳转学习资源页
  - _Requirements: 3.3_

- [ ]* 4.5 编写任务排序属性测试
  - **Property 1: 任务优先级排序正确性**
  - **Validates: Requirements 3.3, 5.2**

- [ ] 4.6 实现学习进度概览
  - 显示各模块完成百分比
  - 使用 Progress 组件展示进度条
  - 支持点击查看完整技能树
  - _Requirements: 3.4_

- [ ] 4.7 实现最近学习记录时间线
  - 显示最近学习活动时间线
  - 按时间倒序排列
  - 显示时间戳和事件描述
  - _Requirements: 3.5_

- [ ]* 4.8 编写时间线排序属性测试
  - **Property 1: 时间线时间倒序正确性**
  - **Validates: Requirements 3.5**

- [ ] 4.9 实现快捷操作
  - 实现"继续学习"按钮跳转上次学习页面
  - 实现任务卡片点击跳转对应资源页
  - _Requirements: 3.6, 3.7_

## Phase 5: 学习地图系统

- [ ] 5. 实现学习地图页面
  - 更新 src/views/Map/index.vue 实现全屏技能树
  - 使用 ECharts 或 D3.js 实现树形图渲染
  - 实现节点组件（圆形/方形，不同状态不同颜色）
  - 实现节点连线表示章节关系
  - _Requirements: 4.1, 4.2_

- [ ]* 5.1 编写节点连线属性测试
  - **Property 1: 节点连线完整性**
  - **Validates: Requirements 4.2**

- [ ] 5.2 实现节点状态样式
  - 已掌握节点：绿色实心
  - 学习中节点：蓝色边框
  - 推荐学习节点：紫色高亮
  - 未开始节点：灰色虚线
  - _Requirements: 4.3_

- [ ]* 5.3 编写节点状态样式属性测试
  - **Property 1: 节点状态样式区分**
  - **Validates: Requirements 4.3**

- [ ] 5.4 实现地图交互功能
  - 实现节点点击展开详情并支持跳转
  - 实现推荐学习路径高亮
  - 实现缩放和平移操作
  - _Requirements: 4.4, 4.5, 4.6_

## Phase 6: 今日任务系统

- [ ] 6. 实现今日任务页面
  - 创建 src/views/Tasks/index.vue 页面
  - 显示今日推荐学习内容列表
  - 显示每个任务的优先级、建议时间、AI 推荐原因
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ]* 6.1 编写任务信息显示属性测试
  - **Property 1: 任务信息完整性**
  - **Validates: Requirements 5.3, 5.4_

- [ ] 6.2 实现任务状态管理
  - 实现开始任务后状态更新（pending → in_progress → completed）
  - 实现任务完成状态持久化
  - _Requirements: 5.5_

- [ ] 6.3 实现专注模式
  - 实现点击"开始学习"进入专注模式或跳转资源页
  - 实现学习倒计时功能
  - 实现专注模式 UI（全屏、计时器、进度）
  - _Requirements: 5.6, 5.7_

## Phase 7: 学习资源系统

- [ ] 7. 实现学习资源页面
  - 创建 src/views/Resource/index.vue 页面
  - 以卡片形式展示学习资源列表
  - 显示资源标题、类型标签、难度等级
  - 显示 AI 推荐原因和 AI 生成标记
  - _Requirements: 6.1, 6.2, 6.3_

- [ ]* 7.1 编写资源卡片信息属性测试
  - **Property 1: 资源卡片信息完整性**
  - **Validates: Requirements 6.2, 6.3**

- [ ] 7.2 实现资源卡片交互
  - 实现展开/收起完整内容
  - 实现收藏功能
  - 实现下载功能（如适用）
  - _Requirements: 6.4, 6.5, 6.6_

- [ ] 7.3 实现 AI 资源再生成
  - 实现点击"再生成"按钮触发 AI 请求
  - 显示生成中状态
  - 更新资源内容
  - _Requirements: 6.7_

- [ ] 7.4 实现视频资源播放
  - 检测资源类型为视频/动画时内嵌播放器
  - 支持在线播放
  - _Requirements: 6.8_

- [ ]* 7.5 编写视频资源渲染属性测试
  - **Property 1: 视频资源播放器渲染**
  - **Validates: Requirements 6.8**

## Phase 8: AI 聊天系统

- [ ] 8. 实现 AI 聊天页面布局
  - 创建 src/views/Chat/index.vue 页面
  - 左侧：历史会话列表
  - 中间：聊天窗口
  - 底部：输入区域
  - _Requirements: 7.1_

- [ ] 8.1 实现消息发送与流式响应
  - 实现 useSSE composable 处理 SSE 流式响应
  - 实现消息发送逻辑
  - 使用 StreamMessage 组件渲染流式输出
  - _Requirements: 7.2_

- [ ] 8.2 实现 Markdown 和代码渲染
  - 集成 Markdown 渲染器（marked 或 markdown-it）
  - 集成代码语法高亮（highlight.js 或 prism.js）
  - 使用 StreamMessage 组件支持渲染
  - _Requirements: 7.3, 7.4_

- [ ]* 8.3 编写代码高亮属性测试
  - **Property 1: 代码块语法高亮正确性**
  - **Validates: Requirements 7.3**

- [ ]* 8.4 编写 Markdown 渲染属性测试
  - **Property 1: Markdown 渲染正确性**
  - **Validates: Requirements 7.4**

- [ ] 8.5 实现 AI 状态显示
  - 使用 AIStatus 组件显示思考中/分析中/推荐中等状态
  - 在 AI 处理过程中显示状态提示
  - _Requirements: 7.5_

- [ ] 8.6 实现文件上传功能
  - 实现上传按钮和文件选择
  - 支持 PDF 文件解析
  - 支持图片预览
  - 支持代码文件解析
  - 将上传内容作为对话上下文
  - _Requirements: 7.6, 7.7, 7.8_

- [ ] 8.7 实现会话管理
  - 实现历史会话列表展示
  - 实现切换会话加载聊天记录
  - 实现新建会话功能
  - _Requirements: 7.9_

## Phase 9: 学习分析系统

- [ ] 9. 实现学习分析页面
  - 创建 src/views/Analysis/index.vue 页面
  - 使用 ECharts 实现各类图表
  - _Requirements: 8.1, 8.2, 8.3, 8.6_

- [ ] 9.1 实现学习时长统计图表
  - 使用 ECharts 柱状图或折线图展示学习时长
  - 支持按日/周/月查看
  - _Requirements: 8.1_

- [ ] 9.2 实现知识掌握度雷达图
  - 使用 ECharts 雷达图展示各知识点掌握度
  - 显示各维度分数
  - _Requirements: 8.2_

- [ ] 9.3 实现学习热力图
  - 使用 ECharts 热力图展示学习活动分布
  - 类似 GitHub 贡献图样式
  - _Requirements: 8.3_

- [ ] 9.4 实现弱项分析列表
  - 显示薄弱知识点列表
  - 显示分数和改进建议
  - _Requirements: 8.4_

- [ ] 9.5 实现 AI 学习总结报告
  - 显示 AI 生成的学习总结
  - 显示个性化学习建议
  - _Requirements: 8.5, 8.7_

## Phase 10: 集成与优化

- [ ] 10. 检查点 - 确保所有测试通过
  - 运行所有单元测试和属性测试
  - 修复失败的测试
  - 如有问题请询问用户

- [ ] 10.1 实现路由集成
  - 配置所有页面路由
  - 实现路由懒加载
  - 实现路由过渡动画
  - _Requirements: 11.3_

- [ ] 10.2 实现响应式布局适配
  - 适配桌面端（1440px+）
  - 适配平板端（768px-1439px）
  - 适配移动端（< 768px）

- [ ] 10.3 性能优化
  - 实现组件懒加载
  - 优化图片资源
  - 配置 Vite 打包优化

- [ ] 10.4 最终检查点 - 确保所有测试通过
  - 运行完整测试套件
  - 确认所有功能正常
  - 如有问题请询问用户
