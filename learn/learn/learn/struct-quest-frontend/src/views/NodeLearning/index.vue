<template>
  <div class="nl-layout">
    <!-- ═══ 顶部栏 ═══ -->
    <header class="nl-topbar">
      <div class="nl-topbar-left">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ path: '/map' }">学习图谱</el-breadcrumb-item>
          <el-breadcrumb-item>{{ chapterTitle }}</el-breadcrumb-item>
        </el-breadcrumb>
      </div>
      <div class="nl-topbar-right">
        <span v-if="todayStudyTime" class="nl-study-timer">{{ todayStudyTime }}</span>
        <span class="nl-status-dot" :class="{ thinking: isAIThinking }"></span>
        <span class="nl-status-text">{{ isAIThinking ? 'AI 思考中...' : '在线' }}</span>
      </div>
    </header>

    <!-- ═══ 三栏主体 ═══ -->
    <div class="nl-main">
      <!-- ▸ 左栏：本章知识目录树 ═══ -->
      <aside class="nl-left" :class="{ collapsed: leftCollapsed }">
        <div class="nl-left-header">
          <span class="nl-left-title">📑 {{ chapterTitle }} · 目录</span>
          <button class="nl-left-toggle" @click="leftCollapsed = !leftCollapsed">
            {{ leftCollapsed ? '▶' : '◀' }}
          </button>
        </div>
        <div v-if="!leftCollapsed" class="nl-left-body">
          <div v-if="treeLoading" class="nl-tree-loading">
            <span class="nl-loading-spinner"></span>
            <span>加载知识树...</span>
          </div>
          <div v-else-if="treeLoadError" class="nl-tree-error">
            <p>⚠️ {{ treeLoadError }}</p>
            <button class="nl-tree-retry" @click="loadKnowledgeTree">🔄 重试</button>
          </div>
          <div v-else-if="!flatTreeNodes.length" class="nl-tree-empty">
            <p>📭 知识节点数据为空</p>
            <p class="nl-tree-empty-sub">请确认后端服务已启动，知识图谱已初始化</p>
            <button class="nl-tree-retry" @click="loadKnowledgeTree">🔄 重新加载</button>
          </div>
          <div v-else class="nl-tree">
            <div
              v-for="node in flatTreeNodes"
              :key="node.id"
              class="nl-tree-node"
              :class="{
                active: selectedTreeNode?.id === node.id,
                completed: node.status === 'completed',
                learning: node.status === 'in_progress',
              }"
              :style="{ paddingLeft: (node.depth * 16 + 12) + 'px' }"
              @click="selectTreeNode(node)"
            >
              <span v-if="node.children?.length" class="nl-tree-expand" @click.stop="toggleTreeNode(node)">
                {{ node.expanded ? '▼' : '▶' }}
              </span>
              <span v-else class="nl-tree-spacer"></span>
              <span class="nl-tree-dot" :class="node.status"></span>
              <span class="nl-tree-label" :title="node.title">{{ node.title }}</span>
              <span v-if="node.status === 'completed'" class="nl-tree-check">✓</span>
            </div>
          </div>
          <!-- 选中节点的简要描述 -->
          <div v-if="selectedTreeNode && selectedTreeNode.description" class="nl-left-detail">
            <p class="nl-left-detail-text">{{ selectedTreeNode.description }}</p>
          </div>
        </div>
      </aside>

      <!-- ▸ 中栏：交互式思维导图 ═══ -->
      <main class="nl-center">
        <div v-if="!mindmapData" class="nl-center-empty">
          <div class="nl-empty-icon">
            <svg width="72" height="72" viewBox="0 0 72 72" fill="none">
              <circle cx="36" cy="36" r="30" stroke="var(--color-primary)" stroke-width="2" stroke-dasharray="6,4" opacity="0.35"/>
              <path d="M24 36h24M36 24v24" stroke="var(--color-primary)" stroke-width="2.5" stroke-linecap="round" opacity="0.6"/>
              <circle cx="36" cy="36" r="8" stroke="var(--color-primary)" stroke-width="1.5" fill="none" opacity="0.4"/>
            </svg>
          </div>
          <h3 class="nl-empty-title">{{ chapterTitle }} · 思维导图</h3>
          <p class="nl-empty-desc">AI 智能体将分析本章节知识结构，自动生成交互式思维导图。<br/>点击任意节点可在右侧面板查看详情和生成学习资源。</p>
          <button class="nl-gen-btn" :disabled="mindmapLoading" @click="() => generateMindmap(focusNodeTitle || nodeName)">
            <span class="nl-gen-btn-icon">{{ mindmapLoading ? '⏳' : '🧠' }}</span>
            <span>{{ mindmapLoading ? 'AI 正在分析知识结构...' : 'AI 生成思维导图' }}</span>
          </button>
          <p v-if="mindmapError" class="nl-error-msg">{{ mindmapError }}</p>
        </div>

        <div v-else class="nl-center-chart">
          <div class="nl-chart-toolbar">
            <span class="nl-chart-title">🧠 {{ mindmapCurrentTopic || chapterTitle }} · 思维导图</span>
            <div class="nl-chart-actions">
              <button class="nl-chart-btn" @click="resetMindmapZoom">🔄 重置</button>
              <button class="nl-chart-btn" @click="regenerateMindmap" :disabled="mindmapLoading">
                {{ mindmapLoading ? '⏳' : '🔁' }} 重新生成
              </button>
            </div>
          </div>
          <div ref="mindmapChartRef" class="nl-echarts-container"></div>
          <div v-if="selectedMindmapNode" class="nl-node-indicator">
            <span class="nl-node-indicator-dot"></span>
            已选中：<strong>{{ selectedMindmapNode }}</strong>
            <span class="nl-node-indicator-hint">— 右侧面板可生成学习资源</span>
          </div>
        </div>
      </main>

      <!-- ▸ 右栏：AI 学习资源面板 ═══ -->
      <aside class="nl-right" :class="{ collapsed: rightCollapsed }">
        <div class="nl-right-header">
          <span class="nl-right-title">⚡ AI 学习工具</span>
          <button class="nl-right-toggle" @click="rightCollapsed = !rightCollapsed">
            {{ rightCollapsed ? '◀' : '▶' }}
          </button>
        </div>

        <div v-if="!rightCollapsed" class="nl-right-body">
          <!-- 未选中思维导图节点 -->
          <div v-if="!selectedMindmapNode" class="nl-right-empty">
            <div class="nl-right-empty-icon">👆</div>
            <p>在思维导图中<br/>点击任意节点开始</p>
            <p class="nl-right-empty-sub">AI 将为你生成该知识点的<br/>专属学习资源</p>
          </div>

          <!-- 已选中节点 → 显示资源面板 -->
          <template v-else>
            <!-- 节点信息 -->
            <div class="nl-right-node-info">
              <h3 class="nl-right-node-name">{{ selectedMindmapNode }}</h3>
              <p class="nl-right-node-hint">选择下方资源类型，AI 智能体将自动生成</p>
            </div>

            <!-- ═══ 资源类型按钮 ═══ -->
            <div class="nl-resource-tabs">
              <button
                v-for="res in resourceSlots"
                :key="res.type"
                class="nl-res-tab"
                :class="{ active: activeResourceType === res.type, loading: res.loading, generated: res.generated }"
                @click="selectResourceTab(res)"
              >
                <span class="nl-res-icon">{{ res.icon }}</span>
                <span class="nl-res-label">{{ res.label }}</span>
                <span v-if="res.loading" class="nl-res-spin">⟳</span>
                <span v-else-if="res.generated" class="nl-res-check">✓</span>
              </button>
            </div>

            <!-- 生成进度 -->
            <div v-if="generatingLabel" class="nl-gen-progress">
              <span class="nl-gen-pulse"></span>
              AI 正在生成 <strong>{{ generatingLabel }}</strong>...
            </div>

            <!-- ═══ 内容展示区（按资源类型切换） ═══ -->
            <div class="nl-right-content">
              <!-- 空状态 -->
              <div v-if="!activeResourceType" class="nl-content-empty">
                <p>点击上方按钮<br/>AI 智能体将为你生成</p>
              </div>

              <!-- 加载中 -->
              <div v-else-if="currentResource?.loading" class="nl-content-loading">
                <span class="nl-loading-spinner"></span>
                <p>AI 正在生成 {{ currentResource?.label }}...</p>
              </div>

              <!-- ── 思维导图子展开 ── -->
              <div v-else-if="activeResourceType === 'sub_mindmap' && subMindmapContent" class="nl-content-section">
                <div class="nl-section-header">
                  <span>🧠 {{ selectedMindmapNode }} · 子导图</span>
                  <button class="nl-section-close" @click="activeResourceType = null">✕</button>
                </div>
                <div ref="subMindmapRef" class="nl-sub-mindmap"></div>
              </div>

              <!-- ── 学习讲义 ── -->
              <div v-else-if="activeResourceType === 'notes' && currentResource?.content" class="nl-content-section">
                <div class="nl-section-header">
                  <span>📖 {{ selectedMindmapNode }} · 学习讲义</span>
                  <el-button size="small" text type="primary" @click="regenerateResource('notes')" :loading="currentResource?.loading">重新生成</el-button>
                </div>
                <div class="nl-markdown markdown-body" v-html="renderMarkdown(currentResource.content)"></div>
              </div>

              <!-- ── 代码案例 ── -->
              <div v-else-if="activeResourceType === 'code_example' && currentResource?.content" class="nl-content-section">
                <div class="nl-section-header">
                  <span>💻 {{ selectedMindmapNode }} · 代码案例</span>
                  <el-button size="small" text type="primary" @click="regenerateResource('code_example')" :loading="currentResource?.loading">重新生成</el-button>
                </div>
                <div class="nl-markdown markdown-body" v-html="renderMarkdown(currentResource.content)"></div>
              </div>

              <!-- ── 练习题（交互式 QuizDisplay） ── -->
              <div v-else-if="activeResourceType === 'quiz'" class="nl-content-section nl-quiz-section">
                <div class="nl-section-header">
                  <span>✏️ {{ selectedMindmapNode }} · 练习题</span>
                  <el-button size="small" text type="primary" @click="regenerateResource('quiz')" :loading="currentResource?.loading">重新生成</el-button>
                </div>
                <QuizDisplay
                  v-if="currentResource?.quiz_items"
                  :quiz-items="currentResource.quiz_items"
                  :title="selectedMindmapNode + ' 练习题'"
                  :node-id="selectedMindmapNode"
                />
                <div v-else-if="currentResource?.content" class="nl-markdown markdown-body" v-html="renderMarkdown(currentResource.content)"></div>
                <div v-else class="nl-content-empty"><p>点击🔄重新生成</p></div>
              </div>

              <!-- ── PPT 大纲（PPT 智能生成器） ── -->
              <div v-else-if="activeResourceType === 'ppt_outline'" class="nl-content-section">
                <div class="nl-section-header">
                  <span>📽️ {{ selectedMindmapNode }} · PPT 大纲</span>
                </div>
                <div class="nl-ppt-entry" @click="openPPTGenerator">
                  <div class="nl-ppt-card">
                    <span class="nl-ppt-card-icon">✨</span>
                    <div class="nl-ppt-card-text">
                      <strong>AI 智能生成 PPT</strong>
                      <p>基于思维导图自动生成 · 支持预览编辑 · 三阶段流程</p>
                    </div>
                    <span class="nl-ppt-card-arrow">→</span>
                  </div>
                </div>
                <PPTGenerator ref="pptGeneratorRef" />
              </div>

              <!-- ── 动画演示 ── -->
              <div v-else-if="activeResourceType === 'animation'" class="nl-content-section nl-anim-section">
                <div class="nl-section-header">
                  <span>🎬 {{ selectedMindmapNode }} · 动画演示</span>
                </div>
                <!-- 视频播放 -->
                <div v-if="animData.video_url" class="nl-anim-video">
                  <video :src="animData.video_url" controls autoplay loop class="nl-anim-player"
                    :poster="animData.thumbnail_url"></video>
                  <div class="nl-anim-meta">
                    <span>⏱️ {{ animData.render_time }}s</span>
                    <span>🎬 {{ animData.scene_name }}</span>
                  </div>
                </div>
                <!-- 输入区 -->
                <div class="nl-anim-input">
                  <div class="nl-anim-mode-tabs">
                    <button :class="{ active: animInputMode === 'description' }" @click="animInputMode = 'description'">文字描述</button>
                    <button :class="{ active: animInputMode === 'code' }" @click="animInputMode = 'code'">粘贴代码</button>
                  </div>
                  <el-input v-model="animInputText" type="textarea" :rows="animInputMode === 'code' ? 6 : 3"
                    :placeholder="animInputMode === 'description' ? '用自然语言描述算法过程...' : '粘贴算法代码...'"
                    class="nl-anim-textarea" />
                  <div v-if="animInputMode === 'code'" class="nl-anim-lang">
                    <label>语言：</label>
                    <el-select v-model="animCodeLang" size="small">
                      <el-option label="Python" value="python" />
                      <el-option label="Java" value="java" />
                      <el-option label="C++" value="cpp" />
                      <el-option label="JavaScript" value="javascript" />
                      <el-option label="Go" value="go" />
                    </el-select>
                  </div>
                  <el-button type="primary" size="small" :loading="animData.loading" :disabled="!animInputText.trim()"
                    @click="generateAnimation" class="nl-anim-gen-btn">
                    {{ animData.loading ? '⏳ 生成中...' : '🎬 生成动画' }}
                  </el-button>
                  <p v-if="animData.error" class="nl-anim-error">⚠️ {{ animData.error }}</p>
                </div>
                <!-- 源码 -->
                <details v-if="animData.source_code" class="nl-anim-source">
                  <summary>🐍 查看 Manim 源码</summary>
                  <textarea v-model="animEditCode" class="nl-anim-code-editor" rows="8" spellcheck="false"></textarea>
                  <el-button size="small" type="primary" @click="rerenderAnimation" :loading="animRerendering" style="margin-top:6px;">▶️ 重新渲染</el-button>
                </details>
              </div>

              <!-- ── 例题讲解 ── -->
              <div v-else-if="activeResourceType === 'example' && currentResource?.content" class="nl-content-section">
                <div class="nl-section-header">
                  <span>📝 {{ selectedMindmapNode }} · 例题讲解</span>
                  <el-button size="small" text type="primary" @click="regenerateResource('example')" :loading="currentResource?.loading">重新生成</el-button>
                </div>
                <div class="nl-markdown markdown-body" v-html="renderMarkdown(currentResource.content)"></div>
              </div>

              <!-- ── 常见错误 ── -->
              <div v-else-if="activeResourceType === 'common_mistakes' && currentResource?.content" class="nl-content-section">
                <div class="nl-section-header">
                  <span>⚠️ {{ selectedMindmapNode }} · 常见错误</span>
                  <el-button size="small" text type="primary" @click="regenerateResource('common_mistakes')" :loading="currentResource?.loading">重新生成</el-button>
                </div>
                <div class="nl-markdown markdown-body" v-html="renderMarkdown(currentResource.content)"></div>
              </div>

              <!-- 需要先生成 -->
              <div v-else-if="activeResourceType" class="nl-content-empty">
                <p>资源尚未生成</p>
                <el-button type="primary" size="small" @click="regenerateResource(activeResourceType)">🚀 立即生成</el-button>
              </div>
            </div>
          </template>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, watch, onMounted, onActivated, onDeactivated, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { marked } from 'marked'
