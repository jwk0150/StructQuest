// ══════════════════════════════════════════════════════
//  三种模式知识图谱差异化配置（适配《数据结构》8章体系）
// ══════════════════════════════════════════════════════

import { stages } from './knowledgeMap'

export const modeConfigs = {
  // ──────────────────────────────────
  // 🌱 基础模式 —— 零基础初学者
  // ──────────────────────────────────
  basic: {
    id: 'basic',
    label: '基础模式',
    icon: '🌱',
    subtitle: '轻松入门 · 激发兴趣',
    description: '从零开始，用生活化的语言理解数据结构的核心概念',
    // 基础模式展示全部8个章节，但只取每个章节最基础的2-3个节点
    includedCategories: ['ch01_intro', 'ch02_linear_list', 'ch03_stack_queue', 'ch04_string_array', 'ch05_tree', 'ch06_graph', 'ch07_search', 'ch08_sort'],
    includedNodeIds: [
      'ch01_data_concept', 'ch01_algorithm',     // 绪论：基本概念、算法分析
      'ch02_seq_list', 'ch02_linked_list',        // 线性表：顺序表、链表
      'ch03_stack_basic', 'ch03_queue_basic',     // 栈和队列：基本概念
      'ch04_string', 'ch04_array',                // 串数组：串、数组
      'ch05_binary_tree', 'ch05_tree_traversal',   // 树：二叉树、遍历
      'ch06_graph_concept', 'ch06_dfs', 'ch06_bfs', // 图：概念、DFS、BFS
      'ch07_seq_search', 'ch07_binary_search',     // 查找：顺序、折半
      'ch08_bubble_sort', 'ch08_quick_sort',       // 排序：冒泡、快排
    ],
    // 节点描述口语化覆盖（基础模式用生活化语言）
    nodeDescOverrides: {
      ch01_data_concept: {
        name: '数据结构初探',
        desc: '什么是数据结构？为什么学它？',
        fullDesc: '数据结构就像整理衣橱——数据是衣服，逻辑结构决定了怎么摆（按颜色/按季节），存储结构决定了放哪里（抽屉里/挂起来）。学好数据结构，你的"程序衣橱"才能井井有条！',
        points: ['什么是数据','数据和数据元素','逻辑结构 vs 存储结构','为什么要学数据结构'],
        aiSuggestion: '先理解"逻辑结构"和"存储结构"的区别，这是整门课的基石。',
      },
      ch01_algorithm: {
        name: '算法效率评价',
        desc: '怎么衡量一个程序快不快？',
        fullDesc: '算法分析就像选快递——有的今天到（O(1)），有的明天到（O(n)），有的一周才到（O(n²)）。大O记号就是告诉你这个包裹大概多久能到，不需要精确计时！',
        points: ['大O是什么','时间复杂度怎么看','空间复杂度是什么','常见复杂度排名'],
        aiSuggestion: '不用记住所有复杂度公式，先理解O(1)<O(log n)<O(n)<O(n²)的关系。',
      },
      ch02_seq_list: {
        name: '顺序表：一排抽屉',
        desc: '每个抽屉有固定编号，能直接打开',
        fullDesc: '顺序表就像一排带编号的抽屉——你说"我要3号"，直接拉开3号抽屉就行了！但如果你想在中间加一个抽屉，就得把所有后面的抽屉都挪一挪位置。',
        points: ['随机访问就像按编号找抽屉','插入/删除为什么需要移动','数组和顺序表的关系','动态扩容是什么'],
        aiSuggestion: '想象一下在排队时插队和离开的场景，就能理解顺序表的插入删除了。',
      },
      ch02_linked_list: {
        name: '链表：寻宝游戏',
        desc: '每个盒子牵着下一个盒子',
        fullDesc: '链表就像寻宝游戏——每个盒子里有宝藏和下一张线索。你得从第一个盒子开始，顺着线索一个一个找。但是插入新盒子超级容易，只要改一下线索就行了！',
        points: ['节点是什么','头指针的作用','插入不需要移动','为什么叫"链"表'],
        aiSuggestion: '画图是理解链表的最好方式，用圆圈+箭头画一个链表试试。',
      },
      ch03_stack_basic: {
        name: '栈：摞盘子',
        desc: '后放上去的先拿走',
        fullDesc: '栈就像食堂摞盘子——你只能从最上面放（入栈），也只能从最上面拿（出栈）。后进先出（LIFO），就是这么简单！按Ctrl+Z撤销、浏览器后退按钮，背后都是栈的原理。',
        points: ['后进先出是什么','入栈和出栈','函数调用栈','浏览器后退按钮'],
        aiSuggestion: '想想你按Ctrl+Z撤销操作——每次撤销的都是最后一次，这就是栈的思想！',
      },
      ch03_queue_basic: {
        name: '队列：排队',
        desc: '先来的人先服务',
        fullDesc: '队列就是排队——新来的人站队尾（入队），从队头依次服务（出队）。先进先出（FIFO），公平公正！打印机的任务队列、BFS广度优先搜索，都是队列的应用。',
        points: ['先进先出是什么','队头和队尾','入队和出队','生活中的队列应用'],
        aiSuggestion: '下次排队买奶茶时想想——这就是一个活生生的队列数据结构！',
      },
      ch04_string: {
        name: '串：字符串的世界',
        desc: '字符组成的有序序列',
        fullDesc: '串就是字符串——由字符组成的序列。我们每天输入的文本、阅读的文章，本质上都是串。串的基本操作包括找子串、比较、连接等。',
        points: ['主串和子串','串的基本操作','空串和空格串','C语言字符串'],
        aiSuggestion: '你每天都在和串打交道——每次搜索、替换文字都在操作串。',
      },
      ch04_array: {
        name: '数组：多维存储',
        desc: '行优先还是列优先？',
        fullDesc: '数组是相同类型数据的有序集合。一维数组像一行格子，二维数组像一张表格（行和列），三维数组像一本数据书。计算机在内存中把它们按一定顺序铺平存储。',
        points: ['一维到多维','行优先存储','列优先存储','地址计算'],
        aiSuggestion: '想象电子表格的单元格——行优先就是按行从左到右存，列优先就是按列从上到下存。',
      },
      ch05_binary_tree: {
        name: '二叉树：家族谱',
        desc: '每个节点最多有两个孩子',
        fullDesc: '二叉树就像简化版的家谱——每个人最多有两个孩子（左孩子和右孩子）。计算机很喜欢用二叉树，因为它能用非常高效的方式组织数据。想象一个能自动排序的"猜数字"游戏树！',
        points: ['左右孩子','满二叉树和完全二叉树','二叉树的数学性质','为什么二叉树这么重要'],
        aiSuggestion: '试着画一棵3层的二叉树，用圆圈表示节点，用线连接父子关系。',
      },
      ch05_tree_traversal: {
        name: '遍历二叉树',
        desc: '前序、中序、后序、层序',
        fullDesc: '遍历就是访问树的每个节点一次。前序（先看爸爸，再看左边孩子，再看右边孩子），中序（先看左边，再看爸爸，再看右边），后序（先看孩子，最后看爸爸），层序（从上到下、从左到右，像读文章一样）。',
        points: ['前序：根左右','中序：左根右','后序：左右根','层序：逐层扫描'],
        aiSuggestion: '画一棵小树，用三种颜色的笔分别标注前中后序的访问顺序，理解会更透彻。',
      },
      ch06_graph_concept: {
        name: '图：关系网',
        desc: '节点和边构成的复杂网络',
        fullDesc: '图是最灵活的数据结构——由节点（顶点）和连线（边）组成。社交网络（你和朋友的关系）、地图导航（城市和道路）、网页链接（页面和超链接），背后都是图！',
        points: ['顶点和边','有向图 vs 无向图','连通分量','图的度'],
        aiSuggestion: '打开微信好友关系图——每个人是一个节点，好友关系是一条边，这就是图！',
      },
      ch06_dfs: {
        name: '深度优先搜索',
        desc: '一条路走到底，不行就回头',
        fullDesc: 'DFS就像走迷宫——选一条路一直走，走到死胡同就回头（回溯），换一条路继续走。用栈（或递归）实现。走在迷宫中你会在每个岔路口做好标记，避免重复走。',
        points: ['一条路走到底','回溯','递归实现','栈实现'],
        aiSuggestion: '用走迷宫的方式理解DFS——一直往前走，走不通就回头。就这么简单！',
      },
      ch06_bfs: {
        name: '广度优先搜索',
        desc: '像水波一样一圈圈扩散',
        fullDesc: 'BFS就像向平静的湖面扔石子——水波一圈圈向外扩散。从起点开始，先访问距离为1的所有邻居，再访问距离为2的，以此类推。用队列实现。',
        points: ['逐层扩散','队列实现','找最短路径','像水波一样'],
        aiSuggestion: '如果把所有朋友按认识顺序排列，你最先认识的那些朋友就是"第一层邻居"。',
      },
      ch07_seq_search: {
        name: '顺序查找',
        desc: '从头找到尾，简单直接',
        fullDesc: '顺序查找就是在列表中一个一个地找——就像你在书架上找一本书，从第一本开始翻到最后一本。虽然慢（O(n)），但不需要数据有序，是最通用的查找方式。',
        points: ['逐个比较','平均查找次数','哨兵优化','不需要排序'],
        aiSuggestion: '在无序的书架上找一本书，你只能一本一本地看，这就是顺序查找。',
      },
      ch07_binary_search: {
        name: '折半查找',
        desc: '每次砍掉一半',
        fullDesc: '折半查找就像猜数字游戏——我说一个1-100之间的数，你猜50，我说小了你就猜76，大了你就猜25...每次都能排除一半！前提是数据必须排好序。',
        points: ['二分思想','前提条件：有序','每次排除一半','O(log n)有多快'],
        aiSuggestion: '玩一局1-100的猜数字游戏，你会发现你的策略就是折半查找！',
      },
      ch08_bubble_sort: {
        name: '冒泡排序',
        desc: '大泡泡往上浮，小泡泡往下沉',
        fullDesc: '冒泡排序就像水里的气泡——大的气泡（大数字）会慢慢浮到水面上。相邻的两个数比较，如果大的在小的前面就交换。每一轮最大的数就像泡泡一样"浮"到最后。',
        points: ['两两比较交换','为什么叫冒泡','冒泡的性能','优化方案：提前结束'],
        aiSuggestion: '拿一副扑克牌，手动模拟一遍冒泡排序，非常直观！',
      },
      ch08_quick_sort: {
        name: '快速排序',
        desc: '分而治之，分分钟搞定',
        fullDesc: '快速排序就像整理一堆试卷——你先挑一张作为"基准"，把分数比它低的放左边，比它高的放右边。然后对左右两边分别做同样的操作。递归完成后，所有试卷就有序了！',
        points: ['选基准','分治法','左右分区','递归排序'],
        aiSuggestion: '想象你整理一堆考试卷子——先挑一张，把高于和低于它的分开，再对每堆重复！',
      },
    },
    themeColor: '#22c55e',
    themeGradient: ['#22c55e', '#4ade80', '#86efac'],
  },

  // ──────────────────────────────────
  // 📚 入门模式 —— 系统进阶
  // ──────────────────────────────────
  beginner: {
    id: 'beginner',
    label: '入门模式',
    icon: '📚',
    subtitle: '系统学习 · 建立体系',
    description: '完整的数据结构与算法体系，建立扎实的计算机科学基础',
    includedCategories: null, // null = 全部
    includedNodeIds: null,
    nodeDescOverrides: {},
    themeColor: '#3b82f6',
    themeGradient: ['#3b82f6', '#60a5fa', '#93c5fd'],
  },

  // ──────────────────────────────────
  // 🎯 考试模式 —— 高强度冲刺
  // ──────────────────────────────────
  exam: {
    id: 'exam',
    label: '考试模式',
    icon: '🎯',
    subtitle: '专项复习 · 高频考点',
    description: '按考试频率重组知识点，聚焦高频考点和真题训练',
    includedCategories: null,
    includedNodeIds: null,
    // 考试模式重新组织为8大专题（对应8章）
    examCategoryOverride: [
      { id: 'exam_intro',      title: '📖 绪论要点',      x: 120, y: 120, icon: '<rect x="6" y="6" width="16" height="16" rx="2" stroke="currentColor" stroke-width="2" fill="none"/><path d="M10 10l4 4M14 10l-4 4" stroke="currentColor" stroke-width="1.5"/>', description: '数据结构概念与算法分析', nodes: ['ch01_data_concept', 'ch01_data_type', 'ch01_adt', 'ch01_algorithm'] },
      { id: 'exam_linear',     title: '🔗 线性表全掌握',   x: 350, y: 120, icon: '<path d="M4 12h16M8 8l8 4-8 4" stroke="currentColor" stroke-width="2" fill="none"/>', description: '顺序表+链表全题型', nodes: ['ch02_seq_list', 'ch02_linked_list', 'ch02_doubly_list', 'ch02_circular_list', 'ch02_static_list'] },
      { id: 'exam_stackqueue', title: '📚 栈队列磨砺',    x: 580, y: 120, icon: '<rect x="4" y="4" width="20" height="20" rx="2" stroke="currentColor" stroke-width="2" fill="none"/><line x1="8" y1="10" x2="20" y2="10" stroke="currentColor" stroke-width="1.5"/><line x1="8" y1="15" x2="16" y2="15" stroke="currentColor" stroke-width="1.5"/>', description: '括号匹配/BFS/循环队列', nodes: ['ch03_stack_basic', 'ch03_seq_stack', 'ch03_chain_stack', 'ch03_queue_basic', 'ch03_circular_queue', 'ch03_chain_queue'] },
      { id: 'exam_stringarray',title: '📝 串数组广义表',   x: 800, y: 120, icon: '<rect x="4" y="6" width="20" height="16" rx="2" stroke="currentColor" stroke-width="2" fill="none"/><line x1="7" y1="11" x2="21" y2="11" stroke="currentColor" stroke-width="1.5"/><line x1="7" y1="16" x2="17" y2="16" stroke="currentColor" stroke-width="1.3"/>', description: 'KMP/稀疏矩阵/广义表', nodes: ['ch04_string', 'ch04_pattern_match', 'ch04_array', 'ch04_sparse_matrix', 'ch04_generalized_list'] },
      { id: 'exam_tree',       title: '🌳 二叉树全家桶',   x: 200, y: 350, icon: '<circle cx="14" cy="6" r="3" fill="currentColor"/><circle cx="8" cy="18" r="2.5" fill="currentColor"/><circle cx="20" cy="18" r="2.5" fill="currentColor"/><line x1="14" y1="9" x2="8" y2="15" stroke="currentColor" stroke-width="1.5"/><line x1="14" y1="9" x2="20" y2="15" stroke="currentColor" stroke-width="1.5"/>', description: '遍历/Huffman/线索化', nodes: ['ch05_tree_basic', 'ch05_binary_tree', 'ch05_tree_traversal', 'ch05_threaded_tree', 'ch05_huffman'] },
      { id: 'exam_graph',      title: '🗺️ 图论攻坚',      x: 450, y: 350, icon: '<circle cx="9" cy="9" r="2.5" fill="currentColor"/><circle cx="19" cy="7" r="2.5" fill="currentColor"/><circle cx="14" cy="19" r="2.5" fill="currentColor"/><line x1="11" y1="8" x2="17" y2="7.5" stroke="currentColor" stroke-width="1.5"/><line x1="10" y1="11" x2="13" y2="17" stroke="currentColor" stroke-width="1.5"/>', description: 'DFS/BFS/MST/最短路径', nodes: ['ch06_graph_concept', 'ch06_graph_storage', 'ch06_dfs', 'ch06_bfs', 'ch06_mst', 'ch06_shortest_path', 'ch06_topo_sort'] },
      { id: 'exam_search',     title: '🔍 查找全攻略',    x: 680, y: 350, icon: '<circle cx="8" cy="10" r="4" fill="none" stroke="currentColor" stroke-width="2"/><path d="M11 14L18 21" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>', description: '二分/BST/哈希/B树', nodes: ['ch07_seq_search', 'ch07_binary_search', 'ch07_block_search', 'ch07_bst_search', 'ch07_hash_search'] },
      { id: 'exam_sort',       title: '⚡ 排序深度对比',   x: 900, y: 350, icon: '<rect x="4" y="6" width="5" height="8" rx="1" fill="currentColor"/><rect x="11" y="4" width="5" height="10" rx="1" fill="currentColor"/><rect x="18" y="8" width="5" height="6" rx="1" fill="currentColor"/>', description: '8大排序稳定性/复杂度', nodes: ['ch08_insert_sort', 'ch08_shell_sort', 'ch08_bubble_sort', 'ch08_quick_sort', 'ch08_selection_sort', 'ch08_heap_sort', 'ch08_merge_sort', 'ch08_radix_sort'] },
    ],
    // 节点考试频率标注
    nodeExamMeta: {
      ch01_data_concept: { frequency: '🔸 中频', examCount: '基础概念题', tips: '数据结构三要素必记' },
      ch01_algorithm:    { frequency: '🔥🔥 中高频', examCount: '选择题必出', tips: '大O复杂度分析基础' },
      ch02_seq_list:     { frequency: '🔥🔥 中高频', examCount: '插入删除移动次数', tips: '平均移动n/2个元素' },
      ch02_linked_list:  { frequency: '🔥🔥🔥 高频', examCount: '每年必考', tips: '反转/合并/环检测高频题' },
      ch02_doubly_list:  { frequency: '🔥🔥 中高频', examCount: 'LRU缓存实现', tips: 'LRU核心数据结构' },
      ch02_circular_list:{ frequency: '🔸 中频', examCount: '约瑟夫问题', tips: '约瑟夫环经典题' },
      ch02_static_list:  { frequency: '🔸 低频', examCount: '偶考', tips: '重点理解游标思想' },
      ch03_stack_basic:  { frequency: '🔥🔥🔥 高频', examCount: '每年必考', tips: '括号匹配/表达式求值' },
      ch03_seq_stack:    { frequency: '🔸 中频', examCount: '共享栈', tips: '两栈共享数组空间' },
      ch03_chain_stack:  { frequency: '🔸 低频', examCount: '与顺序栈对比', tips: '链栈无栈满限制' },
      ch03_queue_basic:  { frequency: '🔥🔥 中高频', examCount: 'BFS基础', tips: 'FIFO特性与应用' },
      ch03_circular_queue:{ frequency: '🔥🔥🔥 高频', examCount: '常考计算题', tips: '队空队满判断条件' },
      ch03_chain_queue:  { frequency: '🔸 中频', examCount: '对比题', tips: '链式队列操作' },
      ch04_string:       { frequency: '🔸 中频', examCount: '子串计算', tips: 'n个字符子串数=n(n+1)/2+1' },
      ch04_pattern_match:{ frequency: '🔥🔥🔥 高频', examCount: 'KMP必考', tips: 'next数组推导过程' },
      ch04_array:        { frequency: '🔥🔥 中高频', examCount: '地址计算', tips: '行优先/列优先地址公式' },
      ch04_sparse_matrix:{ frequency: '🔸 中频', examCount: '三元组转置', tips: '快速转置算法' },
      ch04_generalized_list:{ frequency: '🔸 低频', examCount: '偶考', tips: '深度/表头表尾运算' },
      ch05_tree_basic:   { frequency: '🔸 中频', examCount: '基础概念', tips: '树/森林/二叉树转换' },
      ch05_binary_tree:  { frequency: '🔥🔥🔥 高频', examCount: '性质推导必考', tips: '二叉树性质公式' },
      ch05_tree_traversal:{ frequency: '🔥🔥🔥🔥 最高频', examCount: '每年必考大题', tips: '序列互推确定二叉树' },
      ch05_threaded_tree:{ frequency: '🔥🔥 中高频', examCount: '常考概念', tips: 'ltag/rtag标志含义' },
      ch05_huffman:      { frequency: '🔥🔥🔥 高频', examCount: 'WPL计算', tips: '哈夫曼编码前缀特性' },
      ch06_graph_concept:{ frequency: '🔥🔥 中高频', examCount: '基础概念题', tips: '完全图边数公式' },
      ch06_graph_storage:{ frequency: '🔥🔥🔥 高频', examCount: '邻接矩阵vs邻接表', tips: '空间复杂度对比' },
      ch06_dfs:          { frequency: '🔥🔥🔥 高频', examCount: '遍历必考', tips: 'DFS递归+栈实现' },
      ch06_bfs:          { frequency: '🔥🔥🔥 高频', examCount: '遍历必考', tips: 'BFS队列实现+最短路径' },
      ch06_mst:          { frequency: '🔥🔥 中高频', examCount: 'Prim/Kruskal', tips: '适合的图类型对比' },
      ch06_shortest_path:{ frequency: '🔥🔥🔥 高频', examCount: 'Dijkstra+Floyd', tips: 'Dijkstra贪心/FloydDP' },
      ch06_topo_sort:    { frequency: '🔥🔥 中高频', examCount: 'Kahn算法', tips: '入度表+环检测' },
      ch07_seq_search:   { frequency: '🔸 中频', examCount: 'ASL计算', tips: '(n+1)/2' },
      ch07_binary_search:{ frequency: '🔥🔥🔥 高频', examCount: '判定树ASL', tips: 'O(log n)+判定树' },
      ch07_block_search: { frequency: '🔸 中频', examCount: '分块策略', tips: '√n分块ASL最优' },
      ch07_bst_search:   { frequency: '🔥🔥🔥 高频', examCount: 'BST必考', tips: '删除三种情况/退化' },
      ch07_hash_search:  { frequency: '🔥🔥🔥 高频', examCount: '冲突处理', tips: '拉链法/开放定址' },
      ch08_insert_sort:  { frequency: '🔥🔥 中高频', examCount: '稳定排序', tips: '基本有序O(n)' },
      ch08_shell_sort:   { frequency: '🔸 中频', examCount: '增量序列', tips: '不稳定/O(n^1.3)' },
      ch08_bubble_sort:  { frequency: '🔸 中频', examCount: '概念题', tips: '稳定/优化标志位' },
      ch08_quick_sort:   { frequency: '🔥🔥🔥🔥 最高频', examCount: '每年必考', tips: '基准选择/最坏情况' },
      ch08_selection_sort:{ frequency: '🔸 低频', examCount: '与冒泡对比', tips: '不稳定/交换少' },
      ch08_heap_sort:    { frequency: '🔥🔥🔥 高频', examCount: '建堆O(n)', tips: '筛选调整/不稳定' },
      ch08_merge_sort:   { frequency: '🔥🔥🔥 高频', examCount: '分治合并', tips: '稳定/O(n)空间' },
      ch08_radix_sort:   { frequency: '🔸 中频', examCount: 'LSD/MSD', tips: '非比较/O(d(n+r))' },
    },
    themeColor: '#f97316',
    themeGradient: ['#f97316', '#fb923c', '#fdba74'],
  }
}

