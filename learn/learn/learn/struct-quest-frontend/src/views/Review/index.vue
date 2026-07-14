<template>
  <div class="review-page">
    <!-- ═══ 顶部 Tab 切换 ═══ -->
    <header class="review-tab-bar">
      <button class="review-tab" :class="{ active: activeTab === 'mistakes' }" @click="switchTab('mistakes')">
        📝 错题本
        <span v-if="activeTab !== 'mistakes' && totalCount > 0" class="tab-badge">{{ totalCount }}</span>
      </button>
      <button class="review-tab" :class="{ active: activeTab === 'resources' }" @click="switchTab('resources')">
        📚 学习资料
        <span v-if="activeTab !== 'resources' && savedTotal > 0" class="tab-badge saved">{{ savedTotal }}</span>
      </button>
    </header>

    <!-- ═══════════════════════════════════════ -->
    <!--  Tab 1: 错题本  ═══ -->
    <!-- ═══════════════════════════════════════ -->
    <template v-if="activeTab === 'mistakes'">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <el-icon class="is-loading"><Loading /></el-icon>
      <p>正在加载错题数据...</p>
    </div>

    <div v-else class="review-body">
      <!-- ═══ 左侧：题目区 ═══ -->
      <main class="question-area">
        <template v-if="selectedQuestion">
          <div class="qa-header">
            <el-tag type="danger" size="small" round effect="dark">{{ selectedQuestion.chapter || currentChapterName }}</el-tag>
            <el-tag type="warning" size="small" round>错题</el-tag>
            <span class="qa-subchapter">{{ selectedQuestion.subChapter || currentSubChapterName }}</span>
          </div>

          <div class="question-card">
            <div class="q-title">
              <span class="q-label">📝 题目</span>
            </div>
            <div class="q-content" v-html="renderMarkdown(selectedQuestion.question)"></div>
          </div>

          <!-- ★ 重做模式 -->
          <div v-if="redoMode && selectedQuestion" class="redo-card">
            <div class="redo-header">
              <span class="redo-label">📝 重新作答</span>
              <button class="redo-cancel-btn" @click="cancelRedo">取消</button>
            </div>
            <div class="q-content" v-html="renderMarkdown(selectedQuestion.question)"></div>
            
            <!-- 选择题 -->
            <div v-if="selectedQuestion.questionType !== 'summary' && selectedQuestion.options?.length > 0" class="redo-options">
              <div
                v-for="(opt, idx) in selectedQuestion.options"
                :key="idx"
                class="redo-option"
                :class="{
                  selected: redoSelected === idx,
                  correct: redoSubmitted && idx === correctOptIndex,
                  wrong: redoSubmitted && redoSelected === idx && idx !== correctOptIndex,
                }"
                @click="!redoSubmitted && (redoSelected = idx)"
              >
                <span class="opt-letter">{{ ['A','B','C','D','E','F'][idx] }}</span>
                <span class="opt-text">{{ opt }}</span>
                <span v-if="redoSubmitted && idx === correctOptIndex" class="opt-icon">✓</span>
                <span v-else-if="redoSubmitted && redoSelected === idx && idx !== correctOptIndex" class="opt-icon">✗</span>
              </div>
            </div>

            <!-- 非选择题（文本输入） -->
            <div v-else-if="selectedQuestion.questionType !== 'summary'" class="redo-text-input">
              <el-input
                v-model="redoTextAnswer"
                type="textarea"
                :rows="3"
                :disabled="redoSubmitted"
                placeholder="请输入你的答案..."
              />
            </div>

            <!-- 汇总类型：无重做 -->
            <div v-else class="redo-no-action">
              <p>此类错题暂无详细作答数据，不支持重新作答。</p>
            </div>

            <div class="redo-actions" v-if="selectedQuestion.questionType !== 'summary'">
              <button v-if="!redoSubmitted" class="redo-submit-btn" @click="submitRedo" :disabled="redoSelected === null && !redoTextAnswer.trim()">
                提交答案
              </button>
              <template v-else>
                <!-- 回答正确，未做选择 -->
                <template v-if="redoCorrect && !redoChoiceMade">
                  <div class="redo-result correct">🎉 回答正确！</div>
                  <button class="redo-remove-btn" @click="confirmRemoveAfterCorrect" :disabled="removing">
                    {{ removing ? '移除中...' : '🗑️ 移除错题' }}
                  </button>
                  <button class="redo-keep-btn" @click="keepMistakeAfterCorrect">📌 保留</button>
                </template>
                <!-- 回答正确，已做选择 -->
                <template v-else-if="redoCorrect && redoChoiceMade">
                  <div class="redo-result correct">{{ redoChoiceResult }}</div>
                </template>
                <!-- 回答错误 -->
                <template v-else>
                  <div class="redo-result wrong">❌ 回答错误</div>
                  <button class="redo-retry-btn" @click="resetRedo">再试一次</button>
                  <button class="redo-next-btn" @click="goToNextQuestion">下一题 →</button>
                </template>
              </template>
            </div>
          </div>

          <!-- 查看答案模式 -->
          <div v-else-if="showAnswer && selectedQuestion" class="answer-card">
            <div class="a-section">
              <div class="a-label">✅ 正确答案</div>
              <div class="a-content" v-html="renderMarkdown(selectedQuestion.correctAnswer)"></div>
            </div>

            <div class="a-section mine">
              <div class="a-label">❌ 你的答案</div>
              <div class="a-content" v-html="renderMarkdown(selectedQuestion.yourAnswer)"></div>
            </div>

            <div class="a-section explanation">
              <div class="a-label">💡 解析</div>
              <div class="a-content" v-html="renderMarkdown(selectedQuestion.explanation)"></div>
            </div>

            <div class="a-tags">
              <span class="error-type-tag">{{ errorTypeLabel(selectedQuestion.errorType) }}</span>
              <span class="difficulty-tag">难度: {{ selectedQuestion.difficulty }}</span>
            </div>

            <!-- ★ 答案卡片底部操作按钮 -->
            <div class="answer-actions">
              <button class="action-btn redo-btn" @click="startRedo">
                🔄 重新做
              </button>
              <button class="action-btn remove-btn" @click="removeMistake(selectedQuestion)" :disabled="removing">
                {{ removing ? '移除中...' : '🗑️ 移除错题' }}
              </button>
            </div>
          </div>

          <div v-else-if="selectedQuestion" class="answer-lock">
            <span class="lock-icon">🔒</span>
            <p>点击查看答案与解析</p>
            <div class="lock-actions">
              <button class="lock-btn view-btn" @click="showAnswer = true">👁️ 查看答案</button>
              <button class="lock-btn redo-btn" @click="startRedo">🔄 重新做</button>
            </div>
          </div>
        </template>

        <template v-else>
          <div class="empty-state">
            <div class="empty-icon">📚</div>
            <h3>{{ chapters.length > 0 ? '温故知新' : '暂无错题记录' }}</h3>
            <p>{{ chapters.length > 0 ? '从右侧列表中选择一道错题开始复习' : '完成章节测试后，你的错题会出现在这里' }}</p>
          </div>
        </template>
      </main>

      <!-- ═══ 右侧：章节错题列表 ═══ -->
      <aside class="list-area">
        <div class="list-header">
          <h3>错题本</h3>
          <div class="list-header-right">
            <span class="list-count">共 {{ totalCount }} 题</span>
            <button class="refresh-btn" @click="loadMistakes" :disabled="loading" title="刷新错题数据">
              🔄
            </button>
          </div>
        </div>

        <div v-if="chapters.length === 0" class="empty-list-hint">
          <p>🎉 太棒了！目前没有错题记录</p>
          <span class="hint-sub">继续学习并完成测试，错题会自动收录到这里</span>
        </div>

        <div v-else class="chapter-list">
          <div
            v-for="chapter in chapters"
            :key="chapter.id"
            class="chapter-item"
            :class="{ expanded: expandedChapter === chapter.id }"
          >
            <!-- 大章节 -->
            <div class="chapter-header" @click="toggleChapter(chapter.id)">
              <span class="expand-icon">{{ expandedChapter === chapter.id ? '▼' : '▶' }}</span>
              <span class="chapter-name">{{ chapter.name }}</span>
              <span class="chapter-count">{{ countChapterMistakes(chapter.id) }}</span>
            </div>

            <!-- 小章节列表 -->
            <div v-if="expandedChapter === chapter.id" class="subchapter-list">
              <div
                v-for="sub in chapter.subChapters"
                :key="sub.id"
                class="subchapter-item"
                :class="{ expanded: expandedSubChapter === sub.id }"
              >
                <div class="subchapter-header" @click="toggleSubChapter(sub.id, chapter.id)">
                  <span class="expand-icon">{{ expandedSubChapter === sub.id ? '▼' : '▶' }}</span>
                  <span class="subchapter-name">{{ sub.name }}</span>
                  <span class="subchapter-count">{{ sub.questions.length }}</span>
                </div>

                <!-- 错题列表 -->
                <div v-if="expandedSubChapter === sub.id && expandedChapter === chapter.id" class="question-list">
                  <div
                    v-for="q in sub.questions"
                    :key="q.id"
                    class="question-item"
                    :class="{ active: selectedQuestion?.id === q.id }"
                    @click="selectQuestion(q, chapter.name, sub.name)"
                  >
                    <span class="q-idx">{{ q.idx }}</span>
                    <span class="q-title-preview">{{ q.titlePreview }}</span>
                    <span class="q-date">{{ q.date }}</span>
                    <button
                      class="q-remove-btn"
                      title="移除错题"
                      @click.stop="removeMistake(q)"
                    >×</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </div>  <!-- end review-body -->
    </template>  <!-- end mistakes tab -->

    <!-- ═══════════════════════════════════════ -->
    <!--  Tab 2: 学习资料  ═══ -->
    <!-- ═══════════════════════════════════════ -->
    <template v-if="activeTab === 'resources'">
      <div v-if="resourcesLoading" class="loading-state">
        <el-icon class="is-loading"><Loading /></el-icon>
        <p>正在加载学习资料...</p>
      </div>

      <div v-else class="review-body">
        <!-- 左侧：资料详情 -->
        <main class="question-area">
          <template v-if="selectedResource">
            <div class="qa-header">
              <el-tag :type="resourceTypeColor(selectedResource.content_type)" size="small" round effect="dark">
                {{ resourceTypeLabel(selectedResource.content_type) }}
              </el-tag>
              <span class="qa-subchapter">{{ selectedResource.description || selectedResource.topic_tag || '' }}</span>
              <span class="resource-date">{{ formatDate(selectedResource.created_at) }}</span>
            </div>

            <div class="resource-detail-card" :class="{ 'is-mindmap': selectedResource.content_type === 'mindmap' }">
              <h3 class="resource-detail-title">{{ selectedResource.title }}</h3>
              <!-- 思维导图：ECharts 交互式气泡卡片 -->
              <div v-if="selectedResource.content_type === 'mindmap'" ref="reviewMindmapRef" class="review-mindmap-chart"></div>
              <!-- 其他类型：Markdown 渲染 -->
              <div v-else class="nl-markdown markdown-body" v-html="renderMarkdown(selectedResource.content_text || '无内容')"></div>
            </div>

            <div class="answer-actions" style="margin-top:16px;">
              <button class="action-btn remove-btn" @click="deleteResource(selectedResource)" :disabled="deleting">
                {{ deleting ? '删除中...' : '🗑️ 删除此资料' }}
              </button>
            </div>
          </template>

          <template v-else>
            <div class="empty-state">
              <div class="empty-icon">📚</div>
              <h3>学习资料库</h3>
              <p>{{ savedTotal > 0 ? '从右侧列表中选择一份学习资料查看' : '在学习页面生成的思维导图、讲义、练习题等会自动保存到这里' }}</p>
            </div>
          </template>
        </main>

        <!-- 右侧：资料列表 -->
        <aside class="list-area">
          <div class="list-header">
            <h3>📚 学习资料</h3>
            <div class="list-header-right">
              <span class="list-count" v-if="savedTotal > 0">共 {{ savedTotal }} 份</span>
              <button class="refresh-btn" @click="loadSavedResources" :disabled="resourcesLoading" title="刷新">🔄</button>
            </div>
          </div>

          <div v-if="savedChapters.length === 0" class="empty-list-hint">
            <p>📭 暂无学习资料</p>
            <span class="hint-sub">在知识点学习页面中，AI 生成的思维导图、讲义、练习题等会自动保存</span>
          </div>

          <div v-else class="chapter-list">
            <div
              v-for="chapter in savedChapters"
              :key="chapter.chapter_name"
              class="chapter-item"
              :class="{ expanded: expandedResChapter === chapter.chapter_name }"
            >
              <div class="chapter-header" @click="expandedResChapter = expandedResChapter === chapter.chapter_name ? '' : chapter.chapter_name">
                <span class="expand-icon">{{ expandedResChapter === chapter.chapter_name ? '▼' : '▶' }}</span>
                <span class="chapter-name">{{ chapter.chapter_name }}</span>
                <span class="chapter-count">{{ chapter.resources.length }} 份</span>
              </div>

              <div v-if="expandedResChapter === chapter.chapter_name" class="question-list">
                <div
                  v-for="res in chapter.resources"
                  :key="res.id"
                  class="question-item"
                  :class="{ active: selectedResource?.id === res.id }"
                  @click="selectResource(res)"
                >
                  <span class="q-idx">{{ resourceTypeIcon(res.content_type) }}</span>
                  <span class="q-title-preview">{{ res.title }}</span>
                  <button
                    class="q-remove-btn"
                    title="删除"
                    @click.stop="deleteResource(res)"
                  >×</button>
                </div>
              </div>
            </div>
          </div>
        </aside>
      </div>  <!-- end review-body -->
    </template>  <!-- end resources tab -->

  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onActivated, onUnmounted } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'