import * as echarts from 'echarts'
import { parseMindmap } from '../../utils/mindmapParser.js'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'
import DOMPurify from 'dompurify'
import knowledgeApi from '../../api/knowledge'
import resourceApi from '../../api/resource'
import { useStudyTimer, getTodayStudySeconds } from '../../composables/useStudyTimer'
import PPTGenerator from '../../components/PPTGenerator/index.vue'
import QuizDisplay from '../../components/QuizDisplay/index.vue'

const route = useRoute()

// ── 学习计时器 ──
const { startTimer, stopTimer, elapsedSeconds } = useStudyTimer()
const todayStudyTime = ref('')
let timerInterval = null
function updateTodayTime() {
  const total = getTodayStudySeconds() + elapsedSeconds.value
  todayStudyTime.value = total > 0 ? `今日学习 ${Math.floor(total / 60)} 分钟` : ''
}
function resumeStudy() { startTimer(); updateTodayTime(); if (timerInterval) clearInterval(timerInterval); timerInterval = setInterval(updateTodayTime, 1000) }
function pauseStudy() {
  const secs = stopTimer()
  if (timerInterval) { clearInterval(timerInterval); timerInterval = null }
  const nid = String(route.params.nodeId || '')
  if (nid && secs > 0) import('../../utils/request').then(({ http }) => http.post('/study/stop', { node_id: nid, duration_seconds: Math.floor(secs) }).catch(() => {}))
}
// ── 基础计算 ──
const nodeId = computed(() => String(route.params.nodeId || ''))

