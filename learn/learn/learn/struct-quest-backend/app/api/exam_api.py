"""章节测试 API：生成试卷、提交答案、获取测试结果"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from app.db.session import get_db
from app.auth import get_required_user
from app.models.user import User
from app.models.knowledge_graph import KnowledgeNode
from app.models.learning_progress import LearningProgress
from app.models.exam_result import ExamResult
from app.services.profile_service import recalculate_profile
import os
import json
import re
import time

router = APIRouter(prefix="/api/exam", tags=["exam"])

# ★ 知识库生成的题目缓存 {node_id: {"questions": [...], "cached_at": timestamp}}
_kb_exam_cache = {}
_kb_cache_ttl = 3600  # 缓存1小时


class SubmitExamRequest(BaseModel):
    node_id: str
    answers: List[dict]  # [{question_id, answer, correct}]


class QuizResultRequest(BaseModel):
    node_id: str
    wrong_items: List[dict] = []  # [{ question, answer, user_answer, explanation, type, options, knowledge_point }]
    correct_count: int = 0
    total_count: int = 0


class RemoveMistakeRequest(BaseModel):
    mistake_id: str  # 格式: "mistake_{exam_result_id}_{detail_idx}"


class ExamQuestion(BaseModel):
    id: str
    question: str
    type: str = "choice"  # "choice" | "blank" | "coding"
    options: List[str] = []
    correct_answer: str = ""
    explanation: str = ""
    # 填空题/编程题专用字段
    blank_answer: str = ""       # 填空题正确答案
    coding_template: str = ""    # 编程题代码模板
    test_cases: List[dict] = []  # 编程题测试用例 [{input, expected}]


# ════════════════════════════════════════════════════════
# 内置章节测试题库
# ════════════════════════════════════════════════════════

# ★ 难度标签映射（用于自适应出题）
DIFFICULTY_LEVELS = {
    "easy": "基础记忆",
    "medium": "理解应用",
    "hard": "分析综合",
}

BLOOM_LEVELS = {
    "remember": "记忆",
    "understand": "理解",
    "apply": "应用",
    "analyze": "分析",
}

NODE_EXAMS = {
    # ═══ 线性结构 ═══
    "array": {
        "questions": [
            {"id": "arr_1", "question": "数组在内存中的存储方式是什么？", "options": ["连续存储", "链式存储", "树形存储", "散列存储"], "correct": 0, "explanation": "数组元素在内存中是连续存储的，可以通过首地址+偏移量快速访问。", "difficulty": "easy", "bloom": "remember"},
            {"id": "arr_2", "question": "数组下标从几开始？", "options": ["0", "1", "视语言而定", "2"], "correct": 2, "explanation": "大多数编程语言数组下标从0开始，但也有语言从1开始（如Fortran, MATLAB）。", "difficulty": "easy", "bloom": "understand"},
            {"id": "arr_3", "question": "已知 int a[5]，则 sizeof(a) 的值是？", "options": ["4", "5", "20", "40"], "correct": 2, "explanation": "int 占4字节，5个int共20字节。", "difficulty": "easy", "bloom": "apply"},
            {"id": "arr_4", "question": "二维数组 a[3][4] 按行优先存储，a[2][1] 的偏移量是？", "options": ["4", "9", "8", "12"], "correct": 1, "explanation": "行优先：a[2][1] = 2×4+1 = 9，即第9个元素（从0计数）。", "difficulty": "medium", "bloom": "apply"},
            {"id": "arr_5", "question": "以下关于数组的描述，错误的是？", "options": ["支持随机访问O(1)", "插入删除需要移动元素", "可以动态调整大小", "内存空间连续"], "correct": 2, "explanation": "静态数组大小固定，不能动态调整；动态数组才能扩容。", "difficulty": "medium", "bloom": "understand"},
            {"id": "arr_6", "question": "稀疏矩阵用二维数组存储的缺点是什么？", "options": ["访问太慢", "浪费大量内存空间", "不能随机访问", "插入元素复杂"], "correct": 1, "explanation": "稀疏矩阵中大部分元素为0，二维数组会存储大量无用的0值，浪费空间。", "difficulty": "hard", "bloom": "analyze"},
        ]
    },
    # ★ 别名：linked_list → slist（种子数据 ID 为 slist）
    "linked_list": {"questions": [
        {"id": "ll_1", "question": "单链表中插入一个节点的时间复杂度是？", "options": ["O(1)", "O(n)", "O(log n)", "O(n^2)"], "correct": 0, "explanation": "已知插入位置时，单链表插入为O(1)；但查找插入位置需要O(n)。", "difficulty": "easy", "bloom": "remember"},
        {"id": "ll_2", "question": "链表相比数组的主要优势是？", "options": ["随机访问快", "内存连续", "插入删除效率高", "占用内存少"], "correct": 2, "explanation": "链表插入和删除不需要移动元素，只需修改指针。", "difficulty": "easy", "bloom": "understand"},
        {"id": "ll_3", "question": "双向链表相比单向链表多了一个什么指针？", "options": ["next", "prev", "head", "tail"], "correct": 1, "explanation": "双向链表比单向链表多了一个指向前驱节点的prev指针。", "difficulty": "easy", "bloom": "remember"},
        {"id": "ll_4", "question": "删除单链表中某个已知节点的后继节点，时间复杂度是？", "options": ["O(1)", "O(n)", "O(log n)", "O(n²)"], "correct": 0, "explanation": "已知节点p，删除p的后继只需修改p.next = p.next.next，O(1)。", "difficulty": "medium", "bloom": "apply"},
        {"id": "ll_5", "question": "用单链表实现栈，push操作应该在链表的什么位置？", "options": ["头部", "尾部", "中间", "随机位置"], "correct": 0, "explanation": "栈的push/pop都在栈顶，对应链表头部，这样时间复杂度O(1)。", "difficulty": "medium", "bloom": "apply"},
        {"id": "ll_6", "question": "反转单链表的迭代法时间复杂度是？", "options": ["O(1)", "O(n)", "O(n²)", "O(log n)"], "correct": 1, "explanation": "遍历一次链表，逐个修改指针方向，O(n)。", "difficulty": "hard", "bloom": "analyze"},
    ]},
    "slist": {"questions": [
        {"id": "sl_1", "question": "单链表中插入一个节点的时间复杂度是？", "options": ["O(1)", "O(n)", "O(log n)", "O(n^2)"], "correct": 0, "explanation": "已知插入位置时，单链表插入为O(1)；但查找插入位置需要O(n)。", "difficulty": "easy", "bloom": "remember"},
        {"id": "sl_2", "question": "链表相比数组的主要优势是？", "options": ["随机访问快", "内存连续", "插入删除效率高", "占用内存少"], "correct": 2, "explanation": "链表插入和删除不需要移动元素，只需修改指针。", "difficulty": "easy", "bloom": "understand"},
        {"id": "sl_3", "question": "头插法创建链表时，新节点插入到链表的什么位置？", "options": ["头部", "尾部", "中间", "随机位置"], "correct": 0, "explanation": "头插法每次将新节点插入到链表头部，最终链表顺序与插入顺序相反。", "difficulty": "easy", "bloom": "remember"},
        {"id": "sl_4", "question": "单链表中如何判断是否有环？", "options": ["遍历计数法", "快慢指针法", "哈希表法", "以上都可以"], "correct": 3, "explanation": "快慢指针（Floyd判圈）、哈希表和遍历计数都可以判断链表是否有环。", "difficulty": "medium", "bloom": "apply"},
        {"id": "sl_5", "question": "在带头节点的单链表中，表空的判断条件是？", "options": ["head==NULL", "head->next==NULL", "head->next==head", "head->data==0"], "correct": 1, "explanation": "带头节点的单链表为空时，头节点的next指针指向NULL。", "difficulty": "medium", "bloom": "understand"},
        {"id": "sl_6", "question": "合并两个有序单链表，时间复杂度是？", "options": ["O(1)", "O(n+m)", "O(n×m)", "O(log n)"], "correct": 1, "explanation": "需要遍历两个链表，比较并合并，O(n+m)。", "difficulty": "hard", "bloom": "analyze"},
    ]},
    "dlist": {"questions": [
        {"id": "dl_1", "question": "双向链表每个节点包含几个指针域？", "options": ["1个", "2个", "3个", "4个"], "correct": 1, "explanation": "双向链表每个节点包含前驱指针 prev 和后继指针 next，共2个指针域。", "difficulty": "easy", "bloom": "remember"},
        {"id": "dl_2", "question": "在双向链表中删除一个已知节点的时间复杂度是？", "options": ["O(1)", "O(n)", "O(log n)", "O(n²)"], "correct": 0, "explanation": "已知节点时，通过prev和next指针可以直接修改前后节点的链接，无需遍历。", "difficulty": "easy", "bloom": "understand"},
        {"id": "dl_3", "question": "双向链表相对于单向链表的主要优势是？", "options": ["节省内存", "支持双向遍历", "插入更快", "查找更快"], "correct": 1, "explanation": "双向链表可以向前和向后两个方向遍历，操作更灵活。", "difficulty": "easy", "bloom": "understand"},
        {"id": "dl_4", "question": "在双向链表中，在已知节点p之前插入新节点需要修改几个指针？", "options": ["2个", "3个", "4个", "5个"], "correct": 2, "explanation": "新节点前后指针(2) + p前驱的next(1) + p的prev(1) = 4个指针需要修改。", "difficulty": "medium", "bloom": "apply"},
        {"id": "dl_5", "question": "双向循环链表为空的条件是？", "options": ["head==NULL", "head->next==head且head->prev==head", "head->next==NULL", "head->prev==NULL"], "correct": 1, "explanation": "双向循环链表为空时，头节点的next和prev都指向自身。", "difficulty": "medium", "bloom": "understand"},
        {"id": "dl_6", "question": "LRU缓存使用双向链表+哈希表实现，为什么用双向而不是单向链表？", "options": ["节省空间", "O(1)删除任意节点", "O(1)查找", "实现更简单"], "correct": 1, "explanation": "双向链表已知节点可直接删除（通过prev和next），单向链表删除需要找到前驱O(n)。", "difficulty": "hard", "bloom": "analyze"},
    ]},
    "clist": {"questions": [
        {"id": "cl_1", "question": "循环链表的尾节点指针指向哪里？", "options": ["NULL", "头节点", "自身", "随机地址"], "correct": 1, "explanation": "循环链表的尾节点的next指针指向头节点，形成环状结构。", "difficulty": "easy", "bloom": "remember"},
        {"id": "cl_2", "question": "循环链表适合解决什么问题？", "options": ["约瑟夫问题", "排序问题", "查找问题", "哈希冲突"], "correct": 0, "explanation": "循环链表适合约瑟夫环等需要循环遍历的场景。", "difficulty": "easy", "bloom": "understand"},
        {"id": "cl_3", "question": "循环链表的遍历终止条件是什么？", "options": ["p == NULL", "p.next == head", "p.next == NULL", "count == n"], "correct": 1, "explanation": "循环链表从头节点开始遍历，当回到头节点时表示遍历完成。", "difficulty": "easy", "bloom": "remember"},
        {"id": "cl_4", "question": "用循环链表实现队列，出队操作的时间复杂度是？", "options": ["O(1)", "O(n)", "O(log n)", "O(n²)"], "correct": 0, "explanation": "用头指针指队头、尾指针指队尾，出队即删除头指针后继，O(1)。", "difficulty": "medium", "bloom": "apply"},
        {"id": "cl_5", "question": "n个人的约瑟夫环问题，用循环链表求解的时间复杂度是？", "options": ["O(n)", "O(n×m)", "O(n log n)", "O(n²)"], "correct": 1, "explanation": "需要模拟m步淘汰过程，时间复杂度O(n×m)。", "difficulty": "medium", "bloom": "analyze"},
    ]},
    # ═══ 受限线性结构（栈与队列）═══
    "stack": {
        "questions": [
            {"id": "stk_1", "question": "栈的特点是？", "options": ["先进先出", "先进后出", "随机访问", "双端操作"], "correct": 1, "explanation": "栈是LIFO（后进先出）结构。", "difficulty": "easy", "bloom": "remember"},
            {"id": "stk_2", "question": "用栈实现括号匹配，遇到左括号应执行什么操作？", "options": ["入栈", "出栈", "查看栈顶", "清空栈"], "correct": 0, "explanation": "遇到左括号入栈，遇到右括号出栈并匹配。", "difficulty": "easy", "bloom": "understand"},
            {"id": "stk_3", "question": "递归函数的调用过程本质上使用了什么数据结构？", "options": ["队列", "栈", "数组", "树"], "correct": 1, "explanation": "函数调用通过调用栈（Call Stack）实现，递归本质是栈的运用。", "difficulty": "medium", "bloom": "understand"},
            {"id": "stk_4", "question": "用两个栈模拟队列，入队操作push到哪个栈？", "options": ["栈A", "栈B", "两个栈都push", "先push到B再转到A"], "correct": 0, "explanation": "入队push到栈A即可；出队时如果B空，把A全部pop到B，再从B pop。", "difficulty": "medium", "bloom": "apply"},
            {"id": "stk_5", "question": "入栈序列为1,2,3，以下哪个不可能是出栈序列？", "options": ["3,2,1", "1,2,3", "2,1,3", "3,1,2"], "correct": 3, "explanation": "先出3说明1,2已入栈，1,2出栈顺序必为2,1。3,1,2不可能。", "difficulty": "hard", "bloom": "analyze"},
            {"id": "stk_6", "question": "中缀表达式 a+b*c 转换为后缀表达式的结果是？", "options": ["abc*+", "ab+c*", "a*bc+", "abc+*"], "correct": 0, "explanation": "运算符优先级：*高于+，先处理b*c，再处理a+bc*，最终为abc*+。", "difficulty": "hard", "bloom": "analyze"},
        ]
    },
    "queue": {
        "questions": [
            {"id": "qu_1", "question": "队列的特点是？", "options": ["先进先出", "先进后出", "随机访问", "优先级排序"], "correct": 0, "explanation": "队列是FIFO（先进先出）结构。", "difficulty": "easy", "bloom": "remember"},
            {"id": "qu_2", "question": "循环队列解决的主要问题是什么？", "options": ["空间不足", "假溢出", "入队慢", "查找慢"], "correct": 1, "explanation": "循环队列通过取模运算复用数组空间，解决顺序队列的'假溢出'问题。", "difficulty": "easy", "bloom": "understand"},
            {"id": "qu_3", "question": "BFS（广度优先搜索）使用什么数据结构辅助？", "options": ["栈", "队列", "数组", "堆"], "correct": 1, "explanation": "BFS利用队列的FIFO特性实现逐层遍历。", "difficulty": "medium", "bloom": "understand"},
            {"id": "qu_4", "question": "双端队列（Deque）支持在哪些位置插入？", "options": ["仅队头", "仅队尾", "队头和队尾", "任意位置"], "correct": 2, "explanation": "双端队列允许在两端进行插入和删除操作。", "difficulty": "medium", "bloom": "remember"},
            {"id": "qu_5", "question": "滑动窗口最大值问题使用什么数据结构最优？", "options": ["普通队列", "双端队列", "优先队列", "栈"], "correct": 1, "explanation": "用单调双端队列存储可能成为最大值的元素索引，O(n)解决。", "difficulty": "hard", "bloom": "analyze"},
            {"id": "qu_6", "question": "用两个队列模拟栈，push操作需要做什么？", "options": ["入队到空队列", "入队到非空队列", "两个队列各入一半", "先出队再入队"], "correct": 1, "explanation": "push时直接入队到非空队列；pop时需要把前面n-1个元素转移到另一个队列。", "difficulty": "hard", "bloom": "analyze"},
        ]
    },
    # ═══ 树形结构 ═══
    # ★ 别名：binary_tree → btree
    "binary_tree": {"questions": [
        {"id": "bt_1", "question": "二叉树的深度优先遍历不包括以下哪种？", "options": ["前序遍历", "中序遍历", "后序遍历", "层序遍历"], "correct": 3, "explanation": "深度优先遍历包括前序、中序、后序；层序遍历属于广度优先。", "difficulty": "easy", "bloom": "remember"},
        {"id": "bt_2", "question": "完全二叉树中，度为1的节点数最多为？", "options": ["0个", "1个", "2个", "不确定"], "correct": 1, "explanation": "完全二叉树中最多只有一个度为1的节点。", "difficulty": "easy", "bloom": "understand"},
        {"id": "bt_3", "question": "一棵有n个节点的完全二叉树，其高度为？", "options": ["n", "log₂n", "⌊log₂n⌋+1", "n/2"], "correct": 2, "explanation": "完全二叉树高度为⌊log₂n⌋+1，保证了O(log n)的查找效率。", "difficulty": "medium", "bloom": "understand"},
        {"id": "bt_4", "question": "已知二叉树前序序列为ABDECF，中序序列为DBEAFC，后序序列是？", "options": ["DEBFCA", "DEBAFC", "ABDECF", "DBEAFC"], "correct": 0, "explanation": "根据前序定根、中序分左右子树，递归求解得后序DEBFCA。", "difficulty": "medium", "bloom": "apply"},
        {"id": "bt_5", "question": "满二叉树第k层最多有多少个节点？", "options": ["2^k", "2^(k-1)", "2^k-1", "k²"], "correct": 1, "explanation": "第k层最多有2^(k-1)个节点（根节点为第1层）。", "difficulty": "medium", "bloom": "remember"},
        {"id": "bt_6", "question": "n个节点的二叉树有多少种不同的形态？（卡特兰数）", "options": ["2^n", "n!", "C(2n,n)/(n+1)", "n²"], "correct": 2, "explanation": "n个节点的不同二叉树个数为卡特兰数：C(2n,n)/(n+1)。", "difficulty": "hard", "bloom": "analyze"},
    ]},
    "btree": {"questions": [
        {"id": "btr_1", "question": "二叉树的深度优先遍历不包括以下哪种？", "options": ["前序遍历", "中序遍历", "后序遍历", "层序遍历"], "correct": 3, "explanation": "深度优先遍历包括前序、中序、后序；层序遍历属于广度优先。", "difficulty": "easy", "bloom": "remember"},
        {"id": "btr_2", "question": "二叉树中，叶子节点的度为？", "options": ["0", "1", "2", "视情况而定"], "correct": 0, "explanation": "叶子节点没有子节点，所以度为0。", "difficulty": "easy", "bloom": "remember"},
        {"id": "btr_3", "question": "前序遍历中，根节点的访问顺序是？", "options": ["最后访问", "最先访问", "中间访问", "不确定"], "correct": 1, "explanation": "前序遍历的访问顺序是：根节点→左子树→右子树，根最先访问。", "difficulty": "easy", "bloom": "remember"},
        {"id": "btr_4", "question": "二叉树中n0=n2+1表示什么关系？", "options": ["叶子数=度2节点数+1", "度1节点数=度2节点数+1", "总节点数=叶子数+1", "叶子数=总节点数/2"], "correct": 0, "explanation": "二叉树性质：叶子节点数 = 度为2的节点数 + 1。", "difficulty": "medium", "bloom": "understand"},
        {"id": "btr_5", "question": "用二叉链表存储n个节点的二叉树，有多少个空指针？", "options": ["n", "n+1", "2n", "n-1"], "correct": 1, "explanation": "n个节点有2n个指针域，n-1条边各占一个指针，剩余2n-(n-1)=n+1个空指针。", "difficulty": "hard", "bloom": "analyze"},
    ]},
    "bst": {
        "questions": [
            {"id": "bst_1", "question": "二叉搜索树中序遍历的结果是？", "options": ["降序序列", "升序序列", "随机序列", "层序序列"], "correct": 1, "explanation": "二叉搜索树（左<根<右）中序遍历得到升序序列。", "difficulty": "easy", "bloom": "remember"},
            {"id": "bst_2", "question": "BST删除有两个子节点的节点时，通常用什么节点替换？", "options": ["左子树最大节点", "右子树最小节点", "父节点", "根节点"], "correct": 1, "explanation": "通常用右子树的最小节点（中序后继）替换，也可用左子树最大节点。", "difficulty": "medium", "bloom": "apply"},
            {"id": "bst_3", "question": "在最坏情况下，BST的查找时间复杂度退化为？", "options": ["O(1)", "O(log n)", "O(n)", "O(n²)"], "correct": 2, "explanation": "BST退化为链表时（插入有序序列），查找退化为O(n)。", "difficulty": "medium", "bloom": "understand"},
            {"id": "bst_4", "question": "向空BST依次插入5,3,7,2,4，树的形态是？", "options": ["左斜树", "右斜树", "平衡的二叉搜索树", "完全二叉树"], "correct": 2, "explanation": "5为根，3左4右，7右 → 树基本平衡。", "difficulty": "medium", "bloom": "apply"},
            {"id": "bst_5", "question": "如何验证一棵二叉树是BST？", "options": ["判断左<根<右每层成立", "中序遍历是否严格递增", "后序遍历是否有序", "层序遍历是否递增"], "correct": 1, "explanation": "BST的中序遍历序列必须是严格递增的，这是充要条件。", "difficulty": "hard", "bloom": "analyze"},
        ]
    },
    "avl": {"questions": [
        {"id": "avl_1", "question": "AVL树的平衡因子范围是？", "options": ["[-1, 1]", "[0, 2]", "[-2, 2]", "[0, 1]"], "correct": 0, "explanation": "AVL树的平衡因子（左右子树高度差）必须在-1到1之间。", "difficulty": "easy", "bloom": "remember"},
        {"id": "avl_2", "question": "AVL树中，LR旋转适用于什么场景？", "options": ["左左情况", "左右情况", "右左情况", "右右情况"], "correct": 1, "explanation": "LR旋转（先左旋后右旋）适用于插入节点在左子树的右子树导致失衡的情况。", "difficulty": "medium", "bloom": "understand"},
        {"id": "avl_3", "question": "AVL树查找的时间复杂度是？", "options": ["O(1)", "O(log n)", "O(n)", "O(n log n)"], "correct": 1, "explanation": "AVL树严格平衡，树高为O(log n)，查找也是O(log n)。", "difficulty": "easy", "bloom": "remember"},
        {"id": "avl_4", "question": "AVL树插入一个节点后最多需要几次旋转？", "options": ["1次", "2次", "O(log n)次", "O(n)次"], "correct": 1, "explanation": "AVL插入后最多需要2次旋转（如LR/RL需要先子旋转再父旋转）。", "difficulty": "medium", "bloom": "understand"},
        {"id": "avl_5", "question": "AVL树删除操作可能触发多少次旋转？", "options": ["1次", "2次", "O(log n)次", "O(n)次"], "correct": 2, "explanation": "AVL删除后可能引起祖先节点连续失衡，最坏需要O(log n)次旋转。", "difficulty": "hard", "bloom": "analyze"},
    ]},
    "rbtree": {"questions": [
        {"id": "rb_1", "question": "红黑树中以下哪个说法正确？", "options": ["根节点可以是红色", "红色节点的子节点必须是黑色", "所有叶子节点必须是红色", "相邻节点不能都是黑色"], "correct": 1, "explanation": "红黑树中红色节点的子节点必须是黑色（不能有连续红色节点）。", "difficulty": "easy", "bloom": "remember"},
        {"id": "rb_2", "question": "红黑树相比AVL树的主要优势是？", "options": ["查找更快", "完全平衡", "插入删除旋转次数更少", "内存占用更小"], "correct": 2, "explanation": "红黑树放宽平衡条件，插入删除时旋转操作更少，适合频繁写入场景。", "difficulty": "medium", "bloom": "understand"},
        {"id": "rb_3", "question": "红黑树的5条性质中，保证树高不超过O(log n)的关键是？", "options": ["根节点为黑", "红节点子节点为黑", "黑高度相同", "叶子节点为黑"], "correct": 2, "explanation": "任何路径的黑节点数相同（黑高度相同），限制了树高不超过2log(n+1)。", "difficulty": "medium", "bloom": "understand"},
        {"id": "rb_4", "question": "红黑树插入新节点时，默认颜色是？", "options": ["红色", "黑色", "随机", "取决于父节点"], "correct": 0, "explanation": "默认插入红色节点，因为插入红色可能只影响局部（违反性质4），修复代价小。", "difficulty": "medium", "bloom": "apply"},
        {"id": "rb_5", "question": "为什么数据库索引通常用B+树而不是红黑树？", "options": ["红黑树太高导致IO多", "红黑树查找太慢", "B+树更容易实现", "红黑树不能排序"], "correct": 0, "explanation": "B+树节点存储更多键，高度远小于红黑树，减少磁盘IO次数。", "difficulty": "hard", "bloom": "analyze"},
    ]},
    # ★ 保留合并别名
    "avl_rbtree": {"questions": [
        {"id": "avlrb_1", "question": "AVL树的平衡因子范围是？", "options": ["[-1, 1]", "[0, 2]", "[-2, 2]", "[0, 1]"], "correct": 0, "explanation": "AVL树的平衡因子必须在-1到1之间。"},
        {"id": "avlrb_2", "question": "红黑树中以下哪个说法正确？", "options": ["根节点可以是红色", "红色节点的子节点必须是黑色", "所有叶子节点必须是红色", "相邻节点不能都是黑色"], "correct": 1, "explanation": "红色节点的子节点必须是黑色。"},
        {"id": "avlrb_3", "question": "红黑树相比AVL树的主要优势是？", "options": ["查找更快", "完全平衡", "插入删除旋转次数更少", "内存占用更小"], "correct": 2, "explanation": "红黑树放宽平衡条件，旋转操作更少。"},
    ]},
    "heap": {
        "questions": [
            {"id": "hp_1", "question": "大顶堆的堆顶元素是？", "options": ["最大值", "最小值", "中间值", "随机值"], "correct": 0, "explanation": "大顶堆的堆顶（根节点）是最大值。", "difficulty": "easy", "bloom": "remember"},
            {"id": "hp_2", "question": "堆排序的时间复杂度是？", "options": ["O(n)", "O(n log n)", "O(n²)", "O(log n)"], "correct": 1, "explanation": "堆排序建堆O(n)，每次调整O(log n)，总体O(n log n)。", "difficulty": "easy", "bloom": "remember"},
            {"id": "hp_3", "question": "在堆中插入一个元素后，需要执行什么操作？", "options": ["下沉（sink）", "上浮（swim）", "旋转", "交换左右子树"], "correct": 1, "explanation": "插入元素放在末尾后，通过上浮操作（与父节点比较交换）恢复堆序。", "difficulty": "medium", "bloom": "understand"},
            {"id": "hp_4", "question": "优先队列的底层实现通常使用什么数据结构？", "options": ["链表", "数组", "堆", "树"], "correct": 2, "explanation": "堆提供了高效的插入（O(log n)）和取最大/最小值（O(1)），是优先队列的标准实现。", "difficulty": "medium", "bloom": "apply"},
            {"id": "hp_5", "question": "Top K 问题用小顶堆还是大顶堆更高效？", "options": ["大顶堆", "小顶堆", "都可以", "用排序更快"], "correct": 1, "explanation": "找最大K个用小顶堆（淘汰小的），时间复杂度O(n log k)优于排序的O(n log n)。", "difficulty": "hard", "bloom": "analyze"},
        ]
    },
    "bplus": {"questions": [
        {"id": "bp_1", "question": "B+树中，所有数据存储在什么位置？", "options": ["根节点", "内部节点", "叶子节点", "所有节点"], "correct": 2, "explanation": "B+树的所有数据都存储在叶子节点，内部节点只存储索引键。"},
        {"id": "bp_2", "question": "B+树的叶子节点之间通过什么连接？", "options": ["指针链表", "数组", "哈希表", "树形结构"], "correct": 0, "explanation": "B+树的叶子节点通过指针链接成有序链表，方便范围查询。"},
        {"id": "bp_3", "question": "现代数据库系统（如 InnoDB）的索引结构采用的是什么？", "options": ["B树", "B+树", "红黑树", "哈希表"], "correct": 1, "explanation": "现代数据库系统广泛使用 B+树作为索引结构，支持高效的范围查询和排序。"},
    ]},
    # ═══ 图 ═══
    "graph": {
        "questions": [
            {"id": "gr_1", "question": "图的深度优先搜索（DFS）使用什么数据结构辅助？", "options": ["队列", "栈", "数组", "链表"], "correct": 1, "explanation": "DFS使用栈（递归本质也是栈）实现，BFS使用队列。", "difficulty": "easy", "bloom": "remember"},
            {"id": "gr_2", "question": "一个有n个顶点的连通图至少有多少条边？", "options": ["n-1", "n", "n+1", "n²"], "correct": 0, "explanation": "连通图至少需要n-1条边（树形结构）。", "difficulty": "easy", "bloom": "understand"},
            {"id": "gr_3", "question": "邻接表和邻接矩阵的空间复杂度分别是？", "options": ["O(V+E)和O(V²)", "O(V²)和O(V+E)", "O(V)和O(E)", "O(E)和O(V)"], "correct": 0, "explanation": "邻接表O(V+E)，适合稀疏图；邻接矩阵O(V²)，适合稠密图。", "difficulty": "medium", "bloom": "understand"},
            {"id": "gr_4", "question": "一个有n个顶点的有向完全图有多少条边？", "options": ["n(n-1)", "n(n-1)/2", "n²", "n"], "correct": 0, "explanation": "有向完全图每对顶点之间都有两条方向相反的边，总边数为n(n-1)。", "difficulty": "medium", "bloom": "remember"},
            {"id": "gr_5", "question": "判断无向图中是否存在环，用DFS需要记录什么？", "options": ["visited数组", "parent参数避免回边", "stack栈", "以上都需要"], "correct": 3, "explanation": "需要visited数组标记已访问，parent避免回退，stack用于迭代实现。", "difficulty": "hard", "bloom": "analyze"},
            {"id": "gr_6", "question": "为什么Dijkstra不能处理负权边？", "options": ["算法太慢", "已确定最短路径可能被更新", "空间不够", "需要浮点数"], "correct": 1, "explanation": "Dijkstra每次确定一个顶点的最短路径后继不再考虑，但负权边可能使已确定路径变短。", "difficulty": "hard", "bloom": "analyze"},
        ]
    },
    # ★ 别名：graph_traversal → dfsbfs
    "graph_traversal": {"questions": [
        {"id": "gt_1", "question": "BFS遍历图时，最先被访问的节点是？", "options": ["入度最小的节点", "距离起点最近的节点", "权重最小的边连接的节点", "编号最小的节点"], "correct": 1, "explanation": "BFS按层遍历，距离起点越近越先访问。"},
        {"id": "gt_2", "question": "拓扑排序适用于？", "options": ["无向图", "有向无环图(DAG)", "完全图", "带权图"], "correct": 1, "explanation": "拓扑排序仅适用于有向无环图（DAG）。"},
        {"id": "gt_3", "question": "判断图中是否存在环，可以使用？", "options": ["仅BFS", "仅DFS", "DFS或拓扑排序", "仅Dijkstra"], "correct": 2, "explanation": "有向图可用DFS回溯边或拓扑排序判断环。"},
    ]},
    "dfsbfs": {"questions": [
        {"id": "dfs_1", "question": "BFS遍历图时使用的辅助数据结构是？", "options": ["栈", "队列", "数组", "堆"], "correct": 1, "explanation": "BFS使用队列实现广度优先的逐层遍历。"},
        {"id": "dfs_2", "question": "DFS的递归实现本质上依赖什么数据结构？", "options": ["队列", "系统调用栈", "数组", "链表"], "correct": 1, "explanation": "递归调用使用系统栈，DFS递归实现本质上依赖栈。"},
        {"id": "dfs_3", "question": "拓扑排序适用于什么类型的图？", "options": ["无向图", "有向无环图", "完全图", "带权图"], "correct": 1, "explanation": "拓扑排序只适用于有向无环图(DAG)。"},
    ]},
    # ★ 别名：shortest_path → spath
    "shortest_path": {"questions": [
        {"id": "sp_1", "question": "Dijkstra算法用于解决什么问题？", "options": ["单源最短路径", "多源最短路径", "最小生成树", "拓扑排序"], "correct": 0, "explanation": "Dijkstra算法解决非负权图的单源最短路径问题。"},
        {"id": "sp_2", "question": "Dijkstra算法不能处理以下哪种情况？", "options": ["无向图", "带权图", "负权边", "稠密图"], "correct": 2, "explanation": "Dijkstra假设已确定最短路径不会再被更新，负权边会破坏这个假设。"},
        {"id": "sp_3", "question": "Floyd-Warshall算法的时间复杂度是？", "options": ["O(V log V)", "O(V²)", "O(V³)", "O(VE)"], "correct": 2, "explanation": "Floyd三重循环，O(V³)，解决所有节点对最短路径。"},
    ]},
    "spath": {"questions": [
        {"id": "sp_1x", "question": "Dijkstra算法的核心思想是什么？", "options": ["分治", "贪心", "动态规划", "回溯"], "correct": 1, "explanation": "Dijkstra每次选择距离最短的未处理节点，是典型的贪心策略。"},
        {"id": "sp_2x", "question": "Floyd算法属于什么类型的算法？", "options": ["贪心", "分治", "动态规划", "回溯"], "correct": 2, "explanation": "Floyd算法通过逐步引入中间节点更新最短路径，属于动态规划。"},
        {"id": "sp_3x", "question": "Dijkstra算法用优先队列优化后的时间复杂度是？", "options": ["O(V²)", "O(E log V)", "O(V log V)", "O(VE)"], "correct": 1, "explanation": "用二叉堆/优先队列优化后，Dijkstra为O(E log V)。"},
    ]},
    "mst": {
        "questions": [
            {"id": "mst_1", "question": "Prim算法和Kruskal算法分别适合什么类型的图？", "options": ["都适合稀疏图", "都适合稠密图", "Prim适合稠密，Kruskal适合稀疏", "Prim适合稀疏，Kruskal适合稠密"], "correct": 2, "explanation": "Prim基于顶点扩展，适合稠密图；Kruskal基于边排序，适合稀疏图。"},
            {"id": "mst_2", "question": "Kruskal算法中，判断是否形成环使用什么数据结构？", "options": ["栈", "队列", "哈希表", "并查集"], "correct": 3, "explanation": "Kruskal使用并查集(Disjoint Set Union)判断加入边是否会形成环。"},
            {"id": "mst_3", "question": "一个连通图的最小生成树是唯一的吗？", "options": ["一定唯一", "一定不唯一", "当所有边权值不同时唯一", "与边数有关"], "correct": 2, "explanation": "当所有边权值都不相同时，MST唯一；有权值相同边时可能不唯一。"},
        ]
    },
    # ═══ 散列与查找 ═══
    # ★ 别名：hash_table → hash
    "hash_table": {"questions": [
        {"id": "hs_1", "question": "哈希表查找的平均时间复杂度是？", "options": ["O(1)", "O(n)", "O(log n)", "O(n²)"], "correct": 0, "explanation": "理想情况下哈希表查找为O(1)，但最坏情况可能退化为O(n)。"},
        {"id": "hs_2", "question": "解决哈希冲突的方法不包括？", "options": ["链地址法", "开放定址法", "再哈希法", "冒泡法"], "correct": 3, "explanation": "冒泡法是排序算法，不是解决哈希冲突的方法。"},
        {"id": "hs_3", "question": "哈希表的装载因子（load factor）过高时应该？", "options": ["减少key数量", "扩容并重新哈希", "增加冲突链长度", "更换哈希函数"], "correct": 1, "explanation": "装载因子过高时需扩容并rehash所有元素，以保持O(1)效率。"},
    ]},
    "hash": {"questions": [
        {"id": "h_1", "question": "哈希表的查找时间复杂度平均是？", "options": ["O(1)", "O(n)", "O(log n)", "O(n²)"], "correct": 0, "explanation": "哈希表通过哈希函数直接定位，平均O(1)。"},
        {"id": "h_2", "question": "链地址法中，哈希冲突的元素如何存储？", "options": ["存到下一个空位", "用链表链接", "用树存储", "丢弃"], "correct": 1, "explanation": "链地址法将冲突的元素链接在同一个哈希桶的链表上。"},
        {"id": "h_3", "question": "哈希表扩容时需要进行什么操作？", "options": ["丢弃旧数据", "全部重新哈希", "逐步迁移", "压缩数组"], "correct": 1, "explanation": "扩容后哈希表大小改变，所有元素需要重新计算哈希值再插入。"},
    ]},
    "skiplist": {"questions": [
        {"id": "sk_1", "question": "跳表是在什么数据结构上建立的？", "options": ["数组", "有序链表", "二叉树", "哈希表"], "correct": 1, "explanation": "跳表在有序链表的基础上建立多层索引。"},
        {"id": "sk_2", "question": "跳表的查找时间复杂度是？", "options": ["O(1)", "O(log n)", "O(n)", "O(n log n)"], "correct": 1, "explanation": "跳表通过多层索引实现O(log n)的查找效率。"},
        {"id": "sk_3", "question": "Redis中的有序集合（Sorted Set）底层使用了什么数据结构？", "options": ["B+树", "跳表", "红黑树", "哈希表"], "correct": 1, "explanation": "Redis ZSet 底层使用跳表+哈希表实现。"},
    ]},
    # ★ 别名：binary_search（无对应种子节点，保持独立）
    "binary_search": {"questions": [
        {"id": "bs_1", "question": "二分查找的前提条件是？", "options": ["数据有序", "数据存储在链表中", "数据量小于100", "数据是整数"], "correct": 0, "explanation": "二分查找要求数据有序（通常是升序），才能每次排除一半。"},
        {"id": "bs_2", "question": "二分查找的时间复杂度是？", "options": ["O(1)", "O(n)", "O(log n)", "O(n log n)"], "correct": 2, "explanation": "每次查找范围减半，O(log n)。"},
        {"id": "bs_3", "question": "在旋转排序数组中查找目标值，最佳时间复杂度是？", "options": ["O(n)", "O(log n)", "O(n log n)", "O(1)"], "correct": 1, "explanation": "旋转数组查找可通过变体二分实现O(log n)。"},
    ]},
    # ═══ 排序算法 ═══
    # ★ 别名：basic_sort → bsort
    "basic_sort": {"questions": [
        {"id": "bst_1", "question": "冒泡排序的最好时间复杂度是？", "options": ["O(n)", "O(n log n)", "O(n²)", "O(1)"], "correct": 0, "explanation": "优化后的冒泡排序在已排序情况下只需一次遍历，最好O(n)。"},
        {"id": "bst_2", "question": "以下哪种基础排序是稳定的？", "options": ["选择排序", "冒泡排序", "快速排序", "堆排序"], "correct": 1, "explanation": "冒泡排序和插入排序是稳定的。"},
        {"id": "bst_3", "question": "插入排序最适合什么场景？", "options": ["大规模乱序数据", "基本有序的小规模数据", "链式存储数据", "浮点数排序"], "correct": 1, "explanation": "插入排序在数据基本有序时效率极高（接近O(n)），也适合小数据量。"},
    ]},
    "bsort": {"questions": [
        {"id": "bsr_1", "question": "冒泡排序每趟排序的结果是？", "options": ["最小值移到最前", "最大值移到最后", "全部有序", "部分有序"], "correct": 1, "explanation": "冒泡排序每趟将当前未排序部分的最大值浮到末尾。"},
        {"id": "bsr_2", "question": "以下哪个是稳定排序？", "options": ["选择排序", "冒泡排序", "希尔排序", "快速排序"], "correct": 1, "explanation": "冒泡排序是稳定的，因为相等元素不会交换。"},
        {"id": "bsr_3", "question": "简单选择排序的时间复杂度是？", "options": ["O(n)", "O(n log n)", "O(n²)", "O(log n)"], "correct": 2, "explanation": "无论数据是否有序，选择排序都需要O(n²)的时间。"},
    ]},
    # ★ 别名：advanced_sort → asort
    "advanced_sort": {"questions": [
        {"id": "as_1", "question": "快速排序的平均时间复杂度是？", "options": ["O(n)", "O(n log n)", "O(n²)", "O(log n)"], "correct": 1, "explanation": "快速排序平均O(n log n)，最坏O(n²)。"},
        {"id": "as_2", "question": "以下哪种排序是稳定的？", "options": ["快速排序", "堆排序", "归并排序", "选择排序"], "correct": 2, "explanation": "归并排序是稳定的O(n log n)排序。"},
        {"id": "as_3", "question": "归并排序的空间复杂度是？", "options": ["O(1)", "O(log n)", "O(n)", "O(n²)"], "correct": 2, "explanation": "归并排序需要O(n)额外空间来合并有序数组。"},
    ]},
    "asort": {"questions": [
        {"id": "asr_1", "question": "快速排序在什么情况下时间复杂度最差？", "options": ["数据已有序", "数据随机分布", "数据完全逆序", "数据全部相等"], "correct": 0, "explanation": "已有序数据若选第一个为基准，分区极不平衡，退化为O(n²)。"},
        {"id": "asr_2", "question": "归并排序的核心思想是？", "options": ["分区交换", "分治合并", "堆选择", "希尔插入"], "correct": 1, "explanation": "归并排序采用分治策略，将数组分成两半分别排序后合并。"},
        {"id": "asr_3", "question": "堆排序中建堆的时间复杂度是？", "options": ["O(n)", "O(n log n)", "O(n²)", "O(log n)"], "correct": 0, "explanation": "建堆（从最后一个非叶子节点下沉）的时间复杂度为O(n)。"},
    ]},
    # ═══ 算法思想 ═══
    "dp": {
        "questions": [
            {"id": "dp_1", "question": "动态规划的核心思想是？", "options": ["分而治之", "记忆化搜索", "贪心选择", "暴力枚举"], "correct": 1, "explanation": "动态规划通过记录子问题解（记忆化）避免重复计算。"},
            {"id": "dp_2", "question": "斐波那契数列用动态规划优化后时间复杂度是？", "options": ["O(1)", "O(n)", "O(2ⁿ)", "O(log n)"], "correct": 1, "explanation": "使用DP的斐波那契为O(n)，而朴素递归为O(2ⁿ)。"},
            {"id": "dp_3", "question": "动态规划的两个核心要素是？", "options": ["分治和回溯", "最优子结构和重叠子问题", "贪心选择和局部最优", "递归和剪枝"], "correct": 1, "explanation": "最优子结构和重叠子问题是DP的标志。"},
        ]
    },
    # ★ 别名：recursion → recur
    "recursion": {"questions": [
        {"id": "rc_1", "question": "递归的两个基本要素是？", "options": ["循环和条件", "基准情形和递归公式", "入栈和出栈", "分治和合并"], "correct": 1, "explanation": "递归需要基准情形（终止条件）和递归公式。"},
        {"id": "rc_2", "question": "递归可能导致什么问题？", "options": ["数组越界", "栈溢出", "内存泄漏", "类型错误"], "correct": 1, "explanation": "递归过深会导致调用栈溢出（Stack Overflow）。"},
        {"id": "rc_3", "question": "分治算法的经典例子不包括？", "options": ["归并排序", "快速排序", "二分查找", "冒泡排序"], "correct": 3, "explanation": "冒泡排序没有'分而治之'的思想。"},
    ]},
    "recur": {"questions": [
        {"id": "rcr_1", "question": "递归必须包含的两个要素是？", "options": ["循环和条件", "基准情形和递归公式", "入栈和出栈", "分治和回溯"], "correct": 1, "explanation": "基准情形终止递归，递归公式缩小问题规模。"},
        {"id": "rcr_2", "question": "尾递归优化的目的是？", "options": ["提高速度", "减少栈空间使用", "增加可读性", "支持并行"], "correct": 1, "explanation": "尾递归优化将递归转换为循环，避免栈溢出。"},
        {"id": "rcr_3", "question": "Master定理用于分析什么？", "options": ["贪心算法复杂度", "分治算法复杂度", "动态规划复杂度", "搜索算法复杂度"], "correct": 1, "explanation": "Master定理（主定理）用于分析分治算法的时间复杂度。"},
    ]},
    "greedy": {
        "questions": [
            {"id": "gd_1", "question": "贪心算法的核心原则是？", "options": ["全局最优", "局部最优", "随机选择", "回溯尝试"], "correct": 1, "explanation": "贪心算法每一步都选择当前最优解（局部最优）。"},
            {"id": "gd_2", "question": "以下哪个问题适合用贪心算法解决？", "options": ["0-1背包", "活动选择", "最短路径（负权）", "旅行商"], "correct": 1, "explanation": "活动选择问题可以用贪心算法（最早结束时间优先）求解。"},
            {"id": "gd_3", "question": "贪心算法与动态规划的关键区别是？", "options": ["时间复杂度不同", "贪心不保留子问题解", "贪心不能处理重叠子问题", "贪心只做一次选择"], "correct": 1, "explanation": "贪心做出选择后不再回溯，不保留子问题解。"},
        ]
    },
    "backtr": {"questions": [
        {"id": "bk_1", "question": "回溯算法的核心思想是？", "options": ["分治", "试探+剪枝", "贪心", "动态规划"], "correct": 1, "explanation": "回溯通过递归试探所有可能，用剪枝排除无效分支。"},
        {"id": "bk_2", "question": "N皇后问题适合用什么算法解决？", "options": ["贪心", "回溯", "动态规划", "分治"], "correct": 1, "explanation": "N皇后需要枚举所有放置方案并检查冲突，适合回溯算法。"},
        {"id": "bk_3", "question": "在回溯中，'剪枝'的含义是？", "options": ["删除无用数据", "提前终止不可能的分支", "减少递归深度", "合并重复计算"], "correct": 1, "explanation": "剪枝是在递归过程中提前判断当前路径不可能产生解，从而停止探索。"},
    ]},
    "twoptr": {"questions": [
        {"id": "tp_1", "question": "对撞指针通常用于解决什么问题？", "options": ["有序数组的两数之和", "链表判环", "滑动窗口最大值", "字符串匹配"], "correct": 0, "explanation": "对撞指针（左右指针向中间移动）常用于有序数组中的两数之和等问题。"},
        {"id": "tp_2", "question": "快慢指针常用于解决什么问题？", "options": ["数组排序", "链表判环", "二分查找", "字符串匹配"], "correct": 1, "explanation": "快慢指针是判断链表是否有环的经典方法。"},
        {"id": "tp_3", "question": "滑动窗口算法的时间复杂度通常是？", "options": ["O(1)", "O(n)", "O(n²)", "O(log n)"], "correct": 1, "explanation": "滑动窗口每个元素最多被访问两次（进窗口和出窗口），O(n)。"},
    ]},
    "kmp": {"questions": [
        {"id": "km_1", "question": "KMP算法的核心思想是？", "options": ["暴力匹配", "利用前缀表跳过已匹配部分", "分治匹配", "贪心匹配"], "correct": 1, "explanation": "KMP通过预处理模式串的前缀函数，匹配失败时跳过已匹配部分。"},
        {"id": "km_2", "question": "KMP算法中next数组的含义是？", "options": ["下一个字符的位置", "最长相等前后缀长度", "匹配失败的位置", "模式串长度"], "correct": 1, "explanation": "next数组（前缀函数）记录了模式串每个位置的最长相等前后缀长度。"},
        {"id": "km_3", "question": "KMP算法的时间复杂度是？", "options": ["O(n*m)", "O(n+m)", "O(n log n)", "O(n²)"], "correct": 1, "explanation": "KMP算法预处理O(m)，匹配O(n)，总体O(n+m)。"},
    ]},
    "lru": {"questions": [
        {"id": "lru_1", "question": "LRU缓存淘汰策略淘汰的是哪个数据？", "options": ["最近最少使用的", "最早进入的", "使用频率最低的", "随机淘汰"], "correct": 0, "explanation": "LRU淘汰最近最少被访问的数据。"},
        {"id": "lru_2", "question": "LRU缓存的常用实现数据结构是？", "options": ["数组+指针", "哈希表+双向链表", "二叉搜索树", "堆"], "correct": 1, "explanation": "哈希表提供O(1)查找，双向链表提供O(1)插入删除。"},
        {"id": "lru_3", "question": "LRU中，访问已存在的数据时应该？", "options": ["删除数据", "移到链表头部", "移到链表尾部", "不做任何操作"], "correct": 1, "explanation": "访问已存在的数据时，将其移动到链表头部表示最近使用过。"},
    ]},
    "union": {"questions": [
        {"id": "uf_1", "question": "并查集的Find操作经过路径压缩后的时间复杂度趋近于？", "options": ["O(1)", "O(log n)", "O(n)", "O(α(n))"], "correct": 3, "explanation": "带路径压缩和按秩合并的并查集，每次操作接近O(α(n))（反阿克曼函数），近似常数。"},
        {"id": "uf_2", "question": "并查集Union操作按秩合并的含义是？", "options": ["随机合并", "将小树合并到大树", "按节点值大小合并", "按深度交替合并"], "correct": 1, "explanation": "按秩合并将深度较小的树合并到深度较大的树，控制树高。"},
        {"id": "uf_3", "question": "并查集经典应用场景不包括？", "options": ["连通分量", "Kruskal最小生成树", "拓扑排序", "朋友圈问题"], "correct": 2, "explanation": "拓扑排序通常使用入度表和队列，不是并查集的典型应用。"},
    ]},

    # ════════════════════════════════════════════
    # 第1章：绪论 题库
    # ════════════════════════════════════════════
    "ch01_data_concept": {"questions": [
        {"id": "c1dc_1", "question": "数据结构的三要素不包括以下哪一项？", "options": ["逻辑结构", "存储结构", "数据运算", "算法复杂度"], "correct": 3, "explanation": "数据结构三要素是：逻辑结构、存储结构和数据运算。"},
        {"id": "c1dc_2", "question": "以下哪种属于线性逻辑结构？", "options": ["树形结构", "图状结构", "线性表", "集合结构"], "correct": 2, "explanation": "线性表是最典型的线性逻辑结构，数据元素之间是一对一的线性关系。"},
        {"id": "c1dc_3", "question": "数据的存储结构不包括以下哪种？", "options": ["顺序存储", "链式存储", "索引存储", "树形存储"], "correct": 3, "explanation": "树形存储属于逻辑结构分类，存储结构包括顺序、链式、索引和散列四种。"},
    ]},
    "ch01_data_type": {"questions": [
        {"id": "c1dt_1", "question": "以下哪个是C语言的基本数据类型？", "options": ["数组", "结构体", "整型", "联合体"], "correct": 2, "explanation": "整型(int)是C语言的基本数据类型，数组、结构体、联合体属于构造数据类型。"},
        {"id": "c1dt_2", "question": "数据类型的本质含义是什么？", "options": ["内存大小", "值的集合+操作集合", "变量的名称", "存储位置"], "correct": 1, "explanation": "数据类型是一组性质相同的值的集合以及定义在此集合上的一组操作的总称。"},
        {"id": "c1dt_3", "question": "用typedef定义新类型名的作用是？", "options": ["创建新类型", "为已有类型起别名", "改变类型大小", "删除旧类型"], "correct": 1, "explanation": "typedef为已有数据类型创建新的别名，不产生新类型。"},
    ]},
    "ch01_adt": {"questions": [
        {"id": "c1adt_1", "question": "ADT的三元组表示是哪三个要素？", "options": ["数据对象、数据关系、基本操作", "数据结构、算法、程序", "输入、输出、处理", "数据、类型、操作"], "correct": 0, "explanation": "ADT使用三元组（数据对象、数据关系、基本操作）来描述。"},
        {"id": "c1adt_2", "question": "ADT关注的是？", "options": ["如何实现", "做什么（逻辑特性）", "如何存储", "效率优化"], "correct": 1, "explanation": "ADT的定义仅取决于其逻辑特性，与具体实现无关，关注'做什么'而非'怎么做'。"},
        {"id": "c1adt_3", "question": "以下哪个概念体现了ADT的封装思想？", "options": ["全局变量", "信息隐蔽", "宏定义", "goto语句"], "correct": 1, "explanation": "信息隐蔽（Information Hiding）是ADT和面向对象封装的核心思想。"},
    ]},
    "ch01_algorithm": {"questions": [
        {"id": "c1alg_1", "question": "算法的五个特性中，不包括以下哪项？", "options": ["有穷性", "确定性", "可读性", "可行性"], "correct": 2, "explanation": "算法的五个特性是：有穷性、确定性、可行性、输入、输出。"},
        {"id": "c1alg_2", "question": "以下哪个时间复杂度最优？", "options": ["O(n²)", "O(n)", "O(1)", "O(log n)"], "correct": 2, "explanation": "O(1)的时间复杂度表示常量时间，最优；其次依次是O(log n)、O(n)、O(n²)。"},
        {"id": "c1alg_3", "question": "分析算法时间复杂度时，大O记法表示的是？", "options": ["精确运行时间", "最坏情况的时间上界", "最好情况的时间", "平均时间"], "correct": 1, "explanation": "大O记法表示算法时间复杂度的渐进上界，通常指最坏情况。"},
    ]},
    # ════════════════════════════════════════════
    # 第2章：线性表 题库
    # ════════════════════════════════════════════
    "ch02_seq_list": {"questions": [
        {"id": "c2sl_1", "question": "顺序表的最大优点是？", "options": ["插入删除快", "随机存取", "空间利用率高", "动态扩展"], "correct": 1, "explanation": "顺序表支持O(1)时间复杂度的随机存取，这是它的主要优势。"},
        {"id": "c2sl_2", "question": "在顺序表第i个位置插入元素，平均需要移动多少个元素？", "options": ["n", "n-1", "n/2", "(n-1)/2"], "correct": 2, "explanation": "顺序表插入平均移动n/2个元素，时间复杂度O(n)。"},
        {"id": "c2sl_3", "question": "顺序表删除第i个元素后，需要执行什么操作？", "options": ["将后续元素前移", "将后续元素后移", "置空该位置", "重建整个表"], "correct": 0, "explanation": "删除第i个元素后，需将i之后的所有元素向前移动一个位置。"},
        {"id": "c2sl_4", "question": "动态顺序表扩容时，通常采用什么策略？", "options": ["每次增加1个单元", "每次翻倍", "每次增加固定大小", "不扩容"], "correct": 1, "explanation": "动态数组通常采用翻倍扩容策略，使得均摊时间复杂度为O(1)。"},
    ]},
    "ch02_linked_list": {"questions": [
        {"id": "c2ll_1", "question": "单链表中，已知某节点p，在其后插入新节点的时间复杂度是？", "options": ["O(1)", "O(n)", "O(log n)", "O(n²)"], "correct": 0, "explanation": "已知插入位置时，单链表插入为O(1)；查找需要O(n)。"},
        {"id": "c2ll_2", "question": "头插法创建链表，最终链表元素顺序与插入顺序的关系是？", "options": ["相同", "相反", "不确定", "部分相同"], "correct": 1, "explanation": "头插法每次将新节点插入头部，所以最终顺序与插入顺序相反。"},
        {"id": "c2ll_3", "question": "链表相比顺序表的主要优势是？", "options": ["随机访问快", "插入删除效率高", "占用内存少", "无需额外内存"], "correct": 1, "explanation": "链表的插入和删除只需要修改指针，不需要移动数据元素。"},
    ]},
    "ch02_doubly_list": {"questions": [
        {"id": "c2dl_1", "question": "双向链表每个节点包含几个指针域？", "options": ["1个", "2个", "3个", "4个"], "correct": 1, "explanation": "双向链表每个节点包含前驱指针prior和后继指针next，共2个指针域。"},
        {"id": "c2dl_2", "question": "在双向链表中删除已知节点p的时间复杂度是？", "options": ["O(1)", "O(n)", "O(log n)", "O(n²)"], "correct": 0, "explanation": "通过p->prior和p->next可直接修改前后节点的链接，无需遍历。"},
        {"id": "c2dl_3", "question": "双向链表相对单链表的主要优势是？", "options": ["节省内存", "支持双向遍历", "插入更快", "查找更快"], "correct": 1, "explanation": "双向链表可以向前和向后两个方向遍历，操作更灵活。"},
    ]},
    "ch02_circular_list": {"questions": [
        {"id": "c2cl_1", "question": "循环链表的尾节点指针指向哪里？", "options": ["NULL", "头节点", "自身", "随机地址"], "correct": 1, "explanation": "循环链表的尾节点next指针指向头节点，形成环状结构。"},
        {"id": "c2cl_2", "question": "循环链表适合解决什么问题？", "options": ["约瑟夫问题", "排序问题", "查找问题", "哈希冲突"], "correct": 0, "explanation": "循环链表适合约瑟夫环等需要循环遍历的场景。"},
        {"id": "c2cl_3", "question": "带头节点循环链表的判空条件是什么？", "options": ["head->next == NULL", "head->next == head", "head == NULL", "head->data == 0"], "correct": 1, "explanation": "带头节点循环链表为空时，头节点的next指向自身。"},
    ]},
    "ch02_static_list": {"questions": [
        {"id": "c2slt_1", "question": "静态链表使用什么来代替指针？", "options": ["游标（数组下标）", "哈希值", "地址值", "索引值"], "correct": 0, "explanation": "静态链表使用游标（数组下标）来代替指针，每个节点包含data和cursor字段。"},
        {"id": "c2slt_2", "question": "静态链表中的备用链表是什么？", "options": ["备份的链表", "空闲节点组成的链表", "另一种存储方式", "缓存链表"], "correct": 1, "explanation": "备用链表由数组中未使用的空间组成，插入节点时从备用链表分配。"},
        {"id": "c2slt_3", "question": "静态链表的优点是什么？", "options": ["随机存取", "支持在不支持指针的语言中使用", "动态扩容", "查找更快"], "correct": 1, "explanation": "静态链表用数组实现链式结构，适合不支持指针的高级语言。"},
    ]},
    # ════════════════════════════════════════════
    # 第3章：栈和队列 题库
    # ════════════════════════════════════════════
    "ch03_stack_basic": {"questions": [
        {"id": "c3sb_1", "question": "栈的特点是？", "options": ["先进先出", "先进后出", "随机访问", "双端操作"], "correct": 1, "explanation": "栈是LIFO（后进先出）结构，只能在栈顶操作。"},
        {"id": "c3sb_2", "question": "用栈实现括号匹配，遇到右括号应执行什么操作？", "options": ["入栈", "出栈并匹配", "清空栈", "忽略"], "correct": 1, "explanation": "遇到右括号时出栈一个左括号进行匹配，匹配失败则表达式不合法。"},
        {"id": "c3sb_3", "question": "递归函数调用时，每层调用的返回地址和数据保存在哪里？", "options": ["堆", "栈", "全局变量区", "代码区"], "correct": 1, "explanation": "函数调用通过系统调用栈保存返回地址和局部变量。"},
    ]},
    "ch03_seq_stack": {"questions": [
        {"id": "c3ss_1", "question": "顺序栈中，栈顶指针top通常指向？", "options": ["栈顶元素", "栈顶元素的下一个位置", "栈底元素", "随机位置"], "correct": 0, "explanation": "通常top指向栈顶元素，入栈时top+1，出栈时top-1。"},
        {"id": "c3ss_2", "question": "两个栈共享同一数组空间时，它们如何布局？", "options": ["都从中间开始", "从两端向中间生长", "从同侧生长", "随机分布"], "correct": 1, "explanation": "共享栈中，两个栈分别从数组的两端向中间生长，最大化空间利用率。"},
        {"id": "c3ss_3", "question": "顺序栈的栈满条件（top指向栈顶）是？", "options": ["top == -1", "top == MAX-1", "top == 0", "top == MAX"], "correct": 1, "explanation": "当栈顶指针top等于最大下标MAX-1时，表示栈满。"},
    ]},
    "ch03_chain_stack": {"questions": [
        {"id": "c3cs_1", "question": "链栈的入栈操作相当于在链表的什么位置插入？", "options": ["头部", "尾部", "中间", "随机位置"], "correct": 0, "explanation": "链栈的栈顶在链表头部，入栈相当于头插法。"},
        {"id": "c3cs_2", "question": "链栈相比顺序栈的优点是？", "options": ["查找更快", "不存在栈满问题", "随机存取", "节省空间"], "correct": 1, "explanation": "链栈空间可动态分配，不存在栈满问题。"},
        {"id": "c3cs_3", "question": "链栈出栈操作的时间复杂度是？", "options": ["O(1)", "O(n)", "O(log n)", "O(n²)"], "correct": 0, "explanation": "链栈出栈即删除头节点，只需修改栈顶指针，时间复杂度O(1)。"},
    ]},
    "ch03_queue_basic": {"questions": [
        {"id": "c3qb_1", "question": "队列的特点是？", "options": ["先进先出", "先进后出", "随机访问", "优先级排序"], "correct": 0, "explanation": "队列是FIFO（先进先出）结构，队尾入队，队头出队。"},
        {"id": "c3qb_2", "question": "BFS（广度优先搜索）使用什么数据结构辅助？", "options": ["栈", "队列", "数组", "堆"], "correct": 1, "explanation": "BFS利用队列的FIFO特性实现逐层遍历。"},
        {"id": "c3qb_3", "question": "队列在操作系统中常用于什么场景？", "options": ["进程调度", "内存分配", "文件系统", "中断处理"], "correct": 0, "explanation": "操作系统中的进程调度通常使用队列（就绪队列、等待队列等）。"},
    ]},
    "ch03_circular_queue": {"questions": [
        {"id": "c3cq_1", "question": "循环队列解决的主要问题是什么？", "options": ["空间不足", "假溢出", "入队慢", "查找慢"], "correct": 1, "explanation": "循环队列通过取模运算复用数组空间，解决顺序队列的假溢出问题。"},
        {"id": "c3cq_2", "question": "循环队列中，牺牲一个单元来区分队空队满时，队满的条件是？", "options": ["rear == front", "(rear+1)%max == front", "rear+1 == front", "rear == front+1"], "correct": 1, "explanation": "牺牲一个单元时，队满条件为(rear+1)%max == front，队空条件为rear == front。"},
        {"id": "c3cq_3", "question": "循环队列中，队列长度的计算方法是？", "options": ["rear-front", "(rear-front+max)%max", "rear-front+1", "max-(rear-front)"], "correct": 1, "explanation": "循环队列长度 = (rear - front + max) % max。"},
    ]},
    "ch03_chain_queue": {"questions": [
        {"id": "c3chq_1", "question": "链队列需要设置几个指针？", "options": ["1个", "2个", "3个", "4个"], "correct": 1, "explanation": "链队列需要队头指针front和队尾指针rear两个指针。"},
        {"id": "c3chq_2", "question": "链队列入队操作在哪个位置进行？", "options": ["队头", "队尾", "中间", "随机"], "correct": 1, "explanation": "入队在队尾插入，修改rear指针；出队在队头删除。"},
        {"id": "c3chq_3", "question": "带头节点的链队列为空的条件是？", "options": ["front == NULL", "front->next == NULL && rear == front", "rear == NULL", "rear == front"], "correct": 1, "explanation": "带头节点链队列为空时，front指向头节点，rear指向头节点，front->next == NULL。"},
    ]},
    # ════════════════════════════════════════════
    # 第4章：串、数组和广义表 题库
    # ════════════════════════════════════════════
    "ch04_string": {"questions": [
        {"id": "c4s_1", "question": "空串和空格串的区别是？", "options": ["没有区别", "空串不含任何字符，空格串含空格", "空串含空格，空格串不含", "空串长度为1"], "correct": 1, "explanation": "空串长度为0，不包含任何字符；空格串只包含空格字符。"},
        {"id": "c4s_2", "question": "设主串S='abcdef'，则S的子串个数为？", "options": ["15", "21", "22", "16"], "correct": 2, "explanation": "n个字符的串有n(n+1)/2+1个子串（包含空串），6×7/2+1=22。"},
        {"id": "c4s_3", "question": "C语言中字符串以什么字符结尾？", "options": ["\\n", "\\0", "\\t", "EOF"], "correct": 1, "explanation": "C语言字符串以空字符'\\0'结尾。"},
    ]},
    "ch04_pattern_match": {"questions": [
        {"id": "c4pm_1", "question": "KMP算法的核心思想是什么？", "options": ["暴力匹配", "利用前缀函数跳过已匹配部分", "分治匹配", "贪心匹配"], "correct": 1, "explanation": "KMP通过预处理模式串的前缀函数，在匹配失败时跳过已匹配部分。"},
        {"id": "c4pm_2", "question": "BF算法的时间复杂度是？", "options": ["O(n+m)", "O(n*m)", "O(n log m)", "O(n²)"], "correct": 1, "explanation": "BF算法最坏情况下需要O(n*m)的时间，n为主串长度，m为模式串长度。"},
        {"id": "c4pm_3", "question": "模式串'abaab'的next数组值（从1开始）是多少？", "options": ["01112", "01123", "00112", "01234"], "correct": 1, "explanation": "手动计算KMP的next数组：'abaab'的next值为0,1,1,2,3（下标从1开始）。"},
        {"id": "c4pm_4", "question": "KMP算法中next[j]的含义是？", "options": ["第j个字符的值", "j位置前的最长相等前后缀长度", "模式串长度", "主串位置"], "correct": 1, "explanation": "next[j]表示在j位置失配时，模式串应回溯到的位置，即j之前的最长相等前后缀长度。"},
    ]},
    "ch04_array": {"questions": [
        {"id": "c4arr_1", "question": "二维数组按行优先存储时，a[i][j]的地址计算公式是？", "options": ["a+(i*n+j)*len", "a+(j*m+i)*len", "a+(i+j)*len", "a+i*j*len"], "correct": 0, "explanation": "行优先存储：a[i][j] = 基地址 + (i*列数+j)×每个元素大小。"},
        {"id": "c4arr_2", "question": "三维数组按页优先存储，a[2][3][4]的地址计算复杂度是？", "options": ["O(1)", "O(n)", "O(n²)", "O(log n)"], "correct": 0, "explanation": "数组地址计算是O(1)的常量时间计算。"},
        {"id": "c4arr_3", "question": "对称矩阵的压缩存储通常采用什么方式？", "options": ["只存上三角", "只存下三角(含主对角线)", "只存对角线", "用链表存储"], "correct": 1, "explanation": "对称矩阵通常只存储下三角（含主对角线）元素，节省约一半空间。"},
    ]},
    "ch04_sparse_matrix": {"questions": [
        {"id": "c4sm_1", "question": "稀疏矩阵的三元组表示包含哪三个字段？", "options": ["行、列、值", "行、值、指针", "列、值、指针", "索引、行、列"], "correct": 0, "explanation": "三元组（row, col, value）表示稀疏矩阵中非零元素的行号、列号和值。"},
        {"id": "c4sm_2", "question": "十字链表中，每个非零元素节点包含几个指针域？", "options": ["1个", "2个", "3个", "4个"], "correct": 1, "explanation": "十字链表每个非零元素节点包含指向同一行下一个元素和同一列下一个元素的两个指针。"},
        {"id": "c4sm_3", "question": "稀疏矩阵压缩存储的意义是？", "options": ["加快计算", "节省存储空间", "提高精度", "便于编程"], "correct": 1, "explanation": "稀疏矩阵通过只存储非零元素来显著节省存储空间。"},
    ]},
    "ch04_generalized_list": {"questions": [
        {"id": "c4gl_1", "question": "广义表LS = (a, (b, c), d)的深度是多少？", "options": ["1", "2", "3", "4"], "correct": 1, "explanation": "广义表的深度等于嵌套的最大层数，该表中(b,c)深度为2，整体深度为2。"},
        {"id": "c4gl_2", "question": "广义表的GetHead(GetTail((a,b,c)))的结果是？", "options": ["a", "b", "c", "(b,c)"], "correct": 1, "explanation": "GetTail((a,b,c))=(b,c)，GetHead((b,c))=b。"},
        {"id": "c4gl_3", "question": "广义表与线性表的主要区别是？", "options": ["元素类型不同", "广义表的元素可以是子表", "广义表长度不限", "没有区别"], "correct": 1, "explanation": "广义表是线性表的推广，其元素可以是原子或另一个广义表（子表）。"},
    ]},
    # ════════════════════════════════════════════
    # 第5章：树和二叉树 题库
    # ════════════════════════════════════════════
    "ch05_tree_basic": {"questions": [
        {"id": "c5tb_1", "question": "一棵树的度是指？", "options": ["树的深度", "树中节点的最大度", "树中节点的总数", "叶子节点的个数"], "correct": 1, "explanation": "树的度是树中所有节点度的最大值。"},
        {"id": "c5tb_2", "question": "树的深度（高度）是指？", "options": ["叶子节点数", "节点的最大层数", "节点总数", "分支数"], "correct": 1, "explanation": "树的深度（高度）是树中节点的最大层数（层次数）。"},
        {"id": "c5tb_3", "question": "将森林转换为二叉树的核心规则是？", "options": ["兄弟相连，左孩子右兄弟", "随机转换", "先序遍历", "后序遍历"], "correct": 0, "explanation": "森林转二叉树：将每棵树的根节点用右指针连接（兄弟相连），左指针指第一个孩子。"},
    ]},
    "ch05_binary_tree": {"questions": [
        {"id": "c5bt_1", "question": "深度为h的二叉树最多有多少个节点？", "options": ["2^h", "2^h-1", "2^(h-1)", "2^(h+1)-1"], "correct": 1, "explanation": "深度为h的二叉树最多有2^h-1个节点（满二叉树）。"},
        {"id": "c5bt_2", "question": "完全二叉树中，度为1的节点数最多为？", "options": ["0个", "1个", "2个", "不确定"], "correct": 1, "explanation": "完全二叉树中最多只有一个度为1的节点。"},
        {"id": "c5bt_3", "question": "一棵有n个节点的完全二叉树，其深度（高度）为？", "options": ["log₂n", "⌊log₂n⌋+1", "⌈log₂n⌉", "n/2"], "correct": 1, "explanation": "完全二叉树的深度为⌊log₂n⌋+1。"},
    ]},
    "ch05_tree_traversal": {"questions": [
        {"id": "c5tt_1", "question": "前序遍历的访问顺序是？", "options": ["根左右", "左根右", "左右根", "层序"], "correct": 0, "explanation": "前序遍历（先序遍历）：先访问根节点，再遍历左子树，最后遍历右子树。"},
        {"id": "c5tt_2", "question": "已知二叉树前序序列为ABDECF，中序序列为DBEAFC，其后序序列是？", "options": ["DEBFCA", "DEBAFC", "ABDECF", "DBEAFC"], "correct": 0, "explanation": "前序定根，中序分左右。根为A，左子树DBE，右子树FC。递归分析得后序DEBFCA。"},
        {"id": "c5tt_3", "question": "二叉树层序遍历使用的辅助数据结构是？", "options": ["栈", "队列", "数组", "链表"], "correct": 1, "explanation": "层序遍历使用队列，依次将当前节点的左右孩子入队。"},
    ]},
    "ch05_threaded_tree": {"questions": [
        {"id": "c5th_1", "question": "线索二叉树中，ltag=1表示什么含义？", "options": ["左指针指向左孩子", "左指针指向前驱线索", "右指针指向右孩子", "右指针指向后继线索"], "correct": 1, "explanation": "ltag=1表示左指针指向前驱线索，ltag=0表示左指针指向左孩子。"},
        {"id": "c5th_2", "question": "中序线索二叉树的第一个节点如何找到？", "options": ["遍历所有节点", "从根节点沿左指针一直向左", "从根节点沿右指针向右", "随机选择"], "correct": 1, "explanation": "中序线索二叉树的第一个（最左）节点：从根节点沿左指针一直向左，直到ltag=1。"},
        {"id": "c5th_3", "question": "线索二叉树的主要优势是？", "options": ["节省内存", "遍历不需要递归或栈", "插入删除快", "查找更快"], "correct": 1, "explanation": "线索二叉树利用空指针存放线索，使遍历可以在O(n)时间内直接找到前驱后继。"},
    ]},
    "ch05_huffman": {"questions": [
        {"id": "c5hf_1", "question": "哈夫曼树的WPL是指？", "options": ["树的高度", "所有叶子节点的带权路径长度之和", "所有节点的权值之和", "路径长度之和"], "correct": 1, "explanation": "WPL（带权路径长度）是所有叶子节点的权值与路径长度乘积之和。"},
        {"id": "c5hf_2", "question": "哈夫曼树的构造过程中，每次选择什么节点合并？", "options": ["权值最大的两个", "权值最小的两个", "深度最小的两个", "随机的两个"], "correct": 1, "explanation": "哈夫曼算法每次选择两个权值最小的节点作为左右子树构造新节点。"},
        {"id": "c5hf_3", "question": "哈夫曼编码的特点是？", "options": ["等长编码", "前缀编码（无二义性）", "有歧义编码", "变长但不唯一译码"], "correct": 1, "explanation": "哈夫曼编码是前缀编码，任何一个编码都不是另一个编码的前缀，可唯一译码。"},
    ]},
    # ════════════════════════════════════════════
    # 第6章：图 题库
    # ════════════════════════════════════════════
    "ch06_graph_concept": {"questions": [
        {"id": "c6gc_1", "question": "一个有n个顶点的无向连通图至少有多少条边？", "options": ["n", "n-1", "n+1", "n(n-1)/2"], "correct": 1, "explanation": "n个顶点的无向连通图至少需要n-1条边（树形结构）。"},
        {"id": "c6gc_2", "question": "顶点的度在无向图中表示什么？", "options": ["出度", "入度", "与该顶点相连的边数", "该顶点能到达的顶点数"], "correct": 2, "explanation": "无向图中，顶点的度是关联在该顶点的边数。"},
        {"id": "c6gc_3", "question": "一个有n个顶点的有向完全图有多少条边？", "options": ["n(n-1)", "n(n-1)/2", "n²", "n"], "correct": 0, "explanation": "有向完全图每对顶点之间都有两条方向相反的边，总边数为n(n-1)。"},
    ]},
    "ch06_graph_storage": {"questions": [
        {"id": "c6gs_1", "question": "邻接矩阵的空间复杂度是？", "options": ["O(V+E)", "O(V²)", "O(E)", "O(V)"], "correct": 1, "explanation": "邻接矩阵使用V×V的二维数组，空间复杂度O(V²)。"},
        {"id": "c6gs_2", "question": "邻接表的空间复杂度是？", "options": ["O(V+E)", "O(V²)", "O(V×E)", "O(E)"], "correct": 0, "explanation": "邻接表空间复杂度O(V+E)，V个顶点表头加上E条边。"},
        {"id": "c6gs_3", "question": "稠密图应该使用什么存储结构？", "options": ["邻接表", "邻接矩阵", "十字链表", "逆邻接表"], "correct": 1, "explanation": "稠密图边数接近V²，用邻接矩阵更合适。"},
    ]},
    "ch06_dfs": {"questions": [
        {"id": "c6dfs_1", "question": "DFS（深度优先搜索）使用的辅助数据结构是？", "options": ["队列", "栈（递归本质也是栈）", "数组", "链表"], "correct": 1, "explanation": "DFS使用栈实现，递归实现本质也是系统调用栈。"},
        {"id": "c6dfs_2", "question": "DFS可以应用于以下哪些场景？", "options": ["求无权图最短路径", "连通分量检测", "拓扑排序（仅限DAG）", "以上都可以"], "correct": 3, "explanation": "DFS可应用于连通分量检测、环检测、拓扑排序（DAG）、二分图判定等。"},
        {"id": "c6dfs_3", "question": "DFS遍历连通图的时间复杂度（邻接表存储）是？", "options": ["O(V)", "O(V+E)", "O(V²)", "O(E)"], "correct": 1, "explanation": "邻接表存储时，DFS需要访问所有顶点一次、每条边一次，时间复杂度O(V+E)。"},
    ]},
    "ch06_bfs": {"questions": [
        {"id": "c6bfs_1", "question": "BFS（广度优先搜索）使用的辅助数据结构是？", "options": ["栈", "队列", "数组", "堆"], "correct": 1, "explanation": "BFS使用队列实现，保证按距离递增逐层访问。"},
        {"id": "c6bfs_2", "question": "BFS在无权图中首次到达终点的路径是什么？", "options": ["最长路径", "最短路径（边数最少）", "随机路径", "加权最短路径"], "correct": 1, "explanation": "BFS按层扩展，第一次到达终点时即为最短路径（边数最少）。"},
        {"id": "c6bfs_3", "question": "使用BFS进行拓扑排序的算法通常称为什么？", "options": ["Kahn算法", "Dijkstra算法", "Floyd算法", "Prim算法"], "correct": 0, "explanation": "Kahn算法使用BFS思想，通过计算入度来进行拓扑排序。"},
    ]},
    "ch06_mst": {"questions": [
        {"id": "c6mst_1", "question": "Prim算法和Kruskal算法分别适合什么类型的图？", "options": ["都适合稀疏图", "都适合稠密图", "Prim适合稠密，Kruskal适合稀疏", "Prim适合稀疏，Kruskal适合稠密"], "correct": 2, "explanation": "Prim基于顶点扩展，适合稠密图；Kruskal基于边排序，适合稀疏图。"},
        {"id": "c6mst_2", "question": "Kruskal算法中，判断是否形成环使用什么数据结构？", "options": ["栈", "队列", "哈希表", "并查集"], "correct": 3, "explanation": "Kruskal使用并查集判断加入边是否形成环。"},
        {"id": "c6mst_3", "question": "一个连通图的最小生成树是唯一的吗？", "options": ["一定唯一", "一定不唯一", "当所有边权值不同时唯一", "与边数有关"], "correct": 2, "explanation": "当所有边权值都不相同时，MST唯一；有权值相同边时可能不唯一。"},
    ]},
    "ch06_shortest_path": {"questions": [
        {"id": "c6sp_1", "question": "Dijkstra算法的核心思想是什么？", "options": ["分治", "贪心", "动态规划", "回溯"], "correct": 1, "explanation": "Dijkstra每次选择距离最短的未处理节点，是典型的贪心策略。"},
        {"id": "c6sp_2", "question": "Dijkstra算法不能处理以下哪种情况？", "options": ["无向图", "带权图", "负权边", "稠密图"], "correct": 2, "explanation": "Dijkstra假设已确定最短路径不会再被更新，负权边会破坏这个假设。"},
        {"id": "c6sp_3", "question": "Floyd-Warshall算法的时间复杂度是？", "options": ["O(V log V)", "O(V²)", "O(V³)", "O(VE)"], "correct": 2, "explanation": "Floyd三重循环，O(V³)，解决所有节点对最短路径。"},
    ]},
    "ch06_topo_sort": {"questions": [
        {"id": "c6ts_1", "question": "拓扑排序适用于什么类型的图？", "options": ["无向图", "有向无环图（DAG）", "完全图", "带权图"], "correct": 1, "explanation": "拓扑排序只适用于有向无环图（DAG）。"},
        {"id": "c6ts_2", "question": "Kahn算法进行拓扑排序的核心思想是？", "options": ["每次删除出度为0的顶点", "每次删除入度为0的顶点", "DFS后序遍历", "BFS层序遍历"], "correct": 1, "explanation": "Kahn算法重复删除入度为0的顶点及其出边，直到所有顶点被处理。"},
        {"id": "c6ts_3", "question": "如果一个有向图无法完成拓扑排序，说明什么？", "options": ["图不连通", "图中存在环", "图不是DAG", "B和C都对"], "correct": 3, "explanation": "只有DAG才能进行拓扑排序，无法完成说明图中存在环。"},
    ]},
    # ════════════════════════════════════════════
    # 第7章：查找 题库
    # ════════════════════════════════════════════
    "ch07_seq_search": {"questions": [
        {"id": "c7ss_1", "question": "顺序查找的平均查找长度ASL（查找成功时）是？", "options": ["(n+1)/2", "n/2", "n", "(n-1)/2"], "correct": 0, "explanation": "等概率情况下，顺序查找成功时ASL=(n+1)/2。"},
        {"id": "c7ss_2", "question": "顺序查找设置哨兵优化时，哨兵放在什么位置？", "options": ["表头", "表尾", "表中间", "随机位置"], "correct": 0, "explanation": "哨兵放在表头（或表尾），可以省去越界判断，减少比较次数。"},
        {"id": "c7ss_3", "question": "顺序查找的时间复杂度是？", "options": ["O(1)", "O(n)", "O(log n)", "O(n²)"], "correct": 1, "explanation": "顺序查找最坏和平均时间复杂度都为O(n)。"},
    ]},
    "ch07_binary_search": {"questions": [
        {"id": "c7bs_1", "question": "折半查找的前提条件是？", "options": ["数据有序且顺序存储", "数据存储在链表中", "数据量小于100", "数据是整数"], "correct": 0, "explanation": "折半查找要求数据有序（升序），且采用顺序存储结构。"},
        {"id": "c7bs_2", "question": "折半查找的时间复杂度是？", "options": ["O(1)", "O(n)", "O(log n)", "O(n log n)"], "correct": 2, "explanation": "每次查找范围减半，时间复杂度O(log n)。"},
        {"id": "c7bs_3", "question": "长度为11的有序表进行折半查找，查找成功的平均查找长度ASL是？", "options": ["25/11", "33/11", "20/11", "30/11"], "correct": 1, "explanation": "构造判定树：第1层1个(比较1次)，第2层2个(各2次)，第3层4个(各3次)，第4层4个(各4次)，ASL=(1+2×2+4×3+4×4)/11=33/11。"},
    ]},
    "ch07_block_search": {"questions": [
        {"id": "c7blk_1", "question": "分块查找中，块内数据的特点是？", "options": ["有序", "无序", "完全随机", "降序"], "correct": 1, "explanation": "分块查找中，块内数据可以无序，但块间必须有序。"},
        {"id": "c7blk_2", "question": "分块查找的索引表中记录了什么信息？", "options": ["每块的最大关键字和起始位置", "每块的所有元素", "每块的平均值", "每块的长度"], "correct": 0, "explanation": "索引表存储每块的最大关键字和起始位置，用于快速定位目标元素所在的块。"},
        {"id": "c7blk_3", "question": "分块查找的时间复杂度大致为？", "options": ["O(n)", "O(log n)", "O(√n)", "O(n log n)"], "correct": 2, "explanation": "当块数=√n，块内大小=√n时，分块查找ASL≈√n+1，O(√n)。"},
    ]},
    "ch07_bst_search": {"questions": [
        {"id": "c7bst_1", "question": "二叉排序树中序遍历得到的结果是？", "options": ["降序序列", "升序序列", "随机序列", "层序序列"], "correct": 1, "explanation": "二叉排序树（左<根<右）中序遍历得到递增有序序列。"},
        {"id": "c7bst_2", "question": "BST删除有两个子节点的节点时，通常用什么节点替换？", "options": ["左子树最大节点或右子树最小节点", "父节点", "根节点", "任意叶子节点"], "correct": 0, "explanation": "通常用右子树的最小节点（中序后继）或左子树的最大节点（中序前驱）替换。"},
        {"id": "c7bst_3", "question": "最坏情况下BST的查找时间复杂度退化为？", "options": ["O(1)", "O(log n)", "O(n)", "O(n²)"], "correct": 2, "explanation": "BST退化为链表时（插入有序序列），查找退化为O(n)。"},
    ]},
    "ch07_hash_search": {"questions": [
        {"id": "c7hs_1", "question": "哈希查找的平均时间复杂度是？", "options": ["O(1)", "O(n)", "O(log n)", "O(n²)"], "correct": 0, "explanation": "理想情况下哈希查找为O(1)，但最坏情况可能退化为O(n)。"},
        {"id": "c7hs_2", "question": "解决哈希冲突的方法不包括以下哪项？", "options": ["链地址法", "开放定址法", "再哈希法", "冒泡法"], "correct": 3, "explanation": "冒泡法是排序算法，不是解决哈希冲突的方法。"},
        {"id": "c7hs_3", "question": "哈希表的装填因子（load factor）过高时应该？", "options": ["减少key数量", "扩容并重新哈希", "增加冲突链长度", "更换哈希函数"], "correct": 1, "explanation": "装填因子过高时需扩容并rehash所有元素，以保持O(1)效率。"},
    ]},
    # ════════════════════════════════════════════
    # 第8章：排序 题库
    # ════════════════════════════════════════════
    "ch08_insert_sort": {"questions": [
        {"id": "c8is_1", "question": "直接插入排序的最好时间复杂度是？", "options": ["O(n)", "O(n log n)", "O(n²)", "O(1)"], "correct": 0, "explanation": "直接插入排序在数据基本有序时只需比较，无需移动，最好O(n)。"},
        {"id": "c8is_2", "question": "直接插入排序是稳定的吗？", "options": ["稳定", "不稳定", "视情况而定", "不确定"], "correct": 0, "explanation": "直接插入排序将后一元素插入到有序序列中相等元素后面，是稳定排序。"},
        {"id": "c8is_3", "question": "折半插入排序相比直接插入排序优化了什么？", "options": ["减少了移动次数", "减少了比较次数", "同时减少了比较和移动", "空间复杂度更低"], "correct": 1, "explanation": "折半插入用二分查找优化了查找插入位置的时间，但移动次数不变。"},
    ]},
    "ch08_shell_sort": {"questions": [
        {"id": "c8sh_1", "question": "希尔排序的原理是什么？", "options": ["逐步缩小增量进行插入排序", "相邻元素两两比较", "分治递归", "堆选择"], "correct": 0, "explanation": "希尔排序按增量将序列分组，每组内进行插入排序，逐步缩小增量。"},
        {"id": "c8sh_2", "question": "希尔排序是稳定的吗？", "options": ["稳定", "不稳定", "视增量选择而定", "不确定"], "correct": 1, "explanation": "希尔排序中相同元素可能被分配到不同子序列，是不稳定的。"},
        {"id": "c8sh_3", "question": "希尔排序的时间复杂度约为？", "options": ["O(n)", "O(n log n)", "O(n^1.3)", "O(n²)"], "correct": 2, "explanation": "希尔排序的时间复杂度约O(n^1.3)，具体依赖于增量序列的选择。"},
    ]},
    "ch08_bubble_sort": {"questions": [
        {"id": "c8bb_1", "question": "冒泡排序的最好时间复杂度（优化后）是？", "options": ["O(n)", "O(n log n)", "O(n²)", "O(1)"], "correct": 0, "explanation": "优化冒泡排序设置交换标志，已有序时只需一次遍历，最好O(n)。"},
        {"id": "c8bb_2", "question": "冒泡排序每趟排序的结果是？", "options": ["最小值移到最前", "最大值移到最后", "全部有序", "部分有序"], "correct": 1, "explanation": "冒泡排序每趟将当前未排序部分的最大值浮到末尾。"},
        {"id": "c8bb_3", "question": "以下哪项不是冒泡排序的特点？", "options": ["稳定排序", "相邻比较", "分治思想", "可优化提前结束"], "correct": 2, "explanation": "冒泡排序是简单的比较排序，没有采用分治思想。"},
    ]},
    "ch08_quick_sort": {"questions": [
        {"id": "c8qs_1", "question": "快速排序的平均时间复杂度是？", "options": ["O(n)", "O(n log n)", "O(n²)", "O(log n)"], "correct": 1, "explanation": "快排平均时间复杂度O(n log n)，最坏O(n²)。"},
        {"id": "c8qs_2", "question": "快速排序在什么情况下时间复杂度最差？", "options": ["数据已有序且选择第一个为基准", "数据随机分布", "数据全部相等", "数据量大"], "correct": 0, "explanation": "已有序时若选第一个为基准，分区极不平衡，退化为O(n²)。"},
        {"id": "c8qs_3", "question": "快速排序是稳定的吗？", "options": ["稳定", "不稳定", "视实现方式而定", "不确定"], "correct": 1, "explanation": "快速排序在分区过程中可能改变相等元素的相对顺序，是不稳定的。"},
    ]},
    "ch08_selection_sort": {"questions": [
        {"id": "c8ss_1", "question": "简单选择排序的时间复杂度是？", "options": ["O(n)", "O(n log n)", "O(n²)", "O(log n)"], "correct": 2, "explanation": "无论数据是否有序，简单选择排序都需要O(n²)时间。"},
        {"id": "c8ss_2", "question": "简单选择排序是稳定的吗？", "options": ["稳定", "不稳定", "视实现而定", "不确定"], "correct": 1, "explanation": "选择排序可能将相等元素的顺序改变，是不稳定的。"},
        {"id": "c8ss_3", "question": "简单选择排序每趟选出什么？", "options": ["最大值", "最小值", "中位数", "平均值"], "correct": 1, "explanation": "简单选择排序每趟从待排序序列中选出最小值放到已排序序列末尾。"},
    ]},
    "ch08_heap_sort": {"questions": [
        {"id": "c8hs_1", "question": "堆排序中建堆的时间复杂度是？", "options": ["O(n)", "O(n log n)", "O(n²)", "O(log n)"], "correct": 0, "explanation": "建堆（从最后一个非叶子节点开始向下调整）的时间复杂度为O(n)。"},
        {"id": "c8hs_2", "question": "堆排序的时间复杂度是？", "options": ["O(n)", "O(n log n)", "O(n²)", "O(log n)"], "correct": 1, "explanation": "建堆O(n)，每次调整O(log n)，总体O(n log n)。"},
        {"id": "c8hs_3", "question": "大顶堆的堆顶元素是？", "options": ["最大值", "最小值", "中位数", "任意值"], "correct": 0, "explanation": "大顶堆的堆顶（根节点）是整个堆中的最大值。"},
    ]},
    "ch08_merge_sort": {"questions": [
        {"id": "c8ms_1", "question": "归并排序的核心思想是？", "options": ["分区交换", "分治合并", "堆选择", "希尔插入"], "correct": 1, "explanation": "归并排序采用分治策略，将数组分成两半分别排序后合并。"},
        {"id": "c8ms_2", "question": "归并排序的空间复杂度是？", "options": ["O(1)", "O(log n)", "O(n)", "O(n²)"], "correct": 2, "explanation": "归并排序需要O(n)额外空间来合并有序数组。"},
        {"id": "c8ms_3", "question": "归并排序是以下哪种排序？", "options": ["稳定排序", "不稳定排序", "原地排序", "比较排序但非稳定"], "correct": 0, "explanation": "归并排序是稳定排序，也是O(n log n)的比较排序。"},
    ]},
    "ch08_radix_sort": {"questions": [
        {"id": "c8rs_1", "question": "基数排序属于什么类型的排序？", "options": ["比较排序", "非比较排序", "交换排序", "选择排序"], "correct": 1, "explanation": "基数排序不基于比较，而是基于关键字位的分配和收集。"},
        {"id": "c8rs_2", "question": "基数排序的时间复杂度是？", "options": ["O(n log n)", "O(d(n+r))", "O(n²)", "O(n)"], "correct": 1, "explanation": "d为关键字位数，n为元素个数，r为基数（进制），时间复杂度O(d(n+r))。"},
        {"id": "c8rs_3", "question": "LSD基数排序的排序顺序是？", "options": ["从高位到低位", "从低位到高位", "随机顺序", "按权重"], "correct": 1, "explanation": "LSD（Least Significant Digit）从最低位开始，逐位分配到最高位。"},
    ]},
# ════════════════════════════════════════════
# 混合题型扩展（填空 + 编程），追加到对应章节题库
# ════════════════════════════════════════════
"ch02_seq_list__blank_coding": {"questions": [
    {"id": "c2sl_bl1", "type": "blank", "question": "顺序表插入操作的平均时间复杂度是 O(____)。", "blank_answer": "n", "explanation": "插入平均需移动n/2个元素，故O(n)。", "difficulty": "easy", "bloom": "remember"},
    {"id": "c2sl_bl2", "type": "blank", "question": "顺序表查找第i个元素的时间复杂度是 O(____)。", "blank_answer": "1", "explanation": "顺序表支持随机存取，O(1)。", "difficulty": "easy", "bloom": "remember"},
    {"id": "c2sl_co1", "type": "coding", "question": "请实现顺序表的插入操作insert(arr, pos, val)，在数组指定位置插入元素（不考虑扩容）。", "coding_template": "def insert(arr, pos, val):\n    # 在arr的第pos位置插入val\n    pass", "blank_answer": "def insert(arr, pos, val):\n    arr.append(0)\n    for i in range(len(arr)-2, pos-1, -1):\n        arr[i+1] = arr[i]\n    arr[pos] = val", "explanation": "从末尾开始，将pos之后元素依次后移一位，再赋值。", "difficulty": "medium", "bloom": "apply"},
]},
"ch02_linked_list__blank_coding": {"questions": [
    {"id": "c2ll_bl1", "type": "blank", "question": "单链表中，已知节点p，在p之后插入新节点需要修改 ____ 个指针。", "blank_answer": "2", "explanation": "新节点next指向p.next(1)，p.next指向新节点(1)，共修改2个指针。", "difficulty": "easy", "bloom": "remember"},
    {"id": "c2ll_bl2", "type": "blank", "question": "反转单链表的迭代法时间复杂度为 O(____)。", "blank_answer": "n", "explanation": "遍历一次链表，逐个修改指针方向，O(n)。", "difficulty": "easy", "bloom": "understand"},
    {"id": "c2ll_co1", "type": "coding", "question": "请实现单链表的反转函数reverseList(head)，返回反转后的头节点。", "coding_template": "class ListNode:\n    def __init__(self, val=0, next=None):\n        self.val = val\n        self.next = next\n\ndef reverseList(head):\n    # 反转链表，返回新头节点\n    pass", "blank_answer": "def reverseList(head):\n    prev = None\n    curr = head\n    while curr:\n        nxt = curr.next\n        curr.next = prev\n        prev = curr\n        curr = nxt\n    return prev", "explanation": "遍历链表，逐个修改节点的next指针指向前驱。", "difficulty": "medium", "bloom": "apply"},
]},
"ch03_stack_basic__blank_coding": {"questions": [
    {"id": "c3sb_bl1", "type": "blank", "question": "栈的操作遵循 ____ 原则。", "blank_answer": "后进先出", "explanation": "栈是LIFO（Last In First Out，后进先出）结构。", "difficulty": "easy", "bloom": "remember"},
    {"id": "c3sb_bl2", "type": "blank", "question": "入栈序列为1,2,3，则可能的出栈序列共有 ____ 种。", "blank_answer": "5", "explanation": "可能的出栈序列：123,132,213,231,321共5种（卡特兰数C3=5）。312不可能。", "difficulty": "medium", "bloom": "apply"},
    {"id": "c3sb_co1", "type": "coding", "question": "请实现栈的push和pop操作（用列表模拟），并实现isValid(s)函数判断括号字符串是否有效。", "coding_template": "def isValid(s):\n    # 判断括号字符串'()[]{}'是否有效\n    pass", "blank_answer": "def isValid(s):\n    stack = []\n    pair = {')': '(', ']': '[', '}': '{'}\n    for ch in s:\n        if ch in '([{':\n            stack.append(ch)\n        elif not stack or stack.pop() != pair[ch]:\n            return False\n    return len(stack) == 0", "explanation": "用栈：左括号入栈，右括号匹配栈顶。最后栈空则有效。", "difficulty": "medium", "bloom": "apply"},
]},
"ch03_queue_basic__blank_coding": {"questions": [
    {"id": "c3qb_bl1", "type": "blank", "question": "队列的操作遵循 ____ 原则。", "blank_answer": "先进先出", "explanation": "队列是FIFO（First In First Out，先进先出）结构。", "difficulty": "easy", "bloom": "remember"},
    {"id": "c3qb_bl2", "type": "blank", "question": "循环队列中，队满条件是 (rear+1) % maxSize ____ front。", "blank_answer": "==", "explanation": "牺牲一个单元时，队满条件为(rear+1)%max==front。", "difficulty": "medium", "bloom": "remember"},
    {"id": "c3qb_co1", "type": "coding", "question": "请实现用两个栈模拟队列的MyQueue类（push和pop操作）。", "coding_template": "class MyQueue:\n    def __init__(self):\n        self.s1 = []\n        self.s2 = []\n    def push(self, x):\n        pass\n    def pop(self):\n        pass", "blank_answer": "class MyQueue:\n    def __init__(self):\n        self.s1 = []\n        self.s2 = []\n    def push(self, x):\n        self.s1.append(x)\n    def pop(self):\n        if not self.s2:\n            while self.s1:\n                self.s2.append(self.s1.pop())\n        return self.s2.pop()", "explanation": "入队push到s1；出队时若s2空，把s1全部倒入s2，再从s2 pop。", "difficulty": "medium", "bloom": "apply"},
]},
"ch05_tree_basic__blank_coding": {"questions": [
    {"id": "c5tb_bl1", "type": "blank", "question": "深度为k的二叉树最多有 ____ 个节点。", "blank_answer": "2^k-1", "explanation": "深度为k的满二叉树节点数=2^0+2^1+...+2^(k-1)=2^k-1。", "difficulty": "easy", "bloom": "remember"},
    {"id": "c5tb_bl2", "type": "blank", "question": "二叉树的第i层最多有 ____ 个节点。", "blank_answer": "2^(i-1)", "explanation": "二叉树第i层最多2^(i-1)个节点。", "difficulty": "easy", "bloom": "remember"},
    {"id": "c5tb_co1", "type": "coding", "question": "请实现二叉树的前序遍历（递归版），返回节点值列表。", "coding_template": "class TreeNode:\n    def __init__(self, val=0, left=None, right=None):\n        self.val = val\n        self.left = left\n        self.right = right\n\ndef preorder(root):\n    # 前序遍历：根→左→右\n    pass", "blank_answer": "def preorder(root):\n    if not root:\n        return []\n    return [root.val] + preorder(root.left) + preorder(root.right)", "explanation": "前序：先访问根，再递归左子树，最后右子树。", "difficulty": "medium", "bloom": "apply"},
]},
"ch06_graph_concept__blank_coding": {"questions": [
    {"id": "c6gc_bl1", "type": "blank", "question": "n个顶点的无向完全图有 ____ 条边。", "blank_answer": "n(n-1)/2", "explanation": "无向完全图每对顶点间都有一条边，总数C(n,2)=n(n-1)/2。", "difficulty": "easy", "bloom": "remember"},
    {"id": "c6gc_bl2", "type": "blank", "question": "有n个顶点的连通无向图至少有 ____ 条边。", "blank_answer": "n-1", "explanation": "最少需要n-1条边构成一棵树来连通所有顶点。", "difficulty": "easy", "bloom": "understand"},
    {"id": "c6gc_co1", "type": "coding", "question": "请实现图的DFS遍历函数（邻接表存储），返回遍历序列。", "coding_template": "def dfs(graph, start):\n    # graph: 邻接表 {顶点: [邻接顶点列表]}\n    # 返回遍历序列\n    pass", "blank_answer": "def dfs(graph, start):\n    visited = set()\n    result = []\n    def helper(node):\n        visited.add(node)\n        result.append(node)\n        for nei in graph.get(node, []):\n            if nei not in visited:\n                helper(nei)\n    helper(start)\n    return result", "explanation": "DFS递归实现：访问当前节点，标记已访问，递归遍历未访问的邻接点。", "difficulty": "medium", "bloom": "apply"},
]},
"ch08_quick_sort__blank_coding": {"questions": [
    {"id": "c8qs_bl1", "type": "blank", "question": "快速排序的平均时间复杂度是 O(____)。", "blank_answer": "n log n", "explanation": "快排平均O(n log n)，最坏退化为O(n²)。", "difficulty": "easy", "bloom": "remember"},
    {"id": "c8qs_bl2", "type": "blank", "question": "快速排序最坏情况下时间复杂度退化到 O(____)。", "blank_answer": "n^2", "explanation": "每次选取的基准为最值时，退化为O(n²)。", "difficulty": "medium", "bloom": "understand"},
    {"id": "c8qs_co1", "type": "coding", "question": "请实现快速排序的partition函数（Lomuto分区方案），返回基准的最终位置。", "coding_template": "def partition(arr, lo, hi):\n    # 以arr[hi]为基准\n    pass\n\ndef quicksort(arr, lo, hi):\n    if lo < hi:\n        p = partition(arr, lo, hi)\n        quicksort(arr, lo, p-1)\n        quicksort(arr, p+1, hi)", "blank_answer": "def partition(arr, lo, hi):\n    pivot = arr[hi]\n    i = lo - 1\n    for j in range(lo, hi):\n        if arr[j] < pivot:\n            i += 1\n            arr[i], arr[j] = arr[j], arr[i]\n    arr[i+1], arr[hi] = arr[hi], arr[i+1]\n    return i + 1", "explanation": "遍历[lo,hi)，小于基准的交换到左边。最后基准放入中间位置。", "difficulty": "medium", "bloom": "apply"},
]},
"ch07_binary_search__blank_coding": {"questions": [
    {"id": "c7bs_bl1", "type": "blank", "question": "折半查找（二分查找）的时间复杂度是 O(____)。", "blank_answer": "log n", "explanation": "每次查找范围减半，O(log n)。", "difficulty": "easy", "bloom": "remember"},
    {"id": "c7bs_bl2", "type": "blank", "question": "在有序数组[1,3,5,7,9,11]中查找5，需要比较 ____ 次。", "blank_answer": "1", "explanation": "mid=(0+5)/2=2，arr[2]=5，第一次比较即命中。", "difficulty": "easy", "bloom": "apply"},
    {"id": "c7bs_co1", "type": "coding", "question": "请实现二分查找函数binary_search(arr, target)，返回目标索引，不存在返回-1。", "coding_template": "def binary_search(arr, target):\n    # arr是有序递增数组\n    # 返回target的索引，不存在返回-1\n    pass", "blank_answer": "def binary_search(arr, target):\n    lo, hi = 0, len(arr) - 1\n    while lo <= hi:\n        mid = (lo + hi) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            lo = mid + 1\n        else:\n            hi = mid - 1\n    return -1", "explanation": "每次取中间元素比较，等于则返回，小于则搜索右半，大于则搜索左半。", "difficulty": "medium", "bloom": "apply"},
]},
"ch01_algorithm__blank_coding": {"questions": [
    {"id": "c1alg_bl1", "type": "blank", "question": "算法必须在有限步骤后结束，这一性质称为 ____。", "blank_answer": "有穷性", "accepted_answers": ["有穷性", "有限性"], "explanation": "有穷性要求算法执行有限步后终止。", "difficulty": "easy", "bloom": "remember"},
    {"id": "c1alg_bl2", "type": "blank", "question": "若一个循环每次把问题规模减半，其时间复杂度通常为 O(____)。", "blank_answer": "log n", "accepted_answers": ["log n", "logn", "log2n"], "explanation": "问题规模连续减半，执行次数与 log n 成正比。", "difficulty": "medium", "bloom": "understand"},
    {"id": "c1alg_co1", "type": "coding", "question": "请实现 linear_search(arr, target)，顺序扫描数组并返回目标下标，不存在时返回 -1。", "coding_template": "def linear_search(arr, target):\n    # 返回 target 的下标，不存在返回 -1\n    pass", "blank_answer": "def linear_search(arr, target):\n    for i, value in enumerate(arr):\n        if value == target:\n            return i\n    return -1", "required_tokens": ["linear_search", "for", "return"], "explanation": "顺序查找从头到尾扫描，最坏时间复杂度为 O(n)。", "difficulty": "medium", "bloom": "apply"},
]},
"ch06_shortest_path__blank_coding": {"questions": [
    {"id": "c6sp_bl1", "type": "blank", "question": "Dijkstra 算法不能直接处理含有 ____ 权边的图。", "blank_answer": "负", "accepted_answers": ["负", "负权", "负数"], "explanation": "负权边会破坏 Dijkstra 贪心选择的正确性。", "difficulty": "easy", "bloom": "remember"},
    {"id": "c6sp_bl2", "type": "blank", "question": "Floyd 算法解决的是 ____ 最短路径问题。", "blank_answer": "多源", "accepted_answers": ["多源", "所有顶点对", "全源"], "explanation": "Floyd 使用动态规划求任意两点之间的最短距离。", "difficulty": "medium", "bloom": "understand"},
    {"id": "c6sp_co1", "type": "coding", "question": "请实现 relax(dist, u, v, weight)，若经过 u 到 v 的路径更短则更新 dist[v] 并返回 True，否则返回 False。", "coding_template": "def relax(dist, u, v, weight):\n    # dist 是顶点到当前源点的距离字典\n    pass", "blank_answer": "def relax(dist, u, v, weight):\n    if dist[u] + weight < dist[v]:\n        dist[v] = dist[u] + weight\n        return True\n    return False", "required_tokens": ["relax", "dist", "weight", "return"], "explanation": "松弛操作比较当前距离与经过 u 的新距离，并保留较小值。", "difficulty": "medium", "bloom": "apply"},
]},
}

# ★ 合并：将 __blank_coding 后缀的混合题追加到对应节点
_MIXED_SUFFIX = "__blank_coding"
for key in list(NODE_EXAMS.keys()):
    if key.endswith(_MIXED_SUFFIX):
        base_key = key[: -len(_MIXED_SUFFIX)]
        if base_key in NODE_EXAMS:
            NODE_EXAMS[base_key]["questions"].extend(NODE_EXAMS[key]["questions"])
        else:
            NODE_EXAMS[base_key] = NODE_EXAMS[key]
        del NODE_EXAMS[key]

# 编程模式的离线精选题。即使 LLM 或网络不可用，每个入口也至少有多道代码题。
CODING_MODE_FALLBACKS = {
    "ch01_algorithm": [
        {"id": "c1alg_co2", "type": "coding", "question": "实现 find_max(arr)，在不调用 max() 的前提下返回非空数组最大值。", "coding_template": "def find_max(arr):\n    pass", "blank_answer": "def find_max(arr):\n    best = arr[0]\n    for value in arr[1:]:\n        if value > best:\n            best = value\n    return best", "required_tokens": ["find_max", "for", "return"], "explanation": "维护当前最大值并线性扫描，时间 O(n)、空间 O(1)。", "difficulty": "easy", "bloom": "apply"},
    ],
    "ch02_seq_list": [
        {"id": "c2sl_co2", "type": "coding", "question": "实现 delete_at(arr, pos)，删除顺序表指定下标的元素并返回被删除值。", "coding_template": "def delete_at(arr, pos):\n    pass", "blank_answer": "def delete_at(arr, pos):\n    if pos < 0 or pos >= len(arr):\n        raise IndexError('pos out of range')\n    value = arr[pos]\n    for i in range(pos, len(arr) - 1):\n        arr[i] = arr[i + 1]\n    arr.pop()\n    return value", "required_tokens": ["delete_at", "pop", "return"], "explanation": "删除后把后续元素前移，时间复杂度 O(n)。", "difficulty": "medium", "bloom": "apply"},
    ],
    "ch02_linked_list": [
        {"id": "c2ll_co2", "type": "coding", "question": "实现 has_cycle(head)，使用快慢指针判断单链表是否有环。", "coding_template": "def has_cycle(head):\n    pass", "blank_answer": "def has_cycle(head):\n    slow = fast = head\n    while fast and fast.next:\n        slow = slow.next\n        fast = fast.next.next\n        if slow is fast:\n            return True\n    return False", "required_tokens": ["has_cycle", "while", "fast", "slow", "return"], "explanation": "若存在环，快指针最终会追上慢指针；空间复杂度 O(1)。", "difficulty": "medium", "bloom": "apply"},
    ],
    "ch03_stack_basic": [
        {"id": "c3sb_co2", "type": "coding", "question": "实现 eval_postfix(tokens)，计算只含整数和 +、-、*、/ 的后缀表达式。", "coding_template": "def eval_postfix(tokens):\n    pass", "blank_answer": "def eval_postfix(tokens):\n    stack = []\n    for token in tokens:\n        if token not in {'+', '-', '*', '/'}:\n            stack.append(int(token))\n            continue\n        b, a = stack.pop(), stack.pop()\n        stack.append({'+': a+b, '-': a-b, '*': a*b, '/': int(a/b)}[token])\n    return stack[-1]", "required_tokens": ["eval_postfix", "stack", "pop", "return"], "explanation": "遇到数字入栈，遇到运算符弹出两个操作数计算后再入栈。", "difficulty": "hard", "bloom": "apply"},
    ],
    "ch03_queue_basic": [
        {"id": "c3qb_co2", "type": "coding", "question": "实现 queue_round(items, k)，把队首元素依次移到队尾 k 次并返回新顺序。", "coding_template": "def queue_round(items, k):\n    pass", "blank_answer": "from collections import deque\n\ndef queue_round(items, k):\n    queue = deque(items)\n    if queue:\n        queue.rotate(-(k % len(queue)))\n    return list(queue)", "required_tokens": ["queue_round", "queue", "return"], "explanation": "队列轮转可以用 deque 的 rotate 实现。", "difficulty": "medium", "bloom": "apply"},
    ],
    "ch05_tree_basic": [
        {"id": "c5tb_co2", "type": "coding", "question": "实现 tree_height(root)，返回二叉树高度，空树高度为 0。", "coding_template": "def tree_height(root):\n    pass", "blank_answer": "def tree_height(root):\n    if root is None:\n        return 0\n    return 1 + max(tree_height(root.left), tree_height(root.right))", "required_tokens": ["tree_height", "root.left", "root.right", "return"], "explanation": "树高等于左右子树最大高度加 1。", "difficulty": "medium", "bloom": "apply"},
    ],
    "ch06_graph_concept": [
        {"id": "c6gc_co2", "type": "coding", "question": "实现 bfs(graph, start)，按邻接表顺序返回广度优先遍历结果。", "coding_template": "def bfs(graph, start):\n    pass", "blank_answer": "from collections import deque\n\ndef bfs(graph, start):\n    queue = deque([start])\n    visited = {start}\n    result = []\n    while queue:\n        node = queue.popleft()\n        result.append(node)\n        for nxt in graph.get(node, []):\n            if nxt not in visited:\n                visited.add(nxt)\n                queue.append(nxt)\n    return result", "required_tokens": ["bfs", "queue", "visited", "return"], "explanation": "BFS 使用队列逐层访问，并用集合避免重复访问。", "difficulty": "medium", "bloom": "apply"},
    ],
    "ch06_shortest_path": [
        {"id": "c6sp_co2", "type": "coding", "question": "实现 path_cost(path, weights)，计算路径中相邻顶点边权之和。", "coding_template": "def path_cost(path, weights):\n    pass", "blank_answer": "def path_cost(path, weights):\n    total = 0\n    for u, v in zip(path, path[1:]):\n        total += weights[(u, v)]\n    return total", "required_tokens": ["path_cost", "weights", "for", "return"], "explanation": "遍历路径中的每条边并累加边权。", "difficulty": "easy", "bloom": "apply"},
    ],
    "ch08_quick_sort": [
        {"id": "c8qs_co2", "type": "coding", "question": "实现 quick_sort(values)，返回一个新的升序数组，不修改输入。", "coding_template": "def quick_sort(values):\n    pass", "blank_answer": "def quick_sort(values):\n    if len(values) <= 1:\n        return values[:]\n    pivot = values[len(values) // 2]\n    left = [x for x in values if x < pivot]\n    middle = [x for x in values if x == pivot]\n    right = [x for x in values if x > pivot]\n    return quick_sort(left) + middle + quick_sort(right)", "required_tokens": ["quick_sort", "pivot", "return"], "explanation": "按基准划分为小于、等于和大于三组后递归合并。", "difficulty": "medium", "bloom": "apply"},
    ],
    "ch07_binary_search": [
        {"id": "c7bs_co2", "type": "coding", "question": "实现 lower_bound(arr, target)，返回第一个大于等于 target 的下标。", "coding_template": "def lower_bound(arr, target):\n    pass", "blank_answer": "def lower_bound(arr, target):\n    left, right = 0, len(arr)\n    while left < right:\n        mid = (left + right) // 2\n        if arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid\n    return left", "required_tokens": ["lower_bound", "while", "mid", "return"], "explanation": "维护左闭右开区间，最终 left 即第一个不小于 target 的位置。", "difficulty": "hard", "bloom": "apply"},
    ],
}

# 第三组离线编程题，保证断网或 LLM 不可用时每个编程入口仍有完整训练量。
CODING_MODE_EXTRA_FALLBACKS = {
    "ch01_algorithm": [
        {"id": "c1alg_co3", "type": "coding", "question": "实现 count_occurrences(arr, target)，统计 target 在数组中出现的次数。", "coding_template": "def count_occurrences(arr, target):\n    pass", "blank_answer": "def count_occurrences(arr, target):\n    count = 0\n    for value in arr:\n        if value == target:\n            count += 1\n    return count", "required_tokens": ["count_occurrences", "for", "if", "return"], "explanation": "线性扫描并维护计数器，时间复杂度 O(n)，额外空间 O(1)。", "difficulty": "easy", "bloom": "apply"},
    ],
    "ch02_linked_list": [
        {"id": "c2ll_co3", "type": "coding", "question": "实现 middle_node(head)，使用快慢指针返回单链表的中间节点；偶数长度时返回后一个中间节点。", "coding_template": "def middle_node(head):\n    pass", "blank_answer": "def middle_node(head):\n    slow = fast = head\n    while fast and fast.next:\n        slow = slow.next\n        fast = fast.next.next\n    return slow", "required_tokens": ["middle_node", "slow", "fast", "while", "return"], "explanation": "快指针每次走两步、慢指针走一步，快指针到达末尾时慢指针位于中点。", "difficulty": "medium", "bloom": "apply"},
    ],
    "ch05_tree_basic": [
        {"id": "c5tb_co3", "type": "coding", "question": "实现 count_nodes(root)，递归统计二叉树的节点总数。", "coding_template": "def count_nodes(root):\n    pass", "blank_answer": "def count_nodes(root):\n    if root is None:\n        return 0\n    return 1 + count_nodes(root.left) + count_nodes(root.right)", "required_tokens": ["count_nodes", "root.left", "root.right", "return"], "explanation": "节点总数等于根节点 1 加左右子树节点数，空树返回 0。", "difficulty": "easy", "bloom": "apply"},
    ],
    "ch06_graph_concept": [
        {"id": "c6gc_co3", "type": "coding", "question": "实现 dfs(graph, start)，按邻接表顺序返回从 start 开始的深度优先遍历结果。", "coding_template": "def dfs(graph, start):\n    pass", "blank_answer": "def dfs(graph, start):\n    visited = set()\n    result = []\n\n    def visit(node):\n        if node in visited:\n            return\n        visited.add(node)\n        result.append(node)\n        for nxt in graph.get(node, []):\n            visit(nxt)\n\n    visit(start)\n    return result", "required_tokens": ["dfs", "visited", "for", "return"], "explanation": "DFS 沿一条路径深入后回溯，并使用 visited 防止环导致重复访问。", "difficulty": "medium", "bloom": "apply"},
    ],
    "ch08_quick_sort": [
        {"id": "c8qs_co3", "type": "coding", "question": "实现 three_way_partition(values, pivot)，返回小于、等于和大于 pivot 的三个列表。", "coding_template": "def three_way_partition(values, pivot):\n    pass", "blank_answer": "def three_way_partition(values, pivot):\n    less, equal, greater = [], [], []\n    for value in values:\n        if value < pivot:\n            less.append(value)\n        elif value == pivot:\n            equal.append(value)\n        else:\n            greater.append(value)\n    return less, equal, greater", "required_tokens": ["three_way_partition", "for", "if", "return"], "explanation": "三路划分能集中处理重复基准值，是快速排序处理大量重复元素的常见优化。", "difficulty": "medium", "bloom": "apply"},
    ],
    "ch07_binary_search": [
        {"id": "c7bs_co3", "type": "coding", "question": "实现 first_occurrence(arr, target)，在有序数组中返回 target 第一次出现的下标，不存在返回 -1。", "coding_template": "def first_occurrence(arr, target):\n    pass", "blank_answer": "def first_occurrence(arr, target):\n    left, right = 0, len(arr) - 1\n    answer = -1\n    while left <= right:\n        mid = (left + right) // 2\n        if arr[mid] >= target:\n            if arr[mid] == target:\n                answer = mid\n            right = mid - 1\n        else:\n            left = mid + 1\n    return answer", "required_tokens": ["first_occurrence", "while", "mid", "return"], "explanation": "命中后继续收缩右边界，从而定位最左侧的目标元素。", "difficulty": "hard", "bloom": "apply"},
    ],
    "ch06_shortest_path": [
        {"id": "c6sp_co3", "type": "coding", "question": "实现 reconstruct_path(previous, target)，根据最短路算法记录的前驱字典还原从源点到 target 的路径。", "coding_template": "def reconstruct_path(previous, target):\n    pass", "blank_answer": "def reconstruct_path(previous, target):\n    path = []\n    current = target\n    while current is not None:\n        path.append(current)\n        current = previous.get(current)\n    path.reverse()\n    return path", "required_tokens": ["reconstruct_path", "while", "previous", "reverse", "return"], "explanation": "从目标点沿前驱链逆向回溯，再反转即可得到源点到目标点的正向路径。", "difficulty": "medium", "bloom": "apply"},
    ],
}

for coding_bank in (CODING_MODE_FALLBACKS, CODING_MODE_EXTRA_FALLBACKS):
    for node_key, coding_questions in coding_bank.items():
        NODE_EXAMS.setdefault(node_key, {"questions": []})["questions"].extend(coding_questions)

DEFAULT_EXAM = {
    "questions": [
        {"id": "default_1", "question": "数据结构与算法的关系中，以下说法正确的是？", "options": ["数据结构决定算法效率", "算法与数据结构无关", "只有高级数据结构才需要算法", "算法复杂度总是O(1)"], "correct": 0, "explanation": "数据结构的选择直接影响算法的效率，好的数据结构是高效算法的基础。"},
        {"id": "default_2", "question": "算法的时间复杂度中，O(log n)表示？", "options": ["线性增长", "对数增长", "指数增长", "常数时间"], "correct": 1, "explanation": "O(log n)表示对数时间复杂度，常见于二分查找、平衡树等算法。"},
        {"id": "default_3", "question": "空间换时间的设计思想体现在？", "options": ["用更少内存提速", "用额外存储减少时间开销", "完全不使用内存", "只使用CPU缓存"], "correct": 1, "explanation": "哈希表、动态规划的记忆化等都是典型的空间换时间策略。"},
    ]
}


# ════════════════════════════════════════════════════════
# ★ 基于知识库的题目生成
# ════════════════════════════════════════════════════════

EXAM_KB_PROMPT = """你是一位教育专家。请根据知识库参考资料，为知识点"{node_title}"生成{question_count}道混合练习题。