import DOMPurify from 'dompurify'
import * as echarts from 'echarts'
import { parseMindmap } from '../../utils/mindmapParser.js'
import { Loading } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import examApi from '../../api/exam'
import resourceApi from '../../api/resource'

// ── Markdown 渲染 ──
marked.setOptions({
  highlight(code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value
    }
    return hljs.highlightAuto(code).value
  },
  breaks: true,
})

function renderMarkdown(text) {
  if (!text) return ''
  return DOMPurify.sanitize(marked.parse(text))
}

// ── 状态 ──
const expandedChapter = ref('')
const expandedSubChapter = ref('')
const selectedQuestion = ref(null)
const showAnswer = ref(false)
const currentChapterName = ref('')
const currentSubChapterName = ref('')
const loading = ref(true)
const error = ref(null)

// ── 数据（从后端加载）──
const chapters = ref([])

// ── Fallback Mock 数据（当API失败时使用）──
const mockChapters = [
  {
    id: 'ch1',
    name: '线性结构（示例）',
    subChapters: [
      {
        id: 'sub1-1',
        name: '顺序表',
        questions: [
          {
            id: 'q1',
            idx: 1,
            titlePreview: '顺序表插入操作的时间复杂度分析',
            date: '2026-05-28',
            question: '在长度为 n 的顺序表中，在第 i 个位置插入一个新元素，需要移动多少个元素？',
            correctAnswer: '需要移动 **n - i + 1** 个元素。',
            yourAnswer: '移动 n - i 个元素',
            explanation: '错误：移动元素数量是 n - i + 1 而非 n - i',
            errorType: 'concept',
            difficulty: '⭐⭐'
          },
        ]
      }
    ]
  }
]

