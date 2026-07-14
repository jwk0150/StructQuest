from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import redis.asyncio as aioredis
import os
import logging

logger = logging.getLogger(__name__)

# ===== SQLite 数据库连接（跨设备零配置） =====
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./learn_ai.db"
)

print(f"[DB] 数据库连接URL: {SQLALCHEMY_DATABASE_URL}")
print(f"[DB] 当前工作目录: {os.getcwd()}")

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    """获取数据库会话"""
    print("[DB] 创建新的数据库会话...")
    async with AsyncSessionLocal() as session:
        print("[DB] ✅ 数据库会话创建成功")
        yield session
        print("[DB] 🔚 数据库会话已关闭")


# ===== Redis 缓存连接 =====
class RedisClient:
    _instance = None

    @classmethod
    async def get_instance(cls):
        if cls._instance is None:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            try:
                cls._instance = await aioredis.from_url(
                    redis_url,
                    decode_responses=True,  # 自动解码为字符串
                    max_connections=20,
                )
                logger.info(" Redis 连接成功！")
            except Exception as e:
                logger.warning(f" Redis 连接失败（缓存功能不可用）: {e}")
                cls._instance = None
        return cls._instance


async def get_redis():
    """获取 Redis 客户端"""
    return await RedisClient.get_instance()