## 知识库参考资料
{rag_context}

## 要求
1. 题目必须严格基于知识库内容，考察对资料的理解和掌握
2. 题型必须包含 choice（选择）、blank（填空）、coding（Python编程），至少各1题
3. choice 必须有4个选项和整数 correct；blank 必须有 blank_answer；coding 必须有 coding_template 和 blank_answer（参考代码）
4. 每题附带简要解释，编程题应考察可实际编写的核心操作
5. 难度适中，优先用知识库中的概念出题，不要编造

## 输出格式（严格JSON数组，不要输出任何其他文字）
[
  {{
    "id": "{node_id}_kb_1",
    "type": "choice",
    "question": "题目内容",
    "options": ["A选项", "B选项", "C选项", "D选项"],
    "correct": 0,
    "explanation": "简要解释"
  }},
  {{
    "id": "{node_id}_kb_2",
    "type": "blank",
    "question": "填空题内容 ____",
    "blank_answer": "答案",
    "explanation": "简要解释"
  }},
  {{
    "id": "{node_id}_kb_3",
    "type": "coding",
    "question": "编程任务",
    "coding_template": "def solve(data):\\n    pass",
    "blank_answer": "def solve(data):\\n    return data",
    "explanation": "解题思路"
  }}
]"""


# ★ 章节题库过少时的 LLM 扩题 prompt
EXAM_EXPAND_PROMPT = """你是一位数据结构教育专家。请为知识点"{node_title}"生成 {question_count} 道额外的混合练习题。