// ── 加载错题数据 ──
async function loadMistakes() {
  loading.value = true
  error.value = null

  try {
    const res = await examApi.getMistakes()

    if (res && res.chapters && res.chapters.length > 0) {
      // 使用后端数据
      chapters.value = res.chapters
      console.log(`[Review] ✅ 加载完成，共 ${res.total} 题，${res.chapters.length} 个章节:`, 
        res.chapters.map(c => `${c.name}(${c.subChapters?.reduce((s, sc) => s + (sc.questions?.length || 0), 0) || 0}题)`).join(', '))

      // 默认展开第一个章节
      if (res.chapters.length > 0) {
        expandedChapter.value = res.chapters[0].id
        if (res.chapters[0].subChapters?.length > 0) {
          expandedSubChapter.value = res.chapters[0].subChapters[0].id
        }
      }
    } else {
      // 无错题数据时显示空状态
      chapters.value = []
      console.log('[Review] 暂无错题记录')
    }
  } catch (e) {
    console.error('[Review] 加载错题失败:', e)
    error.value = e.message || '加载失败'

    // 降级到Mock数据
    console.warn('[Review] 使用Mock数据降级显示')
    chapters.value = mockChapters
    expandedChapter.value = mockChapters[0].id
    if (mockChapters[0].subChapters?.length > 0) {
      expandedSubChapter.value = mockChapters[0].subChapters[0].id
    }
  } finally {
    loading.value = false
  }
}

// ═══════════════════════════════════════
//  Tab 切换系统
// ═══════════════════════════════════════
const activeTab = ref('mistakes')

function switchTab(tab) {
  if (activeTab.value === tab) return
  // 切换前清理旧 tab 状态
  if (activeTab.value === 'resources') {
    destroyReviewMindmap()
    selectedResource.value = null
  }
  activeTab.value = tab
  if (tab === 'resources' && savedChapters.value.length === 0) {
    loadSavedResources()
  }
}

// ═══════════════════════════════════════
//  学习资料 Tab 数据
// ═══════════════════════════════════════
const resourcesLoading = ref(false)
const savedChapters = ref([])
const savedTotal = ref(0)
const selectedResource = ref(null)
const expandedResChapter = ref('')
const deleting = ref(false)

async function loadSavedResources() {
  resourcesLoading.value = true
  try {
    const res = await resourceApi.list()
    savedChapters.value = res.chapters || []
    savedTotal.value = res.total || 0
    console.log(`[Review] 📚 加载学习资料: ${savedTotal.value} 份, ${savedChapters.value.length} 个章节`)
    // 默认展开第一个章节
    if (savedChapters.value.length > 0) {
      expandedResChapter.value = savedChapters.value[0].chapter_name
    }
  } catch (e) {
    console.error('[Review] 加载学习资料失败:', e)
    savedChapters.value = []
    savedTotal.value = 0
  } finally {
    resourcesLoading.value = false
  }
}

// ═══════════════════════════════════════
//  思维导图 ECharts 渲染（学习资料 Tab）
// ═══════════════════════════════════════
const reviewMindmapRef = ref(null)
let reviewMindmapChart = null