// ★ 当前节点的真实标题（从知识图谱数据中获取，回退到 ID 格式化）
const currentNodeTitle = ref('加载中...')
// ★ 章标题（大章名称，如"串、数组和广义表"）
const chapterTitle = computed(() => currentCategory.value)

// ★ 当前聚焦的知识点标题（用于生成思维导图等）
const focusNodeTitle = ref('')
const focusNodeId = ref('')

const nodeName = computed(() => focusNodeTitle.value || currentNodeTitle.value)

function resolveNodeTitle(rawId) {
  if (!rawId) return '知识点'
  // 先从已加载的知识图谱数据中查找真实标题
  const found = allNodes.value.find(n => n.id === rawId)
  if (found) return found.title || found.name || rawId
  // 回退：格式化 ID 作为临时显示名
  return decodeURIComponent(rawId).replace(/_/g, ' ').replace(/^\w/, c => c.toUpperCase())
}

const currentCategory = computed(() => {
  // 优先使用从知识图谱查到的 category
  const cur = allNodes.value.find(n => n.id === nodeId.value)
  if (cur?.category) {
    const catMap = { ch01_intro: '绪论', ch02_linear_list: '线性表', ch03_stack_queue: '栈和队列', ch04_string_array: '串数组广义表', ch05_tree: '树', ch06_graph: '图', ch07_search: '查找', ch08_sort: '排序' }
    return catMap[cur.category] || cur.category
  }
  // ★ 回退 1：从 nodeId 前缀推断章节（如 ch04_string → 串数组广义表）
  const id = nodeId.value.toLowerCase()
  if (id.startsWith('ch01_')) return '绪论'
  if (id.startsWith('ch02_')) return '线性表'
  if (id.startsWith('ch03_')) return '栈和队列'
  if (id.startsWith('ch04_')) return '串数组广义表'
  if (id.startsWith('ch05_')) return '树'
  if (id.startsWith('ch06_')) return '图'
  if (id.startsWith('ch07_')) return '查找'
  if (id.startsWith('ch08_')) return '排序'
  // 回退 2：关键词匹配
  const t = nodeName.value.toLowerCase()
  if (t.includes('链表')||t.includes('list')||t.includes('线性表')) return '线性表'
  if (t.includes('栈')||t.includes('队列')) return '栈和队列'
  if (t.includes('树')||t.includes('tree')) return '树'
  if (t.includes('图')||t.includes('graph')) return '图'
  if (t.includes('查找')||t.includes('搜索')) return '查找'
  if (t.includes('排序')) return '排序'
  if (t.includes('串')||t.includes('数组')||t.includes('广义表')) return '串数组广义表'
  if (t.includes('绪论')||t.includes('概念')||t.includes('intro')) return '绪论'
  return '数据结构'
})
const isAIThinking = computed(() => mindmapLoading.value || Object.values(resourceData).some(r => r.loading))

// ═══════════════════════════════════════
// 左栏：知识树
// ═══════════════════════════════════════
const leftCollapsed = ref(false)
const treeLoading = ref(false)
const allNodes = ref([])
const allCategories = ref([])
const selectedTreeNode = ref(null)
const expandedNodeIds = ref(new Set())

const treeLoadError = ref('')
async function loadKnowledgeTree() {
  treeLoading.value = true; treeLoadError.value = ''
  console.log('[NL] 🔄 加载知识树...', { nodeId: nodeId.value })
  try {
    const res = await knowledgeApi.getMap()
    console.log('[NL] 📡 API 返回:', { nodes: res.nodes?.length, categories: res.categories?.length })
    allCategories.value = res.categories || []
    allNodes.value = res.nodes || []
    // ★ 从实际数据中解析当前节点标题
    currentNodeTitle.value = resolveNodeTitle(nodeId.value)
    console.log('[NL] 📛 当前节点标题:', currentNodeTitle.value)
    // 展开当前章节的所有节点
    const chapterNodes = getChapterNodes()
    console.log('[NL] 📂 章节节点数:', chapterNodes.length, 'cat:', getNodeCat())
    if (chapterNodes.length) {
      chapterNodes.forEach(n => { if (n.parent_id) expandedNodeIds.value.add(n.parent_id); expandedNodeIds.value.add(n.id) })
      const cur = chapterNodes.find(n => n.id === nodeId.value) || allNodes.value.find(n => n.id === nodeId.value)
      if (cur) {
        selectedTreeNode.value = cur
        focusNodeTitle.value = cur.title || cur.name
        focusNodeId.value = cur.id
        console.log('[NL] ✅ 聚焦节点:', focusNodeTitle.value)
      }
    } else {
      // 未匹配到章节节点时，显示全部节点
      console.log('[NL] ⚠️ 未找到章节节点，显示全部')
      allNodes.value.forEach(n => expandedNodeIds.value.add(n.id))
      const cur = allNodes.value.find(n => n.id === nodeId.value)
      if (cur) {
        selectedTreeNode.value = cur
        focusNodeTitle.value = cur.title || cur.name
        focusNodeId.value = cur.id
      }
    }
    console.log('[NL] 🌲 flatTreeNodes:', flatTreeNodes.value.length, '条')
    if (!allNodes.value.length) treeLoadError.value = '知识图谱数据为空'
  } catch (e) { console.warn('[NL] ❌ 知识树加载失败:', e); treeLoadError.value = e.message || '加载失败' } finally { treeLoading.value = false }
}

function getChapterNodes() {
  const cat = getNodeCat()
  return cat ? allNodes.value.filter(n => n.category === cat) : allNodes.value
}
function getNodeCat() {
  const cur = allNodes.value.find(n => n.id === nodeId.value)
  if (cur) return cur.category
  for (const c of allCategories.value) { const f = c.nodes?.find(n => n.id === nodeId.value); if (f) return c.id?.replace(/^stage_/, '') || f.category }
  return null
}

const flatTreeNodes = computed(() => {
  const chapterNodes = getChapterNodes()
  if (!chapterNodes.length) return []
  const nodeMap = new Map()
  const roots = []
  chapterNodes.forEach(n => nodeMap.set(n.id, { ...n, children: [], depth: 0, expanded: expandedNodeIds.value.has(n.id) }))
  chapterNodes.forEach(n => {
    const node = nodeMap.get(n.id)
    if (n.parent_id && nodeMap.has(n.parent_id)) { const p = nodeMap.get(n.parent_id); (p.children = p.children || []).push(node) }
    else roots.push(node)
  })
  const flat = []
  function flatten(list, depth) {
    list.sort((a, b) => (a.order_index || 0) - (b.order_index || 0))
    list.forEach(n => { n.depth = depth; flat.push(n); if (n.children?.length && n.expanded) flatten(n.children, depth + 1) })
  }
  flatten(roots, 0)
  return flat
})