## 现有题目（请避免重复，难度和角度需有差异）
{existing_questions}

## 要求
1. 生成 {question_count} 道题目，难度从易到中均有
2. 题型使用 choice、blank、coding；只要题量允许，至少包含1道填空和1道Python编程题
3. choice 提供 options 与整数 correct；blank 提供 blank_answer；coding 提供 coding_template 与 blank_answer（参考代码）
4. 每题附带简要解释（1-2句话）
5. 题目考察核心概念、时间复杂度、典型应用和可实现的算法操作
6. id 字段以 "{node_id}_ex_" 开头

## 输出格式（严格JSON数组，不要任何其他文字）
[
  {{
    "id": "{node_id}_ex_1",
    "type": "choice",
    "question": "题目",
    "options": ["A选项", "B选项", "C选项", "D选项"],
    "correct": 0,
    "explanation": "解释"
  }}
]"""


def _normalize_generated_question(question: dict, node_id: str, index: int) -> Optional[dict]:
    """把不同模型返回的题型字段统一成章节考试使用的结构。"""
    if not isinstance(question, dict) or not str(question.get("question", "")).strip():
        return None

    item = dict(question)
    aliases = {
        "single_choice": "choice", "multiple_choice": "choice",
        "fill_blank": "blank", "fill": "blank",
        "code": "coding", "programming": "coding", "short_answer": "coding",
    }
    qtype = aliases.get(str(item.get("type", "choice")).lower(), str(item.get("type", "choice")).lower())
    if qtype not in {"choice", "blank", "coding"}:
        qtype = "choice"
    item["type"] = qtype
    item["id"] = str(item.get("id") or f"{node_id}_ai_{index}")
    if not item["id"].startswith(node_id):
        item["id"] = f"{node_id}_ai_{index}"
    item["explanation"] = str(item.get("explanation") or "请结合本知识点的定义与操作过程理解。")

    if qtype == "choice":
        options = item.get("options")
        if not isinstance(options, list) or len(options) < 2:
            return None
        try:
            item["correct"] = int(item.get("correct", item.get("answer", 0)))
        except (TypeError, ValueError):
            return None
        if not 0 <= item["correct"] < len(options):
            return None
    else:
        item["blank_answer"] = str(item.get("blank_answer") or item.get("correct_answer") or item.get("answer") or "").strip()
        if not item["blank_answer"]:
            return None
        if qtype == "coding":
            item["coding_template"] = str(item.get("coding_template") or item.get("template") or "# 请在这里编写 Python 代码")
    return item


def _expand_questions_with_llm(node_id: str, node_title: str, existing: List[dict], need_count: int) -> List[dict]:
    """★ 当内置题库不足5题时，用 LLM 自动扩题"""
    if need_count <= 0:
        return []
    try:
        from dotenv import load_dotenv
        load_dotenv()
        import openai as openai_lib
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        if not api_key:
            return []

        # 截取现有题目摘要
        existing_text = "\n".join([
            f"- {q.get('question', '')}（答案：选项{q.get('correct', 0)}）"
            for q in existing[:5]
        ]) or "无"

        prompt = EXAM_EXPAND_PROMPT.format(
            node_title=node_title,
            node_id=node_id,
            question_count=need_count,
            existing_questions=existing_text,
        )

        client = openai_lib.OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "deepseek-chat"),
            messages=[
                {"role": "system", "content": "你是一位出题专家。只输出JSON数组。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.75,
            max_tokens=2048,
        )

        raw = response.choices[0].message.content.strip()
        json_match = re.search(r'\[[\s\S]*\]', raw)
        if not json_match:
            return []
        questions = json.loads(json_match.group())
        if not isinstance(questions, list):
            return []
        valid = []
        for index, q in enumerate(questions, start=1):
            normalized = _normalize_generated_question(q, node_id, index)
            if normalized:
                valid.append(normalized)
        if valid:
            print(f"[Exam-Expand] ✅ 为 {node_id} 自动扩题 {len(valid)} 道")
        return valid
    except Exception as e:
        print(f"[Exam-Expand] ⚠️ 扩题失败: {e}")
        return []


def _generate_kb_questions(node_id: str, node_title: str, subject: str = "数据结构") -> Optional[List[dict]]:
    """
    尝试基于知识库生成章节测试题目。
    返回题目列表，或 None（知识库无内容/LLM不可用）。
    """
    # 1. 从知识库检索相关内容
    try:
        from app.services.rag import rag_service as rag
        context = rag.retrieve_context(
            f"{subject} {node_title} 核心概念 定义 原理 知识点",
            k=5,
        )
    except Exception:
        return None

    if not context or not context.strip():
        return None  # 知识库无内容，回退到硬编码题目

    # 2. 构建 prompt 并调用 LLM
    try:
        from dotenv import load_dotenv
        load_dotenv()
        import openai as openai_lib

        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        if not api_key:
            return None

        prompt = EXAM_KB_PROMPT.format(
            node_title=node_title,
            node_id=node_id,
            question_count=6,
            rag_context=context[:3500],
        )

        client = openai_lib.OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "deepseek-chat"),
            messages=[
                {
                    "role": "system",
                    "content": "你是一位教育专家，必须严格根据资料出题。只输出JSON数组，不要任何其他文字。",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.65,
            max_tokens=2048,
        )

        raw = response.choices[0].message.content.strip()
        # 尝试从响应中提取 JSON 数组
        json_match = re.search(r'\[[\s\S]*\]', raw)
        if not json_match:
            return None
        questions = json.loads(json_match.group())

        # 校验题目格式
        if not isinstance(questions, list) or len(questions) == 0:
            return None
        valid = [
            normalized for index, q in enumerate(questions, start=1)
            if (normalized := _normalize_generated_question(q, node_id, index))
        ]
        if not valid:
            return None

        print(f"[Exam] ✅ 基于知识库为 {node_id} 生成了 {len(valid)} 道题")
        return valid

    except Exception as e:
        print(f"[Exam] ⚠️ KB题目生成失败: {e}")
        return None


def _auto_assign_metadata(questions: List[dict]) -> List[dict]:
    """
    为缺少 difficulty/bloom 的题目自动分配元数据
    按题型索引均匀分配：前半 easy，中段 medium，末尾 hard
    """
    if not questions:
        return questions
    n = len(questions)
    for i, q in enumerate(questions):
        if "difficulty" not in q:
            if n <= 3:
                q["difficulty"] = ["easy", "medium", "hard"][min(i, 2)]
            else:
                ratio = i / max(n - 1, 1)
                if ratio < 0.33:
                    q["difficulty"] = "easy"
                elif ratio < 0.66:
                    q["difficulty"] = "medium"
                else:
                    q["difficulty"] = "hard"
        if "bloom" not in q:
            blooms = ["remember", "understand", "apply", "analyze"]
            q["bloom"] = blooms[min(i, len(blooms) - 1)]
    return questions


def _select_by_difficulty(questions: List[dict], mastery: float, count: int = 6) -> List[dict]:
    """
    根据学生掌握度自适应选择题目难度配比
    mastery < 40: 多出 easy  (4 easy + 2 medium)
    mastery 40-70: 均衡      (2 easy + 3 medium + 1 hard)
    mastery > 70:  多出 hard  (1 easy + 3 medium + 2 hard)
    """
    easy = [q for q in questions if q.get("difficulty") == "easy"]
    medium = [q for q in questions if q.get("difficulty") == "medium"]
    hard = [q for q in questions if q.get("difficulty") == "hard"]

    if mastery < 40:
        pick_easy = min(4, len(easy))
        pick_medium = min(2, len(medium))
        pick_hard = 0
    elif mastery < 70:
        pick_easy = min(2, len(easy))
        pick_medium = min(3, len(medium))
        pick_hard = min(1, len(hard))
    else:
        pick_easy = min(1, len(easy))
        pick_medium = min(3, len(medium))
        pick_hard = min(2, len(hard))

    selected = easy[:pick_easy] + medium[:pick_medium] + hard[:pick_hard]
    # 如果不足 count，补齐
    if len(selected) < count:
        remaining = [q for q in questions if q not in selected]
        selected += remaining[:(count - len(selected))]
    return selected[:count]


def _get_cached_or_generate_questions(node_id: str, node_title: str, subject: str = "数据结构") -> List[dict]:
    """获取章节测试题目：优先用知识库生成（缓存1小时），回退到硬编码题库"""
    now = time.time()

    # 检查缓存
    cached = _kb_exam_cache.get(node_id)
    if cached and (now - cached["cached_at"]) < _kb_cache_ttl:
        return cached["questions"]

    # 尝试基于知识库生成
    kb_questions = _generate_kb_questions(node_id, node_title, subject)
    if kb_questions:
        kb_questions = _auto_assign_metadata(kb_questions)
        _kb_exam_cache[node_id] = {"questions": kb_questions, "cached_at": now}
        return kb_questions

    # 回退到硬编码题库，自动补全缺失的元数据
    raw = _auto_assign_metadata(NODE_EXAMS.get(node_id, DEFAULT_EXAM)["questions"])

    # ★ 题数过少（<5）时，用 LLM 自动扩题（仅第一次，缓存复用）
    if len(raw) < 5 and node_id != "default":
        need = 6 - len(raw)
        extra = _expand_questions_with_llm(node_id, node_title, raw, need)
        if extra:
            raw = raw + _auto_assign_metadata(extra)

    _kb_exam_cache[node_id] = {"questions": raw, "cached_at": now}
    return raw


MODE_DEFAULT_COUNTS = {
    "coding": 3,
    "exam": 10,
    "mock": 15,
    "mixed": 8,
    "challenge": 5,
}

MODE_TYPE_QUOTAS = {
    "exam": {"choice": 7, "blank": 2, "coding": 1},
    "mock": {"choice": 10, "blank": 3, "coding": 2},
    "mixed": {"choice": 4, "blank": 2, "coding": 2},
    "challenge": {"choice": 2, "blank": 1, "coding": 2},
}


def _quota_for_mode(mode: str, count: int) -> dict:
    base = MODE_TYPE_QUOTAS.get(mode, MODE_TYPE_QUOTAS["mixed"])
    base_total = sum(base.values())
    quotas = {
        qtype: max(0, round(count * amount / base_total))
        for qtype, amount in base.items()
    }
    while sum(quotas.values()) < count:
        for qtype in sorted(base, key=base.get, reverse=True):
            quotas[qtype] += 1
            if sum(quotas.values()) >= count:
                break
    while sum(quotas.values()) > count:
        for qtype in sorted(base, key=base.get):
            if quotas[qtype] > 0:
                quotas[qtype] -= 1
                if sum(quotas.values()) <= count:
                    break
    return quotas

def _select_mixed_questions(
    questions: List[dict], mastery: float, count: int = 8, mode: str = "mixed",
) -> List[dict]:
    """先保证题型配比，再在每种题型中按学生掌握度选择难度。"""
    count = max(3, min(int(count), 20))
    difficulty_order = (
        ["easy", "medium", "hard"] if mastery < 40 else
        ["hard", "medium", "easy"] if mastery > 70 else
        ["medium", "easy", "hard"]
    )
    rank = {level: index for index, level in enumerate(difficulty_order)}

    def candidates(qtype: Optional[str] = None) -> List[dict]:
        pool = [q for q in questions if qtype is None or q.get("type", "choice") == qtype]
        return sorted(pool, key=lambda q: rank.get(q.get("difficulty", "medium"), 1))

    # 编程训练与混合测试是两条独立路径：编程模式绝不再用选择题补位。
    if mode == "coding":
        return candidates("coding")[:count]

    quotas = _quota_for_mode(mode, count)

    selected: List[dict] = []
    for qtype in ("choice", "blank", "coding"):
        selected.extend(candidates(qtype)[:quotas[qtype]])

    if len(selected) < count:
        selected_ids = {q["id"] for q in selected}
        remaining = [q for q in candidates() if q["id"] not in selected_ids]
        selected.extend(remaining[:count - len(selected)])
    return selected[:count]


def _get_coding_question_pool(node_id: str, min_count: int) -> List[dict]:
    """Return coding-only questions and ignore mixed/AI caches for coding practice."""
    min_count = max(1, min(int(min_count), 20))
    prefix_fallbacks = {
        "ch01_": "ch01_algorithm",
        "ch02_": "ch02_linked_list",
        "ch03_": "ch03_stack_basic",
        "ch04_": "ch01_algorithm",
        "ch05_": "ch05_tree_basic",
        "ch06_": "ch06_graph_concept",
        "ch07_": "ch07_binary_search",
        "ch08_": "ch08_quick_sort",
    }
    source_keys = [node_id]
    fallback_key = next(
        (fallback for prefix, fallback in prefix_fallbacks.items() if node_id.startswith(prefix)),
        "ch01_algorithm",
    )
    source_keys.append(fallback_key)
    source_keys.extend(key for key in NODE_EXAMS.keys() if key not in source_keys and not key.endswith(_MIXED_SUFFIX))

    selected = []
    seen = set()
    for key in source_keys:
        for question in NODE_EXAMS.get(key, {"questions": []}).get("questions", []):
            if question.get("type", "choice") != "coding":
                continue
            identity = (str(question.get("id", "")), str(question.get("question", "")))
            if identity in seen:
                continue
            item = dict(question)
            if key != node_id:
                item["id"] = f"{node_id}_coding_{len(selected) + 1}_{item.get('id', 'q')}"
            selected.append(item)
            seen.add(identity)
            if len(selected) >= min_count:
                return _auto_assign_metadata(selected)
    return _auto_assign_metadata(selected)
def _get_mixed_question_pool(
    node_id: str, node_title: str, subject: str = "数据结构", min_count: int = 6,
) -> List[dict]:
    """组合 AI/RAG 题和本地预置题；AI 不可用时仍可稳定返回混合题。"""
    now = time.time()
    min_count = max(3, min(int(min_count), 20))
    cached = _kb_exam_cache.get(node_id)
    cache_valid = cached and (now - cached["cached_at"]) < _kb_cache_ttl

    if cache_valid:
        raw = list(cached["questions"])
    else:
        local_questions = [dict(q) for q in NODE_EXAMS.get(node_id, DEFAULT_EXAM)["questions"]]
        # 同一章的细分知识点复用经过人工校验的章节混合题，避免冷门节点退化为纯选择题。
        prefix_fallbacks = {
            "ch01_": "ch01_algorithm",
            "ch02_": "ch02_seq_list",
            "ch03_": "ch03_stack_basic",
            "ch04_": "ch01_algorithm",
            "ch05_": "ch05_tree_basic",
            "ch06_": "ch06_graph_concept",
            "ch07_": "ch07_binary_search",
            "ch08_": "ch08_quick_sort",
        }
        type_counts = {
            qtype: sum(q.get("type", "choice") == qtype for q in local_questions)
            for qtype in ("blank", "coding")
        }
        fallback_key = next(
            (fallback for prefix, fallback in prefix_fallbacks.items() if node_id.startswith(prefix)),
            "ch01_algorithm",
        )
        for fallback in NODE_EXAMS.get(fallback_key, {"questions": []})["questions"]:
            qtype = fallback.get("type", "choice")
            if qtype in {"blank", "coding"} and type_counts[qtype] < 2:
                item = dict(fallback)
                item["id"] = f"{node_id}_fallback_{fallback['id']}"
                local_questions.append(item)
                type_counts[qtype] += 1
        ai_questions = _generate_kb_questions(node_id, node_title, subject) or []
        raw = []
        seen = set()
        # 本地题库是可靠兜底，绝不再被纯选择题的 AI 结果覆盖。
        for q in ai_questions + local_questions:
            identity = (str(q.get("id", "")), str(q.get("question", "")))
            if identity not in seen:
                seen.add(identity)
                raw.append(q)
        raw = _auto_assign_metadata(raw)

    if len(raw) < min_count and node_id != "default":
        extra = _expand_questions_with_llm(node_id, node_title, raw, min_count - len(raw))
        existing_ids = {q["id"] for q in raw}
        raw.extend(q for q in _auto_assign_metadata(extra) if q["id"] not in existing_ids)

    if len(raw) < min_count:
        seen = {(str(q.get("id", "")), str(q.get("question", ""))) for q in raw}
        topup_sources = [DEFAULT_EXAM.get("questions", [])]
        topup_sources.extend(
            bank.get("questions", [])
            for key, bank in NODE_EXAMS.items()
            if key != node_id and not key.endswith(_MIXED_SUFFIX)
        )
        for source in topup_sources:
            for fallback in source:
                identity = (str(fallback.get("id", "")), str(fallback.get("question", "")))
                if identity in seen:
                    continue
                item = dict(fallback)
                item["id"] = f"{node_id}_topup_{len(raw) + 1}_{item.get('id', 'q')}"
                raw.append(item)
                seen.add(identity)
                if len(raw) >= min_count:
                    break
            if len(raw) >= min_count:
                break
        raw = _auto_assign_metadata(raw)

    _kb_exam_cache[node_id] = {"questions": raw, "cached_at": now}
    return raw


# ════════════════════════════════════════════════════════
# API 端点
# ════════════════════════════════════════════════════════

@router.get("/{node_id}/questions")
async def get_exam_questions(
    node_id: str,
    count: Optional[int] = None,
    difficulty: Optional[str] = None,
    mode: str = "mixed",
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """获取章节测试题目（★ 自适应难度：根据学生画像选取难度配比）"""
    # 验证节点存在
    result = await db.execute(
        select(KnowledgeNode).where(KnowledgeNode.id == node_id)
    )
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="知识点不存在")

    mode = mode if mode in {"mixed", "exam", "coding", "mock", "challenge"} else "mixed"
    default_count = MODE_DEFAULT_COUNTS.get(mode, MODE_DEFAULT_COUNTS["mixed"])
    count = default_count if count is None else count
    count = max(3, min(int(count), 20))
    if mode == "coding":
        questions_full = _get_coding_question_pool(node_id, count)
        _kb_exam_cache[node_id] = {"questions": questions_full, "cached_at": time.time()}
    else:
        pool_min_count = 20 if mode in {"exam", "mock"} else count
        questions_full = _get_mixed_question_pool(node_id, node.title, min_count=pool_min_count)

    # ★ 自适应难度：根据学生在该知识点（或相似知识点）的掌握度选取题目配比
    mastery = 50.0  # 默认中等水平
    try:
        from app.models.student_profile import StudentProfile as SPModel
        sp_result = await db.execute(
            select(SPModel).where(SPModel.user_id == user.id)
        )
        sp = sp_result.scalar_one_or_none()
        if sp and sp.knowledge_mastery:
            km = sp.knowledge_mastery
            # 尝试用 node.title、node_id 匹配掌握度
            mastery = float(km.get(node.title, km.get(node_id,
                sum(float(v) for v in km.values()) / max(len(km), 1)
            )))
    except Exception:
        pass

    requested_levels = {
        "easy": 25.0,
        "balanced": 55.0,
        "medium": 55.0,
        "hard": 85.0,
    }
    mastery = requested_levels.get((difficulty or "").lower(), mastery)
    selected = _select_mixed_questions(questions_full, mastery, count=count, mode=mode)

    # 返回给前端时不包含正确答案（但保留 difficulty/bloom/type 供前端渲染）
    questions_clean = []
    for q in selected:
        qtype = q.get("type", "choice")
        item = {
            "id": q["id"],
            "question": q["question"],
            "type": qtype,
            "difficulty": q.get("difficulty", "medium"),
            "bloom": q.get("bloom", "understand"),
        }
        if qtype == "choice":
            item["options"] = q.get("options", [])
        elif qtype == "blank":
            item["options"] = []  # 填空无需选项
        elif qtype == "coding":
            item["options"] = []
            item["coding_template"] = q.get("coding_template", "")
        questions_clean.append(item)

    # 不同类型计数
    type_counts = {}
    for q in questions_clean:
        t = q.get("type", "choice")
        type_counts[t] = type_counts.get(t, 0) + 1
    
    return {
        "node_id": node_id,
        "node_title": node.title,
        "questions": questions_clean,
        "total": len(questions_clean),
        "type_counts": type_counts,
        "adaptive_level": "easy" if mastery < 40 else ("hard" if mastery > 70 else "balanced"),
        "question_source": "ai_with_local_fallback",
    }


@router.get("/mistakes")
async def get_mistakes(
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户的错题本（所有考试中的错误题目）"""
    import json

    # 查询用户所有考试结果（包含错误的）
    result = await db.execute(
        select(ExamResult)
        .where(
            ExamResult.user_id == user.id,
            ExamResult.score < 100,  # 不是满分说明有错误
        )
        .order_by(ExamResult.completed_at.desc())
    )
    exam_results = result.scalars().all()

    if not exam_results:
        return {"chapters": [], "total": 0}

    # 获取涉及的节点信息
    node_ids = list(set([er.node_id for er in exam_results]))
    nodes_result = await db.execute(
        select(KnowledgeNode).where(KnowledgeNode.id.in_(node_ids))
    )
    nodes = {n.id: n for n in nodes_result.scalars().all()}

    # 同时获取所有父节点（大章节）的标题
    parent_ids = list(set([n.parent_id for n in nodes.values() if n.parent_id]))
    parent_map = {}
    if parent_ids:
        parents_result = await db.execute(
            select(KnowledgeNode).where(KnowledgeNode.id.in_(parent_ids))
        )
        for p in parents_result.scalars().all():
            parent_map[p.id] = p.title

    # 按章节（节点）组织错题
    chapters_map = {}  # {chapter_name: {sub_chapters: [...]}}
    mistake_id = 0
    OPTION_LABELS = ['A', 'B', 'C', 'D', 'E', 'F']

    try:
        for er in exam_results:
            node = nodes.get(er.node_id)
            if not node:
                continue

            # 大章节名：优先用父节点的 title，否则用 category，最后兜底
            chapter_name = parent_map.get(node.parent_id) or node.category or "其他"
            node_title = node.title

            # 从考试详情中提取错题（如果有 details 数据）
            mistakes = []
            if hasattr(er, 'details') and er.details:
                try:
                    details = json.loads(er.details) if isinstance(er.details, str) else er.details
                    for detail_idx, detail in enumerate(details):
                        # ★ 跳过已被移除的错题
                        if detail.get('removed'):
                            continue
                        if not detail.get('is_correct', True):  # 只取错误题目
                            user_choice = detail.get('user_choice', -1)
                            correct_answer = detail.get('correct_answer', -1)
                            is_quiz = detail.get('source') == 'quiz'

                            if is_quiz:
                                # ★ 练习题来源：answer 是文本，直接显示
                                your_answer_text = str(user_choice) if user_choice not in (None, -1, '') else '未作答'
                                correct_answer_text = str(correct_answer) if correct_answer not in (None, -1, '') else ''
                            else:
                                # 考试来源：answer 是索引，需要映射为选项文本
                                cached_exam = _kb_exam_cache.get(er.node_id)
                                if cached_exam:
                                    exam_qs = cached_exam["questions"]
                                else:
                                    exam_qs = NODE_EXAMS.get(er.node_id, DEFAULT_EXAM).get("questions", [])
                                q_map = {q["id"]: q for q in exam_qs}
                                q_detail = q_map.get(detail.get('id'), {})
                                options = q_detail.get("options", [])

                                your_answer_text = '未作答'
                                if isinstance(user_choice, int) and 0 <= user_choice < len(options):
                                    your_answer_text = f'{OPTION_LABELS[user_choice]}. {options[user_choice]}'

                                correct_answer_text = ''
                                if isinstance(correct_answer, int) and 0 <= correct_answer < len(options):
                                    correct_answer_text = f'{OPTION_LABELS[correct_answer]}. {options[correct_answer]}'

                            mistakes.append({
                                'id': f'mistake_{er.id}_{detail_idx}',
                                'idx': len(mistakes) + 1,
                                'titlePreview': detail.get('question', '')[:30] + '...' if detail.get('question') else '未知题目',
                                'date': er.completed_at.strftime('%Y-%m-%d') if er.completed_at else '',
                                'question': detail.get('question', ''),
                                'questionType': detail.get('type', 'choice'),
                                'options': detail.get('options', []),
                                'correctAnswer': correct_answer_text or detail.get('explanation', ''),
                                'correctValue': correct_answer,
                                'yourAnswer': your_answer_text,
                                'explanation': detail.get('explanation', ''),
                                'errorType': 'concept',
                                'difficulty': '⭐⭐' if er.score >= 60 else '⭐⭐⭐',
                                'examResultId': er.id,
                                'detailIdx': detail_idx,
                            })
                            mistake_id += 1
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"[mistakes] 解析details失败: {e}")
                    pass

            # 如果没有详细错题数据，创建一个汇总条目
            if not mistakes:
                mistakes.append({
                    'id': f'mistake_{er.id}_0',
                    'idx': 1,
                    'titlePreview': f'{node_title} 测试（得分{er.score}分）',
                    'date': er.completed_at.strftime('%Y-%m-%d') if er.completed_at else '',
                    'question': f'在《{node_title}》章节测试中，你的得分为 **{er.score}** 分{"（未通过）" if not er.passed else ""}。\n\n该测试记录暂无详细错题数据，建议重新测试以记录具体错题。',
                    'questionType': 'summary',
                    'options': [],
                    'correctAnswer': '该章节测试满分100分，及格线60分',
                    'correctValue': -1,
                    'yourAnswer': f'实际得分：{er.score}分',
                    'explanation': f'{"未通过考试，建议复习该章节知识点后重新测试。" if not er.passed else "虽已通过，但仍有提升空间。"}',
                    'errorType': 'other' if er.passed else 'concept',
                    'difficulty': '⭐⭐' if er.score >= 70 else ('⭐⭐⭐' if er.score >= 40 else '⭐⭐⭐⭐'),
                    'examResultId': er.id,
                    'detailIdx': 0,
                })
                mistake_id += 1

            # 组织到章节数据结构中
            if chapter_name not in chapters_map:
                chapters_map[chapter_name] = {
                    'id': f'ch_{len(chapters_map)}',
                    'name': chapter_name,
                    'subChapters': []
                }

            # 合并相同 node_id 的错题到同一个 subChapter
            existing_sub = None
            for sub in chapters_map[chapter_name]['subChapters']:
                if sub['id'] == f'sub_{er.node_id}':
                    existing_sub = sub
                    break

            if existing_sub:
                existing_sub['questions'].extend(mistakes)
                # 重新编号
                for i, q in enumerate(existing_sub['questions']):
                    q['idx'] = i + 1
            else:
                chapters_map[chapter_name]['subChapters'].append({
                    'id': f'sub_{er.node_id}',
                    'name': node_title,
                    'questions': mistakes,
                })

        chapters_list = list(chapters_map.values())

        total_mistakes = 0
        for ch in chapters_list:
            for sub in ch['subChapters']:
                total_mistakes += len(sub['questions'])

        return {
            "chapters": chapters_list,
            "total": total_mistakes,
        }
    except Exception as e:
        print(f"[mistakes] 获取错题失败: {e}")
        import traceback
        traceback.print_exc()
        # 降级返回：只返回基本的考试结果汇总
        fallback_chapters = []
        for er in exam_results:
            node = nodes.get(er.node_id)
            if not node:
                continue
            fallback_chapters.append({
                'id': f'ch_{er.node_id}',
                'name': node.title,
                'subChapters': [{
                    'id': f'sub_{er.node_id}',
                    'name': node.title,
                    'questions': [{
                        'id': f'mistake_{er.id}_0',
                        'idx': 1,
                        'titlePreview': f'{node.title} 测试（得分{int(er.score)}分）',
                        'date': er.completed_at.strftime('%Y-%m-%d') if er.completed_at else '',
                        'question': f'《{node.title}》测试得分 **{int(er.score)}** 分',
                        'questionType': 'summary',
                        'options': [],
                        'correctAnswer': '满分100分',
                        'correctValue': -1,
                        'yourAnswer': f'实际得分{int(er.score)}分',
                        'explanation': '建议复习后重新测试',
                        'errorType': 'other',
                        'difficulty': '⭐⭐',
                        'examResultId': er.id,
                        'detailIdx': 0,
                    }]
                }]
            })
        return {"chapters": fallback_chapters, "total": len(fallback_chapters)}


