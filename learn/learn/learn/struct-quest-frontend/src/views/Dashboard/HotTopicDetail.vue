<template>
  <div class="hot-detail-page">
    <!-- 顶部横幅 -->
    <div class="detail-hero" :style="{ background: topicData.gradient }">
      <button class="back-btn" @click="$router.back()">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5"><path d="M15 18l-6-6 6-6"/></svg>
        返回
      </button>
      <div class="hero-content">
        <span class="hero-icon">{{ topicData.icon }}</span>
        <h1 class="hero-title">{{ topicData.title }}</h1>
        <div class="hero-meta">
          <span class="hero-tag">{{ topicData.tag }}</span>
          <span class="hero-source">{{ topicData.source }}</span>
          <span class="hero-difficulty" :class="'diff-' + topicData.difficulty">
            {{ difficultyLabel(topicData.difficulty) }}
          </span>
        </div>
        <p class="hero-desc">{{ topicData.fullDesc || topicData.desc }}</p>
      </div>
    </div>

    <!-- Tab 导航 -->
    <div class="tab-nav" ref="tabNavRef">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-btn"
        :class="{ active: activeTab === tab.key }"
        @click="switchTab(tab.key)"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        {{ tab.label }}
        <span v-if="tab.count" class="tab-count">{{ tab.count }}</span>
      </button>
    </div>

    <!-- Tab 内容 -->
    <div class="tab-content">
      <!-- 📖 文档/笔记 Tab -->
      <div v-if="activeTab === 'doc'" class="content-section animate-in">
        <div class="section-card" v-for="(doc, i) in contentData.documents" :key="i">
          <div class="card-header-row">
            <span class="card-doc-icon">📄</span>
            <h3 class="card-title">{{ doc.title }}</h3>
            <el-tag size="small" :type="doc.level === 'core' ? 'danger' : 'info'">{{ doc.level === 'core' ? '核心' : '扩展' }}</el-tag>
          </div>
          <div class="card-body-text" v-html="renderMarkdown(doc.content)"></div>
          <div class="card-footer-meta">
            <span><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#999" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg> {{ doc.readTime }}分钟</span>
            <span>{{ doc.points?.length || 0 }}个知识点</span>
          </div>
        </div>
      </div>

      <!-- 🎬 视频 Tab -->
      <div v-if="activeTab === 'video'" class="content-section animate-in">
        <div class="video-grid">
          <div v-for="(vid, i) in contentData.videos" :key="i" class="video-card">
            <div class="video-thumb" :style="{ background: vid.thumbGradient }">
              <span class="video-play-btn">▶</span>
              <span class="video-duration">{{ vid.duration }}</span>
            </div>
            <div class="video-info">
              <h4 class="video-title">{{ vid.title }}</h4>
              <p class="video-desc">{{ vid.desc }}</p>
              <div class="video-meta">
                <span>{{ vid.platform }}</span>
                <span>👀 {{ vid.views }}</span>
                <span v-if="vid.isRecommended" class="video-rec-badge">AI推荐</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 📊 PPT/思维导图 Tab -->
      <div v-if="activeTab === 'ppt'" class="content-section animate-in">
        <div class="ppt-container">
          <div v-for="(slide, i) in contentData.pptSlides" :key="i" class="ppt-slide" :style="{ borderColor: slide.color + '30', background: slide.bgColor || '#fff' }">
            <div class="slide-header" :style="{ borderBottomColor: slide.color + '20' }">
              <span class="slide-num">Slide {{ i + 1 }}</span>
              <span class="slide-title" :style="{ color: slide.color }">{{ slide.title }}</span>
            </div>
            <div class="slide-content">
              <ul class="slide-points">
                <li v-for="(pt, j) in slide.points" :key="j">{{ pt }}</li>
              </ul>
              <div v-if="slide.code" class="slide-code-block">
                <pre><code>{{ slide.code }}</code></pre>
              </div>
              <div v-if="slide.diagram" class="slide-diagram">
                {{ slide.diagram }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ✏️ 题目 Tab -->
      <div v-if="activeTab === 'exercise'" class="content-section animate-in">
        <div class="exercise-header">
          <h3>📝 章节练习题</h3>
          <p class="exercise-subtitle">共{{ totalExercises }}道题 · 建议用时{{ estimatedTime }}分钟</p>
          <div class="exercise-actions">
            <button class="action-btn primary" @click="startExamMode">
              ⏱️ 模拟考试模式（限时）
            </button>
            <button class="action-btn" @click="toggleShowAnswers">
              {{ showAnswers ? '隐藏答案' : '显示答案' }}
            </button>
          </div>
        </div>

        <div class="exercise-list">
          <div v-for="(ex, i) in contentData.exercises" :key="i" class="exercise-item" :class="ex.type">
            <div class="ex-header">
              <span class="ex-num">{{ i + 1 }}</span>
              <span class="ex-type-tag" :class="ex.type">{{ typeLabel(ex.type) }}</span>
              <span v-if="ex.difficulty" class="ex-diff" :class="'diff-' + ex.difficulty">{{ difficultyLabel(ex.difficulty) }}</span>
            </div>
            <div class="ex-question">{{ ex.question }}</div>
            
            <!-- 选择题选项 -->
            <div v-if="ex.type === 'choice'" class="ex-options">
              <label v-for="(opt, j) in ex.options" :key="j" class="ex-option" :class="{ correct: showAnswers && opt.isCorrect, wrong: userAnswers[i] === opt.key && !opt.isCorrect && showAnswers }">
                <input type="radio" :name="'q' + i" :value="opt.key" v-model="userAnswers[i]" />
                <span class="opt-key">{{ opt.key }}</span>
                {{ opt.text }}
              </label>
            </div>

            <!-- 判断题 -->
            <div v-if="ex.type === 'judge'" class="ex-options judge-options">
              <label class="ex-option" :class="{ correct: showAnswers && ex.answer, wrong: userAnswers[i] !== null && userAnswers[i] !== ex.answer && showAnswers }">
                <input type="radio" :name="'q' + i" value="true" v-model="userAnswers[i]" /> ✓ 正确
              </label>
              <label class="ex-option" :class="{ correct: showAnswers && !ex.answer, wrong: userAnswers[i] !== null && userAnswers[i] === ex.answer && showAnswers }">
                <input type="radio" :name="'q' + i" value="false" v-model="userAnswers[i]" /> ✗ 错误
              </label>
            </div>

            <!-- 填空题 / 编程题 -->
            <div v-if="ex.type === 'fill' || ex.type === 'code'" class="ex-input-area">
              <textarea v-model="userAnswers[i]" placeholder="在此输入你的答案..." rows="3"></textarea>
            </div>

            <!-- 解析（显示答案后） -->
            <transition name="expand">
              <div v-if="showAnswers" class="ex-explanation" :class="ex.type">
                <div class="explain-label">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
                  解析
                </div>
                <div class="explain-content">
                  <p v-if="ex.explanation" v-html="renderMarkdown(ex.explanation)"></p>
                  <div v-if="ex.answerCode" class="answer-code">
                    <strong>参考代码：</strong>
                    <pre><code>{{ ex.answerCode }}</code></pre>
                  </div>
                  <div v-if="ex.tips" class="ex-tips">
                    💡 <strong>提示：</strong>{{ ex.tips }}
                  </div>
                  <div v-if="ex.relatedPoints" class="related-points">
                    关联知识点：
                    <span v-for="(rp, k) in ex.relatedPoints" :key="k" class="rp-tag">{{ rp }}</span>
                  </div>
                </div>
              </div>
            </transition>
          </div>
        </div>

        <!-- 提交结果 -->
        <div v-if="submitted" class="submit-result" :class="{ pass: score >= 60, fail: score < 60 }">
          <h3>{{ score >= 60 ? '🎉 通过！' : '💪 继续加油！' }}</h3>
          <div class="result-score">
            <span class="score-num">{{ score }}</span>
            <span class="score-unit">分</span>
          </div>
          <p class="result-detail">{{ correctCount }}/{{ totalExercises }} 正确</p>
        </div>

        <button v-if="!submitted" class="submit-btn" @click="submitExercises" :disabled="isSubmitting">
          {{ isSubmitting ? '提交中...' : '提交答案' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSessionStore } from '../../store/session'

const route = useRoute()
const router = useRouter()
const session = useSessionStore()

// ═══ 当前模式 ═══
const currentMode = computed(() => route.query.mode || session.learningMode || 'beginner')

// ═══ Tab 定义 ═══
const tabs = [
  { key: 'doc', label: '文档', icon: '📖', count: null },
  { key: 'video', label: '视频', icon: '🎬', count: null },
  { key: 'ppt', label: 'PPT大纲', icon: '📊', count: null },
  { key: 'exercise', label: '题目', icon: '✏️', count: null },
]
const activeTab = ref('doc')

function switchTab(key) {
  activeTab.value = key
}

// ═══ 根据topicId获取内容数据 ═══
const topicId = computed(() => route.params.topicId)

// 模拟数据：根据不同模式和topicId返回不同的丰富内容
const topicData = computed(() => {
  const id = topicId.value
  // 从route query或session获取mode
  const mode = currentMode.value
  
  // 默认数据，后续可从后端API加载
  return getMockTopicData(id, mode)
})

const contentData = computed(() => {
  const id = topicId.value
  const mode = currentMode.value
  return getMockContentData(id, mode)
})

// ═══ 题目相关状态 ═══
const userAnswers = ref({})
const showAnswers = ref(false)
const submitted = ref(false)
const score = ref(0)
const correctCount = ref(0)
const isSubmitting = ref(false)

const totalExercises = computed(() => contentData.value.exercises?.length || 0)
const estimatedTime = computed(() => Math.ceil(totalExercises.value * 1.5))

function toggleShowAnswers() {
  showAnswers.value = !showAnswers.value
}

async function submitExercises() {
  isSubmitting.value = true
  
  // 模拟评分逻辑
  let correct = 0
  const exercises = contentData.value.exercises || []
  
  for (let i = 0; i < exercises.length; i++) {
    const ex = exercises[i]
    if (ex.type === 'choice') {
      if (userAnswers.value[i] && ex.options.find(o => o.key === userAnswers.value[i]?.toString())?.isCorrect) {
        correct++
      }
    } else if (ex.type === 'judge') {
      if (userAnswers.value[i]?.toString() === String(ex.answer)) correct++
    }
    // fill/code 类型暂不做自动判分
  }

  await new Promise(r => setTimeout(r, 600))
  
  score.value = Math.round((correct / exercises.length) * 100)
  correctCount.value = correct
  submitted.value = true
  showAnswers.value = true
  isSubmitting.value = false

  // 记录到学习日历
  recordLearningToCalendar()
}

function startExamMode() {
  alert('模拟考试模式：限时完成所有题目，倒计时即将开始...')
}

function recordLearningToCalendar() {
  // 这里可以调用后端API记录今日的学习活动
  console.log('[HotTopicDetail] 记录学习到日历:', topicData.value.title, score.value + '分')
}

// ═══ 工具函数 ═══
function difficultyLabel(d) {
  const map = { easy: '入门', medium: '中等', hard: '困难' }
  return map[d] || d
}
function typeLabel(t) {
  const map = { choice: '选择题', judge: '判断题', fill: '填空题', code: '编程题' }
  return map[t] || t
}
function renderMarkdown(text) {
  if (!text) return ''
  // 简单的markdown转换（实际项目中可用marked库）
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br/>')
}

onMounted(() => {
  // 更新tabs的count
  const data = contentData.value
  tabs[0].count = data.documents?.length
  tabs[1].count = data.videos?.length
  tabs[2].count = data.pptSlides?.length
  tabs[3].count = data.exercises?.length
})

// ═══ Mock 数据生成器 ═══
function getMockTopicData(id, mode) {
  // 基础数据映射表
  const baseTopics = {
    basic_0: {
      title: '3分钟看懂什么是数组',
      icon: '🟰',
      tag: '入门',
      source: '数据结构 · 入门',
      heat: '12.1k',
      gradient: 'linear-gradient(135deg, #22c55e, #4ade80)',
      difficulty: 'easy',
      fullDesc: '数组是计算机科学中最基础的数据结构之一。想象你有一排带编号的储物柜——这就是数组的本质。本专题将用最通俗的语言带你理解数组的内存模型、随机访问特性、动态扩容原理。',
    },
    basic_1: {
      title: '链表到底是什么？动画演示',
      icon: '🔗',
      tag: '链表',
      source: '数据结构 · 入门',
      heat: '9.8k',
      gradient: 'linear-gradient(135deg, #22c55e, #86efac)',
      difficulty: 'easy',
      fullDesc: '链表是数据结构中最重要的基础概念之一。不同于数组，链表的元素在内存中不需要连续排列。通过"指针"将零散的内存块串联起来。本专题通过大量动画演示帮你彻底理解链表的插入、删除、遍历操作。',
    },
    beginner_0: {
      title: 'DeepSeek 如何实现推理能力',
      icon: '🤖',
      tag: 'AI前沿',
      source: '技术解析 · 热门',
      heat: '18.2k',
      gradient: 'linear-gradient(135deg, #3b82f6, #60a5fa)',
      difficulty: 'medium',
      fullDesc: '深入解析大语言模型的推理机制，从MoE架构到强化学习训练，全面理解DeepSeek等国产大模型的技术创新点。涵盖注意力机制、KV Cache、推测解码等核心技术。',
    },
    beginner_1: {
      title: '红黑树 vs AVL树：该如何选择',
      icon: '🌳',
      tag: '二叉树',
      source: '数据结构 · 核心',
      heat: '11.5k',
      gradient: 'linear-gradient(135deg, #1d4ed8, #3b82f6)',
      difficulty: 'medium',
      fullDesc: '红黑树与AVL树都是自平衡二叉搜索树的经典实现。它们各有优劣，适用于不同场景。本专题从插入效率、查询效率、实现复杂度三个维度进行深度对比分析，并给出选择建议。',
    },
    exam_0: {
      title: '近三年考研数据结构高频考点Top10',
      icon: '📝',
      tag: '考研必备',
      source: '考试 · 高频',
      heat: '23.1k',
      gradient: 'linear-gradient(135deg, #f97316, #fb923c)',
      difficulty: 'hard',
      fullDesc: '统计2024-2026年考研408真题，这些知识点反复出现！链表操作、二叉树遍历、排序算法稳定性、哈希表冲突处理、图的遍历、最短路径...每一个考点都配有真题解析和解题模板。',
    },
    exam_1: {
      title: '排序算法稳定性：考试必考判断题',
      icon: '⚡',
      tag: '排序',
      source: '考试 · 必考',
      heat: '19.8k',
      gradient: 'linear-gradient(135deg, #ea580c, #f97316)',
      difficulty: 'hard',
      fullDesc: '一张表格记住所有常见排序算法的稳定性、时间复杂度、空间复杂度和适用场景。附历年考研/软考真题中的典型判断题，覆盖冒泡、选择、插入、快排、归并、堆排序、希尔排序等全部主流排序算法。',
    },
  }

  // 如果找不到精确匹配，尝试模糊匹配
  let data = baseTopics[`${mode}_${id}`] || baseTopics[id]
  
  // 最终兜底
  if (!data) {
    data = {
      title: id.replace(/_/g, ' ') || '未知主题',
      icon: '📌',
      tag: '知识',
      source: '推荐',
      heat: '--',
      gradient: 'linear-gradient(135deg, #8b5cf6, #a78bfa)',
      difficulty: 'medium',
      fullDesc: '这是一个关于该知识点的深入学习专题，包含文档、视频、PPT大纲和练习题等多种形式的学习资源。',
    }
  }

  return data
}

function getMockContentData(id, mode) {
  // 根据不同模式生成不同难度和深度的内容
  const levelMultiplier = mode === 'exam' ? 2 : mode === 'beginner' ? 1 : 0.5

  // ═══ 辅助函数：安全拼接内容（避免反引号嵌套问题） ═══
  const _ = (parts) => parts.join('')
  const b = (val) => mode === 'basic' ? val : null
  const m = (basicVal, otherVal) => mode === 'basic' ? basicVal : otherVal

  // 文档内容
  const documents = [
    {
      title: m('一、什么是数组？', '一、数组的核心概念'),
      level: 'core',
      readTime: 8 + Math.floor(levelMultiplier * 4),
      points: ['内存连续分配', 'O(1)随机访问', '固定大小 vs 动态扩容'],
      content: _([
        '**', m('想象一下...', '定义'), '**\n\n',
        m(
          '你家里有一个书架，上面有10个格子，每个格子上标着编号1~10。你想拿第5本书时，直接走到第5号格子就行——不用从第1本一本翻过去。**这就是数组的核心思想！**',
          '数组（Array）是一种线性数据结构，它使用一段**连续的内存空间**来存储相同类型的元素。每个元素可以通过一个**下标（index）**在 O(1) 时间内直接访问。\n\n### 时间复杂度\n- **访问**: O(1)\n- **查找**: O(n)\n- **插入/删除尾部**: O(1) 均摊\n- **插入/删除中间**: O(n)'
        ),
        '\n\n## ', m('为什么这么快？', '核心优势'), '\n\n',
        '因为数组的元素在内存里是**挨着排**的。当你知道第一个元素的地址后，想找第N个元素，只需要做一个简单的数学计算：\n\n',
        '$$address(N) = address(0) + N \\times elementSize$$\n\n',
        '这就是**随机访问**的能力！\n\n---\n\n',
        '## ', m('什么时候用数组？', '适用场景'), '\n',
        m(
          '\n- 存一批成绩单\n- 游戏里的背包物品栏\n- 图片像素点阵',
          '\n- 需要频繁按索引访问的场景\n- 数据量已知且变化不大\n- 作为更复杂数据结构的底层存储\n- 实现哈希表、堆、邻接矩阵等'
        ),
        '\n\n## 注意事项\n',
        m(
          '数组创建后大小就定了（大多数语言），不能随意加长缩短。就像你的书架只有10个格子，想放第11本书就得换个新的大书架！',
          '静态数组的大小在编译期确定；动态数组支持运行时扩容（如 C++ std::vector、Java ArrayList）。扩容策略通常是将容量翻倍（amortized O(1))。'
        )
      ]),
    },
    {
      title: m('二、动手试试', '二、数组的基本操作'),
      level: 'core',
      readTime: 10,
      points: [m('创建数组', '初始化'), m('读写元素', '增删改查'), '遍历'],
      content: _([
        m('让我们用生活中的例子来理解数组的操作...', '以下是各语言的数组初始化方式：'),
        '\n\n### ', m('创建一个数组', '初始化示例'), '\n\n',
        '```python\n# Python\narr = [1, 2, 3, 4, 5]\n\n# JavaScript\nconst arr = new Array(10).fill(0)\n\n# Java\nint[] arr = new int[] {1, 2, 3};\n```\n\n',
        '### ', m('读取第3个数', '访问元素'), '\n\n',
        '```python\nprint(arr[2])  # 输出: 3 （注意下标从0开始！）\n```\n\n',
        '> **', m('💡 小贴士：程序员数数从0开始哦！', '**注意**：大多数编程语言的下标从0开始。'), '**\n\n',
        '### ', m('修改一个值', '修改元素'), '\n\n',
        '```python\narr[0] = 100  # 把第一个位置改成100\n```\n'
      ]),
    },
    {
      title: m('三、进阶小知识', '三、高级话题'),
      level: mode === 'exam' ? 'core' : 'extend',
      readTime: 6,
      points: m(['多维数组', '越界问题'], ['动态数组扩容', '缓存友好性']),
      content: mode === 'basic'
        ? _([
            '## 多维数组\n\n',
            '二维数组就像一个棋盘——有行有列。其实它就是"数组的数组"！\n\n',
            '```\n棋盘[行][列]\n棋盘[0][0] = "车"\n棋盘[0][7] = "车"\n```\n\n',
            '## 小心越界！\n\n',
            '如果你的数组只有5个格子，却去读第100个格子……程序会崩溃！这叫"数组越界"，是最常见的bug之一。'
          ])
        : _([
            '## 动态数组扩容机制\n\n',
            '当容量不足时，通常采用 **2倍扩容** 策略：\n\n',
            '1. 分配一块 2倍 大小的内存\n2. 将旧数据复制到新内存\n3. 释放旧内存\n\n',
            '均摊时间复杂度仍为 **O(1)**。\n\n',
            '## CPU缓存友好性\n\n',
            '由于数组内存连续，CPU预取（Prefetch）效果极佳。这也是为什么数组遍历比链表快的原因之一。'
          ]),
    },
  ]

  // 视频列表
  const videos = [
    {
      title: mode === 'basic' ? '【动画演示】数组到底怎么工作？(3分钟)' : '数组底层原理深度解析 (15分钟)',
      desc: mode === 'basic' 
        ? '配合可视化动画，直观感受数组的内存布局和访问过程' 
        : '从汇编层面讲解数组寻址过程、Cache Line命中原理',
      platform: 'B站',
      views: mode === 'basic' ? '52万' : '23万',
      duration: mode === 'basic' ? '3:28' : '14:52',
      thumbGradient: 'linear-gradient(135deg, #667eea, #764ba2)',
      isRecommended: true,
    },
    {
      title: mode === 'basic' ? '手写一个动态数组（入门级）' : '手写 ArrayList 源码级别解析',
      desc: mode === 'basic' ? '跟着一步步实现' : '逐行解读 JDK/C++ STL 源码',
      platform: 'B站',
      views: '18万',
      duration: '22:10',
      thumbGradient: 'linear-gradient(135deg, #f093fb, #f5576c)',
      isRecommended: false,
    },
    {
      title: mode === 'basic' ? 'LeetCode 数组专题：前10道必刷题' : '数组面试高频题 Top50 详解',
      desc: mode === 'basic' ? '两数之和、合并两个有序数组等' : '双指针、滑动窗口、前缀和技巧全覆盖',
      platform: 'B站',
      views: '35万',
      duration: mode === 'basic' ? '45:00' : '120:00',
      thumbGradient: 'linear-gradient(135deg, #4facfe, #00f2fe)',
      isRecommended: true,
    },
  ]

  // PPT 大纲
  const pptSlides = [
    {
      title: '概述',
      color: '#3b82f6',
      bgColor: '#eff6ff',
      points: [
        mode === 'basic' ? '什么是数组？' : '数组的定义与特征',
        '历史背景（最早的数据结构）',
        mode === 'basic' ? '生活中哪些地方用到数组？' : '在各编程语言中的实现差异',
        '本章学习目标',
      ],
    },
    {
      title: '内存模型',
      color: '#22c55e',
      bgColor: '#f0fdf4',
      points: [
        '连续内存布局示意图',
        '地址计算公式',
        mode === 'basic' ? '为什么数组下标从0开始？' : 'Cache Line 与空间局部性',
        '对比：数组 vs 链表的内存布局',
      ],
      diagram: '[ 图解：连续内存 vs 链式内存 对比图 ]',
    },
    {
      title: '基本操作',
      color: '#E07A5F',
      bgColor: '#fff7ed',
      points: [
        '① 创建/初始化',
        '② 读取/修改',
        '③ 遍历',
        '④ 插入/删除（及其复杂度）',
      ],
      code: mode === 'basic' 
        ? _([
            '// 创建并遍历\n',
            'let arr = [10, 20, 30, 40];\n',
            'for (let i = 0; i < arr.length; i++) {\n',
            '  console.log(arr[i]);\n',
            '}'
          ])
        : _([
            '// Java 动态数组扩容\n',
            'public void add(E e) {\n',
            '  if (size == capacity) grow();\n',
            '  elementData[size++] = e;\n',
            '}\n',
            'private void grow() {\n',
            '  int oldCap = capacity;\n',
            '  int newCap = oldCap + (oldCap >> 1); // x1.5\n',
            '  Arrays.copyOf(elementData, newCap);\n',
            '}'
          ]),
    },
    {
      title: mode === 'basic' ? '实战小练习' : '经典题目解析',
      color: '#8b5cf6',
      bgColor: '#f5f3ff',
      points: [
        mode === 'basic' ? '找出最大的数字' : '两数之和 (LeetCode 1)',
        mode === 'basic' ? '反转数组' : '合并两个有序数组 (LeetCode 88)',
        mode === 'basic' ? '去掉重复的数字' : '移除元素 (LeetCode 27)',
        mode === 'basic' ? '' : '接雨水 (LeetCode 42) - 困难题',
      ].filter(Boolean),
    },
  ]

  // 练习题 —— 根据模式调整难度和数量
  const exerciseCount = mode === 'exam' ? 8 : mode === 'beginner' ? 5 : 3
  const exercises = []

  for (let i = 0; i < exerciseCount; i++) {
    if (mode === 'basic' && i === 0) {
      exercises.push({
        type: 'choice',
        difficulty: 'easy',
        question: '以下关于数组的描述，哪一个是**正确**的？',
        options: [
          { key: 'A', text: '数组中的元素必须类型相同', isCorrect: true },
          { key: 'B', text: '数组可以在任意位置以 O(1) 时间插入元素', isCorrect: false },
          { key: 'C', text: '数组的下标从1开始', isCorrect: false },
          { key: 'D', text: '数组一旦创建就不能改变大小', isCorrect: false },
        ],
        explanation: '**A正确**。数组要求元素类型相同（同构）。B错误，中间插入需要移动后续元素，为O(n)。C错误，大多数语言从0开始。D错误，动态数组可以扩容。',
        relatedPoints: ['数组定义', '时间复杂度'],
        tips: '记住：数组 = 同类型 + 连续内存 + 下标访问',
      })
    } else if ((mode === 'beginner' || mode === 'exam') && i <= 2) {
      exercises.push({
        type: 'choice',
        difficulty: mode === 'exam' ? 'hard' : 'medium',
        question: i === 1 
          ? '在一个长度为 n 的数组中，删除某个指定元素的时间复杂度是多少？'
          : '以下哪种情况下，数组的访问速度明显优于链表？',
        options: [
          { key: 'A', text: i === 1 ? 'O(n)，需要移动后续元素' : '频繁的头插操作', isCorrect: i === 2 },
          { key: 'B', text: i === 1 ? 'O(1)，直接跳过即可' : '按索引随机访问', isCorrect: i === 1 },
          { key: 'C', text: i === 1 ? 'O(log n)，可以用二分查找' : '频繁的中间插入删除', isCorrect: false },
          { key: 'D', text: i === 1 ? 'O(n²)，最坏情况' : '不知道数据量大小', isCorrect: false },
        ],
        explanation: i === 1 
          ? '**B正确但需注意**：如果只是标记删除（lazy deletion）则可以是O(1)；如果要真正移除并保持紧凑，则需要O(n)挪动后续元素。'
          : '**B正确**。数组的随机访问是O(1)优势来源，得益于连续内存+公式计算地址。',
        answerCode: i === 1 ? _([
            '// 删除元素 - 紧凑方式 O(n)\n',
            'def removeElement(nums, val):\n',
            '    i = 0\n',
            '    for j in range(len(nums)):\n',
            '        if nums[j] != val:\n',
            '            nums[i] = nums[j]\n',
            '            i += 1\n',
            '    return i'
          ]) : '',
        relatedPoints: i === 1 ? ['数组删除', '时间复杂度'] : ['随机访问', 'Cache友好性'],
        tips: i === 1 ? '面试常考！注意区分"逻辑删除"和"物理删除"' : '这是数组相对于链表的最大优势',
      })
    } else if (i === 3 && mode !== 'basic') {
      exercises.push({
        type: 'judge',
        difficulty: 'medium',
        question: '动态数组每次扩容时，将容量扩大为原来的2倍，其均摊插入时间复杂度为 O(1)。这个说法正确吗？',
        answer: true,
        explanation: '**正确**。虽然单次扩容操作是O(n)，但由于每扩容一次就能支撑后续n次O(1)插入，摊下来每次操作平均成本趋近于常数。这被称为"均摊分析"(Amortized Analysis)。',
        relatedPoints: ['均摊分析', '动态扩容', '几何增长'],
        tips: '记住口诀："加倍扩容，均摊常数"',
      })
    } else {
      exercises.push({
        type: mode === 'exam' && i > 4 ? 'code' : 'fill',
        difficulty: mode === 'exam' ? 'hard' : (mode === 'beginner' ? 'medium' : 'easy'),
        question: mode === 'exam'
          ? '请实现一个支持泛型、自动扩容的动态数组类 DynamicArray，要求包含 push、pop、get、insert、delete 方法，并分析每个方法的时间和空间复杂度。'
          : mode === 'beginner'
            ? '请简述数组在以下场景下的优劣势：(1) 需要频繁随机访问 (2) 需要频繁头部插入 (3) 已知数据量且不变'
            : '请用一个生活例子解释"数组下标为什么从0开始"：',
        explanation: mode === 'exam'
          ? '标准答案应包含：内部数组容器、size/capacity跟踪、扩容阈值检查、copy语义、异常边界处理。'
          : mode === 'beginner'
            ? '(1) 优势：O(1)随机访问，Cache友好；(2) 劣势：O(n)头部插入；(3) 最佳场景，无浪费。'
            : '因为数组表示的是"偏移量(offset)"的概念。arr[0] 表示"从起始位置偏移0个单位"，arr[1]就是"偏移1个单位"。这和内存地址的计算方式完全一致。',
        answerCode: mode === 'exam' ? _([
            'class DynamicArray<T> {\n',
            '  private data: T[];\n',
            '  private size: number;\n',
            '  private capacity: number;\n',
            '  \n',
            '  constructor(cap = 16) {\n',
            '    this.data = new Array(cap);\n',
            '    this.size = 0;\n',
            '    this.capacity = cap;\n',
            '  }\n',
            '  \n',
            '  push(val: T): void {\n',
            '    if (this.size === this.capacity) this.grow();\n',
            '    this.data[this.size++] = val;\n',
            '  }\n',
            '  \n',
            '  pop(): T | undefined {\n',
            '    if (this.size === 0) return undefined;\n',
            '    return this.data[--this.size];\n',
            '  }\n',
            '  \n',
            '  get(idx: number): T | undefined {\n',
            '    if (idx < 0 || idx >= this.size) return undefined;\n',
            '    return this.data[idx];\n',
            '  }\n',
            '  \n',
            '  insert(val: T, idx: number): void {\n',
            '    if (idx < 0 || idx > this.size) throw Error("Out of bounds");\n',
            '    if (this.size === this.capacity) this.grow();\n',
            '    for (let i = this.size; i > idx; i--) this.data[i] = this.data[i-1];\n',
            '    this.data[idx] = val;\n',
            '    this.size++;\n',
            '  }\n',
            '  \n',
            '  delete(idx: number): T | undefined {\n',
            '    if (idx < 0 || idx >= this.size) return undefined;\n',
            '    const val = this.data[idx];\n',
            '    for (let i = idx; i < this.size - 1; i++) this.data[i] = this.data[i+1];\n',
            '    this.size--;\n',
            '    return val;\n',
            '  }\n',
            '  \n',
            '  private grow(): void {\n',
            '    this.capacity *= 2; // or * 1.5\n',
            '    const newData = new Array(this.capacity);\n',
            '    for (let i = 0; i < this.size; i++) newData[i] = this.data[i];\n',
            '    this.data = newData;\n',
            '  }\n',
            '}'
          ]) : '',
        relatedPoints: mode === 'exam' ? ['泛型编程', '均摊复杂度', 'Copy-on-write'] : [],
        tips: mode === 'exam' ? '注意边界条件、空数组情况、扩容倍率的选择理由' : '',
      })
    }
  }

  return { documents, videos, pptSlides, exercises }
}
</script>

<style lang="scss" scoped>
.hot-detail-page {
  max-width: 900px;
  margin: 0 auto;
  min-height: 100vh;
  background: #f8f9fa;
}

/* ── Hero ── */
.detail-hero {
  padding: 48px 32px 36px;
  color: #fff;
  position: relative;
  overflow: hidden;
  &::after {
    content: '';
    position: absolute;
    inset: 0;
    background: rgba(0,0,0,0.08);
  }
}
.back-btn {
  position: absolute;
  top: 16px; left: 16px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 14px;
  border-radius: 8px;
  background: rgba(255,255,255,0.2);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255,255,255,0.25);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  &:hover { background: rgba(255,255,255,0.3); transform: translateX(-2px); }
}
.hero-content { position: relative; z-index: 1; }
.hero-icon { font-size: 42px; filter: drop-shadow(0 2px 8px rgba(0,0,0,0.2)); }
.hero-title {
  font-size: 26px;
  font-weight: 800;
  margin: 12px 0 10px;
  letter-spacing: -0.5px;
}
.hero-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.hero-tag {
  padding: 3px 10px;
  border-radius: 6px;
  background: rgba(255,255,255,0.25);
  font-size: 12px;
  font-weight: 700;
}
.hero-source { font-size: 13px; opacity: 0.85; }
.hero-difficulty {
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  &.diff-easy { background: rgba(34,197,94,0.35); }
  &.diff-medium { background: rgba(59,130,246,0.35); }
  &.diff-hard { background: rgba(249,115,22,0.35); }
}
.hero-desc {
  font-size: 15px;
  line-height: 1.65;
  opacity: 0.92;
  max-width: 720px;
  margin: 0;
}

/* ── Tabs ── */
.tab-nav {
  display: flex;
  gap: 0;
  background: #fff;
  padding: 0 20px;
  border-bottom: 1px solid #eee;
  position: sticky;
  top: 0;
  z-index: 10;
}
.tab-btn {
  padding: 14px 18px;
  border: none;
  background: transparent;
  font-size: 14px;
  font-weight: 600;
  color: #888;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 2.5px solid transparent;
  display: flex;
  align-items: center;
  gap: 5px;
  .tab-icon { font-size: 16px; }
  .tab-count {
    font-size: 10px;
    padding: 1px 6px;
    border-radius: 8px;
    background: #f0f0f0;
    color: #888;
    font-weight: 700;
  }
  &:hover { color: #555; background: #fafafa; }
  &.active {
    color: var(--theme-color, #E07A5F);
    border-bottom-color: var(--theme-color, #E07A5F);
    .tab-count { background: rgba(var(--theme-color-rgb), 0.1); color: var(--theme-color, #E07A5F); }
  }
}

/* ── Content ── */
.tab-content { padding: 24px 20px 48px; }
.content-section { animation: fadeInUp 0.4s ease both; }

/* ── Document Cards ── */
.section-card {
  background: #fff;
  border-radius: 14px;
  border: 1px solid #eee;
  padding: 22px 24px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.card-header-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.card-doc-icon { font-size: 20px; }
.card-title { font-size: 17px; font-weight: 700; color: #333; margin: 0; flex: 1; }
.card-body-text {
  font-size: 14px;
  line-height: 1.75;
  color: #555;
  code { background: #f5f5f5; padding: 1px 5px; border-radius: 4px; font-size: 13px; font-family: 'JetBrains Mono', monospace; }
  strong { color: #222; font-weight: 700; }
}
.card-footer-meta {
  display: flex;
  gap: 16px;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid #f5f5f5;
  font-size: 12px;
  color: #aaa;
  span { display: flex; align-items: center; gap: 3px; }
}

/* ── Video Grid ── */
.video-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}
.video-card {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #eee;
  transition: all 0.25s;
  &:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,0.08); .video-thumb { transform: scale(1.03); } }
}
.video-thumb {
  height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  transition: transform 0.3s ease;
}
.video-play-btn {
  width: 44px; height: 44px;
  border-radius: 50%;
  background: rgba(255,255,255,0.92);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: #E07A5F;
  box-shadow: 0 2px 12px rgba(0,0,0,0.15);
  z-index: 1;
}
.video-duration {
  position: absolute;
  bottom: 8px; right: 8px;
  padding: 2px 7px;
  border-radius: 4px;
  background: rgba(0,0,0,0.65);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
}
.video-info { padding: 12px 14px 14px; }
.video-title { font-size: 14px; font-weight: 700; color: #333; margin: 0 0 5px; line-height: 1.3; }
.video-desc { font-size: 12px; color: #999; margin: 0 0 8px; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.video-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: #bbb;
}
.video-rec-badge {
  padding: 1px 6px;
  border-radius: 6px;
  background: rgba(139,92,246,0.1);
  color: #7c3aed;
  font-weight: 600;
  font-size: 10px;
}

/* ── PPT Slides ── */
.ppt-container { display: flex; flex-direction: column; gap: 16px; }
.ppt-slide {
  border-radius: 12px;
  border-width: 1.5px;
  border-style: solid;
  overflow: hidden;
}
.slide-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  border-bottom-width: 1px;
  border-bottom-style: solid;
}
.slide-num { font-size: 11px; color: #999; font-weight: 600; }
.slide-title { font-size: 15px; font-weight: 800; }
.slide-content { padding: 16px 20px 18px; }
.slide-points { margin: 0 0 12px; padding-left: 20px; list-style: none;
  li {
    font-size: 14px; color: #444; line-height: 1.75;
    padding: 3px 0;
    &::before { content: "▸"; color: inherit; margin-right: 8px; font-weight: 700; }
  }
}
.slide-code-block {
  background: #1e1e2e;
  border-radius: 8px;
  padding: 14px 16px;
  margin-top: 10px;
  pre { margin: 0; }
  code { color: #cdd6f4; font-family: 'JetBrains Mono', monospace; font-size: 12px; line-height: 1.6; white-space: pre-wrap; word-break: break-all; }
}
.slide-diagram {
  text-align: center;
  padding: 20px;
  background: #f8f9fc;
  border-radius: 8px;
  border: 1px dashed #ddd;
  color: #999;
  font-size: 13px;
  margin-top: 10px;
}

/* ── Exercises ── */
.exercise-header {
  background: linear-gradient(135deg, rgba(99,102,241,0.06), rgba(234,88,12,0.06));
  border-radius: 12px;
  padding: 20px 22px;
  margin-bottom: 20px;
}
.exercise-header h3 { font-size: 17px; font-weight: 800; margin: 0 0 4px; }
.exercise-subtitle { font-size: 13px; color: #888; margin: 0 0 12px; }
.exercise-actions { display: flex; gap: 10px; flex-wrap: wrap; }
.action-btn {
  padding: 8px 18px;
  border-radius: 8px;
  border: 1.5px solid #e0e0e0;
  background: #fff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  &.primary { background: linear-gradient(135deg, #6366f1, #4f46e5); color: #fff; border-color: #6366f1; }
  &:hover:not(.primary) { border-color: #ccc; background: #fafafa; }
  &:hover.primary { box-shadow: 0 4px 14px rgba(99,102,241,0.3); transform: translateY(-1px); }
}

.exercise-list { display: flex; flex-direction: column; gap: 18px; }
.exercise-item {
  background: #fff;
  border-radius: 14px;
  border: 1px solid #eee;
  padding: 20px 22px;
  &.code, &.fill { border-left: 3px solid #8b5cf6; }
  &.choice, &.judge { border-left: 3px solid #3b82f6; }
}
.ex-header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.ex-num {
  width: 26px; height: 26px;
  border-radius: 50%;
  background: #f0f0f0;
  color: #666;
  font-size: 12px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.ex-type-tag {
  padding: 2px 8px;
  border-radius: 5px;
  font-size: 10px;
  font-weight: 700;
  background: #f0f0f0;
  color: #777;
  &.choice { background: #eff6ff; color: #2563eb; }
  &.judge { background: #fef3c7; color: #d97706; }
  &.fill { background: #f3e8ff; color: #7c3aed; }
  &.code { background: #ede9fe; color: #6d28d9; }
}
.ex-diff {
  padding: 2px 8px;
  border-radius: 5px;
  font-size: 10px;
  font-weight: 700;
  &.diff-easy { background: #dcfce7; color: #16a34a; }
  &.diff-medium { background: #dbeafe; color: #2563eb; }
  &.diff-hard { background: #fee2e2; color: #dc2626; }
}
.ex-question {
  font-size: 15px;
  font-weight: 500;
  color: #333;
  line-height: 1.6;
  margin: 0 0 14px;
}
.ex-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 4px;
}
.judge-options { flex-direction: row; gap: 16px; }
.ex-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border: 1.5px solid #e8e8e8;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
  color: #444;
  input[type=radio] { accent-color: var(--theme-color, #3b82f6); }
  &:hover { border-color: #ccc; background: #fafafa; }
  &.correct { border-color: #22c55e; background: #f0fdf4; }
  &.wrong { border-color: #ef4444; background: #fef2f2; }
}
.ex-input-area textarea {
  width: 100%;
  padding: 10px 14px;
  border: 1.5px solid #e8e8e8;
  border-radius: 10px;
  resize: vertical;
  font-size: 14px;
  font-family: inherit;
  outline: none;
  &:focus { border-color: var(--theme-color, #3b82f6); box-shadow: 0 0 0 3px rgba(var(--theme-color-rgb), 0.08); }
}

/* ── Explanation ── */
.ex-explanation {
  margin-top: 14px;
  padding: 14px 16px;
  border-radius: 10px;
  &.choice, &.judge { background: #f8faff; border: 1px solid #ede9fe; }
  &.fill, &.code { background: #fffbf0; border: 1px solid #fef3c7; }
}
.explain-label {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  font-weight: 700;
  color: #7c3aed;
  margin-bottom: 8px;
}
.explain-content { font-size: 13px; line-height: 1.65; color: #555;
  p { margin: 0 0 8px; }
}
.answer-code {
  margin: 8px 0;
  pre {
    background: #1e1e2e;
    border-radius: 8px;
    padding: 12px 14px;
    overflow-x: auto;
    margin: 0;
  }
  code { color: #cdd6f4; font-family: 'JetBrains Mono', monospace; font-size: 11px; line-height: 1.5; }
}
.ex-tips { margin-top: 8px; font-size: 12px; color: #E6A23C; strong { color: #E6A23C; } }
.related-points { margin-top: 8px; display: flex; flex-wrap: wrap; gap: 4px;
  .rp-tag { padding: 2px 8px; border-radius: 5px; background: #f0f0f0; font-size: 11px; color: #777; font-weight: 600; }
}

/* ── Submit Result ── */
.submit-result {
  text-align: center;
  padding: 28px 20px;
  border-radius: 14px;
  margin-top: 20px;
  &.pass { background: linear-gradient(135deg, #f0fdf4, #dcfce7); border: 1px solid #bbf7d0; }
  &.fail { background: linear-gradient(135deg, #fef2f2, #fee2e2); border: 1px solid #fecaca; }
  h3 { margin: 0 0 12px; font-size: 20px; }
}
.result-score {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 2px;
  .score-num { font-size: 56px; font-weight: 900; &.pass { color: #16a34a; } &.fail { color: #ef4444; } }
  .score-unit { font-size: 18px; font-weight: 700; color: #999; }
}
.result-detail { font-size: 14px; color: #888; margin: 4px 0 0; }
.submit-btn {
  display: block;
  margin: 20px auto 0;
  padding: 12px 40px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, #E07A5F, #D2654B);
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  &:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(224,122,95,0.35); }
  &:disabled { opacity: 0.5; cursor: not-allowed; }
}

.expand-enter-active, .expand-leave-active { transition: all 0.3s ease; overflow: hidden; }
.expand-enter-from, .expand-leave-to { opacity: 0; max-height: 0; margin-top: 0; padding: 0; }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
</style>
