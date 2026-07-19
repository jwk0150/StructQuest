// 知识图谱数据 —— Map & Dashboard 共享（55节点 · 含进阶内容与依赖关系）
// prerequisites 字段表示该节点的前置依赖节点 id 列表
export const stages = [
  // ════════════════════════════════════════════
  // 第1章：绪论
  // ════════════════════════════════════════════
  {
    id: 'ch01_intro', num: '01', title: '绪论', status: 'locked',
    icon: '<rect x="6" y="3" width="16" height="22" rx="2" stroke="currentColor" stroke-width="1.8" fill="none"/><line x1="9" y1="9" x2="19" y2="9" stroke="currentColor" stroke-width="1.5"/><line x1="9" y1="14" x2="19" y2="14" stroke="currentColor" stroke-width="1.5"/><line x1="9" y1="19" x2="15" y2="19" stroke="currentColor" stroke-width="1.5"/>',
    x: 180, y: 200,
    description: '数据结构入门，理解数据、数据元素、数据结构三要素，以及算法分析的基本方法。',
    nodes: [
      { id: 'ch01_data_concept',  name: '数据结构基本概念',  status: 'locked', desc: '数据·数据元素·数据结构三要素', progress: 0, prerequisites: [], fullDesc: '数据是信息的载体，数据元素是数据的基本单位。数据结构研究逻辑结构、存储结构和对数据的运算。', points: ['数据', '数据元素', '数据对象', '数据结构三要素'], aiSuggestion: '先理解"数据元素"和"数据项"的区别，再掌握逻辑结构与存储结构的映射关系。' },
      { id: 'ch01_data_type',     name: '数据类型',         status: 'locked', desc: '原子类型·结构类型·类型定义', progress: 0, prerequisites: ['ch01_data_concept'], fullDesc: '数据类型是一组值及定义在该组值上的一组操作的总称。C语言提供基本类型和构造类型。', points: ['原子类型', '结构类型', 'C语言基本类型', '类型定义'], aiSuggestion: '重点理解 typedef 如何创建别名以及它与结构体配合使用的场景。' },
      { id: 'ch01_adt',           name: '抽象数据类型',     status: 'locked', desc: 'ADT·数据封装·操作定义', progress: 0, prerequisites: ['ch01_data_type'], fullDesc: '抽象数据类型(ADT)通过定义数据和操作来封装实现细节，是面向对象思想的基础。', points: ['ADT', '数据封装', '操作定义', '信息隐蔽'], aiSuggestion: 'ADT的核心是"做什么"而不是"怎么做"，建议对比int和栈的ADT定义来理解。' },
      { id: 'ch01_algorithm',     name: '算法与算法分析',   status: 'locked', desc: '算法特性·时间/空间复杂度', progress: 0, prerequisites: ['ch01_data_concept'], fullDesc: '算法是解决问题步骤的有限序列。时间复杂度衡量运行时间，空间复杂度衡量内存占用。', points: ['算法特性', '时间复杂度', '空间复杂度', '大O表示法'], aiSuggestion: '掌握大O表示法的渐进含义，学会分析循环嵌套的复杂度。' },
    ]
  },
  // ════════════════════════════════════════════
  // 第2章：线性表
  // ════════════════════════════════════════════
  {
    id: 'ch02_linear_list', num: '02', title: '线性表', status: 'locked',
    icon: '<rect x="4" y="4" width="20" height="20" rx="2" stroke="currentColor" stroke-width="1.8" fill="none"/><line x1="8" y1="10" x2="20" y2="10" stroke="currentColor" stroke-width="1.5"/><line x1="8" y1="15" x2="16" y2="15" stroke="currentColor" stroke-width="1.5"/><polyline points="4,8 2,8 2,20 4,20" stroke="currentColor" stroke-width="1.2" fill="none"/>',
    x: 440, y: 200,
    description: '线性结构的基础，掌握顺序表和链表的存储与操作，理解不同存储方式的优劣。',
    nodes: [
      { id: 'ch02_seq_list',      name: '顺序表',           status: 'locked', desc: '顺序存储·随机访问·动态扩容', progress: 0, prerequisites: ['ch01_adt', 'ch01_algorithm'], fullDesc: '用连续内存空间存储线性表，支持 O(1) 随机访问。插入删除需要移动元素。', points: ['顺序存储', '随机访问', '插入删除', '动态扩容'], aiSuggestion: '顺序表插入操作的时间复杂度分析是重点，理解均摊思想。' },
      { id: 'ch02_linked_list',   name: '链表',             status: 'locked', desc: '链式存储·头插尾插·指针操作', progress: 0, prerequisites: ['ch02_seq_list'], fullDesc: '通过指针串联零散内存块，插入删除 O(1) 但不支持随机访问。', points: ['链式存储', '头插法', '尾插法', '指针操作'], aiSuggestion: '画图是理解链表的最好方式，建议用"删除倒数第N个节点"巩固指针操作。' },
      { id: 'ch02_doubly_list',   name: '双向链表',         status: 'locked', desc: '前驱指针·后继指针·双向遍历', progress: 0, prerequisites: ['ch02_linked_list'], fullDesc: '每个节点同时持有前驱和后继指针，支持双向遍历，删除操作更高效。', points: ['前驱指针', '后继指针', '双向遍历', '删除效率'], aiSuggestion: '学完单链表后自然过渡，建议结合LRU缓存场景理解双向链表的优势。' },
      { id: 'ch02_circular_list', name: '循环链表',         status: 'locked', desc: '循环结构·尾指针·约瑟夫问题', progress: 0, prerequisites: ['ch02_linked_list'], fullDesc: '尾节点的next指向头节点形成环，适合轮询调度等场景。', points: ['循环结构', '尾指针', '约瑟夫问题', '环形缓冲区'], aiSuggestion: '约瑟夫问题是循环链表的经典应用，可以亲手实现一遍。' },
      { id: 'ch02_static_list',   name: '静态链表',         status: 'locked', desc: '数组模拟·游标实现·静态分配', progress: 0, prerequisites: ['ch02_linked_list'], fullDesc: '用数组模拟链表，通过游标（数组下标）代替指针，适用于不支持指针的高级语言。', points: ['数组模拟', '游标实现', '备用链表', '静态分配'], aiSuggestion: '理解静态链表的"备用链表"概念，它类似于内存管理中的空闲链表。' },
    ]
  },
  // ════════════════════════════════════════════
  // 第3章：栈和队列
  // ════════════════════════════════════════════
  {
    id: 'ch03_stack_queue', num: '03', title: '栈和队列', status: 'locked',
    icon: '<rect x="4" y="4" width="20" height="20" rx="2" stroke="currentColor" stroke-width="1.8" fill="none"/><line x1="8" y1="10" x2="20" y2="10" stroke="currentColor" stroke-width="1.5"/><line x1="8" y1="15" x2="16" y2="15" stroke="currentColor" stroke-width="1.5"/><polyline points="4,8 2,8 2,20 4,20" stroke="currentColor" stroke-width="1.2" fill="none"/>',
    x: 700, y: 200,
    description: '在线性表基础上施加操作限制，衍生出栈(LIFO)和队列(FIFO)两种核心结构。',
    nodes: [
      { id: 'ch03_stack_basic',   name: '栈的基本概念',     status: 'locked', desc: '栈顶栈底·LIFO·入栈出栈', progress: 0, prerequisites: ['ch02_seq_list', 'ch02_linked_list'], fullDesc: '后进先出的受限线性表，仅在栈顶操作。广泛应用于函数调用、括号匹配。', points: ['栈顶栈底', 'LIFO', '入栈出栈', '函数调用栈'], aiSuggestion: '栈在DFS、回溯等算法中扮演关键角色，建议与递归对比学习。' },
      { id: 'ch03_seq_stack',     name: '顺序栈',           status: 'locked', desc: '顺序存储·栈顶指针·共享栈', progress: 0, prerequisites: ['ch03_stack_basic'], fullDesc: '用数组实现栈，top指针指向栈顶。两个栈可共享同一数组空间。', points: ['顺序存储', '栈顶指针', '栈满判断', '共享栈'], aiSuggestion: '共享栈能节省空间，理解两个栈"相向生长"的设计思想。' },
      { id: 'ch03_chain_stack',   name: '链栈',             status: 'locked', desc: '链式存储·头插法·无栈满限制', progress: 0, prerequisites: ['ch03_stack_basic', 'ch02_linked_list'], fullDesc: '用链表实现栈，头插法入栈相当于push，头删法出栈相当于pop。', points: ['链式存储', '头插法', '无栈满限制', '节点回收'], aiSuggestion: '链栈相比顺序栈的优势是不会栈满，适合数据量不确定的场景。' },
      { id: 'ch03_queue_basic',   name: '队列',             status: 'locked', desc: '队头队尾·FIFO·入队出队', progress: 0, prerequisites: ['ch02_seq_list', 'ch02_linked_list'], fullDesc: '先进先出的受限线性表。队尾入队，队头出队。适用于BFS、任务调度。', points: ['队头队尾', 'FIFO', '入队出队', 'BFS辅助'], aiSuggestion: '队列是BFS的核心数据结构，建议结合二叉树层序遍历一起练习。' },
      { id: 'ch03_circular_queue', name: '循环队列',        status: 'locked', desc: '取模运算·假溢出·队空队满判断', progress: 0, prerequisites: ['ch03_queue_basic'], fullDesc: '用数组模拟循环结构，通过取模运算复用已出队空间，解决假溢出问题。', points: ['取模运算', '假溢出', '队空队满判断', '循环复用'], aiSuggestion: '区分"牺牲一个单元"和"增设size变量"两种队空队满判断方式。' },
      { id: 'ch03_chain_queue',   name: '链队列',           status: 'locked', desc: '头尾指针·链式存储·动态扩展', progress: 0, prerequisites: ['ch03_queue_basic', 'ch02_linked_list'], fullDesc: '用链表实现队列，设置头尾两个指针分别指向队头和队尾。', points: ['头尾指针', '链式存储', '动态扩展', '入队出队操作'], aiSuggestion: '链队列的入队出队操作只需修改指针，不需要移动数据。' },
    ]
  },
  // ════════════════════════════════════════════
  // 第4章：串、数组和广义表
  // ════════════════════════════════════════════
  {
    id: 'ch04_string_array', num: '04', title: '串数组广义表', status: 'locked',
    icon: '<rect x="4" y="6" width="20" height="16" rx="2" stroke="currentColor" stroke-width="1.8" fill="none"/><line x1="7" y1="11" x2="21" y2="11" stroke="currentColor" stroke-width="1.5"/><line x1="7" y1="16" x2="17" y2="16" stroke="currentColor" stroke-width="1.3"/>',
    x: 960, y: 200,
    description: '字符串模式匹配、多维数组存储、稀疏矩阵压缩以及广义表的递归定义。',
    nodes: [
      { id: 'ch04_string',        name: '串',               status: 'locked', desc: '字符串·定长顺序·堆分配存储', progress: 0, prerequisites: ['ch02_seq_list'], fullDesc: '串是由零个或多个字符组成的有限序列。有定长顺序存储和堆分配存储两种方式。', points: ['字符串', '定长顺序存储', '堆分配存储', '串操作'], aiSuggestion: '重点理解C语言中字符串以"\\0"结尾的特性及其安全隐患。' },
      { id: 'ch04_pattern_match', name: '模式匹配',         status: 'locked', desc: '朴素匹配·KMP算法·next数组', progress: 0, prerequisites: ['ch04_string'], fullDesc: '模式匹配是在主串中查找子串首次出现的位置。KMP通过next数组避免回溯，O(n+m)。', points: ['朴素模式匹配', 'KMP算法', 'next数组', '时间复杂度O(n+m)'], aiSuggestion: 'KMP的next数组推导是难点，建议用"前缀相同跳过"来理解核心思想。' },
      { id: 'ch04_array',         name: '数组',             status: 'locked', desc: '多维数组·行优先·列优先', progress: 0, prerequisites: ['ch01_data_concept'], fullDesc: '数组是由相同类型数据元素构成的集合。多维数组按行优先或列优先存储。', points: ['多维数组', '行优先', '列优先', '地址计算'], aiSuggestion: '掌握三维数组中 a[i][j][k] 的地址计算公式推导。' },
      { id: 'ch04_sparse_matrix', name: '稀疏矩阵',         status: 'locked', desc: '三元组·十字链表·压缩存储', progress: 0, prerequisites: ['ch04_array'], fullDesc: '非零元素远少于零元素的矩阵。用三元组或十字链表压缩存储以节省空间。', points: ['三元组', '十字链表', '压缩存储', '转置运算'], aiSuggestion: '十字链表适合矩阵运算中非零元素位置频繁变化的场景。' },
      { id: 'ch04_generalized_list', name: '广义表',        status: 'locked', desc: '表头表尾·深度·递归定义', progress: 0, prerequisites: ['ch02_linked_list'], fullDesc: '广义表是线性表的推广，元素可以是单个元素或另一个广义表，具有递归结构。', points: ['表头表尾', '深度', '递归定义', '共享存储'], aiSuggestion: '广义表的深度计算是递归思想的良好训练。' },
    ]
  },
  // ════════════════════════════════════════════
  // 第5章：树和二叉树（含进阶）
  // ════════════════════════════════════════════
  {
    id: 'ch05_tree', num: '05', title: '树和二叉树', status: 'locked',
    icon: '<circle cx="14" cy="6" r="3" fill="none" stroke="currentColor" stroke-width="1.8"/><line x1="14" y1="9" x2="8" y2="17" stroke="currentColor" stroke-width="1.5"/><line x1="14" y1="9" x2="20" y2="17" stroke="currentColor" stroke-width="1.5"/><circle cx="8" cy="19" r="2.5" fill="none" stroke="currentColor" stroke-width="1.5"/><circle cx="20" cy="19" r="2.5" fill="none" stroke="currentColor" stroke-width="1.5"/>',
    x: 180, y: 550,
    description: '从线性到非线性的跨越，树是层次化数据的核心结构，含平衡树与B树等进阶内容。',
    nodes: [
      { id: 'ch05_tree_basic',    name: '树',               status: 'locked', desc: '树形结构·节点度·树的深度', progress: 0, prerequisites: ['ch01_data_concept'], fullDesc: '树是由n个节点组成的层次结构。除根节点外每个节点有且仅有一个父节点。', points: ['树形结构', '节点度', '树的深度', '森林转换'], aiSuggestion: '掌握树、森林与二叉树的相互转换规则，这是考试常见题型。' },
      { id: 'ch05_binary_tree',   name: '二叉树',           status: 'locked', desc: '左右子树·满二叉树·完全二叉树', progress: 0, prerequisites: ['ch05_tree_basic'], fullDesc: '每个节点最多两个子节点。满二叉树和完全二叉树有特殊的性质。', points: ['左右子树', '满二叉树', '完全二叉树', '性质推导'], aiSuggestion: '熟记二叉树第i层最多2^(i-1)个节点、深度h最多2^h-1个节点等性质。' },
      { id: 'ch05_tree_traversal', name: '二叉树遍历',      status: 'locked', desc: '前中后序遍历·层序遍历', progress: 0, prerequisites: ['ch05_binary_tree', 'ch03_stack_basic', 'ch03_queue_basic'], fullDesc: '四种遍历方式：前序(根左右)、中序(左根右)、后序(左右根)、层序(逐层)。', points: ['前序遍历', '中序遍历', '后序遍历', '层序遍历'], aiSuggestion: '由两种遍历序列唯一确定二叉树是高频考点，建议多练习。' },
      { id: 'ch05_threaded_tree', name: '线索二叉树',       status: 'locked', desc: '前驱后继线索·线索化·遍历优化', progress: 0, prerequisites: ['ch05_tree_traversal'], fullDesc: '利用空指针域存放前驱后继线索，实现无需栈和递归的遍历。', points: ['前驱后继线索', '线索化', '中序线索树', '遍历优化'], aiSuggestion: '理解线索二叉树的"线索"本质上是将空指针重新利用。' },
      { id: 'ch05_huffman',       name: '哈夫曼树',         status: 'locked', desc: '最优二叉树·带权路径长度·哈夫曼编码', progress: 0, prerequisites: ['ch05_binary_tree'], fullDesc: '带权路径长度WPL最小的二叉树。用于数据压缩中的哈夫曼编码。', points: ['最优二叉树', '带权路径长度', '哈夫曼编码', '前缀编码'], aiSuggestion: '哈夫曼编码保证是前缀编码（无二义性），理解"前缀"的含义。' },
      { id: 'ch05_avl',           name: 'AVL平衡二叉树',    status: 'locked', desc: '自平衡·平衡因子·四种旋转', progress: 0, prerequisites: ['ch05_binary_tree', 'ch07_bst_search'], fullDesc: 'AVL树是任意结点左右子树高度差不超过1的二叉搜索树。插入删除时通过LL、RR、LR、RL四种旋转调整平衡。', points: ['平衡因子', 'LL/RR旋转', 'LR/RL旋转', '自平衡'], aiSuggestion: 'AVL树解决了BST退化为链表的问题，理解四种旋转是核心难点。' },
      { id: 'ch05_rbtree',        name: '红黑树',           status: 'locked', desc: '自平衡·红黑着色·工程应用', progress: 0, prerequisites: ['ch05_avl'], fullDesc: '红黑树通过红黑着色规则保证最长路径不超过最短路径两倍。应用：Linux内核、Java TreeMap。', points: ['红黑性质', '变色旋转', '插入调整', '工程应用'], aiSuggestion: '红黑树是面试与工程高频考点，相比AVL插入删除效率更高。' },
      { id: 'ch05_btree',         name: 'B树',              status: 'locked', desc: '多路平衡·关键字分裂·外存查找', progress: 0, prerequisites: ['ch05_binary_tree', 'ch07_bst_search'], fullDesc: 'B树是一种多路平衡查找树，每个结点可包含多个关键字。适合磁盘等外存数据组织。', points: ['m阶B树', '关键字分裂', '关键字合并', '外存查找'], aiSuggestion: 'B树是为磁盘存储设计的结构，理解其减少IO次数的设计动机。' },
      { id: 'ch05_bplus_tree',    name: 'B+树',             status: 'locked', desc: '叶子链表·范围查询·数据库索引', progress: 0, prerequisites: ['ch05_btree'], fullDesc: 'B+树所有数据存于叶子结点，叶子通过链表相连，支持范围查询。MySQL InnoDB索引即基于B+树。', points: ['叶子链表', '范围查询', '数据库索引', '顺序遍历'], aiSuggestion: 'B+树是数据库索引的事实标准，理解其范围查询优势是关键。' },
      { id: 'ch05_union_find',    name: '并查集',           status: 'locked', desc: '路径压缩·按秩合并·连通分量', progress: 0, prerequisites: ['ch05_tree_basic'], fullDesc: '并查集支持高效查找元素所属集合和合并两个集合。应用：连通分量、Kruskal最小生成树。', points: ['路径压缩', '按秩合并', '连通分量', 'Kruskal算法'], aiSuggestion: '并查集代码极简但应用极广，是图论算法的必备工具。' },
    ]
  },
  // ════════════════════════════════════════════
  // 第6章：图（含进阶）
  // ════════════════════════════════════════════
  {
    id: 'ch06_graph', num: '06', title: '图', status: 'locked',
    icon: '<circle cx="8" cy="8" r="3" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="20" cy="8" r="3" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="14" cy="20" r="3" fill="none" stroke="currentColor" stroke-width="1.8"/><line x1="10.5" y1="9.5" x2="17.5" y2="9.5" stroke="currentColor" stroke-width="1.5"/><line x1="9.5" y1="10.5" x2="12.5" y2="17.5" stroke="currentColor" stroke-width="1.2"/><line x1="18.5" y1="10.5" x2="15.5" y2="17.5" stroke="currentColor" stroke-width="1.2"/>',
    x: 440, y: 550,
    description: '最通用的非线性结构，描述万物之间的复杂关系，掌握图搜索、最短路径与关键路径。',
    nodes: [
      { id: 'ch06_graph_concept', name: '图的基本概念',     status: 'locked', desc: '顶点边·有向无向·连通分量', progress: 0, prerequisites: ['ch05_tree_basic'], fullDesc: '由顶点集合和边集合组成的结构。分为有向图和无向图，连通分量是重要概念。', points: ['顶点边', '有向无向', '完全图', '连通分量'], aiSuggestion: '理解连通图、强连通图、连通分量、强连通分量的区别。' },
      { id: 'ch06_graph_storage', name: '图的存储结构',     status: 'locked', desc: '邻接矩阵·邻接表·空间复杂度', progress: 0, prerequisites: ['ch06_graph_concept', 'ch02_linked_list'], fullDesc: '邻接矩阵用二维数组存储，适合稠密图。邻接表用链表存储，适合稀疏图。', points: ['邻接矩阵', '邻接表', '逆邻接表', '空间复杂度'], aiSuggestion: '理解邻接矩阵和邻接表的空间复杂度差异，以及它们分别适合什么场景。' },
      { id: 'ch06_dfs',           name: '深度优先搜索',     status: 'locked', desc: 'DFS·递归栈·访问标记·连通性', progress: 0, prerequisites: ['ch06_graph_storage', 'ch03_stack_basic'], fullDesc: '从一个顶点出发，沿着一条路径走到底再回溯。用栈或递归实现。', points: ['DFS', '递归栈', '访问标记', '连通性判断'], aiSuggestion: 'DFS是图算法的基础，掌握递归和显式栈两种实现方式。' },
      { id: 'ch06_bfs',           name: '广度优先搜索',     status: 'locked', desc: 'BFS·队列实现·逐层遍历', progress: 0, prerequisites: ['ch06_graph_storage', 'ch03_queue_basic'], fullDesc: '从一个顶点出发，逐层访问所有邻接顶点。用队列实现，可求最短路径。', points: ['BFS', '队列实现', '逐层遍历', '最短路径'], aiSuggestion: 'BFS常用于求解无权图中的最短路径问题。' },
      { id: 'ch06_mst',           name: '最小生成树',       status: 'locked', desc: 'Prim·Kruskal·贪心策略·并查集', progress: 0, prerequisites: ['ch06_dfs', 'ch06_bfs'], fullDesc: '在连通带权图中找出连接所有顶点的最小权值边集。', points: ['Prim算法', 'Kruskal算法', '贪心策略', '并查集'], aiSuggestion: 'Kruskal需要并查集支持，建议先学Prim再扩展到Kruskal。' },
      { id: 'ch06_shortest_path', name: '最短路径',         status: 'locked', desc: 'Dijkstra·Floyd·松弛操作', progress: 0, prerequisites: ['ch06_bfs'], fullDesc: '单源最短路径用Dijkstra（非负权），多源用Floyd。', points: ['Dijkstra', 'Floyd', '松弛操作', '负权边限制'], aiSuggestion: 'Dijkstra是面试高频题，理解"松弛操作"的概念是关键。' },
      { id: 'ch06_topo_sort',     name: '拓扑排序',         status: 'locked', desc: 'AOV网·入度表·BFS实现·环检测', progress: 0, prerequisites: ['ch06_dfs'], fullDesc: '对有向无环图(DAG)的顶点进行线性排序。常用BFS（Kahn算法）实现。', points: ['AOV网', '入度表', 'BFS实现', '环检测'], aiSuggestion: '拓扑排序可用于检测有向图中是否存在环。' },
      { id: 'ch06_critical_path', name: '关键路径',         status: 'locked', desc: 'AOE网·关键活动·最短工期', progress: 0, prerequisites: ['ch06_topo_sort'], fullDesc: 'AOE网是用边表示活动的带权有向无环图。关键路径决定工程最短工期。', points: ['AOE网', '关键活动', '最早发生时间', '最迟发生时间'], aiSuggestion: '关键路径是项目管理中的核心算法，理解"松弛时间"概念是关键。' },
    ]
  },
  // ════════════════════════════════════════════
  // 第7章：查找（含进阶）
  // ════════════════════════════════════════════
  {
    id: 'ch07_search', num: '07', title: '查找', status: 'locked',
    icon: '<circle cx="8" cy="10" r="4" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M11 14L18 21" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><circle cx="16" cy="18" r="1" fill="currentColor"/><line x1="13" y1="6" x2="18" y2="6" stroke="currentColor" stroke-width="1.5"/><line x1="14" y1="10" x2="19" y2="10" stroke="currentColor" stroke-width="1.3"/><line x1="13" y1="14" x2="17" y2="14" stroke="currentColor" stroke-width="1"/>',
    x: 700, y: 550,
    description: '从顺序查找到哈希查找，含跳表与字典树等进阶结构，掌握不同查找算法的效率。',
    nodes: [
      { id: 'ch07_seq_search',    name: '顺序查找',         status: 'locked', desc: '线性查找·哨兵优化·ASL分析', progress: 0, prerequisites: ['ch02_seq_list', 'ch02_linked_list'], fullDesc: '从头到尾逐个比较。设置哨兵可以减少比较次数。', points: ['线性查找', '哨兵优化', 'ASL分析', '无序查找'], aiSuggestion: '哨兵优化虽然简单，但体现了"用空间换时间"的思想。' },
      { id: 'ch07_binary_search', name: '折半查找',         status: 'locked', desc: '有序表·二分思想·判定树·O(log n)', progress: 0, prerequisites: ['ch07_seq_search'], fullDesc: '在有序表中每次取中间元素比较，将查找范围缩小一半。O(log n)。', points: ['有序表', '二分思想', '判定树', 'O(log n)'], aiSuggestion: '折半查找的判定树是一棵平衡二叉搜索树，理解ASL的计算方法。' },
      { id: 'ch07_block_search',  name: '分块查找',         status: 'locked', desc: '索引表·块内无序·块间有序·ASL', progress: 0, prerequisites: ['ch07_seq_search', 'ch07_binary_search'], fullDesc: '将数据分为若干块，块间有序块内无序。查找分两步：先查索引表确定块，再在块内顺序查找。', points: ['索引表', '块内无序', '块间有序', '平均查找长度'], aiSuggestion: '分块查找结合了顺序查找和折半查找的思想，适合动态变化的数据。' },
      { id: 'ch07_bst_search',    name: '二叉排序树',       status: 'locked', desc: '左小右大·中序有序·查找插入删除', progress: 0, prerequisites: ['ch05_binary_tree', 'ch07_binary_search'], fullDesc: '左子树所有节点<根节点<右子树所有节点。中序遍历得到递增有序序列。', points: ['左小右大', '中序有序', '查找插入删除', '平衡问题'], aiSuggestion: 'BST退化为链表的场景需要理解，为AVL树和红黑树做铺垫。' },
      { id: 'ch07_hash_search',   name: '哈希查找',         status: 'locked', desc: '哈希函数·冲突解决·拉链法·装填因子', progress: 0, prerequisites: ['ch01_data_concept'], fullDesc: '通过哈希函数将关键字映射到存储位置。拉链法和开放定址法解决冲突。', points: ['哈希函数', '冲突解决', '拉链法', '装填因子'], aiSuggestion: '装填因子α直接影响查找效率，理解α=0.5和α=0.8的区别。' },
      { id: 'ch07_skip_list',     name: '跳表',             status: 'locked', desc: '多层索引·概率平衡·Redis应用', progress: 0, prerequisites: ['ch02_linked_list', 'ch07_binary_search'], fullDesc: '跳表通过多层索引链表实现O(log n)的查找插入删除，是平衡树的概率替代方案。', points: ['多层索引', '概率平衡', '空间换时间', 'Redis应用'], aiSuggestion: '跳表以简单实现达到平衡树性能，是工程中平衡树的优质替代方案。' },
      { id: 'ch07_trie',          name: '字典树',           status: 'locked', desc: '前缀共享·自动补全·词频统计', progress: 0, prerequisites: ['ch05_tree_basic', 'ch04_string'], fullDesc: '字典树将字符串按字符拆分存储于树中，公共前缀共享路径。应用：搜索引擎自动补全。', points: ['前缀共享', '自动补全', '词频统计', '空间换时间'], aiSuggestion: '字典树是字符串处理的核心结构，理解前缀共享思想是关键。' },
    ]
  },
  // ════════════════════════════════════════════
  // 第8章：排序（含进阶）
  // ════════════════════════════════════════════
  {
    id: 'ch08_sort', num: '08', title: '排序', status: 'locked',
    icon: '<rect x="4" y="6" width="5" height="4" rx="1" fill="none" stroke="currentColor" stroke-width="1.8"/><rect x="11" y="10" width="5" height="7" rx="1" fill="none" stroke="currentColor" stroke-width="1.8"/><rect x="18" y="4" width="5" height="10" rx="1" fill="none" stroke="currentColor" stroke-width="1.8"/>',
    x: 960, y: 550,
    description: '掌握各类排序算法的原理、时间/空间复杂度、稳定性，含计数排序与桶排序等进阶内容。',
    nodes: [
      { id: 'ch08_insert_sort',   name: '插入排序',         status: 'locked', desc: '直接插入·折半插入·稳定排序', progress: 0, prerequisites: ['ch02_seq_list'], fullDesc: '将未排序元素插入到已排序序列的正确位置。折半插入用二分查找优化比较次数。', points: ['直接插入', '折半插入', '稳定排序', 'O(n²)'], aiSuggestion: '插入排序在基本有序的数组上效率很高，最佳情况O(n)。' },
      { id: 'ch08_shell_sort',    name: '希尔排序',         status: 'locked', desc: '增量序列·分组插入·不稳定', progress: 0, prerequisites: ['ch08_insert_sort'], fullDesc: '将相隔某个增量的元素组成子表进行插入排序，逐步缩小增量。', points: ['增量序列', '分组插入', '不稳定', 'O(n^1.3)'], aiSuggestion: '希尔排序的时间复杂度依赖于增量序列的选择，理解"分组跳跃"的思想。' },
      { id: 'ch08_bubble_sort',   name: '冒泡排序',         status: 'locked', desc: '相邻交换·优化标记·稳定排序', progress: 0, prerequisites: ['ch02_seq_list'], fullDesc: '两两比较相邻元素，顺序不对则交换。每轮将最大元素"浮"到最后。', points: ['相邻交换', '优化标记', '稳定排序', '最佳O(n)'], aiSuggestion: '设置交换标记优化后，冒泡排序在有序数组上只需O(n)。' },
      { id: 'ch08_quick_sort',    name: '快速排序',         status: 'locked', desc: '分治交换·基准选择·最坏O(n²)', progress: 0, prerequisites: ['ch08_bubble_sort', 'ch01_algorithm'], fullDesc: '选取基准将数组分为小于和大于两部分，递归排序。平均O(n log n)。', points: ['分治交换', '基准选择', '最坏O(n²)', '不稳定'], aiSuggestion: '快排是工业界默认排序算法，掌握"三数取中"优化基准选择。' },
      { id: 'ch08_selection_sort', name: '简单选择排序',    status: 'locked', desc: '最小值选择·不稳定·交换次数少', progress: 0, prerequisites: ['ch02_seq_list'], fullDesc: '每轮从未排序部分选出最小值放到已排序部分的末尾。', points: ['最小值选择', '不稳定', 'O(n²)', '交换次数少'], aiSuggestion: '简单选择排序的交换次数是O(n)，比冒泡少，但比较次数相同。' },
      { id: 'ch08_heap_sort',     name: '堆排序',           status: 'locked', desc: '大顶堆·建堆O(n)·筛选调整·不稳定', progress: 0, prerequisites: ['ch05_binary_tree'], fullDesc: '利用堆这种数据结构进行排序。建堆O(n)，每次调整O(log n)。', points: ['大顶堆', '建堆O(n)', '筛选调整', '不稳定'], aiSuggestion: '理解"建堆"和"堆调整"的区别，建堆是从最后一个非叶子节点开始向下调整。' },
      { id: 'ch08_merge_sort',    name: '归并排序',         status: 'locked', desc: '分治合并·稳定排序·O(n)空间', progress: 0, prerequisites: ['ch01_algorithm', 'ch08_insert_sort'], fullDesc: '将序列不断二分直到单元素，再两两合并为有序序列。稳定排序，需额外O(n)空间。', points: ['分治合并', '稳定排序', 'O(n)空间', '外部排序'], aiSuggestion: '归并排序是外部排序的基础，理解"多路归并"的概念。' },
      { id: 'ch08_radix_sort',    name: '基数排序',         status: 'locked', desc: '多关键字·LSD·MSD·稳定排序', progress: 0, prerequisites: ['ch02_seq_list'], fullDesc: '按位数从低位到高位（LSD）或高位到低位（MSD）依次分配收集。', points: ['多关键字', 'LSD', 'MSD', '稳定排序'], aiSuggestion: '基数排序的时间复杂度是O(d(n+r))，与数据范围有关而不是数据本身。' },
      { id: 'ch08_counting_sort', name: '计数排序',         status: 'locked', desc: '计数数组·线性时间·数据范围限制', progress: 0, prerequisites: ['ch08_radix_sort'], fullDesc: '计数排序通过统计每个元素出现次数实现排序，时间复杂度O(n+k)。适合数据范围不大的整数排序。', points: ['计数数组', '线性时间', '数据范围限制', '稳定排序'], aiSuggestion: '计数排序突破了比较排序下界，但要求数据范围可控。' },
      { id: 'ch08_bucket_sort',   name: '桶排序',           status: 'locked', desc: '分桶策略·桶内排序·均匀分布', progress: 0, prerequisites: ['ch08_counting_sort'], fullDesc: '桶排序将数据分配到若干有序桶中，每个桶内单独排序后按序合并。平均O(n+k)。', points: ['分桶策略', '桶内排序', '均匀分布', '线性期望'], aiSuggestion: '桶排序利用数据分布特征实现线性排序，理解分桶策略是关键。' },
    ]
  },
]