@router.post("/mistakes/remove")
async def remove_mistake(
    req: RemoveMistakeRequest,
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """移除错题本中的一道错题（标记为已掌握）"""
    import re
    import json as _json

    # 解析 mistake_id: "mistake_{exam_result_id}_{detail_idx}"
    match = re.match(r'^mistake_(\d+)_(\d+)$', req.mistake_id)
    if not match:
        raise HTTPException(status_code=400, detail=f"无效的错题ID格式: {req.mistake_id}")

    er_id = int(match.group(1))
    detail_idx = int(match.group(2))

    # 查找考试结果记录
    result = await db.execute(
        select(ExamResult).where(
            and_(ExamResult.id == er_id, ExamResult.user_id == user.id)
        )
    )
    er = result.scalar_one_or_none()
    if not er:
        raise HTTPException(status_code=404, detail="错题记录不存在")

    # 解析 details
    try:
        details = _json.loads(er.details) if isinstance(er.details, str) else (er.details or [])
    except (_json.JSONDecodeError, TypeError):
        raise HTTPException(status_code=500, detail="错题数据格式错误")

    if detail_idx < 0 or detail_idx >= len(details):
        raise HTTPException(status_code=400, detail=f"错题索引越界: {detail_idx} (共{len(details)}条)")

    # 标记为已移除（软删除，保留原始数据用于追溯）
    target = details[detail_idx]
    if target.get('removed'):
        error_count = sum(1 for d in details if not d.get('is_correct', True) and not d.get('removed'))
        return {"success": True, "message": "该错题已经被移除了", "remaining_errors": error_count}

    target['removed'] = True
    er.details = _json.dumps(details, ensure_ascii=False)

    # 重新计算得分：移除一道错题后，正确率上升
    total = len(details)
    error_count = sum(1 for d in details if not d.get('is_correct', True) and not d.get('removed'))
    if total > 0:
        er.score = round((total - error_count) / total * 100, 1)
    else:
        er.score = 100
    er.passed = er.score >= 60

    await db.commit()

    return {
        "success": True,
        "message": "错题已移除",
        "new_score": er.score,
        "remaining_errors": error_count,
    }


def _normalize_text_answer(value) -> str:
    """宽容处理空格、大小写和常见全角符号。"""
    text = str(value or "").strip().lower()
    translation = str.maketrans({"（": "(", "）": ")", "＾": "^", "＝": "=", "　": " "})
    return re.sub(r"\s+", "", text.translate(translation))


def _grade_exam_answer(question: dict, user_answer) -> tuple[bool, object, str]:
    """按题型评分；编程题使用安全的结构检查，不执行用户代码。"""
    qtype = question.get("type", "choice")
    if qtype == "choice":
        expected = question.get("correct", -1)
        try:
            submitted = int(user_answer)
        except (TypeError, ValueError):
            submitted = user_answer
        return submitted == expected, expected, "按正确选项评分"

    expected = question.get("blank_answer", question.get("correct_answer", ""))
    if qtype == "blank":
        accepted = question.get("accepted_answers") or [expected]
        normalized_user = _normalize_text_answer(user_answer)
        normalized_accepted = {_normalize_text_answer(answer) for answer in accepted}
        # 允许用户把题干外层的 O(...) 一并写入。
        variants = {normalized_user}
        if normalized_user.startswith("o(") and normalized_user.endswith(")"):
            variants.add(normalized_user[2:-1])
        return bool(variants & normalized_accepted), expected, "忽略空格与大小写后匹配"

    code = str(user_answer or "").strip()
    reference = str(expected or "")
    required_tokens = list(question.get("required_tokens") or [])
    if not required_tokens:
        required_tokens.extend(re.findall(r"def\s+([a-zA-Z_]\w*)", reference))
        if "return" in reference:
            required_tokens.append("return")
    lowered = code.lower()
    has_placeholder = bool(re.search(r"(^|\n)\s*pass\s*(#.*)?($|\n)", code))
    has_structure = len(code) >= 25 and all(str(token).lower() in lowered for token in required_tokens)
    return (
        bool(code and not has_placeholder and has_structure),
        reference,
        "安全结构检查（函数名、关键操作、是否仍含 pass）；不会在服务器执行用户代码",
    )


@router.post("/{node_id}/submit")
async def submit_exam(
    node_id: str,
    req: SubmitExamRequest,
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """提交章节测试答案并评分"""
    import traceback, sys
    try:
        # 验证节点存在
        result = await db.execute(
            select(KnowledgeNode).where(KnowledgeNode.id == node_id)
        )
        node = result.scalar_one_or_none()
        if not node:
            raise HTTPException(status_code=404, detail="知识点不存在")

        # ★ 优先用缓存的KB题目，否则用硬编码题库
        cached = _kb_exam_cache.get(node_id)
        if cached:
            questions = cached["questions"]
        else:
            questions = NODE_EXAMS.get(node_id, DEFAULT_EXAM)["questions"]
        question_map = {q["id"]: q for q in questions}

        correct_count = 0
        total = 0
        details = []

        for answer in req.answers:
            qid = answer.get("id", "")
            user_choice = answer.get("answer", -1)
            q = question_map.get(qid)
            if q is None:
                continue
            total += 1
            is_correct, correct_answer, grading_note = _grade_exam_answer(q, user_choice)
            if is_correct:
                correct_count += 1
            details.append({
                "id": qid,
                "question": q["question"],
                "user_choice": user_choice,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "explanation": q["explanation"],
                "type": q.get("type", "choice"),
                "grading_note": grading_note,
                "difficulty": q.get("difficulty", "medium"),
                "bloom": q.get("bloom", "understand"),
            })

        exam_score = round(correct_count / max(total, 1) * 100, 1)
        passed = exam_score >= 60

        # 保存考试结果
        from sqlalchemy.sql import func
        import json as _json
        exam_result = await db.execute(
            select(ExamResult).where(
                and_(
                    ExamResult.user_id == user.id,
                    ExamResult.node_id == node_id,
                )
            )
        )
        existing_exam = exam_result.scalar_one_or_none()
        if existing_exam is None:
            existing_exam = ExamResult(user_id=user.id, node_id=node_id)
            db.add(existing_exam)
        existing_exam.score = exam_score
        existing_exam.passed = passed
        existing_exam.completed_at = func.now()
        # ★ 保存每道题的详细答题情况（含错题）到 details 字段
        existing_exam.details = _json.dumps(details, ensure_ascii=False)

        # 更新学习进度：学习内容已完成 + 考试已通过 = 章节完结
        p_result = await db.execute(
            select(LearningProgress).where(
                and_(
                    LearningProgress.user_id == user.id,
                    LearningProgress.node_id == node_id,
                )
            )
        )
        prog = p_result.scalar_one_or_none()

        # ★ 计算资源部分进度（讲义25% + 练习题25% = 最多50%）
        def _get_resource_base(p):
            rp = (p.resource_progress or {}) if hasattr(p, 'resource_progress') else {}
            base = 0
            if rp.get("notes"):
                base += 25
            if rp.get("quiz"):
                base += 25
            return base

        if prog is not None:
            # ★ 已有学习记录
            resource_base = _get_resource_base(prog)
            if passed:
                # 考试 >= 60 → 直接 100%
                prog.status = "completed"
                prog.progress = 100
                prog.completed_at = func.now()
            else:
                # 考试 < 60 → 资源部分 + 考试部分
                exam_add = int((exam_score / 60) * 50)
                prog.progress = resource_base + exam_add
                if prog.progress >= 100:
                    prog.status = "completed"
                    prog.completed_at = func.now()
            # 保留最高分
            prog.score = max(prog.score or 0, exam_score)
        else:
            # ★ 没有任何学习记录
            resource_base = 0  # 新记录无资源进度
            if passed:
                # 考试通过 → 创建完结记录
                prog = LearningProgress(
                    user_id=user.id, node_id=node_id,
                    status="completed", score=exam_score,
                    progress=100, completed_at=func.now()
                )
            else:
                # 考试未通过 → 按比例计算（资源0 + 考试部分）
                exam_add = int((exam_score / 60) * 50)
                prog = LearningProgress(
                    user_id=user.id, node_id=node_id,
                    status="in_progress", score=exam_score,
                    progress=exam_add, started_at=func.now()
                )
            db.add(prog)

        await db.commit()

        # ★ 触发能力值更新（考试/练习完成）
        try:
            from app.services.ability_service import ability_service
            is_quiz = not passed and exam_score > 0
            await ability_service.on_exam_submitted(db, user.id, exam_score, passed, is_quiz=is_quiz)
        except Exception as e:
            print(f"[Ability] 考试能力值更新失败: {e}")

        # ★ 新增：考试完成后写入学习事件
        try:
            from app.services.learning_record_service import learning_record_service
            await learning_record_service.log_event(
                db=db,
                user_id=user.id,
                event_type="exam_completed",
                node_id=node_id,
                score=exam_score,
                event_data={
                    "correct_count": correct_count,
                    "total_count": total,
                    "passed": passed,
                    "exam_type": "chapter_test",
                },
            )
        except Exception as e:
            print(f"[Exam] 学习事件记录失败: {e}")

        # ★ 画像重算：考试提交后调用统一服务更新 student_profiles + 同步 users.profile_data
        try:
            sp = await recalculate_profile(
                user_id=user.id, db=db,
                node_title=node.title,
                trigger_score=exam_score,
            )
            print(f"[Profile] ✅ 画像已更新: user={user.id}, score={exam_score}, "
                  f"level={sp.ability_level}, trend={sp.mastery_trend}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[Profile] 画像更新失败: {e}")

        return {
            "node_id": node_id,
            "node_title": node.title,
            "score": exam_score,
            "passed": passed,
            "correct_count": correct_count,
            "total": total,
            "details": details,
            "chapter_completed": prog.status == "completed",
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════
# ★ AI 学后反馈报告
# ════════════════════════════════════════════════════════

FEEDBACK_PROMPT = """你是一位经验丰富的教育诊断专家。请根据学生的画像数据和本次章节测试结果，生成一份个性化的学习反馈报告。

## 学生画像
- 能力等级：{ability_level}
- 学习节奏：{rhythm}
- 强项：{strengths}
- 薄弱点：{weaknesses}
- 整体掌握趋势：{trend}

## 本次测试结果
- 章节：{chapter_title}
- 得分：{score}分（{passed_text}）
- 正确率：{correct_count}/{total_count}
- 错题详情：{wrong_details}

## 输出要求
请以 JSON 格式输出一份温暖的、有针对性的学习反馈。语言口语化、有鼓励性。必须严格按照以下格式：

```json
{{
    "overall_comment": "一句话总体评价（30字，要具体到本章内容）",
    "good_at": "你做得好的方面（1-2句话，引用具体知识点）",
    "need_improve": "需要加强的方面（1-2句话，具体到概念或技能）",
    "specific_advice": "针对性的下一步行动建议（50-80字，具体可执行）",
    "next_topic_suggestion": "建议接下来学习的主题（结合画像薄弱点）",
    "encouragement": "一句温暖的鼓励（15字左右）",
    "difficulty_assessment": "对你来说本章难度（偏易/适中/偏难）以及原因"
}}
```
只输出 JSON，不要其他内容。"""


@router.get("/{node_id}/feedback")
async def get_exam_feedback(
    node_id: str,
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """
    ★ 获取章节学后的 AI 诊断反馈
    基于学生画像 + 本次考试得分 + 错题详情 → LLM 生成个性化建议
    """
    import json as _json

    # 1. 获取章节信息
    result = await db.execute(
        select(KnowledgeNode).where(KnowledgeNode.id == node_id)
    )
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="知识点不存在")

    # 2. 获取最近一次考试结果
    exam_result = await db.execute(
        select(ExamResult).where(
            and_(ExamResult.user_id == user.id, ExamResult.node_id == node_id)
        ).order_by(ExamResult.completed_at.desc())
    )
    exam = exam_result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="未找到考试记录，请先完成章节测试")

    # 3. 获取学生画像
    ability_level = "beginner"
    strengths = []
    weaknesses = []
    rhythm = "持续型"
    trend = "stable"

    try:
        from app.models.student_profile import StudentProfile as SPModel
        sp_result = await db.execute(
            select(SPModel).where(SPModel.user_id == user.id)
        )
        sp = sp_result.scalar_one_or_none()
        if sp:
            ability_level = sp.ability_level or "beginner"
            strengths = sp.strengths or []
            weaknesses = sp.weaknesses or []
            rhythm = sp.learning_rhythm or "持续型"
            trend = sp.mastery_trend or "stable"
    except Exception:
        pass

    # 4. 解析错题详情
    wrong_details_text = "无错题"
    if exam.details:
        try:
            details = _json.loads(exam.details) if isinstance(exam.details, str) else exam.details
            wrong_items = [d for d in details if not d.get("is_correct", True)]
            if wrong_items:
                wrong_parts = []
                for w in wrong_items[:3]:  # 最多展示3道错题
                    q = w.get("question", "")[:50]
                    wrong_parts.append(f"- {q}（你的答案错误）")
                wrong_details_text = "\n".join(wrong_parts)
        except Exception:
            pass

    # 5. 计算正确数/总题数
    total_count = 3  # 默认
    if exam.details:
        try:
            dets = _json.loads(exam.details) if isinstance(exam.details, str) else exam.details
            total_count = len(dets)
        except Exception:
            pass
    correct_count = round(exam.score * total_count / 100)

    # 6. 构建 prompt 并调用 LLM
    passed_text = "已通过" if exam.passed else "未通过"
    prompt = FEEDBACK_PROMPT.format(
        ability_level={"beginner":"初学", "intermediate":"中等", "advanced":"进阶", "expert":"专家"}.get(ability_level, ability_level),
        rhythm=rhythm,
        strengths="、".join(strengths[:3]) if strengths else "待发现",
        weaknesses="、".join(weaknesses[:3]) if weaknesses else "暂无",
        trend={"improving":"上升中", "stable":"稳定", "declining":"需关注"}.get(trend, trend),
        chapter_title=node.title,
        score=int(exam.score),
        passed_text=passed_text,
        correct_count=correct_count,
        total_count=total_count,
        wrong_details=wrong_details_text,
    )

    try:
        from dotenv import load_dotenv
        load_dotenv()
        import openai as openai_lib

        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        if not api_key:
            # 无 LLM 时返回规则生成的反馈
            return _fallback_feedback(node, exam, strengths, weaknesses)

        client = openai_lib.OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "deepseek-chat"),
            messages=[
                {"role": "system", "content": "你是一位温暖的、善于鼓励的教育诊断专家。只输出JSON。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=1024,
        )
        raw = response.choices[0].message.content.strip()
        json_match = re.search(r'\{[\s\S]*\}', raw)
        if json_match:
            feedback = _json.loads(json_match.group())
            return {"node_id": node_id, "node_title": node.title, "feedback": feedback}
    except Exception as e:
        print(f"[Feedback] LLM 生成失败: {e}")

    return _fallback_feedback(node, exam, strengths, weaknesses)


def _fallback_feedback(node, exam, strengths, weaknesses) -> dict:
    """LLM 不可用时的规则反馈"""
    score = int(exam.score)
    if score >= 80:
        comment = f"《{node.title}》掌握得很好，基础扎实！"
        advice = "可以挑战更高难度的综合题，尝试用所学知识解决实际问题"
    elif score >= 60:
        comment = f"《{node.title}》基本通过，但还有提升空间"
        advice = f"建议回顾错题涉及的概念，做2-3道针对性练习巩固"
    else:
        comment = f"《{node.title}》需要加强，别灰心，这是学习必经之路"
        advice = f"建议重新学习本章核心概念，从简单题目开始建立信心"

    return {
        "node_id": node.id,
        "node_title": node.title,
        "feedback": {
            "overall_comment": comment,
            "good_at": "你勇敢面对了测试挑战",
            "need_improve": "部分概念需要再次理解",
            "specific_advice": advice,
            "next_topic_suggestion": weaknesses[0] if weaknesses else "回顾基础知识",
            "encouragement": "每一次错误都是成长的机会",
            "difficulty_assessment": "适中" if 40 <= score <= 80 else ("偏难" if score < 40 else "偏易"),
        }
    }


@router.post("/quiz-result")
async def save_quiz_result(
    req: QuizResultRequest,
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """★ 保存"今日学习"练习题中的错题到温故知新"""
    import traceback, sys
    from sqlalchemy.sql import func as sql_func
    import json as _json

    try:
        node_id = req.node_id

        # 查找或创建 ExamResult
        result = await db.execute(
            select(ExamResult).where(
                and_(
                    ExamResult.user_id == user.id,
                    ExamResult.node_id == node_id,
                )
            )
        )
        existing = result.scalar_one_or_none()

        # 构建新错题的 details 条目
        new_details = []
        import uuid
        for item in req.wrong_items:
            user_ans = item.get('user_answer', '')
            correct_ans = item.get('answer', '')
            detail = {
                "id": item.get('id', str(uuid.uuid4())[:8]),
                "question": item.get('question', ''),
                "user_choice": user_ans,
                "correct_answer": correct_ans,
                "is_correct": False,
                "explanation": item.get('explanation', ''),
                "type": item.get('type', 'choice'),
                "options": item.get('options', []),
                "knowledge_point": item.get('knowledge_point', ''),
                "source": "quiz",  # 标记来源：练习题
            }
            new_details.append(detail)

        if existing is None:
            # 新建记录
            total = max(req.total_count, len(req.wrong_items))
            score = round(req.correct_count / max(total, 1) * 100, 1) if req.total_count > 0 else 0
            existing = ExamResult(
                user_id=user.id,
                node_id=node_id,
                score=score,
                passed=score >= 60,
                details=_json.dumps(new_details, ensure_ascii=False),
                completed_at=sql_func.now(),
            )
            db.add(existing)
        else:
            # 合并：保留已有错题，追加新错题（去重：同一问题只保留最新的）
            old_details = []
            if existing.details:
                try:
                    old_details = _json.loads(existing.details) if isinstance(existing.details, str) else existing.details
                except (_json.JSONDecodeError, TypeError):
                    old_details = []

            # 用 question 文本去重
            existing_questions = {d.get('question', '') for d in old_details}
            filtered_new = [d for d in new_details if d.get('question', '') not in existing_questions]

            merged = old_details + filtered_new
            existing.details = _json.dumps(merged, ensure_ascii=False)

            # ★ 更新得分：quiz 错题合并后取较低分，确保错题能在温故知新中显示
            if req.total_count > 0:
                new_score = round(req.correct_count / req.total_count * 100, 1)
                existing.score = min(existing.score or 100, new_score)  # 取较低分（有错题就降低分数）
            existing.passed = (existing.score >= 60)
            existing.completed_at = sql_func.now()

        await db.commit()
        await db.refresh(existing)

        # ★ 触发能力值更新（练习完成/错题）
        try:
            from app.services.ability_service import ability_service
            if req.wrong_items:
                # 有错题标记为练习行为
                await ability_service.on_event(db, user.id, "complete_quiz", {"node_id": node_id})
        except Exception as e:
            print(f"[Ability] 练习题能力值更新失败: {e}")

        # ★ 新增：练习题完成后写入学习事件
        try:
            from app.services.learning_record_service import learning_record_service
            await learning_record_service.log_event(
                db=db,
                user_id=user.id,
                event_type="quiz_completed",
                node_id=node_id,
                score=round(req.correct_count / max(req.total_count, 1) * 100, 1) if req.total_count else 0,
                event_data={
                    "correct_count": req.correct_count,
                    "total_count": req.total_count,
                    "wrong_count": len(req.wrong_items),
                },
            )
        except Exception as e:
            print(f"[Quiz] 学习事件记录失败: {e}")

        return {
            "success": True,
            "node_id": node_id,
            "saved_wrong_count": len(new_details),
            "total_wrong_count": len(_json.loads(existing.details)) if existing.details else 0,
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))