# ===== 知识图谱种子数据（55 节点 · 含进阶内容与依赖关系） =====
# 元组格式: (id, title, description, full_desc, category, difficulty, order_index,
#           parent_id, prerequisites(JSON), icon, points(JSON), ai_suggestion)
def _build_seed_nodes():
    return [
        # ═══ ch01: 绪论 ═══
        ('ch01_data_concept', '数据结构基本概念', '数据结构三要素：逻辑结构、存储结构、数据运算', '数据结构是计算机存储、组织数据的方式。包括三要素：逻辑结构（集合、线性、树形、图状）、存储结构（顺序、链式、索引、散列）和数据运算（插入、删除、查找、排序等）。是算法设计的基础。', 'ch01_intro', 1, 0, None, '[]', '', '["逻辑结构", "存储结构", "数据运算", "数据结构三要素"]', '数据结构是算法设计的基石，建议结合生活实例理解逻辑结构与存储结构的区别。'),
        ('ch01_data_type', '数据类型', '数据类型的定义与分类', '数据类型是一组性质相同的值的集合以及定义在此集合上的一组操作的总称。分为基本数据类型（整型、浮点型、字符型等）和构造数据类型（数组、结构体等）。', 'ch01_intro', 1, 1, None, '["ch01_data_concept"]', '', '["基本数据类型", "构造数据类型", "类型定义", "类型分类"]', '掌握数据类型是理解后续所有抽象数据类型的前提。'),
        ('ch01_adt', '抽象数据类型', 'ADT的概念与定义方法', '抽象数据类型（ADT）指一个数学模型以及定义在该模型上的一组操作。ADT的定义仅取决于其逻辑特性，与具体实现无关。使用三元组表示：（数据对象、数据关系、基本操作）。', 'ch01_intro', 2, 2, None, '["ch01_data_type"]', '', '["ADT定义", "数据对象", "数据关系", "基本操作"]', 'ADT是面向对象编程中封装思想的理论来源，理解ADT有助于学习后续各种数据结构。'),
        ('ch01_algorithm', '算法与算法分析', '算法的定义、特性和复杂度分析', '算法是对特定问题求解步骤的描述。五大特性：有穷性、确定性、可行性、输入、输出。算法分析包括时间复杂度分析和空间复杂度分析，使用大O记号表示渐进复杂度。', 'ch01_intro', 2, 3, None, '["ch01_data_concept"]', '', '["算法特性", "时间复杂度", "空间复杂度", "大O记号"]', '复杂度分析是评价算法优劣的核心手段，需重点掌握常见复杂度量级。'),

        # ═══ ch02: 线性表 ═══
        ('ch02_seq_list', '顺序表', '基于数组的线性表存储结构', '顺序表是用一组地址连续的存储单元依次存储线性表的数据元素。具有随机存取特性，查找时间复杂度O(1)，但插入删除需要移动大量元素，平均时间复杂度O(n)。', 'ch02_linear_list', 1, 0, None, '["ch01_adt", "ch01_algorithm"]', '', '["随机存取", "插入操作", "删除操作", "动态扩容"]', '顺序表是线性表最基础的实现方式，理解其随机存取特性与插入删除的效率权衡。'),
        ('ch02_linked_list', '链表', '基于指针链接的线性表存储结构', '链表通过一组任意的存储单元存储线性表数据元素，结点之间通过指针链接。插入删除只需修改指针，时间复杂度O(1)，但不支持随机存取。', 'ch02_linear_list', 1, 1, None, '["ch02_seq_list"]', '', '["结点定义", "头插法", "尾插法", "指针操作"]', '链表是理解指针操作和动态内存管理的最佳数据结构。'),
        ('ch02_doubly_list', '双向链表', '带前驱和后继指针的链表', '双向链表每个结点包含data、prior（前驱指针）和next（后继指针）三个域。支持双向遍历，在删除和插入操作上比单链表更灵活，但占用更多存储空间。', 'ch02_linear_list', 2, 2, None, '["ch02_linked_list"]', '', '["前驱指针", "后继指针", "双向遍历", "结点删除"]', '学习时注意与单链表的对比，理解双向链表在哪些场景更有优势。'),
        ('ch02_circular_list', '循环链表', '首尾相连的环状链表', '循环链表是另一种形式的链式存储结构，最后一个结点的next指针指向头结点，整个链表形成一个环。适合需要循环访问的场景，如约瑟夫问题、操作系统进程轮询。', 'ch02_linear_list', 2, 3, None, '["ch02_linked_list"]', '', '["环状结构", "约瑟夫问题", "循环遍历", "尾指针优化"]', '循环链表的遍历终止条件与普通链表不同，编程实现时需特别注意。'),
        ('ch02_static_list', '静态链表', '用数组实现的链表结构', '静态链表使用数组描述链式结构，每个数组元素包含data和cursor（游标）两个域，游标指示后继元素在数组中的下标。适合不支持指针的高级语言。', 'ch02_linear_list', 3, 4, None, '["ch02_linked_list"]', '', '["游标实现", "备用链表", "插入操作", "删除操作"]', '静态链表是理解"逻辑结构独立于存储结构"的绝佳例子。'),

        # ═══ ch03: 栈和队列 ═══
        ('ch03_stack_basic', '栈的基本概念', '后进先出的线性表', '栈是限定仅在表尾进行插入和删除操作的线性表。表尾称为栈顶（top），表头称为栈底（bottom）。栈的操作遵循后进先出（LIFO）原则。', 'ch03_stack_queue', 1, 0, None, '["ch02_seq_list", "ch02_linked_list"]', '', '["栈顶", "栈底", "LIFO", "进栈出栈"]', '栈是计算机系统中应用最广泛的数据结构之一，务必理解其LIFO特性。'),
        ('ch03_seq_stack', '顺序栈', '基于数组的栈实现', '顺序栈利用一组地址连续的存储单元存放自栈底到栈顶的数据元素，附设栈顶指针top指示栈顶位置。入栈时top加1，出栈时top减1。', 'ch03_stack_queue', 2, 1, None, '["ch03_stack_basic"]', '', '["栈顶指针", "入栈操作", "出栈操作", "栈满判断"]', '顺序栈的实现简单直观，注意栈满和栈空的条件判断。'),
        ('ch03_chain_stack', '链栈', '基于链表的栈实现', '链栈是采用链式存储结构的栈，栈顶在链表头部。入栈相当于头插法，出栈相当于删除头结点。链栈不存在栈满问题，空间可动态扩展。', 'ch03_stack_queue', 2, 2, None, '["ch03_stack_basic", "ch02_linked_list"]', '', '["链式存储", "头插法", "栈顶操作", "动态扩展"]', '链栈与顺序栈的对比体现了顺序存储和链式存储各自的优劣。'),
        ('ch03_queue_basic', '队列', '先进先出的线性表', '队列是限定在表的一端插入、另一端删除的线性表。允许插入的一端称为队尾（rear），允许删除的一端称为队头（front）。遵循先进先出（FIFO）原则。', 'ch03_stack_queue', 1, 3, None, '["ch02_seq_list", "ch02_linked_list"]', '', '["队头", "队尾", "FIFO", "入队出队"]', '队列在BFS、任务调度、缓冲区等场景广泛应用。'),
        ('ch03_circular_queue', '循环队列', '解决假溢出问题的队列实现', '循环队列将顺序队列臆造为一个环状空间，通过取模运算实现队头和队尾指针在数组空间内循环。解决了顺序队列的"假溢出"问题，提高了空间利用率。', 'ch03_stack_queue', 2, 4, None, '["ch03_queue_basic"]', '', '["假溢出", "取模运算", "队空队满判断", "循环利用"]', '循环队列的队满判断条件（(rear+1)%max == front）是常见考点。'),
        ('ch03_chain_queue', '链队列', '基于链表的队列实现', '链队列是用链式存储结构实现的队列，队头指针指向头结点，队尾指针指向终端结点。入队在队尾插入，出队在队头删除。', 'ch03_stack_queue', 2, 5, None, '["ch03_queue_basic", "ch02_linked_list"]', '', '["队头指针", "队尾指针", "入队操作", "出队操作"]', '链队列不存在队满问题，适合不确定数据量的场景。'),

        # ═══ ch04: 串、数组和广义表 ═══
        ('ch04_string', '串', '字符串的基本概念与操作', '串（String）是由零个或多个字符组成的有限序列。串中任意连续字符组成的子序列称为子串。串的基本操作包括赋值、比较、求长度、连接、求子串、定位等。', 'ch04_string_array', 1, 0, None, '["ch02_seq_list"]', '', '["主串", "子串", "串比较", "串连接"]', '串是一种特殊的线性表，其数据元素为单个字符。'),
        ('ch04_pattern_match', '模式匹配', '子串定位的经典算法', '模式匹配是在主串中查找与模式串相同的子串的定位操作。经典算法包括BF（暴力匹配）算法和KMP（快速模式匹配）算法。KMP通过next数组避免回溯，时间复杂度O(n+m)。', 'ch04_string_array', 3, 1, None, '["ch04_string"]', '', '["BF算法", "KMP算法", "next数组", "失配回溯"]', 'KMP算法是模式匹配的经典算法，理解next数组的求解是关键。'),
        ('ch04_array', '数组', '多维数组的定义与存储', '数组是由类型相同的数据元素构成的集合，元素在内存中按一定顺序排列。多维数组的存储方式有行优先和列优先两种，通过地址计算公式实现随机存取。', 'ch04_string_array', 1, 2, None, '["ch01_data_concept"]', '', '["行优先", "列优先", "地址计算", "多维数组"]', '数组是最简单的数据结构，但其地址计算是理解内存布局的基础。'),
        ('ch04_sparse_matrix', '稀疏矩阵', '稀疏矩阵的三元组存储与运算', '稀疏矩阵中非零元素远少于零元素。采用三元组（行、列、值）只存储非零元素以节省空间。转置运算可通过快速转置算法优化。十字链表适用于矩阵运算中元素位置频繁变化的场景。', 'ch04_string_array', 3, 3, None, '["ch04_array"]', '', '["三元组", "稀疏矩阵转置", "十字链表", "压缩存储"]', '稀疏矩阵的压缩存储体现了"以时间换空间"的工程思想。'),
        ('ch04_generalized_list', '广义表', '递归定义的线性表扩展', '广义表是线性表的推广，元素可以是单个元素（原子）或另一个广义表（子表）。采用链式存储结构，每个结点包含标志域、值域和指向下一个元素的指针。典型应用包括m元多项式表示。', 'ch04_string_array', 3, 4, None, '["ch02_linked_list"]', '', '["原子", "子表", "递归定义", "链式存储"]', '广义表的递归定义使其成为理解递归算法和LISP语言的基础。'),

        # ═══ ch05: 树和二叉树（含进阶） ═══
        ('ch05_tree_basic', '树', '树的基本概念与表示方法', '树是n（n>=0）个结点的有限集，有且仅有一个根结点。树是递归定义的，每个结点可以有多个子树。基本术语包括：结点度、树的度、叶子结点、分支结点、层次、深度、森林等。', 'ch05_tree', 1, 0, None, '["ch01_data_concept"]', '', '["根结点", "结点的度", "叶子结点", "树的深度"]', '树是最重要的非线性结构之一，建议从树的递归定义入手理解。'),
        ('ch05_binary_tree', '二叉树', '二叉树的性质与存储结构', '二叉树是每个结点最多有两个子树的树结构，子树有左右之分。重要性质：第i层最多有2^(i-1)个结点；深度为k的二叉树最多有2^k-1个结点。存储方式包括顺序存储和链式存储。', 'ch05_tree', 1, 1, None, '["ch05_tree_basic"]', '', '["左子树", "右子树", "满二叉树", "完全二叉树"]', '二叉树是所有树结构的基础，后续的二叉排序树、哈夫曼树等都建立在二叉树之上。'),
        ('ch05_tree_traversal', '二叉树遍历', '前序、中序、后序、层序遍历', '二叉树遍历分为深度优先遍历（前序、中序、后序）和广度优先遍历（层序）。前序：根左右；中序：左根右；后序：左右根；层序：按层从上到下、从左到右。', 'ch05_tree', 2, 2, None, '["ch05_binary_tree", "ch03_stack_basic", "ch03_queue_basic"]', '', '["前序遍历", "中序遍历", "后序遍历", "层序遍历"]', '遍历是二叉树最基本的操作，掌握递归和迭代两种实现方式。'),
        ('ch05_threaded_tree', '线索二叉树', '利用空指针域加速遍历', '线索二叉树利用二叉链表中的空指针域存放指向前驱或后继的线索，使遍历不再需要递归或栈。ltag/rtag标志位区分指针是孩子还是线索。', 'ch05_tree', 3, 3, None, '["ch05_tree_traversal"]', '', '["前驱线索", "后继线索", "ltag/rtag", "线索化"]', '线索二叉树是优化遍历效率的经典技巧。'),
        ('ch05_huffman', '哈夫曼树', '最优二叉树与哈夫曼编码', '哈夫曼树是带权路径长度最小的二叉树，也称最优二叉树。构造算法：每次选择权值最小的两个结点合并。哈夫曼编码是前缀编码，广泛应用于数据压缩。', 'ch05_tree', 3, 4, None, '["ch05_binary_tree"]', '', '["带权路径长度", "哈夫曼算法", "前缀编码", "数据压缩"]', '哈夫曼树是贪心算法的经典应用，体现了理论与实践的结合。'),
        ('ch05_avl', 'AVL平衡二叉树', '自平衡二叉搜索树', 'AVL树是任意结点左右子树高度差不超过1的二叉搜索树。插入删除时通过LL、RR、LR、RL四种旋转调整平衡。查找O(log n)，适合频繁查找少插入删除的场景。', 'ch05_tree', 4, 5, None, '["ch05_binary_tree", "ch07_bst_search"]', '', '["平衡因子", "LL/RR旋转", "LR/RL旋转", "自平衡"]', 'AVL树解决了BST退化为链表的问题，理解四种旋转是核心难点。'),
        ('ch05_rbtree', '红黑树', '工程中最常用的平衡树', '红黑树是一种自平衡二叉搜索树，通过红黑着色规则保证最长路径不超过最短路径两倍。五大性质：根黑、叶黑、红不连续、黑高相同、结点有颜色。应用：Linux内核、Java TreeMap。', 'ch05_tree', 5, 6, None, '["ch05_avl"]', '', '["红黑性质", "变色旋转", "插入调整", "工程应用"]', '红黑树是面试与工程高频考点，相比AVL插入删除效率更高，应用更广。'),
        ('ch05_btree', 'B树', '多路平衡查找树', 'B树是一种多路平衡查找树，每个结点可包含多个关键字和多个子树。m阶B树每个结点最多m个子树。所有叶子在同一层，适合磁盘等外存数据组织。', 'ch05_tree', 4, 7, None, '["ch05_binary_tree", "ch07_bst_search"]', '', '["m阶B树", "关键字分裂", "关键字合并", "外存查找"]', 'B树是为磁盘存储设计的结构，理解其减少IO次数的设计动机。'),
        ('ch05_bplus_tree', 'B+树', '数据库索引核心结构', 'B+树是B树的变体，所有数据存于叶子结点，非叶子结点仅存索引。叶子结点通过链表相连，支持范围查询和顺序遍历。MySQL InnoDB索引即基于B+树。', 'ch05_tree', 5, 8, None, '["ch05_btree"]', '', '["叶子链表", "范围查询", "数据库索引", "顺序遍历"]', 'B+树是数据库索引的事实标准，理解其范围查询优势是关键。'),
        ('ch05_union_find', '并查集', '不相交集合的合并与查找', '并查集支持高效查找元素所属集合和合并两个集合。采用路径压缩和按秩合并优化后，单次操作接近O(1)。应用：连通分量、Kruskal最小生成树、等价类判定。', 'ch05_tree', 3, 9, None, '["ch05_tree_basic"]', '', '["路径压缩", "按秩合并", "连通分量", "Kruskal算法"]', '并查集代码极简但应用极广，是图论算法的必备工具。'),

        # ═══ ch06: 图（含进阶） ═══
        ('ch06_graph_concept', '图的基本概念', '图的定义、分类与基本术语', '图由顶点集V和边集E组成。分类：有向图/无向图、连通图/非连通图、稀疏图/稠密图、带权图/无权图。基本术语包括：度、入度、出度、路径、回路、连通分量等。', 'ch06_graph', 1, 0, None, '["ch05_tree_basic"]', '', '["有向图", "无向图", "连通分量", "顶点的度"]', '图是最灵活的数据结构，几乎可以表达所有复杂关系。'),
        ('ch06_graph_storage', '图的存储结构', '邻接矩阵与邻接表', '邻接矩阵用二维数组存储顶点间关系，空间复杂度O(V^2)，适合稠密图。邻接表为每个顶点建立单链表存储其邻接点，空间复杂度O(V+E)，适合稀疏图。', 'ch06_graph', 2, 1, None, '["ch06_graph_concept", "ch02_linked_list"]', '', '["邻接矩阵", "邻接表", "空间复杂度", "存储选择"]', '两种存储结构的选择直接影响图算法的效率。'),
        ('ch06_dfs', '深度优先搜索', '递归探索的图遍历算法', 'DFS从起点出发，沿着一条路径尽可能深入，直到无法继续再回溯。使用栈（递归）实现。应用包括：连通分量判定、环检测、拓扑排序、二分图判定等。', 'ch06_graph', 2, 2, None, '["ch06_graph_storage", "ch03_stack_basic"]', '', '["递归实现", "栈实现", "回溯", "连通分量"]', 'DFS的本质是系统化的试探和回溯。'),
        ('ch06_bfs', '广度优先搜索', '逐层扩展的图遍历算法', 'BFS从起点出发，按距离递增逐层访问所有顶点。使用队列实现。应用包括：最短路径（无权图）、连通分量、二分图判定等。', 'ch06_graph', 2, 3, None, '["ch06_graph_storage", "ch03_queue_basic"]', '', '["队列实现", "逐层遍历", "无权最短路径", "连通分量"]', 'BFS在无权图中第一次到达某顶点即为最短路径。'),
        ('ch06_mst', '最小生成树', 'Prim与Kruskal算法', '最小生成树是在连通带权图中找出连接所有顶点的权值最小的树。Prim算法从顶点出发扩展，适合稠密图；Kruskal算法按边权排序贪心选择，适合稀疏图。', 'ch06_graph', 3, 4, None, '["ch06_dfs", "ch06_bfs"]', '', '["Prim算法", "Kruskal算法", "贪心策略", "并查集"]', 'MST是贪心算法的典型应用场景。'),
        ('ch06_shortest_path', '最短路径', 'Dijkstra与Floyd算法', 'Dijkstra算法解决单源最短路径（非负权图），贪心思想，可用优先队列优化至O(E log V)。Floyd算法解决所有顶点对最短路径，动态规划思想，时间复杂度O(V^3)。', 'ch06_graph', 3, 5, None, '["ch06_bfs"]', '', '["Dijkstra算法", "Floyd算法", "单源路径", "多源路径"]', 'Dijkstra和Floyd分别代表贪心和DP在路径问题中的应用。'),
        ('ch06_topo_sort', '拓扑排序', '有向无环图的线性排序', '拓扑排序是对有向无环图（DAG）的顶点进行排序，使得对每条有向边(u,v)，u在排序中出现在v之前。常用算法：Kahn算法（基于入度）和DFS-based算法。', 'ch06_graph', 3, 6, None, '["ch06_dfs"]', '', '["DAG", "Kahn算法", "入度表", "DFS排序"]', '拓扑排序是判断有向图是否有环的常用方法。'),
        ('ch06_critical_path', '关键路径', 'AOE网与工程最短工期', 'AOE网是用边表示活动的带权有向无环图。关键路径是从源点到汇点路径长度最长的路径，决定工程最短工期。需计算顶点最早/最迟发生时间和活动最早/最迟开始时间。', 'ch06_graph', 4, 7, None, '["ch06_topo_sort"]', '', '["AOE网", "关键活动", "最早发生时间", "最迟发生时间"]', '关键路径是项目管理中的核心算法，理解"松弛时间"概念是关键。'),

        # ═══ ch07: 查找（含进阶） ═══
        ('ch07_seq_search', '顺序查找', '线性表的顺序查找方法', '顺序查找从线性表一端开始逐个比较，直到找到目标或遍历完整个表。平均查找长度ASL=(n+1)/2，时间复杂度O(n)。适用于顺序表和链表，不要求数据有序。', 'ch07_search', 1, 0, None, '["ch02_seq_list", "ch02_linked_list"]', '', '["ASL", "顺序比较", "哨兵优化", "线性表"]', '顺序查找是最简单但效率最低的查找方法。'),
        ('ch07_binary_search', '折半查找', '有序表的二分查找方法', '折半查找要求数据有序且顺序存储，每次取中间元素比较，将查找范围缩小一半。时间复杂度O(log n)。折半查找的判定树是一棵平衡二叉搜索树。', 'ch07_search', 2, 1, None, '["ch07_seq_search"]', '', '["二分判定", "有序表", "判定树", "对数时间"]', '折半查找是O(log n)算法思想的经典代表。'),
        ('ch07_block_search', '分块查找', '索引顺序表的查找方法', '分块查找将数据分为若干块，块内无序、块间有序。建立索引表记录每块的最大关键字和起始位置。查找时先在索引表中折半查找确定块，再在块内顺序查找。', 'ch07_search', 2, 2, None, '["ch07_seq_search", "ch07_binary_search"]', '', '["索引表", "分块", "块间有序", "块内无序"]', '分块查找结合了顺序查找和折半查找的优点。'),
        ('ch07_bst_search', '二叉排序树', '二叉排序树的查找与维护', '二叉排序树（BST）左子树所有结点小于根，右子树所有结点大于根。中序遍历得到递增序列。查找插入删除平均O(log n)。删除操作分三种情况：叶子、单子树、双子树。', 'ch07_search', 2, 3, None, '["ch05_binary_tree", "ch07_binary_search"]', '', '["左小右大", "中序有序", "查找插入删除", "删除三种情况"]', 'BST是动态查找的基石，理解其退化问题才能理解平衡树的必要性。'),
        ('ch07_hash_search', '哈希查找', '散列表的构造与冲突处理', '哈希查找通过哈希函数将关键字映射为存储地址。常见哈希函数：除留余数法、直接定址法等。冲突处理方法：链地址法、开放定址法（线性探测、二次探测、再哈希法）。装填因子影响查找效率。', 'ch07_search', 2, 4, None, '["ch01_data_concept"]', '', '["哈希函数", "链地址法", "开放定址法", "装填因子"]', '哈希表实现了理论上O(1)的查找效率，是空间换时间的典型。'),
        ('ch07_skip_list', '跳表', '概率平衡的有序查找结构', '跳表通过多层索引链表实现O(log n)的查找插入删除，是平衡树的概率替代方案。每层是下层的稀疏子集，顶层最稀疏。Redis的有序集合即基于跳表实现。', 'ch07_search', 4, 5, None, '["ch02_linked_list", "ch07_binary_search"]', '', '["多层索引", "概率平衡", "空间换时间", "Redis应用"]', '跳表以简单实现达到平衡树性能，是工程中平衡树的优质替代方案。'),
        ('ch07_trie', '字典树', '字符串前缀检索树', '字典树（Trie树/前缀树）将字符串按字符拆分存储于树中，公共前缀共享路径。查找插入O(L)，L为字符串长度。应用：搜索引擎自动补全、IP路由表、词频统计。', 'ch07_search', 4, 6, None, '["ch05_tree_basic", "ch04_string"]', '', '["前缀共享", "自动补全", "词频统计", "空间换时间"]', '字典树是字符串处理的核心结构，理解前缀共享思想是关键。'),

        # ═══ ch08: 排序（含进阶） ═══
        ('ch08_insert_sort', '插入排序', '直接插入排序算法', '直接插入排序将待排序元素插入到已排序序列的合适位置。最好情况O(n)，平均和最坏O(n^2)。稳定排序，适合基本有序的小规模数据。', 'ch08_sort', 1, 0, None, '["ch02_seq_list"]', '', '["直接插入", "稳定排序", "部分有序", "最佳情况"]', '插入排序虽简单，但在数据基本有序时效率很高。'),
        ('ch08_shell_sort', '希尔排序', '缩小增量排序算法', '希尔排序将整个序列分割成若干子序列分别进行插入排序，逐步缩小增量直到1。时间复杂度约O(n^1.3)，不稳定排序。突破了O(n^2)的瓶颈。', 'ch08_sort', 2, 1, None, '["ch08_insert_sort"]', '', '["增量序列", "子序列", "插入排序", "不稳定"]', '希尔排序是第一个突破O(n^2)的排序算法。'),
        ('ch08_bubble_sort', '冒泡排序', '相邻元素两两比较的排序算法', '冒泡排序通过相邻元素两两比较，将最大元素逐步"浮"到最后。优化：设置标志位，某趟无交换则提前结束。最好O(n)，平均最坏O(n^2)，稳定排序。', 'ch08_sort', 1, 2, None, '["ch02_seq_list"]', '', '["相邻比较", "优化标志位", "稳定排序", "提前结束"]', '冒泡排序因简单直观而广为人知，但实际应用较少。'),
        ('ch08_quick_sort', '快速排序', '基于分治的高效排序算法', '快速排序选取基准元素，通过划分将序列分为小于和大于基准的两部分，递归排序。平均O(n log n)，最坏O(n^2)。不稳定排序。是实际应用最广泛的排序算法。', 'ch08_sort', 3, 3, None, '["ch08_bubble_sort", "ch01_algorithm"]', '', '["基准选择", "划分算法", "递归分治", "最坏情况"]', '快排是工业界默认排序算法，理解其分治思想比记住实现更重要。'),
        ('ch08_selection_sort', '简单选择排序', '每次选择最小元素的排序算法', '简单选择排序每趟从未排序序列中选出最小元素放到已排序序列末尾。无论数据分布如何，时间复杂度始终为O(n^2)。不稳定排序。', 'ch08_sort', 1, 4, None, '["ch02_seq_list"]', '', '["选择最小", "无序到有序", "O(n^2)", "不稳定"]', '选择排序的特点是交换次数最少（最多n-1次）。'),
        ('ch08_heap_sort', '堆排序', '利用堆结构的选择排序', '堆排序利用堆（完全二叉树）进行排序。建堆O(n)，每次调整O(log n)，总体O(n log n)。不稳定排序。大顶堆用于升序排序，小顶堆用于降序排序。', 'ch08_sort', 3, 5, None, '["ch05_binary_tree"]', '', '["建堆", "调整", "大顶堆", "不稳定"]', '堆排序没有递归，不需要大量额外空间，适合嵌入式等内存受限场景。'),
        ('ch08_merge_sort', '归并排序', '分治合并的排序算法', '归并排序将序列递归分成两半分别排序后合并。时间复杂度O(n log n)，稳定排序。空间复杂度O(n)。2路归并排序是最常见的实现方式。', 'ch08_sort', 3, 6, None, '["ch01_algorithm", "ch08_insert_sort"]', '', '["分治合并", "稳定排序", "O(n)空间", "2路归并"]', '归并排序是唯一稳定O(n log n)的排序算法。'),
        ('ch08_radix_sort', '基数排序', '按位分配收集的非比较排序', '基数排序不基于比较，而是按关键字位进行分配和收集。分为最低位优先（LSD）和最高位优先（MSD）。时间复杂度O(d(n+r))，稳定排序。', 'ch08_sort', 3, 7, None, '["ch02_seq_list"]', '', '["LSD", "MSD", "分配收集", "非比较排序"]', '基数排序突破了比较排序的下界O(n log n)。'),
        ('ch08_counting_sort', '计数排序', '线性时间非比较排序', '计数排序通过统计每个元素出现次数实现排序，时间复杂度O(n+k)，k为数据范围。适合数据范围不大的整数排序，是基数排序的基础。稳定排序。', 'ch08_sort', 3, 8, None, '["ch08_radix_sort"]', '', '["计数数组", "线性时间", "数据范围限制", "稳定排序"]', '计数排序突破了比较排序下界，但要求数据范围可控。'),
        ('ch08_bucket_sort', '桶排序', '分桶后桶内排序的线性排序', '桶排序将数据分配到若干有序桶中，每个桶内单独排序后按序合并。平均O(n+k)，最坏O(n^2)。适合数据均匀分布的场景。稳定排序（取决于桶内排序）。', 'ch08_sort', 4, 9, None, '["ch08_counting_sort"]', '', '["分桶策略", "桶内排序", "均匀分布", "线性期望"]', '桶排序利用数据分布特征实现线性排序，理解分桶策略是关键。'),
    ]