function toggleTreeNode(node) {
  if (expandedNodeIds.value.has(node.id)) expandedNodeIds.value.delete(node.id)
  else expandedNodeIds.value.add(node.id)
  expandedNodeIds.value = new Set(expandedNodeIds.value)
}
function selectTreeNode(node) {
  if (selectedTreeNode.value?.id === node.id) return  // 不重复点击

  // ★ 保存当前节点状态到缓存
  if (focusNodeId.value) snapshotCurrentNodeState()

  selectedTreeNode.value = node
  focusNodeTitle.value = node.title || node.name
  focusNodeId.value = node.id

  // ★ 尝试从缓存恢复
  const restored = restoreNodeState(node.id)
  if (restored) {
    console.log('[NL] 📦 从缓存恢复节点:', node.id, focusNodeTitle.value)
    return  // 已恢复，无需重新生成
  }

  // ★ 无缓存 → 清空面板，等待用户手动点击生成
  console.log('[NL] 🆕 新节点，等待用户手动生成:', node.id)
  selectedMindmapNode.value = null
  mindmapChartData.value = null
  mindmapRawContent.value = ''
  mindmapCurrentTopic.value = ''
  if (mindmapChart) { try { mindmapChart.off('click'); mindmapChart.off('mousedown'); mindmapChart.dispose() } catch(_){}; mindmapChart = null }
  clearRightPanel()
  // ★ 不再自动生成，等用户点击「AI 生成思维导图」按钮
}

// ═══════════════════════════════════════
// 中栏：思维导图
// ═══════════════════════════════════════
const mindmapChartRef = ref(null)
const mindmapLoading = ref(false)
const mindmapRawContent = ref('')
const mindmapChartData = ref(null)
const mindmapError = ref('')
const selectedMindmapNode = ref(null)
const mindmapCurrentTopic = ref('')   // ★ 当前思维导图对应的知识点标题
let mindmapChart = null

const mindmapData = computed(() => mindmapChartData.value)

async function generateMindmap(topic) {
  if (mindmapLoading.value) return
  const targetTopic = topic || focusNodeTitle.value || nodeName.value
  mindmapLoading.value = true; mindmapError.value = ''
  mindmapCurrentTopic.value = targetTopic  // ★ 记录当前导图的知识点
  try {
    const res = await fetch('/api/learning/resource/generate', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resource_type: 'mindmap', subject: '数据结构与算法', topic: targetTopic, goal: `为「${targetTopic}」生成完整的知识体系思维导图` }),
    })
    if (!res.ok) throw new Error((await res.json().catch(()=>({detail:res.statusText}))).detail || `HTTP ${res.status}`)
    const result = await res.json()
    if (!result.success || !result.data) throw new Error(result.detail || '返回数据为空')
    mindmapRawContent.value = result.data.content || ''
    const treeData = parseMindmap(mindmapRawContent.value)
    mindmapChartData.value = (treeData && treeData.children?.length) ? treeData : { name: targetTopic, children: [{ name: '生成内容为空，请重新生成' }] }
    await nextTick(); renderMindmapChart()
    // ★ 自动保存思维导图到后端
    resourceApi.save({
      resource_type: 'mindmap',
      title: `🧠 ${targetTopic} · 思维导图`,
      content_text: mindmapRawContent.value,
      topic_tag: focusNodeId.value,
      topic_name: focusNodeTitle.value || targetTopic,
      chapter_name: chapterTitle.value,
      format: 'markdown',
    }).then(res => console.log('[NL] 💾 思维导图已保存, id=', res?.id)).catch(e => console.warn('[NL] ⚠️ 保存思维导图失败:', e?.message || e))
  } catch (e) {
    mindmapError.value = e.message
    mindmapChartData.value = { name: targetTopic, children: [{ name: `生成失败: ${e.message}` }] }
    await nextTick(); renderMindmapChart()
  } finally { mindmapLoading.value = false }
}

async function regenerateMindmap() {
  mindmapChartData.value = null; mindmapRawContent.value = ''; selectedMindmapNode.value = null
  if (mindmapChart) { mindmapChart.dispose(); mindmapChart = null }
  await generateMindmap(mindmapCurrentTopic.value)
}

function renderMindmapChart() {
  if (!mindmapChartRef.value || !mindmapChartData.value) return
  if (mindmapChart) { try { mindmapChart.off('click'); mindmapChart.off('mousedown'); mindmapChart.dispose() } catch(_){}; mindmapChart = null }
  mindmapChart = echarts.init(mindmapChartRef.value)

  // 节点基础色
  const primaryColor = '#E07A5F'
  const leafColor = '#81B29A'

  mindmapChart.setOption({
    tooltip: { trigger: 'item', triggerOn: 'mousemove', backgroundColor: 'rgba(29,53,87,0.92)', borderColor: '#457B9D', textStyle: { color: '#fff', fontSize: 13 },
      formatter: (p) => p.dataType === 'node' ? `<b>${p.name}</b><br/><span style="font-size:11px;opacity:0.7">点击查看更多</span>` : `<b>${p.name}</b>` },
    series: [{
      type: 'tree', data: [mindmapChartData.value], top: '8%', left: '3%', bottom: '8%', right: '16%', orient: 'LR',
      symbol: 'none',
      symbolSize: 1,
      edgeShape: 'curve', edgeForkPosition: '65%', initialTreeDepth: 2, roam: true, scaleLimit: { min: 0.25, max: 4 },
      label: {
        position: 'right', verticalAlign: 'middle', align: 'left', fontSize: 12, fontWeight: 'bold', color: '#1D3557',
        backgroundColor: '#ffffff', borderColor: primaryColor, borderWidth: 2, borderRadius: 10,
        padding: [7, 14], distance: 14, overflow: 'truncate', ellipsis: '...', width: 140,
        shadowBlur: 6, shadowColor: 'rgba(0,0,0,0.08)', shadowOffsetY: 2,
        lineHeight: 18,
        formatter: (p) => {
          if (!p.data || !p.data.name) return ''
          const name = p.data.name
          if (!p.data.children || !p.data.children.length) {
            return `{leaf|${name}}`
          }
          return `{branch|${name}}`
        },
        rich: {
          branch: { fontSize: 12, fontWeight: 'bold', color: '#1D3557', padding: [2, 0] },
          leaf: { fontSize: 11, fontWeight: 'normal', color: '#455A64', padding: [2, 0] },
        },
      },
      leaves: {
        label: {
          position: 'right', verticalAlign: 'middle', align: 'left', fontSize: 11, fontWeight: 'normal', color: '#455A64',
          backgroundColor: '#f0faf5', borderColor: leafColor, borderWidth: 2, borderRadius: 10,
          padding: [5, 12], distance: 10, shadowBlur: 4, shadowColor: 'rgba(129,178,154,0.15)', shadowOffsetY: 1,
          lineHeight: 16,
          formatter: (p) => {
            if (!p.data || !p.data.name) return ''
            return `{name|${p.data.name}}`
          },
          rich: {
            name: { fontSize: 11, fontWeight: 'normal', color: '#455A64' },
          },
        },
      },
      itemStyle: { borderWidth: 0 },
      lineStyle: { color: '#C4CBD4', width: 1.8, curveness: 0.5 },
      emphasis: {
        focus: 'descendant',
        lineStyle: { color: '#E07A5F', width: 3.5, shadowBlur: 8, shadowColor: 'rgba(224,122,95,0.35)' },
        label: {
          shadowBlur: 14, shadowColor: 'rgba(224,122,95,0.45)', shadowOffsetY: 3,
          borderColor: 'var(--color-primary-dark)', borderWidth: 2.5,
        },
      },
      expandAndCollapse: true,
      animationDuration: 600,
      animationDurationUpdate: 800,
      animationEasing: 'cubicInOut',
      animationEasingUpdate: 'cubicInOut',
    }],
  })

  // ★ 点击节点 → 右侧面板激活
  // 注：tree + expandAndCollapse 模式下 ECharts click 事件可能被内部消费，
  // 改用 mousedown 作为主监听（已验证 mousedown 100% 触发且携带正确 name）
  mindmapChart.off('mousedown')
  mindmapChart.on('mousedown', function(params) {
    if (!params || !params.name) return
    console.log('[NL] 选中思维导图节点:', params.name)
    if (selectedMindmapNode.value !== params.name) {
      selectedMindmapNode.value = params.name
      nextTick(() => clearRightPanel())
    }
  })

  // click 备用（部分 ECharts 版本可触发）
  mindmapChart.off('click')
  mindmapChart.on('click', function(params) {
    const isNode = params && (params.dataType === 'node' || (!params.dataType && params.name && params.seriesType === 'tree'))
    if (isNode && params.name && selectedMindmapNode.value !== params.name) {
      selectedMindmapNode.value = params.name
      nextTick(() => clearRightPanel())
    }
  })
}
function resetMindmapZoom() { if (mindmapChart) mindmapChart.dispatchAction({ type: 'restore' }) }