function renderReviewMindmap(contentText) {
  if (!reviewMindmapRef.value || !contentText) return
  // 销毁旧图表
  if (reviewMindmapChart) { try { reviewMindmapChart.dispose() } catch (_) {}; reviewMindmapChart = null }

  const treeData = parseMindmap(contentText)
  if (!treeData || !treeData.children?.length) {
    // 解析失败则显示纯文本
    console.warn('[Review] 思维导图解析失败，回退到文本显示')
    return
  }

  reviewMindmapChart = echarts.init(reviewMindmapRef.value)
  const primaryColor = '#E07A5F'
  const leafColor = '#81B29A'

  reviewMindmapChart.setOption({
    tooltip: {
      trigger: 'item', triggerOn: 'mousemove',
      backgroundColor: 'rgba(29,53,87,0.92)', borderColor: '#457B9D',
      textStyle: { color: '#fff', fontSize: 12 },
      formatter: (p) => p.dataType === 'node' ? `<b>${p.name}</b>` : `<b>${p.name}</b>`,
    },
    series: [{
      type: 'tree', data: [treeData],
      top: '5%', left: '2%', bottom: '5%', right: '12%',
      orient: 'LR', symbol: 'none', symbolSize: 1,
      edgeShape: 'curve', edgeForkPosition: '65%',
      initialTreeDepth: 2, roam: true,
      scaleLimit: { min: 0.3, max: 4 },
      label: {
        position: 'right', verticalAlign: 'middle', align: 'left',
        fontSize: 11, fontWeight: 'bold', color: '#1D3557',
        backgroundColor: '#ffffff', borderColor: primaryColor, borderWidth: 2, borderRadius: 10,
        padding: [6, 12], distance: 12, overflow: 'truncate', ellipsis: '...', width: 130,
        shadowBlur: 6, shadowColor: 'rgba(0,0,0,0.08)', shadowOffsetY: 2,
        lineHeight: 16,
        formatter: (p) => {
          if (!p.data || !p.data.name) return ''
          const name = p.data.name
          if (!p.data.children || !p.data.children.length) return `{leaf|${name}}`
          return `{branch|${name}}`
        },
        rich: {
          branch: { fontSize: 11, fontWeight: 'bold', color: '#1D3557', padding: [2, 0] },
          leaf: { fontSize: 10, fontWeight: 'normal', color: '#455A64', padding: [2, 0] },
        },
      },
      leaves: {
        label: {
          position: 'right', verticalAlign: 'middle', align: 'left',
          fontSize: 10, fontWeight: 'normal', color: '#455A64',
          backgroundColor: '#f0faf5', borderColor: leafColor, borderWidth: 2, borderRadius: 10,
          padding: [5, 10], distance: 8,
          shadowBlur: 4, shadowColor: 'rgba(129,178,154,0.15)', shadowOffsetY: 1,
          lineHeight: 14,
          formatter: (p) => p.data?.name ? `{name|${p.data.name}}` : '',
          rich: { name: { fontSize: 10, fontWeight: 'normal', color: '#455A64' } },
        },
      },
      itemStyle: { borderWidth: 0 },
      lineStyle: { color: '#C4CBD4', width: 1.6, curveness: 0.5 },
      emphasis: {
        focus: 'descendant',
        lineStyle: { color: '#E07A5F', width: 3, shadowBlur: 8, shadowColor: 'rgba(224,122,95,0.35)' },
        label: {
          shadowBlur: 12, shadowColor: 'rgba(224,122,95,0.4)', shadowOffsetY: 2,
          borderColor: '#D2654B', borderWidth: 2.5,
        },
      },
      expandAndCollapse: true,
      animationDuration: 600,
      animationDurationUpdate: 800,
      animationEasing: 'cubicInOut',
      animationEasingUpdate: 'cubicInOut',
    }],
  })

  // 响应窗口大小
  const onResize = () => reviewMindmapChart?.resize()
  window.addEventListener('resize', onResize)
  // 标记清理函数
  reviewMindmapChart._onResize = onResize
}

function destroyReviewMindmap() {
  if (reviewMindmapChart) {
    try {
      if (reviewMindmapChart._onResize) window.removeEventListener('resize', reviewMindmapChart._onResize)
      reviewMindmapChart.dispose()
    } catch (_) {}
    reviewMindmapChart = null
  }
}

// 选中资源时：如果是思维导图类型，延迟渲染 ECharts
watch(selectedResource, (newRes) => {
  destroyReviewMindmap()
  if (newRes?.content_type === 'mindmap' && newRes?.content_text) {
    nextTick(() => renderReviewMindmap(newRes.content_text))
  }
})

function selectResource(res) {
  if (selectedResource.value?.id === res.id) return
  selectedResource.value = res
}

async function deleteResource(res) {
  if (deleting.value) return
  try {
    await ElMessageBox.confirm('确定要删除这份学习资料吗？', '删除确认', {
      confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning',
    })
  } catch { return }

  deleting.value = true
  try {
    await resourceApi.remove(res.id)
    ElMessage.success('资料已删除！')
    // 从本地列表中移除
    for (const ch of savedChapters.value) {
      const idx = ch.resources.findIndex(r => r.id === res.id)
      if (idx !== -1) {
        ch.resources.splice(idx, 1)
        savedTotal.value--
        break
      }
    }
    savedChapters.value = savedChapters.value.filter(ch => ch.resources.length > 0)
    if (selectedResource.value?.id === res.id) selectedResource.value = null
  } catch (e) {
    console.error('[Review] 删除资料失败:', e)
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  } finally {
    deleting.value = false
  }
}

function resourceTypeLabel(type) {
  const map = {
    mindmap: '思维导图', notes: '学习讲义', quiz: '练习题',
    code_example: '代码案例', example: '例题讲解', common_mistakes: '常见错误',
    ppt: 'PPT 大纲', animation: '动画演示',
  }
  return map[type] || type || '学习资料'
}

function resourceTypeIcon(type) {
  const map = {
    mindmap: '🧠', notes: '📖', quiz: '✏️',
    code_example: '💻', example: '📝', common_mistakes: '⚠️',
    ppt: '📽️', animation: '🎬',
  }
  return map[type] || '📄'
}

function resourceTypeColor(type) {
  const map = {
    mindmap: '', notes: 'success', quiz: 'warning',
    code_example: 'primary', example: '', common_mistakes: 'danger',
    ppt: '', animation: 'danger',
  }
  return map[type] || ''
}

