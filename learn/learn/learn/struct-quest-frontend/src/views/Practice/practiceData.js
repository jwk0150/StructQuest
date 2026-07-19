/**
 * AI 智能练习中心 — 静态元数据 & 章节配置
 * 设计原则：API 优先 → 数据降级 → 默认推荐
 */

/** 6 个练习模式（一级大厅入口） */
export const PRACTICE_MODES = [
  {
    key: 'exam',
    icon: '📖',
    title: '考研模式',
    desc: '408 真题 / 章节练习 / 顺序 / 错题 / 收藏',
    stats: { count: 8, unit: '章' },
    gradient: 'purple',
    route: '/app/practice/exam',
    color: '#d97982',
  },
  {
    key: 'coding',
    icon: '💻',
    title: '编程模式',
    desc: 'LeetCode 风格在线评测 + AI 代码分析',
    stats: { count: 6, unit: '类' },
    gradient: 'blue',
    route: '/app/practice/coding',
    color: '#b94b5a',
  },
  {
    key: 'random',
    icon: '🧠',
    title: 'AI 随机练习',
    desc: 'AI 根据学习画像个性化生成题目',
    stats: { count: 8, unit: '题' },
    gradient: 'pink',
    route: '/app/practice/random',
    color: '#ec4899',
  },
  {
    key: 'wrong',
    icon: '❌',
    title: '错题重练',
    desc: '智能错题本 + 间隔重复算法，精准攻克薄弱点',
    stats: { count: 0, unit: '题', dynamic: true },
    gradient: 'orange',
    route: '/app/practice/wrong',
    color: '#f97316',
  },
  {
    key: 'daily',
    icon: '🏆',
    title: '每日挑战',
    desc: '排行榜 + 勋章 + 连续签到打卡',
    stats: { count: 18, unit: '天' },
    gradient: 'gold',
    route: '/app/practice/daily',
    color: '#f59e0b',
  },
  {
    key: 'mock',
    icon: '📊',
    title: 'AI 模拟考试',
    desc: '智能组卷 + AI 自动评分 + 学习报告',
    stats: { count: 15, unit: '题' },
    gradient: 'teal',
    route: '/app/practice/mock',
    color: '#14b8a6',
  },
]

/** 考研模式 — 章节数据（nodeId 对应后端 KnowledgeNode.id，兼容 /knowledge/map 结果） */
export const CHAPTERS = [
  { id: 'ch1',  name: '顺序表',   nodeId: 'ch02_seq_list',     icon: '📋' },
  { id: 'ch2',  name: '链表',     nodeId: 'ch02_linked_list',  icon: '🔗' },
  { id: 'ch3',  name: '栈',       nodeId: 'ch03_stack_basic',  icon: '📚' },
  { id: 'ch4',  name: '队列',     nodeId: 'ch03_queue_basic',  icon: '🚶' },
  { id: 'ch5',  name: '树',       nodeId: 'ch05_tree_basic',   icon: '🌳' },
  { id: 'ch6',  name: '图',       nodeId: 'ch06_graph_concept',icon: '🕸️' },
  { id: 'ch7',  name: '排序',     nodeId: 'ch08_quick_sort',   icon: '🔢' },
  { id: 'ch8',  name: '查找',     nodeId: 'ch07_binary_search',icon: '🔍' },
]

/** 编程模式 — 分类 */
export const CODING_CATEGORIES = [
  { key: 'basics',    label: '基础算法',   icon: '🧮', nodeId: 'ch01_algorithm' },
  { key: 'linked',    label: '链表',       icon: '🔗', nodeId: 'ch02_linked_list' },
  { key: 'tree',      label: '树',         icon: '🌳', nodeId: 'ch05_tree_basic' },
  { key: 'graph',     label: '图',         icon: '🕸️', nodeId: 'ch06_graph_concept' },
  { key: 'sort',      label: '排序',       icon: '🔢', nodeId: 'ch08_quick_sort' },
  { key: 'search',    label: '搜索',       icon: '🔍', nodeId: 'ch07_binary_search' },
  { key: 'dp',        label: '动态规划',   icon: '🧩', nodeId: 'ch06_shortest_path' },
]

/** 挑战地图 — 节点 */
export const MAP_STAGES = [
  { id: 1, name: '基础',    status: 'mastered',   score: 5 },
  { id: 2, name: '链表',    status: 'mastered',   score: 5 },
  { id: 3, name: '栈',      status: 'mastered',   score: 4 },
  { id: 4, name: '树',      status: 'learning',   score: 3 },
  { id: 5, name: '图',      status: 'not_started', score: 0 },
  { id: 6, name: '排序',    status: 'not_started', score: 0 },
  { id: 7, name: '查找',    status: 'not_started', score: 0 },
  { id: 8, name: '最短路径', status: 'locked',     score: 0 },
]

/** 默认 AI 推荐（新用户降级） */
export const DEFAULT_RECOMMEND = {
  nodeName: '树结构',
  nodeId: 'ch05_tree_basic',
  stars: 5,
  duration: 20,
  reason: '树结构是考研高频考点，也是后续图和排序算法的基础，建议优先掌握。',
}

/** 推荐原因模板 */
export function generateReason(nodeName, mistakeCount, daysAgo, lastNode) {
  if (mistakeCount >= 4) {
    return `${nodeName} 已连续错 ${mistakeCount} 次，建议针对性强化练习。`
  }
  if (mistakeCount >= 2) {
    return `最近 ${nodeName} 错误 ${mistakeCount} 次，趁热打铁巩固一下。`
  }
  if (daysAgo >= 3) {
    return `距离上次练习${nodeName}已过去 ${daysAgo} 天，及时复习防止遗忘。`
  }
  if (lastNode) {
    return `刚学完${lastNode}，${nodeName}是自然的下一步，趁热打铁效率最高。`
  }
  return `${nodeName}是数据结构核心模块，建议优先攻克。`
}

/** 每日挑战 — 模拟挑战数据 */
export const DAILY_CHALLENGE = {
  topic: 'DFS 深度优先搜索',
  stars: 5,
  rank: '前 10%',
  reward: { exp: 100, badge: '🏅 坚持之星' },
  streak: 18,
}

/** AI 随机练习 — 生成预览 */
export const RANDOM_PREVIEW = {
  choices: 4,
  blanks: 2,
  coding: 2,
  duration: 18,
}

/** 模拟考试 — 预设 */
export const MOCK_EXAM_PRESET = {
  title: '408 数据结构模拟卷',
  duration: 45,
  questions: 15,
  features: ['AI 自动组卷', 'AI 自动评分', 'AI 学习报告'],
}