// ── 子思维导图 ──
const subMindmapRef = ref(null)
const subMindmapContent = ref('')
const subMindmapLoading = ref(false)
let subMindmapChart = null

async function generateSubMindmap() {
  if (subMindmapLoading.value || !selectedMindmapNode.value) return
  subMindmapLoading.value = true
  try {
    const res = await fetch('/api/learning/resource/generate', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resource_type: 'mindmap', subject: '数据结构与算法', topic: selectedMindmapNode.value, goal: `为「${selectedMindmapNode.value}」生成详细子知识点思维导图` }),
    })
    if (!res.ok) throw new Error((await res.json().catch(()=>({detail:res.statusText}))).detail || `HTTP ${res.status}`)
    const result = await res.json()
    if (!result.success || !result.data) throw new Error(result.detail || '返回数据为空')
    subMindmapContent.value = result.data.content || ''
    resourceData.sub_mindmap.content = subMindmapContent.value
    resourceData.sub_mindmap.generated = true
    await nextTick(); renderSubMindmap()
    // ★ 自动保存子导图
    resourceApi.save({
      resource_type: 'mindmap',
      title: `🧠 ${selectedMindmapNode.value} · 子导图`,
      content_text: subMindmapContent.value,
      topic_tag: focusNodeId.value,
      topic_name: selectedMindmapNode.value || focusNodeTitle.value,
      chapter_name: chapterTitle.value,
      format: 'markdown',
    }).then(res => console.log('[NL] 💾 子导图已保存, id=', res?.id)).catch(e => console.warn('[NL] ⚠️ 保存子导图失败:', e?.message || e))
  } catch (e) { subMindmapContent.value = `# 生成失败\n## ${e.message}`; await nextTick(); renderSubMindmap() }
  finally { subMindmapLoading.value = false }
}

function renderSubMindmap() {
  if (!subMindmapRef.value || !subMindmapContent.value) return
  if (subMindmapChart) { subMindmapChart.dispose(); subMindmapChart = null }
  const treeData = parseMindmap(subMindmapContent.value)
  if (!treeData || !treeData.children?.length) return
  subMindmapChart = echarts.init(subMindmapRef.value)
  subMindmapChart.setOption({
    tooltip: { trigger: 'item', triggerOn: 'mousemove', backgroundColor: 'rgba(29,53,87,0.92)', borderColor: '#457B9D', textStyle: { color: '#fff', fontSize: 12 } },
    series: [{ type: 'tree', data: [treeData], top: '2%', left: '4%', bottom: '2%', right: '8%', orient: 'LR',
      symbol: 'circle', symbolSize: [8,8], edgeShape: 'curve', edgeForkPosition: '63%', initialTreeDepth: 2, roam: true, scaleLimit: { min: 0.4, max: 3 },
      label: { position: 'right', verticalAlign: 'middle', align: 'left', fontSize: 11, color: '#1D3557' },
      itemStyle: { borderWidth: 0, color: '#E07A5F' }, lineStyle: { color: '#B0BEC5', width: 1.2, curveness: 0.5 },
      expandAndCollapse: true, animationDuration: 400,
    }],
  })
}

// ═══════════════════════════════════════
// 右栏：AI 资源生成（智能体驱动）
// ═══════════════════════════════════════
const rightCollapsed = ref(false)
const activeResourceType = ref(null)
const generatingLabel = ref('')
const pptGeneratorRef = ref(null)

// ── 资源槽位定义 ──
const RESOURCE_DEFS = [
  { type: 'notes',           icon: '📖', label: '学习讲义' },
  { type: 'sub_mindmap',     icon: '🧠', label: '子导图' },
  { type: 'quiz',            icon: '✏️', label: '练习题' },
  { type: 'code_example',    icon: '💻', label: '代码案例' },
  { type: 'example',         icon: '📝', label: '例题讲解' },
  { type: 'common_mistakes', icon: '⚠️', label: '常见错误' },
  { type: 'ppt_outline',     icon: '📽️', label: 'PPT 大纲' },
  { type: 'animation',       icon: '🎬', label: '动画演示' },
]

// ── 资源数据存储 ──
const resourceData = reactive({
  notes:           { content: '', loading: false, generated: false },
  sub_mindmap:     { content: '', loading: false, generated: false },
  quiz:            { content: '', loading: false, generated: false, quiz_items: null },
  code_example:    { content: '', loading: false, generated: false },
  example:         { content: '', loading: false, generated: false },
  common_mistakes: { content: '', loading: false, generated: false },
  ppt_outline:     { content: '', loading: false, generated: false },
  animation:       { content: '', loading: false, generated: false, video_url: '', source_code: '', render_time: 0, scene_name: 'AlgorithmScene', error: '' },
})

const resourceSlots = computed(() =>
  RESOURCE_DEFS.map(d => ({ ...d, loading: resourceData[d.type].loading, generated: resourceData[d.type].generated }))
)
const currentResource = computed(() => {
  if (!activeResourceType.value) return null
  const def = RESOURCE_DEFS.find(d => d.type === activeResourceType.value)
  return def ? { ...def, ...resourceData[activeResourceType.value] } : null
})

// ★ 节点状态缓存 — 按 focusNodeId 保存所有生成的内容，切换节点时不丢失
const nodeStateCache = reactive(new Map())  // key: focusNodeId, value: { mindmapRaw, mindmapData, resources: {...}, selectedMindmapNode, activeResourceType }

function snapshotCurrentNodeState() {
  const nid = focusNodeId.value
  if (!nid) return
  const snap = {
    mindmapRaw: mindmapRawContent.value,
    mindmapData: mindmapChartData.value,
    mindmapTopic: mindmapCurrentTopic.value,
    selectedNode: selectedMindmapNode.value,
    activeResType: activeResourceType.value,
    resources: {},
  }
  RESOURCE_DEFS.forEach(d => {
    snap.resources[d.type] = { ...resourceData[d.type] }
  })
  nodeStateCache.set(nid, snap)
}

function restoreNodeState(nid) {
  const snap = nodeStateCache.get(nid)
  if (!snap) return false
  mindmapRawContent.value = snap.mindmapRaw
  mindmapChartData.value = snap.mindmapData
  mindmapCurrentTopic.value = snap.mindmapTopic || ''
  selectedMindmapNode.value = snap.selectedNode || null
  activeResourceType.value = snap.activeResType || null
  if (snap.resources) {
    RESOURCE_DEFS.forEach(d => {
      if (snap.resources[d.type]) {
        Object.assign(resourceData[d.type], snap.resources[d.type])
      }
    })
  }
  // 恢复后重新渲染思维导图
  if (mindmapChartData.value) {
    nextTick(() => renderMindmapChart())
  }
  return true
}

// 保存当前选中节点状态（覆盖写入）
function persistCurrentResourceToBackend(resType) {
  const data = resourceData[resType]
  if (!data?.generated || !data?.content) return
  const def = RESOURCE_DEFS.find(d => d.type === resType)
  const title = def ? `${def.icon} ${selectedMindmapNode.value || focusNodeTitle.value} · ${def.label}` : `${resType} - ${focusNodeTitle.value}`
  resourceApi.save({
    resource_type: resType,
    title,
    content_text: data.content || '',
    content_json: data.quiz_items ? { quiz_items: data.quiz_items } : undefined,
    file_url: data.video_url || data.file_url || undefined,
    topic_tag: focusNodeId.value,
    topic_name: focusNodeTitle.value,
    chapter_name: chapterTitle.value,
    format: resType === 'quiz' ? 'json' : 'markdown',
  }).then(res => {
    console.log(`[NL] 💾 已保存 ${resType}→后端, id=${res?.id}`)
  }).catch(e => {
    console.warn(`[NL] ⚠️ 保存 ${resType} 失败:`, e?.message || e)
  })
}

function clearRightPanel() {
  // ★ 只重置当前视图状态，不清除已生成的资源数据（它们已在缓存中）
  activeResourceType.value = null
  generatingLabel.value = ''
}