function formatDate(isoStr) {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${m}-${day} ${h}:${min}`
}

// 页面挂载时加载数据
onMounted(() => {
  if (activeTab.value === 'mistakes') loadMistakes()
  else loadSavedResources()
})

// ★ keep-alive 重新激活时刷新数据（从其他页面回来时自动更新）
onActivated(() => {
  console.log('[Review] 页面激活，重新加载数据...')
  if (activeTab.value === 'mistakes') loadMistakes()
  else loadSavedResources()
})

onUnmounted(() => {
  destroyReviewMindmap()
})

// ── 计算 ──
const totalCount = computed(() => {
  let count = 0
  chapters.value.forEach(ch => {
    ch.subChapters.forEach(sub => {
      count += sub.questions.length
    })
  })
  return count
})

function countChapterMistakes(chapterId) {
  const ch = chapters.value.find(c => c.id === chapterId)
  if (!ch) return ''
  let count = 0
  ch.subChapters.forEach(sub => {
    count += sub.questions.length
  })
  return `${count} 题`
}

function errorTypeLabel(type) {
  const map = {
    concept: '🔴 概念混淆',
    confusion: '🟠 知识混淆',
    logic: '🟡 逻辑错误',
    detail: '🔵 细节遗漏',
    other: '⚪ 其他'
  }
  return map[type] || '⚪ 其他'
}

// ── 交互 ──
function toggleChapter(id) {
  expandedChapter.value = expandedChapter.value === id ? '' : id
  expandedSubChapter.value = ''
}

function toggleSubChapter(subId, chapterId) {
  if (expandedChapter.value !== chapterId) {
    expandedChapter.value = chapterId
  }
  expandedSubChapter.value = expandedSubChapter.value === subId ? '' : subId
}

function selectQuestion(q, chapterName, subChapterName) {
  selectedQuestion.value = q
  showAnswer.value = false
  redoMode.value = false
  redoSubmitted.value = false
  redoSelected.value = null
  redoTextAnswer.value = ''
  redoCorrect.value = false
  redoChoiceMade.value = false
  redoChoiceResult.value = ''
  currentChapterName.value = chapterName
  currentSubChapterName.value = subChapterName
}

// ── 移除错题 ──
const removing = ref(false)

async function removeMistake(q) {
  if (removing.value) return
  
  try {
    await ElMessageBox.confirm(
      '确定要将这道题从错题本中移除吗？',
      '移除确认',
      { confirmButtonText: '确定移除', cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return // 用户取消
  }

  removing.value = true
  try {
    await examApi.removeMistake(q.id)
    ElMessage.success('错题已移除！')

    // 从本地数据中移除
    removeQuestionFromLocal(q.id)

    // 如果移除的是当前选中的题，清空选择
    if (selectedQuestion.value?.id === q.id) {
      selectedQuestion.value = null
      showAnswer.value = false
      redoMode.value = false
    }
  } catch (e) {
    console.error('[Review] 移除错题失败:', e)
    ElMessage.error(e?.response?.data?.detail || '移除失败，请重试')
  } finally {
    removing.value = false
  }
}

function removeQuestionFromLocal(mistakeId) {
  for (const ch of chapters.value) {
    for (const sub of ch.subChapters) {
      const idx = sub.questions.findIndex(q => q.id === mistakeId)
      if (idx !== -1) {
        sub.questions.splice(idx, 1)
        // 重新编号
        sub.questions.forEach((q, i) => q.idx = i + 1)
        // 如果子章节无题目了，移除子章节
        if (sub.questions.length === 0) {
          const subIdx = ch.subChapters.indexOf(sub)
          ch.subChapters.splice(subIdx, 1)
        }
        // 如果大章节无子章节了，移除大章节
        if (ch.subChapters.length === 0) {
          const chIdx = chapters.value.indexOf(ch)
          chapters.value.splice(chIdx, 1)
        }
        return
      }
    }
  }
}

// ── 重新做模式 ──
const redoMode = ref(false)
const redoSelected = ref(null)
const redoTextAnswer = ref('')
const redoSubmitted = ref(false)
const redoCorrect = ref(false)
const redoChoiceMade = ref(false)       // 答对后是否已做了移除/保留选择
const redoChoiceResult = ref('')        // 选择后的结果文字

// 计算正确选项的索引（复用 QuizDisplay 的 answersMatch 算法）
const correctOptIndex = computed(() => {
  if (!selectedQuestion.value) return -1
  const cv = selectedQuestion.value.correctValue
  const options = selectedQuestion.value.options || []
  if (!options.length) return -1

  const answer = String(cv ?? '').trim()
  if (!answer) return -1

  // 1. 纯数字索引
  if (/^\d+$/.test(answer)) {
    const idx = parseInt(answer)
    if (idx >= 0 && idx < options.length) return idx
  }

  // 2. 字母前缀匹配 (A, B, C...)
  const LETTERS = ['A', 'B', 'C', 'D', 'E', 'F']
  const answerLetter = answer.match(/^[A-Za-z]+(?=[\.\s、\)])/)?.[0]
  if (answerLetter) {
    const idx = LETTERS.indexOf(answerLetter.toUpperCase())
    if (idx >= 0 && idx < options.length) return idx
  }

  // 3. 纯字母匹配（没有后缀的情况）
  const plainLetter = LETTERS.indexOf(answer.toUpperCase())
  if (plainLetter >= 0 && plainLetter < options.length) return plainLetter

  // 4. 选项文本匹配
  for (let i = 0; i < options.length; i++) {
    const opt = String(options[i])

    // 精确匹配选项文本
    if (opt === answer) return i
    // "A. optiontext" 格式
    if (`${LETTERS[i]}. ${opt}` === answer || `${LETTERS[i]}、${opt}` === answer) return i
    // 仅字母 + 空格 + 文本
    if (`${LETTERS[i]} ${opt}` === answer) return i
    // 忽略大小写模糊匹配
    if (opt.toLowerCase().trim() === answer.toLowerCase().trim()) return i
    // 答案文本包含在选项中
    if (answer.length > 1 && opt.toLowerCase().includes(answer.toLowerCase())) return i
  }

  return -1
})

function startRedo() {
  if (!selectedQuestion.value) return
  if (selectedQuestion.value.questionType === 'summary') {
    ElMessage.info('此类错题暂无详细作答数据，不支持重新作答')
    return
  }
  redoMode.value = true
  showAnswer.value = false
  redoSelected.value = null
  redoTextAnswer.value = ''
  redoSubmitted.value = false
  redoCorrect.value = false
  redoChoiceMade.value = false
  redoChoiceResult.value = ''
}

function cancelRedo() {
  redoMode.value = false
  showAnswer.value = false
}

function resetRedo() {
  redoSelected.value = null
  redoTextAnswer.value = ''
  redoSubmitted.value = false
  redoCorrect.value = false
  redoChoiceMade.value = false
  redoChoiceResult.value = ''
}

async function submitRedo() {
  if (!selectedQuestion.value) return
  const q = selectedQuestion.value

  let isCorrect = false

  if (q.options?.length > 0) {
    // 选择题：比较索引
    isCorrect = redoSelected.value === correctOptIndex.value
  } else {
    // 文本题：比较文本
    const userAns = redoTextAnswer.value.trim().toLowerCase()
    const correctAns = String(q.correctValue || '').trim().toLowerCase()
    isCorrect = userAns === correctAns
  }

  redoSubmitted.value = true
  redoCorrect.value = isCorrect
}

// ── 查找下一题（不修改列表，纯查询）──
function findNextQuestion(currentId) {
  const allQuestions = []
  for (const ch of chapters.value) {
    for (const sub of ch.subChapters) {
      for (const q of sub.questions) {
        allQuestions.push({ question: q, chapterName: ch.name, subChapterName: sub.name })
      }
    }
  }
  const currentIdx = allQuestions.findIndex(item => item.question.id === currentId)
  if (currentIdx === -1 || currentIdx >= allQuestions.length - 1) {
    return null
  }
  return allQuestions[currentIdx + 1]
}

// ── 导航到指定题目 ──
function navigateToQuestion(item) {
  selectQuestion(item.question, item.chapterName, item.subChapterName)
  const ch = chapters.value.find(c => c.name === item.chapterName)
  if (ch) {
    expandedChapter.value = ch.id
    const sub = ch.subChapters.find(s => s.name === item.subChapterName)
    if (sub) expandedSubChapter.value = sub.id
  }
}

// ── 答对后：手动选择移除/保留 ──
async function confirmRemoveAfterCorrect() {
  if (!selectedQuestion.value || removing.value) return
  const q = selectedQuestion.value

  // ★ 先找到下一题，再移除当前题（避免移除后找不到当前题导致误判"全部完成"）
  const nextQ = findNextQuestion(q.id)

  removing.value = true
  try {
    await examApi.removeMistake(q.id)
    removeQuestionFromLocal(q.id)
    redoChoiceMade.value = true
    redoChoiceResult.value = '🗑️ 已从错题本移除'
    ElMessage.success('错题已移除！')
    // 自动跳转下一题
    setTimeout(() => {
      if (nextQ) {
        navigateToQuestion(nextQ)
      } else {
        selectedQuestion.value = null
        showAnswer.value = false
        redoMode.value = false
        ElMessage.info('🎉 已完成全部错题复习！')
      }
    }, 800)
  } catch (e) {
    console.error('[Review] 移除失败:', e)
    ElMessage.error('移除失败，请重试')
  } finally {
    removing.value = false
  }
}

function keepMistakeAfterCorrect() {
  redoChoiceMade.value = true
  redoChoiceResult.value = '📌 已保留在错题本'
  ElMessage.info('错题已保留，可随时复习')
  // 自动跳转下一题
  setTimeout(() => goToNextQuestion(), 800)
}

// ── 跳转下一题 ──
function goToNextQuestion() {
  if (!selectedQuestion.value) return
  const nextQ = findNextQuestion(selectedQuestion.value.id)
  if (!nextQ) {
    selectedQuestion.value = null
    showAnswer.value = false
    redoMode.value = false
    ElMessage.info('🎉 已完成全部错题复习！')
    return
  }
  navigateToQuestion(nextQ)
}
</script>

<style lang="scss" scoped>
.review-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--topnav-height));
  overflow: hidden;
  background: var(--bg-secondary);
}

/* Tab 内容两栏布局容器 */
.review-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* ═══ Tab 切换栏 ═══ */
.review-tab-bar {
  display: flex;
  align-items: center;
  gap: 0;
  padding: 0 20px;
  height: 44px;
  flex-shrink: 0;
  background: #fff;
  border-bottom: 1px solid var(--border-color, #e5e6eb);

  .review-tab {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 10px 20px;
    border: none;
    background: transparent;
    font-size: 14px;
    color: var(--text-secondary, #86909c);
    cursor: pointer;
    border-bottom: 2px solid transparent;
    transition: all 0.2s;
    margin-bottom: -1px;

    &:hover { color: var(--color-primary, #E07A5F); }
    &.active {
      color: var(--color-primary, #E07A5F);
      font-weight: 600;
      border-bottom-color: var(--color-primary, #E07A5F);
    }

    .tab-badge {
      font-size: 10px;
      background: #ef4444;
      color: #fff;
      padding: 1px 6px;
      border-radius: 8px;
      min-width: 16px;
      text-align: center;
      &.saved { background: var(--color-primary, #E07A5F); }
    }
  }
}

/* Tab 内容区域包裹 */
.review-page > .loading-state,
.review-page > template {
  display: flex;
  flex: 1;
  overflow: hidden;
}
/* 让错题/资料 tab 的内容填满剩余空间 */
.review-page > template {
  display: contents;
}

/* ═══ 学习资料详情 ═══ */
.resource-detail-card {
  background: white;
  border-radius: 14px;
  padding: 24px 28px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.04);
  border: 1px solid var(--border-light);
  min-height: 200px;

  &.is-mindmap {
    padding: 16px 8px 8px 8px;
    display: flex;
    flex-direction: column;
    flex: 1;
    min-height: 0;

    .resource-detail-title {
      padding: 0 14px 10px;
      margin-bottom: 8px;
    }
  }

  .resource-detail-title {
    font-size: 16px;
    font-weight: 700;
    color: var(--text-main);
    margin: 0 0 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border-light);
  }

  .review-mindmap-chart {
    flex: 1;
    min-height: 400px;
    width: 100%;
  }

  .nl-markdown {
    font-size: 13px;
    line-height: 1.8;
    color: var(--text-main);

    :deep(h1),:deep(h2),:deep(h3) { margin-top: 1.2em; margin-bottom: .5em; font-weight: 700; }
    :deep(pre) {
      background: #1e1e2e;
      color: #cdd6f4;
      border-radius: 10px;
      padding: 14px 16px;
      overflow-x: auto;
      code { background: none; color: inherit; padding: 0; font-size: 12px; }
    }
    :deep(code) { background: rgba(224,122,95,.08); padding: 2px 6px; border-radius: 4px; font-size: .9em; }
    :deep(table) { width: 100%; border-collapse: collapse; th,td { border: 1px solid var(--border-color,#e5e6eb); padding: 6px 10px; font-size: 12px; } th { background: var(--bg-secondary,#f7f8fa); font-weight: 600; } }
  }
}

.resource-date {
  font-size: 11px;
  color: var(--text-tertiary);
  margin-left: auto;
}

/* ── 加载状态 ── */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 16px;
  color: var(--text-secondary);
  font-size: 24px;
  p { margin: 0; font-size: 14px; }
}

/* ═══ 题目区 ═══ */
.question-area {
  flex: 1;
  overflow-y: auto;
  padding: 32px 40px;
  background: var(--bg-secondary);
}

.qa-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;

  .qa-subchapter {
    font-size: 13px;
    color: var(--text-tertiary);
    margin-left: 4px;
  }
}

.question-card {
  background: white;
  border-radius: 14px;
  padding: 24px 28px;
  margin-bottom: 20px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.04);
  border: 1px solid var(--border-light);

  .q-title {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border-light);

    .q-label {
      font-size: 14px;
      font-weight: 700;
      color: var(--text-main);
    }
  }

  .q-content {
    font-size: 14px;
    line-height: 1.8;
    color: var(--text-main);

    :deep(pre) {
      background: #1e1e2e;
      border-radius: 10px;
      padding: 16px 20px;
      overflow-x: auto;
      margin: 12px 0;
    }
    :deep(code) {
      font-size: 13px;
      font-family: 'Fira Code', 'Consolas', monospace;
    }
    :deep(p) { margin: 8px 0; }
    :deep(strong) { color: var(--color-primary); }
  }
}

/* 答案区 */
.answer-card {
  background: white;
  border-radius: 14px;
  padding: 24px 28px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.04);
  border: 1px solid var(--border-light);
  animation: fadeIn 0.3s ease;

  .a-section {
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 1px dashed var(--border-light);

    &:last-of-type { border-bottom: none; }

    &.mine {
      .a-label { color: #e74c3c; }
      .a-content {
        background: rgba(231,76,60,0.04);
        padding: 12px 16px;
        border-radius: 8px;
        border-left: 3px solid rgba(231,76,60,0.3);
      }
    }

    &.explanation {
      .a-content {
        background: rgba(79,70,229,0.03);
        padding: 12px 16px;
        border-radius: 8px;
        border-left: 3px solid rgba(79,70,229,0.25);
      }
    }
  }

  .a-label {
    font-size: 13px;
    font-weight: 700;
    color: var(--color-primary);
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .a-content {
    font-size: 13px;
    line-height: 1.8;
    color: var(--text-main);

    :deep(pre) {
      background: #1e1e2e;
      border-radius: 10px;
      padding: 14px 18px;
      overflow-x: auto;
      margin: 8px 0;
    }
    :deep(code) {
      font-size: 12px;
      font-family: 'Fira Code', 'Consolas', monospace;
    }
    :deep(p) { margin: 6px 0; }
    :deep(table) {
      border-collapse: collapse;
      width: 100%;
      margin: 10px 0;
      font-size: 12px;
      th, td { border: 1px solid var(--border-light); padding: 8px 12px; text-align: left; }
      th { background: var(--bg-secondary); font-weight: 600; }
    }
  }

  .a-tags {
    display: flex;
    align-items: center;
    gap: 10px;
    padding-top: 10px;

    .error-type-tag {
      font-size: 12px;
      padding: 3px 10px;
      background: rgba(var(--color-primary-rgb), 0.06);
      border-radius: 6px;
      color: var(--text-secondary);
    }

    .difficulty-tag {
      font-size: 11px;
      color: var(--text-tertiary);
    }
  }
}

.answer-lock {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  background: white;
  border-radius: 14px;
  border: 1px solid var(--border-light);
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;

  &:hover {
    border-color: var(--color-primary-light);
    background: rgba(var(--color-primary-rgb), 0.02);
  }

  .lock-icon { font-size: 36px; margin-bottom: 10px; }
  p { color: var(--text-tertiary); font-size: 13px; margin: 0 0 16px; }

  .lock-actions {
    display: flex;
    gap: 10px;

    .lock-btn {
      padding: 8px 18px;
      border-radius: 8px;
      font-size: 13px;
      border: 1px solid var(--border-light);
      background: white;
      cursor: pointer;
      transition: all 0.15s;

      &.view-btn:hover {
        background: var(--color-primary);
        color: white;
        border-color: var(--color-primary);
      }

      &.redo-btn:hover {
        background: #f59e0b;
        color: white;
        border-color: #f59e0b;
      }
    }
  }
}

/* ★ 答案卡片底部操作按钮 */
.answer-actions {
  display: flex;
  gap: 10px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border-light);

  .action-btn {
    padding: 8px 16px;
    border-radius: 8px;
    font-size: 13px;
    border: 1px solid var(--border-light);
    background: white;
    cursor: pointer;
    transition: all 0.15s;
    display: flex;
    align-items: center;
    gap: 4px;

    &.redo-btn:hover {
      background: #f59e0b;
      color: white;
      border-color: #f59e0b;
    }

    &.remove-btn:hover:not(:disabled) {
      background: #ef4444;
      color: white;
      border-color: #ef4444;
    }

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-tertiary);

  .empty-icon { font-size: 56px; margin-bottom: 16px; }
  h3 { margin: 0 0 8px; font-size: 20px; color: var(--text-secondary); }
  p { margin: 0; font-size: 13px; }
}

/* ═══ 重新做卡片 ═══ */
.redo-card {
  background: white;
  border-radius: 14px;
  padding: 24px 28px;
  margin-bottom: 20px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.04);
  border: 1px solid var(--border-light);
  animation: fadeIn 0.3s ease;

  .redo-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border-light);

    .redo-label {
      font-size: 14px;
      font-weight: 700;
      color: #f59e0b;
    }

    .redo-cancel-btn {
      padding: 4px 12px;
      border-radius: 6px;
      font-size: 12px;
      border: 1px solid var(--border-light);
      background: var(--bg-secondary);
      cursor: pointer;
      color: var(--text-secondary);
      &:hover { background: #fee2e2; color: #ef4444; border-color: #fecaca; }
    }
  }

  .q-content {
    font-size: 14px;
    line-height: 1.8;
    color: var(--text-main);
    margin-bottom: 20px;
  }

  .redo-options {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-bottom: 20px;
  }

  .redo-option {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    border: 2px solid var(--border-light);
    border-radius: 10px;
    cursor: pointer;
    transition: all 0.15s;
    font-size: 13px;

    &:hover:not(.correct):not(.wrong) {
      border-color: var(--color-primary-light);
      background: rgba(var(--color-primary-rgb), 0.03);
    }

    &.selected:not(.correct):not(.wrong) {
      border-color: var(--color-primary);
      background: rgba(var(--color-primary-rgb), 0.06);
    }

    &.correct {
      border-color: #22c55e;
      background: rgba(34, 197, 94, 0.08);
      cursor: default;
    }

    &.wrong {
      border-color: #ef4444;
      background: rgba(239, 68, 68, 0.06);
      cursor: default;
    }

    .opt-letter {
      width: 28px;
      height: 28px;
      border-radius: 50%;
      background: var(--bg-secondary);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 12px;
      flex-shrink: 0;
    }

    &.correct .opt-letter { background: #22c55e; color: white; }
    &.wrong .opt-letter { background: #ef4444; color: white; }
    &.selected:not(.correct):not(.wrong) .opt-letter { background: var(--color-primary); color: white; }

    .opt-text { flex: 1; }

    .opt-icon {
      font-weight: 700;
      &.correct { color: #22c55e; }
      &.wrong { color: #ef4444; }
    }
  }

  .redo-text-input {
    margin-bottom: 20px;
  }

  .redo-no-action {
    padding: 24px;
    text-align: center;
    color: var(--text-tertiary);
    font-size: 13px;
  }

  .redo-actions {
    display: flex;
    align-items: center;
    gap: 12px;

    .redo-submit-btn {
      padding: 10px 28px;
      border-radius: 8px;
      font-size: 14px;
      font-weight: 600;
      border: none;
      background: #f59e0b;
      color: white;
      cursor: pointer;
      transition: all 0.15s;

      &:hover:not(:disabled) { background: #d97706; }
      &:disabled { opacity: 0.4; cursor: not-allowed; }
    }

    .redo-retry-btn {
      padding: 8px 20px;
      border-radius: 8px;
      font-size: 13px;
      border: 1px solid var(--border-light);
      background: white;
      cursor: pointer;
      &:hover { background: var(--bg-secondary); }
    }

    .redo-next-btn {
      padding: 8px 20px;
      border-radius: 8px;
      font-size: 13px;
      border: 1px solid var(--color-primary-light);
      background: var(--color-primary);
      color: white;
      cursor: pointer;
      font-weight: 500;
      &:hover { background: var(--color-primary-dark, #3730a3); }
    }

    .redo-remove-btn {
      padding: 8px 20px;
      border-radius: 8px;
      font-size: 13px;
      border: 1px solid #fecaca;
      background: #fef2f2;
      color: #dc2626;
      cursor: pointer;
      font-weight: 500;
      transition: all 0.15s;
      &:hover:not(:disabled) { background: #ef4444; color: white; border-color: #ef4444; }
      &:disabled { opacity: 0.5; cursor: not-allowed; }
    }

    .redo-keep-btn {
      padding: 8px 20px;
      border-radius: 8px;
      font-size: 13px;
      border: 1px solid var(--border-light);
      background: white;
      cursor: pointer;
      font-weight: 500;
      transition: all 0.15s;
      &:hover { background: var(--bg-secondary); border-color: var(--color-primary-light); }
    }

    .redo-result {
      flex: 1;
      padding: 10px 16px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 600;

      &.correct {
        background: rgba(34, 197, 94, 0.1);
        color: #16a34a;
      }
      &.wrong {
        background: rgba(239, 68, 68, 0.08);
        color: #dc2626;
      }
    }
  }
}

/* ═══ 右侧列表区 ═══ */
.list-area {
  width: 340px;
  background: white;
  border-left: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  flex-shrink: 0;
}

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 20px 14px;
  border-bottom: 1px solid var(--border-light);

  h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 700;
    color: var(--text-main);
  }

  .list-header-right {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .list-count {
    font-size: 11px;
    color: var(--text-tertiary);
    background: var(--bg-secondary);
    padding: 2px 10px;
    border-radius: 10px;
  }

  .refresh-btn {
    width: 28px;
    height: 28px;
    border: 1px solid var(--border-light);
    border-radius: 6px;
    background: var(--bg-secondary);
    cursor: pointer;
    font-size: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s;

    &:hover:not(:disabled) {
      background: var(--color-primary);
      color: white;
      border-color: var(--color-primary);
    }

    &:disabled {
      opacity: 0.4;
      cursor: not-allowed;
    }
  }
}

.empty-list-hint {
  padding: 40px 20px;
  text-align: center;
  p {
    margin: 0 0 8px;
    font-size: 15px;
    color: var(--text-secondary);
    font-weight: 600;
  }
  .hint-sub {
    font-size: 12px;
    color: var(--text-tertiary);
  }
}

.chapter-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

/* 大章节 */
.chapter-item {
  .chapter-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 20px;
    cursor: pointer;
    transition: background 0.15s;
    font-size: 14px;
    font-weight: 600;
    color: var(--text-main);

    &:hover { background: var(--bg-secondary); }

    .expand-icon {
      font-size: 10px;
      color: var(--text-tertiary);
      width: 14px;
      text-align: center;
      flex-shrink: 0;
    }

    .chapter-name { flex: 1; }

    .chapter-count {
      font-size: 11px;
      font-weight: 400;
      color: var(--text-tertiary);
      background: var(--bg-secondary);
      padding: 1px 8px;
      border-radius: 8px;
    }
  }
}

/* 小章节 */
.subchapter-list {
  .subchapter-item {
    .subchapter-header {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 7px 20px 7px 34px;
      cursor: pointer;
      font-size: 13px;
      color: var(--text-secondary);
      transition: background 0.15s;
      border-left: 2px solid transparent;

      &:hover {
        background: rgba(var(--color-primary-rgb), 0.03);
        border-left-color: var(--color-primary-light);
      }

      .expand-icon {
        font-size: 9px;
        color: var(--text-tertiary);
        width: 12px;
        text-align: center;
        flex-shrink: 0;
      }

      .subchapter-name { flex: 1; }

      .subchapter-count {
        font-size: 10px;
        color: var(--text-tertiary);
        background: var(--bg-secondary);
        padding: 1px 6px;
        border-radius: 6px;
      }
    }
  }
}

/* 错题列表 */
.question-list {
  .question-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 20px 8px 46px;
    cursor: pointer;
    font-size: 12px;
    color: var(--text-secondary);
    transition: all 0.15s;
    border-left: 2px solid transparent;

    &:hover {
      background: rgba(var(--color-primary-rgb), 0.04);
      color: var(--text-main);
    }

    &.active {
      background: rgba(var(--color-primary-rgb), 0.08);
      border-left-color: var(--color-primary);
      color: var(--color-primary);
      font-weight: 500;
    }

    .q-idx {
      width: 20px;
      height: 20px;
      border-radius: 50%;
      background: var(--bg-secondary);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 10px;
      font-weight: 600;
      flex-shrink: 0;
    }

    .q-title-preview {
      flex: 1;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .q-date {
      font-size: 10px;
      color: var(--text-tertiary);
      flex-shrink: 0;
    }

    .q-remove-btn {
      width: 20px;
      height: 20px;
      border-radius: 50%;
      border: none;
      background: transparent;
      color: var(--text-tertiary);
      font-size: 14px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      opacity: 0;
      transition: all 0.15s;
      flex-shrink: 0;
      line-height: 1;

      &:hover {
        background: #fee2e2;
        color: #ef4444;
      }
    }

    &:hover .q-remove-btn {
      opacity: 1;
    }
  }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: none; }
}
</style>