/**
 * 根据当前模式获取过滤后的知识图谱数据
 * @param {'basic'|'beginner'|'exam'} mode 
 * @returns {{ stages: Array, themeColor: string, themeGradient: Array, isExamMode: boolean }}
 */
export function getModeKnowledgeMap(mode) {
  const config = modeConfigs[mode] || modeConfigs.beginner
  
  if (config.examCategoryOverride) {
    return buildExamModeMap(config)
  }
  
  return buildStandardModeMap(config, stages)
}

function buildStandardModeMap(config, originalStages) {
  const filteredStages = []
  
  for (const stage of originalStages) {
    if (config.includedCategories && !config.includedCategories.includes(stage.id)) continue
    
    const filteredNodes = stage.nodes.map(node => {
      const override = config.nodeDescOverrides?.[node.id]
      if (override) {
        return { ...node, ...override }
      }
      if (config.includedNodeIds && !config.includedNodeIds.includes(node.id)) {
        return { ...node, _hiddenInMode: true }
      }
      return node
    }).filter(n => !n._hiddenInMode)
    
    if (filteredNodes.length === 0) continue
    
    filteredStages.push({
      ...stage,
      nodes: filteredNodes,
      _modeConfig: config,
    })
  }
  
  return {
    stages: filteredStages,
    themeColor: config.themeColor,
    themeGradient: config.themeGradient,
    isExamMode: false,
  }
}