function selectResourceTab(res) {
  if (activeResourceType.value === res.type) { activeResourceType.value = null; return }
  activeResourceType.value = res.type
  if (res.type === 'sub_mindmap' && !resourceData.sub_mindmap.generated) generateSubMindmap()
}

// ── 通用资源生成（智能体 API） ──
async function generateResourceContent(resType) {
  const data = resourceData[resType]
  if (data.loading) return
  data.loading = true; data.content = ''; data.generated = false
  generatingLabel.value = RESOURCE_DEFS.find(d => d.type === resType)?.label || resType

  const topic = selectedMindmapNode.value || nodeName.value
  let goal = `为「${topic}」生成详细的${generatingLabel.value}内容`
  let apiType = resType

  // 映射到后端支持的 resource_type
  const typeMapping = {
    notes: 'notes', sub_mindmap: 'mindmap', quiz: 'quiz', code_example: 'code_example',
    example: 'notes', common_mistakes: 'notes', ppt_outline: 'ppt_outline', animation: 'animation',
  }
  apiType = typeMapping[resType] || resType

  // 特殊 goal 调整
  if (resType === 'example') goal = `为「${topic}」提供经典例题讲解，包含解题思路、步骤推导和多种解法对比`
  else if (resType === 'common_mistakes') goal = `总结「${topic}」学习中常见的错误、易混淆概念、避坑指南和最佳实践`

  try {
    const res = await fetch('/api/learning/resource/generate', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resource_type: apiType, subject: '数据结构与算法', topic, goal }),
    })
    if (!res.ok) throw new Error((await res.json().catch(()=>({detail:res.statusText}))).detail || `HTTP ${res.status}`)
    const result = await res.json()
    if (!result.success || !result.data) throw new Error(result.detail || '返回数据为空')
    const d = result.data
    Object.assign(data, { content: d.content || '', quiz_items: d.quiz_items || null, loading: false, generated: true })
    // ★ 自动保存到后端（温故知新）
    persistCurrentResourceToBackend(resType)
  } catch (e) {
    data.content = `### ⚠️ 生成失败\n\n${e.message}\n\n请稍后重试。`
    data.loading = false
  } finally { generatingLabel.value = '' }
}

async function regenerateResource(resType) { await generateResourceContent(resType) }

// ── PPT 生成器 ──
function openPPTGenerator() {
  if (pptGeneratorRef.value) pptGeneratorRef.value.open({ mindmapData: mindmapRawContent.value || resourceData.sub_mindmap.content || null, targetPages: 10 })
}

// ── 动画生成 ──
const animInputMode = ref('description')
const animInputText = ref('')
const animCodeLang = ref('python')
const animEditCode = ref('')
const animRerendering = ref(false)
const animData = computed(() => resourceData.animation)

async function generateAnimation() {
  if (!animInputText.value.trim() || resourceData.animation.loading) return
  resourceData.animation.loading = true; resourceData.animation.error = ''
  generatingLabel.value = '动画演示'
  const API_BASE = import.meta.env.VITE_API_BASE || '/api'
  try {
    const body = { topic: selectedMindmapNode.value || nodeName.value, input_mode: animInputMode.value, input_text: animInputText.value, scene_name: 'AlgorithmScene', timeout: 120 }
    if (animInputMode.value === 'code') body.code_language = animCodeLang.value || undefined
    const resp = await fetch(`${API_BASE}/learning/animation/generate`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
    const result = await resp.json()
    if (result.success && result.data) {
      Object.assign(resourceData.animation, { video_url: result.data.video_url || '', source_code: result.data.content || '', render_time: result.data.render_time || 0, thumbnail_url: result.data.thumbnail_url || '', scene_name: result.data.scene_name || 'AlgorithmScene', error: '', generated: true })
      animEditCode.value = result.data.content || ''
      // ★ 自动保存动画到后端
      persistCurrentResourceToBackend('animation')
    } else { resourceData.animation.error = result.detail || '生成失败' }
  } catch (e) { resourceData.animation.error = `网络错误: ${e.message}` }
  finally { resourceData.animation.loading = false; generatingLabel.value = '' }
}

async function rerenderAnimation() {
  if (!animEditCode.value || animRerendering.value) return
  animRerendering.value = true
  const API_BASE = import.meta.env.VITE_API_BASE || '/api'
  try {
    const resp = await fetch(`${API_BASE}/learning/animation/rerender`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic: selectedMindmapNode.value, custom_code: animEditCode.value, scene_name: resourceData.animation.scene_name || 'AlgorithmScene', timeout: 120 }) })
    const result = await resp.json()
    if (result.success && result.data) Object.assign(resourceData.animation, { video_url: result.data.video_url || '', source_code: result.data.source_code || animEditCode.value, render_time: result.data.render_time || 0, thumbnail_url: result.data.thumbnail_url || '', error: '', generated: true })
    else resourceData.animation.error = result.detail || '渲染失败'
  } catch (e) { resourceData.animation.error = `网络错误: ${e.message}` }
  finally { animRerendering.value = false }
}

// ═══════════════════════════════════════
// Markdown 渲染
// ═══════════════════════════════════════
try { marked.setOptions({ highlight(code, lang) { if (lang && hljs.getLanguage(lang)) return hljs.highlight(code, { language: lang }).value; return hljs.highlightAuto(code).value }, breaks: true }) } catch (_) {}
function renderMarkdown(content) { if (!content) return ''; return DOMPurify.sanitize(marked.parse(content)) }

// ── resize ──
function onResize() { if (mindmapChart) mindmapChart.resize(); if (subMindmapChart) subMindmapChart.resize() }

// ═══════════════════════════════════════
// ★ 生命周期钩子（必须在所有变量/函数声明之后）
// ═══════════════════════════════════════
onMounted(() => {
  resumeStudy()
  loadKnowledgeTree()
  window.addEventListener('resize', onResize)
})
onActivated(() => {
  resumeStudy()
  if (!allNodes.value.length) loadKnowledgeTree()
})
onDeactivated(() => pauseStudy())
onUnmounted(() => {
  pauseStudy()
  if (mindmapChart) { try { mindmapChart.off('click'); mindmapChart.off('mousedown'); mindmapChart.dispose() } catch(_){} }
  if (subMindmapChart) { try { subMindmapChart.dispose() } catch(_){} }
  window.removeEventListener('resize', onResize)
})

// ★ 监听路由变化 → 保存旧状态 + 恢复新状态 + 重新加载知识树
watch(nodeId, (newId, oldId) => {
  if (newId && newId !== oldId) {
    // 保存旧节点状态
    if (focusNodeId.value) snapshotCurrentNodeState()
    // 更新标题
    currentNodeTitle.value = resolveNodeTitle(newId)
    const cur = allNodes.value.find(n => n.id === newId)
    // 销毁旧导图
    if (mindmapChart) { try { mindmapChart.off('click'); mindmapChart.off('mousedown'); mindmapChart.dispose() } catch(_){}; mindmapChart = null }
    if (cur) {
      selectedTreeNode.value = cur
      focusNodeTitle.value = cur.title || cur.name
      focusNodeId.value = cur.id
      // 尝试从缓存恢复
      if (!restoreNodeState(cur.id)) {
        // 无缓存，清空面板，等待用户手动点击生成
        selectedMindmapNode.value = null
        mindmapChartData.value = null
        mindmapRawContent.value = ''
        mindmapCurrentTopic.value = ''
        clearRightPanel()
        // ★ 不再自动生成，等用户点击「AI 生成思维导图」按钮
      }
    }
    if (!allNodes.value.length) loadKnowledgeTree()
  }
})
</script>