// ════════════════════════════════════════════
// 工具函数：ID → 中文名映射（从 stages 自动派生）
// ════════════════════════════════════════════

/** 从 stages 数据自动构建的 id → 中文名 映射表 */
const nodeIdMap = {}
stages.forEach(chapter => {
  // 章节自身
  nodeIdMap[chapter.id] = chapter.title
  // 章节下所有知识点
  chapter.nodes.forEach(node => {
    nodeIdMap[node.id] = node.name
  })
})

/**
 * 将知识点/章节 ID 翻译为中文名
 * @param {string} id - 节点或章节 ID，如 'ch05_binary_tree'
 * @returns {string} 中文名，未命中原样返回
 */
export function getNodeNameById(id) {
  return nodeIdMap[id] || id
}

/** 8 章前缀 → 中文章名映射 */
const CHAPTER_PREFIX_MAP = {
  ch01_: '绪论',
  ch02_: '线性表',
  ch03_: '栈和队列',
  ch04_: '串数组广义表',
  ch05_: '树和二叉树',
  ch06_: '图',
  ch07_: '查找',
  ch08_: '排序',
}

/**
 * 将 50+ 个知识点的掌握度分数聚合成 8 章分数
 * @param {Object} mastery - { 'ch01_algorithm': 85, 'ch05_binary_tree': 60, ... }
 * @returns {Object} - { '绪论': 77.5, '线性表': 50, ... }
 */
export function aggregateToChapters(mastery) {
  const groups = {}
  for (const [key, score] of Object.entries(mastery)) {
    for (const [prefix, chapName] of Object.entries(CHAPTER_PREFIX_MAP)) {
      if (key.startsWith(prefix)) {
        if (!groups[chapName]) groups[chapName] = []
        groups[chapName].push(Number(score))
        break
      }
    }
  }
  const result = {}
  for (const [name, scores] of Object.entries(groups)) {
    result[name] = scores.reduce((a, b) => a + b, 0) / scores.length
  }
  return result
}