function buildExamModeMap(config) {
  const allNodesMap = {}
  for (const stage of stages) {
    for (const node of stage.nodes) {
      allNodesMap[node.id] = {
        ...node,
        ...(config.nodeDescOverrides?.[node.id] || {}),
        ...(config.nodeExamMeta?.[node.id] || {}),
      }
    }
  }
  
  const examStages = config.examCategoryOverride.map(cat => ({
    id: cat.id,
    title: cat.title,
    icon: cat.icon,
    x: cat.x,
    y: cat.y,
    description: cat.description,
    nodes: cat.nodes
      .map(nodeId => ({ ...allNodesMap[nodeId], _originalStageId: nodeId }))
      .filter(n => n.name),
    _modeConfig: config,
  })).filter(s => s.nodes.length > 0)
  
  return {
    stages: examStages,
    themeColor: config.themeColor,
    themeGradient: config.themeGradient,
    isExamMode: true,
  }
}

export function isNodeVisibleInMode(nodeId, mode) {
  const config = modeConfigs[mode] || modeConfigs.beginner
  if (!config.includedNodeIds) return true
  return config.includedNodeIds.includes(nodeId)
}

export function getNodeModeInfo(nodeId, mode) {
  const config = modeConfigs[mode] || modeConfigs.beginner
  if (config.nodeExamMeta?.[nodeId]) {
    return config.nodeExamMeta[nodeId]
  }
  if (config.nodeDescOverrides?.[nodeId]) {
    return config.nodeDescOverrides[nodeId]
  }
  return null
}