<style lang="scss" scoped>
.nl-layout { display:flex;flex-direction:column;height:calc(100vh - var(--topnav-height));overflow:hidden;background:var(--bg-color,#f7f8fa); }

/* ═══ 顶部栏 ═══ */
.nl-topbar { display:flex;align-items:center;justify-content:space-between;padding:0 20px;height:48px;flex-shrink:0;background:#fff;border-bottom:1px solid var(--border-color,#e5e6eb);
  .nl-topbar-left :deep(.el-breadcrumb) { font-size:13px; }
  .nl-topbar-right { display:flex;align-items:center;gap:8px;
    .nl-study-timer { font-size:12px;color:var(--text-secondary,#86909c);background:var(--bg-secondary,#f2f3f5);padding:2px 10px;border-radius:10px; }
    .nl-status-dot { width:7px;height:7px;border-radius:50%;background:#52c41a;&.thinking{background:#faad14;animation:nl-pulse 1.2s infinite;} }
    .nl-status-text { font-size:11px;color:var(--text-tertiary,#86909c); }
  }
}
@keyframes nl-pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.5;transform:scale(1.5)} }
@keyframes nl-spin { to{transform:rotate(360deg)} }

/* ═══ 三栏主体 ═══ */
.nl-main { display:flex;flex:1;overflow:hidden; }

/* ── 左栏 ── */
.nl-left { width:280px;min-width:40px;flex-shrink:0;display:flex;flex-direction:column;background:#fff;border-right:1px solid var(--border-color,#e5e6eb);transition:width .3s;overflow:hidden;&.collapsed{width:40px;} }
.nl-left-header { display:flex;align-items:center;justify-content:space-between;padding:12px 14px;border-bottom:1px solid var(--border-color,#e5e6eb);flex-shrink:0;
  .nl-left-title { font-size:13px;font-weight:600;color:var(--text-main,#1d2129);white-space:nowrap;overflow:hidden; }
  .nl-left-toggle { width:24px;height:24px;border:1px solid var(--border-color,#e5e6eb);border-radius:6px;background:var(--bg-secondary,#f7f8fa);cursor:pointer;font-size:10px;color:var(--text-secondary,#86909c);display:flex;align-items:center;justify-content:center;flex-shrink:0;&:hover{background:var(--bg-tertiary);} }
}
.nl-left-body { flex:1;overflow-y:auto;padding:4px 0;&::-webkit-scrollbar{width:4px}&::-webkit-scrollbar-thumb{background:rgba(0,0,0,.1);border-radius:2px} }
.nl-tree-loading { text-align:center;padding:20px;font-size:12px;color:var(--text-tertiary,#9e9892);display:flex;align-items:center;justify-content:center;gap:8px;
  .nl-loading-spinner{width:14px;height:14px;border:2px solid rgba(var(--color-primary-rgb),.15);border-top-color:var(--color-primary);border-radius:50%;animation:nl-spin .8s linear infinite}
}
.nl-tree-error { text-align:center;padding:20px;color:#ef4444;font-size:12px;
  p{margin:0 0 10px}
  .nl-tree-retry{padding:4px 14px;border:1px solid var(--border-color,#e5e6eb);border-radius:6px;background:#fff;color:var(--color-primary);font-size:11px;cursor:pointer;&:hover{background:rgba(var(--color-primary-rgb),.06)}}
}
.nl-tree-empty { text-align:center;padding:20px;font-size:12px;color:var(--text-tertiary,#9e9892); }
.nl-tree-node { display:flex;align-items:center;gap:6px;padding:7px 12px;cursor:pointer;font-size:12px;color:var(--text-secondary,#4e5969);transition:all .15s;user-select:none;
  &:hover{background:var(--bg-secondary,#f2f3f5)}
  &.active{background:rgba(var(--color-primary-rgb),.1);color:var(--color-primary);font-weight:600;.nl-tree-dot{box-shadow:0 0 6px var(--color-primary)}}
  &.completed .nl-tree-label{color:#16a34a}
  .nl-tree-expand{width:14px;height:14px;display:flex;align-items:center;justify-content:center;font-size:8px;color:var(--text-tertiary,#9e9892);flex-shrink:0;&:hover{color:var(--text-main,#333)}}
  .nl-tree-spacer{width:14px;flex-shrink:0}
  .nl-tree-dot{width:6px;height:6px;border-radius:50%;background:#c9cdd4;flex-shrink:0;&.completed{background:#52c41a}&.in_progress{background:var(--color-primary);animation:nl-pulse 2s infinite}}
  .nl-tree-label{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;line-height:1.4}
  .nl-tree-check{font-size:10px;color:#52c41a;font-weight:bold;flex-shrink:0}
}
.nl-left-detail { padding:10px 14px;border-top:1px solid var(--border-light);background:var(--bg-secondary,#f7f8fa);
  .nl-left-detail-text { font-size:12px;color:var(--text-secondary,#86909c);margin:0;line-height:1.5; }
}

/* ── 中栏 ── */
.nl-center { flex:1;display:flex;flex-direction:column;overflow:hidden;background:linear-gradient(135deg,#f8f9fb,#f0f2f5); }
.nl-center-empty { flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px;padding:40px;
  .nl-empty-icon{opacity:.7}
  .nl-empty-title{font-size:20px;font-weight:700;color:var(--text-main,#1d2129);margin:0}
  .nl-empty-desc{font-size:13px;color:var(--text-secondary,#86909c);margin:0;max-width:380px;text-align:center;line-height:1.6}
}
.nl-gen-btn { display:flex;align-items:center;gap:10px;padding:14px 36px;border:none;border-radius:14px;background:linear-gradient(135deg,var(--color-primary),var(--color-primary-dark));color:#fff;font-size:16px;font-weight:700;cursor:pointer;transition:all .3s;box-shadow:0 4px 20px rgba(var(--color-primary-rgb),.3);
  &:hover:not(:disabled){transform:translateY(-2px);box-shadow:0 8px 30px rgba(var(--color-primary-rgb),.4)}
  &:disabled{opacity:.7;cursor:not-allowed}
  .nl-gen-btn-icon{font-size:22px}
}
.nl-error-msg { font-size:12px;color:#ef4444;margin:0; }
.nl-center-chart { flex:1;display:flex;flex-direction:column;overflow:hidden; }
.nl-chart-toolbar { display:flex;align-items:center;justify-content:space-between;padding:8px 16px;background:#fff;border-bottom:1px solid var(--border-color,#e5e6eb);flex-shrink:0;
  .nl-chart-title{font-size:13px;font-weight:600;color:var(--text-main,#1d2129)}
  .nl-chart-btn{padding:4px 12px;border:1px solid var(--border-color,#e5e6eb);border-radius:8px;background:#fff;font-size:11px;color:var(--text-secondary,#4e5969);cursor:pointer;&:hover:not(:disabled){border-color:var(--color-primary);color:var(--color-primary)}&:disabled{opacity:.5;cursor:not-allowed}}
}
.nl-echarts-container { flex:1;min-height:0; }
.nl-node-indicator { display:flex;align-items:center;gap:6px;padding:8px 16px;background:rgba(var(--color-primary-rgb),.06);border-top:1px solid rgba(var(--color-primary-rgb),.15);font-size:12px;color:var(--text-secondary,#4e5969);flex-shrink:0;
  .nl-node-indicator-dot{width:6px;height:6px;border-radius:50%;background:var(--color-primary)}
  strong{color:var(--color-primary)}
  .nl-node-indicator-hint{color:var(--text-tertiary,#9e9892);font-size:11px}
}

/* ── 右栏 ── */
.nl-right { width:360px;min-width:40px;flex-shrink:0;display:flex;flex-direction:column;background:#fff;border-left:1px solid var(--border-color,#e5e6eb);transition:width .3s;overflow:hidden;&.collapsed{width:40px} }
.nl-right-header { display:flex;align-items:center;justify-content:space-between;padding:12px 14px;border-bottom:1px solid var(--border-color,#e5e6eb);flex-shrink:0;
  .nl-right-title{font-size:13px;font-weight:600;color:var(--text-main,#1d2129);white-space:nowrap;overflow:hidden}
  .nl-right-toggle{width:24px;height:24px;border:1px solid var(--border-color,#e5e6eb);border-radius:6px;background:var(--bg-secondary,#f7f8fa);cursor:pointer;font-size:10px;color:var(--text-secondary,#86909c);display:flex;align-items:center;justify-content:center;flex-shrink:0;&:hover{background:var(--bg-tertiary)}}
}
.nl-right-body { flex:1;overflow-y:auto;display:flex;flex-direction:column;&::-webkit-scrollbar{width:4px}&::-webkit-scrollbar-thumb{background:rgba(0,0,0,.1);border-radius:2px} }
.nl-right-empty { flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;padding:40px 20px;text-align:center;
  .nl-right-empty-icon{font-size:36px;opacity:.6}
  p{font-size:13px;color:var(--text-tertiary,#9e9892);line-height:1.6;margin:0}
  .nl-right-empty-sub{font-size:11px;opacity:.7}
}
.nl-right-node-info { padding:14px 16px;border-bottom:1px solid var(--border-color,#e5e6eb);background:linear-gradient(135deg,rgba(var(--color-primary-rgb),.04),rgba(var(--color-accent-teal-rgb),.04));
  .nl-right-node-name{font-size:16px;font-weight:700;color:var(--text-main,#1d2129);margin:0 0 4px}
  .nl-right-node-hint{font-size:12px;color:var(--text-secondary,#86909c);margin:0;line-height:1.4}
}

/* 资源类型标签 */
.nl-resource-tabs { display:flex;flex-wrap:wrap;gap:4px;padding:10px 12px;border-bottom:1px solid var(--border-light); }
.nl-res-tab { display:flex;align-items:center;gap:4px;padding:6px 12px;border:1px solid var(--border-color,#e5e6eb);border-radius:8px;background:#fff;font-size:12px;color:var(--text-secondary,#4e5969);cursor:pointer;transition:all .2s;white-space:nowrap;
  &:hover{border-color:var(--color-primary);color:var(--color-primary)}
  &.active{border-color:var(--color-primary);background:rgba(var(--color-primary-rgb),.08);color:var(--color-primary);font-weight:600}
  &.generated{border-color:rgba(var(--color-accent-teal-rgb),.3);.nl-res-check{color:#16a34a}}
  .nl-res-icon{font-size:13px}
  .nl-res-spin{font-size:12px;color:var(--color-primary);animation:nl-spin 1s linear infinite}
  .nl-res-check{font-size:10px;color:#16a34a;font-weight:bold}
}
.nl-gen-progress { display:flex;align-items:center;gap:8px;padding:8px 14px;font-size:12px;color:var(--color-primary);background:linear-gradient(90deg,rgba(var(--color-primary-rgb),.05),rgba(245,158,11,.04));border-bottom:1px solid rgba(var(--color-primary-rgb),.08);
  .nl-gen-pulse{width:7px;height:7px;border-radius:50%;background:var(--color-primary);animation:nl-pulse 1.2s infinite}
}

/* 内容区 */
.nl-right-content { flex:1;overflow-y:auto;min-height:0; }
.nl-content-empty { flex:1;display:flex;align-items:center;justify-content:center;padding:30px 20px;text-align:center;p{font-size:13px;color:var(--text-tertiary,#9e9892);margin:0 0 10px;line-height:1.6} }
.nl-content-loading { flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;padding:30px;
  .nl-loading-spinner{width:24px;height:24px;border:2px solid rgba(var(--color-primary-rgb),.15);border-top-color:var(--color-primary);border-radius:50%;animation:nl-spin .8s linear infinite}
  p{font-size:12px;color:var(--text-tertiary,#9e9892);margin:0}
}
.nl-content-section { display:flex;flex-direction:column;height:100%; }
.nl-section-header { display:flex;align-items:center;justify-content:space-between;padding:10px 14px;border-bottom:1px solid var(--border-color,#e5e6eb);background:var(--bg-secondary,#f7f8fa);flex-shrink:0;
  span{font-size:13px;font-weight:600;color:var(--text-main,#1d2129)}
  .nl-section-close{width:22px;height:22px;border:none;border-radius:6px;background:transparent;color:var(--text-tertiary,#9e9892);cursor:pointer;font-size:12px;display:flex;align-items:center;justify-content:center;&:hover{background:var(--bg-tertiary)}}
}
.nl-markdown { flex:1;overflow-y:auto;padding:14px 16px;font-size:13px;line-height:1.8;color:var(--text-main,#1d2129);
  :deep(h1),:deep(h2),:deep(h3){margin-top:1.3em;margin-bottom:.5em;font-weight:700}
  :deep(h1){font-size:1.3em;border-bottom:2px solid var(--border-color,#e5e6eb);padding-bottom:6px}
  :deep(h2){font-size:1.15em}
  :deep(p){margin:0 0 .7em}
  :deep(ul),:deep(ol){padding-left:1.4em;margin:0 0 .7em}
  :deep(code){background:rgba(var(--color-primary-rgb),.08);padding:2px 6px;border-radius:4px;font-size:.9em;font-family:'JetBrains Mono',monospace}
  :deep(pre){background:#1e1e2e;color:#cdd6f4;border-radius:10px;padding:14px 16px;overflow-x:auto;margin:10px 0;code{background:none;color:inherit;padding:0;font-size:12px}}
  :deep(blockquote){border-left:3px solid var(--color-primary);margin:10px 0;padding:8px 14px;background:rgba(var(--color-primary-rgb),.04);border-radius:0 8px 8px 0}
  :deep(table){width:100%;border-collapse:collapse;margin:10px 0;th,td{border:1px solid var(--border-color,#e5e6eb);padding:6px 10px;font-size:12px}th{background:var(--bg-secondary,#f7f8fa);font-weight:600}}
  :deep(a){color:var(--color-primary);text-decoration:none}
}

/* ── 子思维导图 ── */
.nl-sub-mindmap { height:300px;border-radius:8px; }

/* ── PPT 入口 ── */
.nl-ppt-entry { cursor:pointer;padding:12px 14px;
  .nl-ppt-card{display:flex;align-items:center;gap:14px;padding:16px;background:linear-gradient(135deg,#f0f4ff,#faf5ff);border:2px solid rgba(var(--color-primary-rgb),.15);border-radius:12px;transition:all .3s;&:hover{transform:translateY(-2px);box-shadow:0 6px 20px rgba(var(--color-primary-rgb),.15);border-color:rgba(var(--color-primary-rgb),.35);.nl-ppt-card-arrow{transform:translateX(4px);color:var(--color-primary)}}}
  .nl-ppt-card-icon{font-size:28px}
  .nl-ppt-card-text{flex:1;strong{display:block;font-size:14px;font-weight:700;color:#1d2129;margin-bottom:2px}p{font-size:11px;color:#86909c;margin:0}}
  .nl-ppt-card-arrow{font-size:18px;color:#b0b3ba;transition:all .25s}
}

/* ── 动画 ── */
.nl-anim-section { .nl-section-header{border-bottom:1px solid var(--border-color,#e5e6eb)} }
.nl-anim-video { background:#1a1a2e;border-radius:10px;overflow:hidden;margin:10px;
  .nl-anim-player{width:100%;max-height:260px;display:block;background:#000}
  .nl-anim-meta{display:flex;gap:14px;padding:6px 10px;font-size:11px;color:#a0a0b8;background:rgba(0,0,0,.3)}
}
.nl-anim-input { padding:10px 14px;display:flex;flex-direction:column;gap:8px;
  .nl-anim-mode-tabs{display:flex;gap:6px;button{padding:4px 14px;border:1px solid #d0d5e0;border-radius:6px;background:#fff;font-size:11px;cursor:pointer;&.active{background:var(--color-primary);border-color:var(--color-primary);color:#fff}}}
  .nl-anim-textarea :deep(textarea){font-size:12px;line-height:1.5}
  .nl-anim-lang{display:flex;align-items:center;gap:8px;label{font-size:11px;color:#6b7280}}
  .nl-anim-gen-btn{align-self:flex-start}
  .nl-anim-error{font-size:11px;color:#ef4444;margin:0;padding:6px 10px;background:rgba(239,68,68,.06);border-radius:6px}
}
.nl-anim-source { margin:0 10px 10px;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;
  summary{padding:8px 12px;font-size:12px;font-weight:600;color:var(--color-primary);background:#f0f4ff;cursor:pointer}
  .nl-anim-code-editor{width:100%;min-height:120px;padding:10px 12px;font-family:'JetBrains Mono',monospace;font-size:11px;line-height:1.5;color:#e2e8f0;background:#1e1e2e;border:none;resize:vertical;outline:none}
}
</style>