# ===== 应用启动时初始化 =====
async def init_database():
    """创建数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    #  自动迁移：尝试补充缺失的列（SQLite 兼容）
    try:
        from sqlalchemy import text
        async with engine.begin() as conn:
            # SQLite: 使用 PRAGMA 检查列是否存在
            for table, col, col_type in [
                ("exam_results", "details", "TEXT"),
                ("knowledge_documents", "doc_id", "VARCHAR(64)"),
                ("knowledge_documents", "file_size", "FLOAT"),
                ("knowledge_documents", "status", "VARCHAR(20) DEFAULT 'active'"),
                ("learning_progress", "resource_progress", "JSON"),
                ("users", "is_admin", "BOOLEAN DEFAULT 0"),
                # 冷启动画像新增字段
                ("users", "major", "VARCHAR(100)"),
                ("users", "grade", "VARCHAR(50)"),
                ("users", "course", "VARCHAR(100)"),
                ("users", "learning_goal", "VARCHAR(100)"),
                ("users", "target_score", "VARCHAR(20)"),
                ("users", "daily_study_time", "VARCHAR(20)"),
                ("users", "exam_date", "VARCHAR(50)"),
                ("users", "learning_purpose", "VARCHAR(50)"),
                ("users", "preferred_styles", "JSON"),
                ("users", "diagnostic_results", "JSON"),
            ]:
                try:
                    pragma = await conn.execute(text(f"PRAGMA table_info({table})"))
                    cols = [row[1] for row in pragma.fetchall()]
                    if col not in cols:
                        await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
                        print(f" 数据库迁移：已添加 {table}.{col} 列")
                except Exception:
                    pass  # 表可能不存在，忽略
    except Exception as e:
        print(f" 数据库迁移检查失败（可忽略）: {e}")

    #  初始化/升级知识图谱节点数据（55节点 · 含进阶内容与依赖关系）
    try:
        from sqlalchemy import text
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT COUNT(*) FROM knowledge_nodes"))
            count = result.scalar() or 0
            seed_nodes = _build_seed_nodes()

            # 判断是否需要升级：检测进阶节点是否存在
            need_upgrade = False
            if count == 0:
                need_upgrade = True
            else:
                adv_result = await conn.execute(
                    text("SELECT COUNT(*) FROM knowledge_nodes WHERE id = 'ch05_avl'")
                )
                if (adv_result.scalar() or 0) == 0:
                    need_upgrade = True

            if need_upgrade:
                if count == 0:
                    print(" 正在初始化知识图谱节点数据（《数据结构》8章55节点体系）...")
                else:
                    print(f" 检测到旧版知识图谱数据（{count}个节点），升级至含进阶内容的55节点体系...")

                # 读取现有节点 ID，用 upsert 方式更新（保留学习进度引用）
                existing_result = await conn.execute(text("SELECT id FROM knowledge_nodes"))
                existing_ids = {row[0] for row in existing_result.fetchall()}

                for node_data in seed_nodes:
                    params = {
                        "id": node_data[0], "title": node_data[1], "desc": node_data[2],
                        "full_desc": node_data[3], "cat": node_data[4], "diff": node_data[5],
                        "ord": node_data[6], "pid": node_data[7], "preq": node_data[8],
                        "icon": node_data[9], "pts": node_data[10], "ai": node_data[11],
                    }
                    if node_data[0] in existing_ids:
                        # 已存在节点：更新（重点是 prerequisites 等字段）
                        await conn.execute(text(
                            "UPDATE knowledge_nodes SET title=:title, description=:desc, full_desc=:full_desc, "
                            "category=:cat, difficulty=:diff, order_index=:ord, prerequisites=:preq, "
                            "icon=:icon, points=:pts, ai_suggestion=:ai WHERE id=:id"
                        ), params)
                    else:
                        # 新增进阶节点：插入
                        await conn.execute(text(
                            "INSERT INTO knowledge_nodes (id, title, description, full_desc, category, difficulty, "
                            "order_index, parent_id, prerequisites, icon, points, ai_suggestion) "
                            "VALUES (:id, :title, :desc, :full_desc, :cat, :diff, :ord, :pid, :preq, :icon, :pts, :ai)"
                        ), params)

                print(f" 知识图谱初始化/升级完成：共 {len(seed_nodes)} 个节点（含10个进阶节点与完整依赖关系）")
            else:
                print(f" 知识图谱已是最新版（55节点含进阶内容），无需升级")
    except Exception as e:
        print(f" 知识图谱初始化/迁移失败（可忽略）: {e}")

    print(" SQLite 数据库表创建/更新完成")
