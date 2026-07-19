<template>
  <div ref="mapRoot" class="map-view" :class="[`mode-${viewMode}`]">
    <!-- 顶部标题栏 -->
    <div class="map-topbar">
      <div class="topbar-left">
        <div class="brain-mark" aria-hidden="true"><span></span><span></span><span></span></div>
        <div>
          <h1 class="map-title">知识大脑</h1>
          <p class="map-subtitle">数据结构与算法 · {{ allNodes.length }} 个知识点 · {{ completionRate }}% 已点亮</p>
        </div>
      </div>
      <div class="view-switch" aria-label="知识图谱视图">
        <button v-for="mode in viewModes" :key="mode.value"
          :class="{ active: viewMode === mode.value }" @click="setViewMode(mode.value)">
          <span>{{ mode.icon }}</span>{{ mode.label }}
        </button>
      </div>
      <div class="topbar-right">
        <div class="map-search">
          <span class="search-icon">⌕</span>
          <input v-model.trim="searchQuery" type="search" placeholder="搜索知识点"
            @keydown.enter.prevent="openFirstSearchResult" />
          <div v-if="searchQuery && searchResults.length" class="search-results">
            <button v-for="node in searchResults" :key="node.id" @click="focusSearchResult(node)">
              <span>{{ node.name }}</span><small>{{ node._chapterTitle }}</small>
            </button>
          </div>
        </div>
        <button class="icon-action" :class="{ active: showDeps }" @click="toggleDependencies" title="切换依赖关系">⤳</button>
        <button class="icon-action wide" @click="expandAll" title="展开全部章节">全部</button>
        <button class="icon-action wide" @click="collapseAll" title="收起全部章节">收起</button>
      </div>
    </div>

    <!-- 地图画布 -->
    <div class="map-canvas" ref="canvasRef" @mousedown="onPanStart" @wheel.prevent="onWheel">
      <div class="brain-atmosphere" aria-hidden="true">
        <span v-for="i in 18" :key="i" :style="{ '--i': i, '--x': ((i * 37) % 96) + '%', '--y': ((i * 53) % 92) + '%' }"></span>
      </div>
      <!-- 加载状态 -->
      <div v-if="loading" class="map-loading">
        <div class="map-loading-spinner"></div>
        <p class="map-loading-text">正在加载知识图谱...</p>
      </div>

      <!-- 空状态 -->
      <div v-else-if="!chapters.length" class="map-empty">
        <h3>暂无知识图谱数据</h3>
        <p>知识图谱数据加载失败或尚未初始化。</p>
        <button class="map-empty-btn" @click="loadMapData">重新加载</button>
      </div>

      <!-- 可拖拽缩放的内容层 -->
      <div v-else class="map-stage"
        :style="{ transform: `translate(${panX}px, ${panY}px) scale(${scale})`, transformOrigin: 'center center', width: stageW + 'px', height: stageH + 'px', marginLeft: (-stageW/2) + 'px', marginTop: (-stageH/2) + 'px' }"
      >
        <!-- 背景装饰 -->
        <svg class="map-bg" :width="stageW" :height="stageH">
          <defs>
            <radialGradient id="bgGlow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stop-color="rgba(59,130,246,0.05)" />
              <stop offset="60%" stop-color="rgba(217,121,130,0.02)" />
              <stop offset="100%" stop-color="transparent" />
            </radialGradient>
          </defs>
          <circle :cx="cx" :cy="cy" :r="R1 + 120" fill="url(#bgGlow)" />
          <circle :cx="cx" :cy="cy" :r="R1" fill="none" stroke="rgba(0,0,0,0.04)" stroke-width="1" stroke-dasharray="4,6" />
        </svg>

        <!-- ═══ 连线层 ═══ -->
        <svg class="map-lines" :width="stageW" :height="stageH">
          <!-- 包含关系：中心→章节（实线） -->
          <g class="containment-lines">
            <line v-for="ch in chapters" :key="'c-c-'+ch.id"
              :x1="cx" :y1="cy" :x2="ch.x" :y2="ch.y"
              :stroke="ch.color" stroke-width="2" stroke-opacity="0.35"
            />
          </g>
          <!-- 包含关系：章节→已展开的子节点（实线） -->
          <g class="containment-lines">
            <template v-for="ch in chapters" :key="'cs-'+ch.id">
              <line v-if="expandedSet.has(ch.id)"
                v-for="n in ch.nodes" :key="'l-'+n.id"
                :x1="ch.x" :y1="ch.y" :x2="n.x" :y2="n.y"
                :stroke="ch.color" stroke-width="1.5" stroke-opacity="0.25"
              />
            </template>
          </g>
          <!-- 依赖关系：仅涉及已展示节点的虚线 -->
          <g class="dependency-lines" v-if="showDeps">
            <path v-for="d in visibleDepLines" :key="'d-'+d.from+'-'+d.to"
              :d="d.path"
              fill="none"
              :stroke="isLineHighlighted(d) ? '#ef4444' : '#94a3b8'"
              :stroke-width="isLineHighlighted(d) ? 2 : 1"
              :stroke-opacity="isLineHighlighted(d) ? 0.9 : 0.18"
              stroke-dasharray="5,4"
              :marker-end="isLineHighlighted(d) ? 'url(#arrowHl)' : 'url(#arrowDim)'"
            />
          </g>
          <!-- 多智能体规划的个性化学习路径 -->
          <g v-if="viewMode === 'personal'" class="personal-path-lines">
            <path v-for="(line, index) in personalizedLines" :key="'personal-'+index"
              :d="line.path" class="personal-path-glow" />
            <path v-for="(line, index) in personalizedLines" :key="'personal-flow-'+index"
              :d="line.path" class="personal-path-flow" />
          </g>
          <defs>
            <marker id="arrowDim" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
              <path d="M0,0 L8,4 L0,8 Z" fill="#94a3b8" opacity="0.4"/>
            </marker>
            <marker id="arrowHl" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto">
              <path d="M0,0 L9,4.5 L0,9 Z" fill="#ef4444"/>
            </marker>
          </defs>
        </svg>

        <!-- ═══ 中心枢纽 ═══ -->
        <div class="node-center"
          :style="{ left: cx + 'px', top: cy + 'px' }"
          :class="{ selected: selectedType === 'center' }"
          @click.stop="selectCenter"
        >
          <div class="center-inner">
            <span class="center-title">数据结构</span>
            <span class="center-sub">{{ totalCompleted }}/{{ allNodes.length }} 已掌握</span>
          </div>
        </div>

        <!-- ═══ 章节节点 ═══ -->
        <div v-for="ch in chapters" :key="ch.id"
          class="node-chapter"
          :class="[chapterStatusClass(ch), { selected: selectedId === ch.id, expanded: expandedSet.has(ch.id), dim: isChapterDimmed(ch) }]"
          :style="{ left: ch.x + 'px', top: ch.y + 'px', '--ch-color': ch.color }"
          @click.stop="toggleChapter(ch)"
          @mouseenter="hoverId = ch.id"
          @mouseleave="hoverId = null"
        >
          <div class="chapter-circle">
            <span class="chapter-num">{{ ch.num }}</span>
            <!-- 展开/收缩指示器 -->
            <span class="chapter-toggle-icon" :class="{ open: expandedSet.has(ch.id) }">
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 6l4 4 4-4"/></svg>
            </span>
          </div>
          <span class="chapter-name">{{ ch.title }}</span>
          <span class="chapter-count">{{ ch.nodes.length }} 个知识点</span>
          <span class="chapter-progress">{{ chapterCompleted(ch) }}/{{ ch.nodes.length }}</span>
        </div>

        <!-- ═══ 子节点（仅渲染已展开章节的子节点） ═══ -->
        <template v-for="ch in chapters" :key="'sn-'+ch.id">
          <div v-if="expandedSet.has(ch.id)" v-for="n in ch.nodes" :key="n.id"
            class="node-sub"
            :class="[nodeStatusClass(n), {
              selected: selectedId === n.id,
              dim: isDimmed(n.id),
              hl: isHighlighted(n.id),
              'on-personal-path': isOnPersonalPath(n.id),
              'path-current': isCurrentPathNode(n.id)
            }, masteryClass(n)]"
            :style="{ left: n.x + 'px', top: n.y + 'px', '--ch-color': n._color, '--mastery-color': masteryColor(n), '--mastery': nodeMastery(n) + '%' }"
            @click.stop="selectSubNode(n)"
            @mouseenter="hoverId = n.id"
            @mouseleave="hoverId = null"
          >
            <div class="sub-dot">
              <span v-if="viewMode === 'mastery'" class="mastery-dot-score">{{ nodeMastery(n) }}</span>
              <svg v-else-if="n._status === 'done'" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3"><path d="M5 12l5 5L20 7"/></svg>
              <span v-else-if="n._status === 'learning'" class="sub-pulse"></span>
            </div>
            <span class="sub-label">{{ n.name }}</span>
            <span v-if="pathStepNumber(n.id)" class="path-step-badge">{{ pathStepNumber(n.id) }}</span>
          </div>
        </template>
      </div>

      <!-- 缩放控件 -->
      <div class="zoom-controls">
        <button @click="zoomIn" title="放大">＋</button>
        <button @click="zoomOut" title="缩小">−</button>
        <button @click="resetView" title="重置视图">◎</button>
        <button @click="fitToExpanded" title="适应视图">⊡</button>
        <span class="zoom-level">{{ Math.round(scale * 100) }}%</span>
      </div>
      <div class="map-legend">
        <span><i class="done"></i>已掌握</span><span><i class="learning"></i>学习中</span>
        <span><i class="recommended"></i>AI 推荐</span>
      </div>
    </div>

    <!-- ═══ 右侧详情面板 ═══ -->
    <transition name="panel-slide">
      <div v-if="selectedType" class="detail-panel">
        <button class="detail-close" @click="closePanel">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3 3L13 13M13 3L3 13" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
        </button>

        <!-- 中心概览 -->
        <template v-if="selectedType === 'center'">
          <div class="dp-header">
            <span class="dp-badge center">课程总览</span>
            <h2 class="dp-title">数据结构</h2>
          </div>
          <p class="dp-desc">本课程涵盖 {{ chapters.length }} 大章节、{{ allNodes.length }} 个知识点，从基础概念到进阶的平衡树、B+树、跳表等，构建完整的数据结构知识体系。点击各章节可展开查看详细知识点。</p>
          <div class="dp-stats">
            <div class="stat-item"><span class="stat-num">{{ totalCompleted }}</span><span class="stat-label">已掌握</span></div>
            <div class="stat-item"><span class="stat-num">{{ totalLearning }}</span><span class="stat-label">学习中</span></div>
            <div class="stat-item"><span class="stat-num">{{ allNodes.length - totalCompleted - totalLearning }}</span><span class="stat-label">未学习</span></div>
            <div class="stat-item"><span class="stat-num">{{ completionRate }}%</span><span class="stat-label">完成率</span></div>
          </div>
          <div class="dp-section">
            <h4>章节列表（点击展开详情）</h4>
            <div v-for="ch in chapters" :key="ch.id" class="chapter-row" @click="toggleChapter(ch)">
              <span class="chapter-row-dot" :style="{ background: ch.color }"></span>
              <span class="chapter-row-name">{{ ch.num }} · {{ ch.title }}</span>
              <span class="chapter-row-count">{{ chapterCompleted(ch) }}/{{ ch.nodes.length }}</span>
              <span class="chapter-row-arrow" :class="{ open: expandedSet.has(ch.id) }">›</span>
            </div>
          </div>
        </template>

        <!-- 章节详情 -->
        <template v-else-if="selectedType === 'chapter'">
          <div class="dp-header">
            <span class="dp-badge" :style="{ background: selectedData._color + '18', color: selectedData._color }">第{{ selectedData.num }}章</span>
            <h2 class="dp-title">{{ selectedData.title }}</h2>
          </div>
          <p class="dp-desc">{{ selectedData.description }}</p>
          <div class="dp-progress-bar">
            <div class="dp-progress-fill" :style="{ width: chapterProgress(selectedData) + '%', background: selectedData._color }"></div>
          </div>
          <div class="dp-section">
            <h4>包含知识点（{{ selectedData.nodes.length }}）</h4>
            <div v-for="(n, i) in selectedData.nodes" :key="n.id"
              class="sub-row"
              :class="nodeStatusClass(n)"
              @click="selectSubNode(n); ensureChapterExpanded(n)"
            >
              <span class="sub-row-idx">{{ String(i + 1).padStart(2, '0') }}</span>
              <div class="sub-row-body">
                <span class="sub-row-name">{{ n.name }}</span>
                <span class="sub-row-desc">{{ n.desc || n.description || '' }}</span>
              </div>
              <span class="sub-row-status">{{ statusLabel(n._status) }}</span>
            </div>
          </div>
        </template>

        <!-- 子节点详情 -->
        <template v-else-if="selectedType === 'sub'">
          <div class="dp-header">
            <span class="dp-badge personal">{{ selectedData._chapterTitle }} · {{ selectedPathPosition }}</span>
            <h2 class="dp-title">{{ selectedData.name }}</h2>
            <p class="dp-path">{{ selectedData._chapterTitle }} / {{ selectedData.name }}</p>
          </div>
          <div class="detail-tabs">
            <button v-for="tab in detailTabs" :key="tab.value"
              :class="{ active: detailTab === tab.value }" @click="detailTab = tab.value">{{ tab.label }}</button>
          </div>

          <template v-if="detailTab === 'overview'">
            <div class="mastery-card">
              <div class="mastery-ring" :style="{ '--mastery': nodeMastery(selectedData) + '%' }">
                <strong>{{ nodeMastery(selectedData) }}%</strong><small>掌握度</small>
              </div>
              <div class="mastery-copy">
                <strong>{{ statusLabel(selectedData._status) }}</strong>
                <span>预计 {{ selectedPathStep?.estimated_minutes || 15 }} 分钟</span>
                <p>{{ selectedData.fullDesc || selectedData.desc || '完成本知识点后，将解锁更多关联内容。' }}</p>
              </div>
            </div>
            <div v-if="selectedData.prerequisites && selectedData.prerequisites.length" class="dp-section">
              <h4>前置知识</h4>
              <div class="dep-chips">
                <span v-for="pid in selectedData.prerequisites" :key="pid" class="dep-chip" @click="jumpToNode(pid)">{{ nodeName(pid) }}</span>
              </div>
            </div>
            <div v-if="dependentsOf(selectedData.id).length" class="dp-section">
              <h4>后续知识</h4>
              <div class="dep-chips">
                <span v-for="did in dependentsOf(selectedData.id)" :key="did" class="dep-chip subsequent" @click="jumpToNode(did)">{{ nodeName(did) }}</span>
              </div>
            </div>
            <div class="dp-section">
              <h4>核心内容</h4>
              <div class="point-tags">
                <span v-for="p in (selectedData.points || [])" :key="p" class="point-tag">{{ p }}</span>
              </div>
            </div>
          </template>

          <template v-else-if="detailTab === 'recommendation'">
            <div class="agent-reason-card">
              <div class="agent-reason-head">
                <span class="agent-orbit"><i></i></span>
                <div><strong>多智能体推荐</strong><small>{{ pathSourceLabel }}</small></div>
              </div>
              <p class="agent-summary">{{ selectedTeachingHint }}</p>
              <ul><li v-for="reason in selectedReasons" :key="reason">{{ reason }}</li></ul>
            </div>
            <div class="agent-pipeline">
              <span v-for="agent in agentPipeline" :key="agent.label" :class="{ done: agent.done, active: agent.active }">
                <i>{{ agent.icon }}</i><small>{{ agent.label }}</small>
              </span>
            </div>
          </template>

          <template v-else>
            <div class="resource-readiness">
              <div v-for="resource in selectedResources" :key="resource.type" class="resource-ready-row">
                <span class="resource-ready-icon">{{ resource.icon }}</span>
                <div><strong>{{ resource.label }}</strong><small>{{ resource.description }}</small></div>
                <span :class="['resource-state', resource.ready ? 'ready' : 'pending']">{{ resource.ready ? '已准备' : '按需生成' }}</span>
              </div>
            </div>
          </template>

          <div class="dp-actions">
            <button class="btn-primary" @click="startLearn(selectedData)">
              {{ selectedData._status === 'done' ? '复习巩固' : selectedData._status === 'learning' ? '继续学习' : '进入学习工作台' }}
            </button>
            <button class="btn-secondary" @click="goToExam(selectedData)">知识点测验</button>
          </div>
        </template>
      </div>
    </transition>
    <section v-if="viewMode === 'personal'" class="path-dock" :class="{ collapsed: pathDockCollapsed }">
      <button class="path-dock-toggle" @click="pathDockCollapsed = !pathDockCollapsed">
        {{ pathDockCollapsed ? '展开路径' : '收起' }}
      </button>
      <div class="path-dock-heading">
        <span class="ai-badge">AI</span>
        <div><strong>我的个性化学习路径</strong><small>{{ pathSourceLabel }} · {{ personalizedPath.length }} 个步骤</small></div>
      </div>
      <div v-if="!pathDockCollapsed" class="path-steps">
        <button v-for="(step, index) in personalizedPath" :key="step.node.id"
          :class="{ completed: step.status === 'completed', current: index === currentPathIndex }"
          @click="jumpToNode(step.node.id)">
          <span>{{ step.status === 'completed' ? '✓' : index + 1 }}</span>
          <div><strong>{{ step.node.name }}</strong><small>{{ step.estimated_minutes || 15 }} 分钟</small></div>
        </button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onActivated, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { gsap } from 'gsap'
import knowledgeApi from '@/api/knowledge'
import { useLearningStore } from '@/store/learning'
import { stages as fallbackStages } from '@/data/knowledgeMap.js'

const router = useRouter()
const learningStore = useLearningStore()
const mapRoot = ref(null)
const viewMode = ref('personal')
const searchQuery = ref('')
const pathDockCollapsed = ref(false)
const detailTab = ref('overview')
const detailTabs = [
  { value: 'overview', label: '节点概览' },
  { value: 'recommendation', label: 'AI 推荐' },
  { value: 'resources', label: '学习资源' },
]
const viewModes = [
  { value: 'overview', label: '全局图谱', icon: '◉' },
  { value: 'personal', label: '我的路径', icon: '✦' },
  { value: 'mastery', label: '掌握热力', icon: '◐' },
  { value: 'dependencies', label: '依赖关系', icon: '⌁' },
]
let entranceContext = null

// ═══ 画布尺寸（足够大以容纳所有展开的节点） ═══
const stageW = 3600
const stageH = 2800
const cx = stageW / 2
const cy = stageH / 2
const R1 = 420           // 章节环半径

// ═══ 章节配色 ═══
const CHAPTER_META = {
  ch01_intro:        { num: '01', title: '绪论',         color: '#b94b5a' },
  ch02_linear_list:  { num: '02', title: '线性表',       color: '#22c55e' },
  ch03_stack_queue:  { num: '03', title: '栈和队列',     color: '#06b6d4' },
  ch04_string_array: { num: '04', title: '串数组广义表', color: '#c84c5a' },
  ch05_tree:         { num: '05', title: '树和二叉树',   color: '#14b8a6' },
  ch06_graph:        { num: '06', title: '图',           color: '#d97982' },
  ch07_search:       { num: '07', title: '查找',         color: '#f97316' },
  ch08_sort:         { num: '08', title: '排序',         color: '#ec4899' },
}

// ═══ 数据 ═══
const loading = ref(true)
const chapters = ref([])          // 含位置和子节点位置
const allNodes = ref([])          // 扁平节点列表（原始数据）
const showDeps = ref(false)

// ═══ 展开/收缩状态 ═══
const expandedSet = ref(new Set()) // 已展开的章节 ID 集合

// ═══ 平移缩放 ═══
const scale = ref(0.62)
const panX = ref(0)
const panY = ref(0)
const canvasRef = ref(null)
let isPanning = false
let panStartX = 0
let panStartY = 0
let panOriginX = 0
let panOriginY = 0

function onPanStart(e) {
  if (e.target.closest('.node-center, .node-chapter, .node-sub, .detail-panel, .zoom-controls')) return
  isPanning = true
  panStartX = e.clientX
  panStartY = e.clientY
  panOriginX = panX.value
  panOriginY = panY.value
  window.addEventListener('mousemove', onPanMove)
  window.addEventListener('mouseup', onPanEnd)
}
function onPanMove(e) {
  if (!isPanning) return
  panX.value = panOriginX + (e.clientX - panStartX)
  panY.value = panOriginY + (e.clientY - panStartY)
}
function onPanEnd() {
  isPanning = false
  window.removeEventListener('mousemove', onPanMove)
  window.removeEventListener('mouseup', onPanEnd)
}
function onWheel(e) {
  const delta = e.deltaY > 0 ? -0.08 : 0.08
  scale.value = Math.min(2.5, Math.max(0.2, scale.value + delta))
}
function animateGraphEntrance() {
  if (!mapRoot.value || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  entranceContext?.revert()
  entranceContext = gsap.context(() => {
    gsap.from('.node-center', { autoAlpha: 0, scale: 0.72, duration: 0.7, ease: 'back.out(1.5)' })
    gsap.from('.node-chapter', { autoAlpha: 0, scale: 0.78, duration: 0.5, stagger: 0.055, ease: 'power2.out' })
  }, mapRoot.value)
}
function saveMapState() {
  try {
    sessionStorage.setItem('structquest-map-view', JSON.stringify({
      scale: scale.value, panX: panX.value, panY: panY.value,
      expanded: [...expandedSet.value], selectedId: selectedId.value,
      selectedType: selectedType.value, viewMode: viewMode.value,
    }))
  } catch (_) {}
}
function restoreMapState() {
  try {
    const saved = JSON.parse(sessionStorage.getItem('structquest-map-view') || 'null')
    if (!saved) return false
    expandedSet.value = new Set((saved.expanded || []).filter(id => chapters.value.some(ch => ch.id === id)))
    applyExpandedLayout()
    viewMode.value = viewModes.some(item => item.value === saved.viewMode) ? saved.viewMode : 'personal'
    showDeps.value = viewMode.value === 'dependencies'
    if (expandedSet.value.size === 0 || viewMode.value === 'mastery') {
      nextTick(() => fitToOverview())
    } else if (expandedSet.value.size > 1) {
      nextTick(() => fitToExpanded())
    } else {
      scale.value = Number(saved.scale) || 0.72
      panX.value = Number(saved.panX) || 0
      panY.value = Number(saved.panY) || 0
    }
    if (saved.selectedType === 'sub' && allSubNodes.value.some(node => node.id === saved.selectedId)) {
      selectedType.value = 'sub'; selectedId.value = saved.selectedId
    } else if (saved.selectedType === 'chapter' && chapters.value.some(ch => ch.id === saved.selectedId)) {
      selectedType.value = 'chapter'; selectedId.value = saved.selectedId
    }
    return true
  } catch (_) { return false }
}

function zoomIn() { scale.value = Math.min(2.5, scale.value + 0.15) }
function zoomOut() { scale.value = Math.max(0.2, scale.value - 0.15) }
function resetView() {
  fitToOverview()
}

function cameraFit(points, {
  padX = 180,
  padY = 170,
  minScale = 0.42,
  maxScale = 0.98,
  panelReserve = selectedType.value ? 430 : 0,
  dockReserve = viewMode.value === 'personal' ? 118 : 28,
  centerYOffset = 0,
  animate = true,
} = {}) {
  const rect = canvasRef.value?.getBoundingClientRect()
  if (!rect || !points.length) {
    if (animate) animateScale(scale.value, 0.72)
    else scale.value = 0.72
    return
  }

  const minX = Math.min(...points.map(point => point.x))
  const maxX = Math.max(...points.map(point => point.x))
  const minY = Math.min(...points.map(point => point.y))
  const maxY = Math.max(...points.map(point => point.y))
  const bboxW = Math.max(1, maxX - minX)
  const bboxH = Math.max(1, maxY - minY)
  const availableW = Math.max(360, rect.width - panelReserve - 72)
  const availableH = Math.max(300, rect.height - dockReserve - 36)
  const fitScale = Math.min(availableW / (bboxW + padX), availableH / (bboxH + padY))
  const targetScale = Math.max(minScale, Math.min(maxScale, fitScale))
  const bboxCx = (minX + maxX) / 2
  const bboxCy = (minY + maxY) / 2
  const targetCenterX = (rect.width - panelReserve) / 2
  const targetCenterY = (rect.height - dockReserve) / 2 + centerYOffset

  panX.value = targetCenterX - rect.width / 2 - (bboxCx - cx) * targetScale
  panY.value = targetCenterY - rect.height / 2 - (bboxCy - cy) * targetScale
  if (animate) animateScale(scale.value, targetScale)
  else scale.value = targetScale
}

function overviewFitPoints() {
  return [
    { x: cx, y: cy },
    ...chapters.value.map(chapter => ({ x: chapter.x, y: chapter.y })),
  ]
}

function fitToOverview() {
  cameraFit(overviewFitPoints(), {
    padX: 360,
    padY: 390,
    minScale: 0.5,
    maxScale: 0.7,
    panelReserve: 0,
    dockReserve: viewMode.value === 'personal' ? 118 : 28,
    centerYOffset: -16,
  })
}

/** 根据当前展开状态自适应缩放 */
function fitToExpanded() {
  const expCount = expandedSet.value.size
  if (expCount === 0) {
    fitToOverview()
    return
  }

  const visibleNodes = visibleSubNodes.value
  const visibleChapters = chapters.value.filter(chapter => expandedSet.value.has(chapter.id))
  const points = [
    { x: cx, y: cy },
    ...chapters.value.map(chapter => ({ x: chapter.x, y: chapter.y })),
    ...visibleChapters.map(chapter => ({ x: chapter.x, y: chapter.y })),
    ...visibleNodes.map(node => ({ x: node.x, y: node.y })),
  ]

  cameraFit(points, {
    padX: expCount > 1 ? 260 : 210,
    padY: expCount > 1 ? 280 : 220,
    minScale: expCount > 1 ? 0.4 : 0.58,
    maxScale: expCount > 1 ? 0.78 : 0.92,
    centerYOffset: 6,
  })
}
/** Smoothly transition to the target zoom. */
function animateScale(from, to) {
  const steps = 12
  let step = 0
  const diff = to - from
  const tick = () => {
    step++
    const t = step / steps
    const ease = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2
    scale.value = from + diff * ease
    if (step < steps) requestAnimationFrame(tick)
  }
  tick()
}

// ═══ 加载数据 ═══
function buildCompleteMap(apiCategories = [], apiNodes = []) {
  const apiById = new Map((apiNodes || []).map(node => [node.id, node]))
  const seenIds = new Set()
  const flatNodes = []

  const categories = fallbackStages.map(stage => {
    const apiCategory = (apiCategories || []).find(cat => cat.id?.replace(/^stage_/, '') === stage.id)
    const nodes = stage.nodes.map(localNode => {
      const apiNode = apiById.get(localNode.id)
      seenIds.add(localNode.id)
      const merged = {
        ...localNode,
        ...apiNode,
        id: localNode.id,
        title: apiNode?.title || localNode.title || localNode.name,
        name: apiNode?.title || localNode.name || localNode.title,
        description: apiNode?.description || localNode.desc || localNode.description || '',
        desc: apiNode?.description || localNode.desc || localNode.description || '',
        full_desc: apiNode?.full_desc || localNode.fullDesc || localNode.full_desc || '',
        fullDesc: apiNode?.full_desc || localNode.fullDesc || localNode.full_desc || '',
        category: stage.id,
        prerequisites: apiNode?.prerequisites || localNode.prerequisites || [],
        points: apiNode?.points || localNode.points || [],
        ai_suggestion: apiNode?.ai_suggestion || localNode.aiSuggestion || '',
        aiSuggestion: apiNode?.ai_suggestion || localNode.aiSuggestion || '',
        status: apiNode?.status || localNode.status || 'available',
        progress: apiNode?.progress ?? localNode.progress ?? 0,
        score: apiNode?.score ?? localNode.score ?? 0,
      }
      flatNodes.push(merged)
      return merged
    })

    return {
      ...stage,
      ...apiCategory,
      id: stage.id,
      title: apiCategory?.title || stage.title,
      description: apiCategory?.description || stage.description,
      nodes,
    }
  })

  for (const apiNode of apiNodes || []) {
    if (seenIds.has(apiNode.id)) continue
    const categoryId = apiNode.category?.replace(/^stage_/, '')
    const category = categories.find(item => item.id === categoryId)
    if (!category) continue
    category.nodes.push(apiNode)
    flatNodes.push(apiNode)
  }

  return { categories, nodes: flatNodes }
}

async function loadMapData() {
  loading.value = true
  try {
    const res = await knowledgeApi.getMap()
    const completeMap = buildCompleteMap(res.categories || [], res.nodes || [])
    allNodes.value = completeMap.nodes
    chapters.value = buildLayout(completeMap.categories, completeMap.nodes)
  } catch (e) {
    console.warn('[Map] backend map load failed, using local fallback:', e)
    const flatNodes = []
    const cats = fallbackStages.map(s => {
      const ns = s.nodes.map(n => ({ ...n, category: s.id }))
      flatNodes.push(...ns)
      return { id: s.id, title: s.title, nodes: ns }
    })
    allNodes.value = flatNodes
    chapters.value = buildLayout(cats, flatNodes)
  } finally {
    loading.value = false
    nextTick(() => {
      const restored = restoreMapState()
      if (!restored) {
        applyExpandedLayout()
        fitToOverview()
      }
      animateGraphEntrance()
    })
  }
}


// ═══ 布局计算 ═══
function projectedPoint(chX, chY, angle, radial, tangent) {
  const ux = Math.cos(angle)
  const uy = Math.sin(angle)
  const tx = -Math.sin(angle)
  const ty = Math.cos(angle)
  return { x: chX + ux * radial + tx * tangent, y: chY + uy * radial + ty * tangent }
}

function wideNodePosition(chX, chY, angle, index, count) {
  const rows = Math.max(1, Math.min(4, Math.ceil(Math.sqrt(count))))
  const column = Math.floor(index / rows)
  const row = index % rows
  const itemsInColumn = Math.min(rows, count - column * rows)
  const tangent = (row - (itemsInColumn - 1) / 2) * 156
  const radial = 260 + column * 168
  return projectedPoint(chX, chY, angle, radial, tangent)
}

function applyExpandedLayout() {
  const useWideLayout = expandedSet.value.size > 1
  chapters.value = chapters.value.map(chapter => ({
    ...chapter,
    nodes: chapter.nodes.map(node => {
      const wide = useWideLayout && expandedSet.value.has(chapter.id)
      return {
        ...node,
        x: wide ? node._wideX : node._normalX,
        y: wide ? node._wideY : node._normalY,
      }
    }),
  }))
}

function buildLayout(categories, nodes) {
  const order = ['ch01_intro','ch02_linear_list','ch03_stack_queue','ch04_string_array','ch05_tree','ch06_graph','ch07_search','ch08_sort']
  const sorted = [...categories].sort((a, b) => {
    const ak = a.id.replace(/^stage_/, '')
    const bk = b.id.replace(/^stage_/, '')
    return order.indexOf(ak) - order.indexOf(bk)
  })

  const nodeMap = {}
  for (const n of nodes) nodeMap[n.id] = n

  return sorted.map((cat, i) => {
    const catKey = cat.id.replace(/^stage_/, '')
    const meta = CHAPTER_META[catKey] || { num: String(i + 1).padStart(2, '0'), title: cat.title, color: '#888' }
    const angle = (-90 + i * (360 / sorted.length)) * Math.PI / 180
    const chX = cx + R1 * Math.cos(angle)
    const chY = cy + R1 * Math.sin(angle)

    // 子节点布局：动态 R2 和角度步长，确保不重叠
    const catNodes = (cat.nodes && cat.nodes.length) ? cat.nodes : nodes.filter(n => n.category === catKey)
    const N = catNodes.length
    // 根据节点数量动态计算子节点半径和扇形角度范围
    // 节点多 → 更大的半径 + 更宽的扇形
    const baseSpread = Math.min(140, N * 9)  // 扇形半角（度）
    const spreadRad = baseSpread * Math.PI / 180
    // 半径随节点数增长，保证间距
    const dynamicR2 = 205 + Math.min(N * 14, 230)
    const half = (N - 1) / 2
    // 步长 = 总扇形角度 / (N-1)
    const step = N > 1 ? (2 * spreadRad) / (N - 1) : 0

    const positionedNodes = catNodes.map((n, j) => {
      const subAngle = angle + (j - half) * step
      const normal = projectedPoint(chX, chY, subAngle, dynamicR2, 0)
      const wide = wideNodePosition(chX, chY, angle, j, N)
      const status = n.status === 'completed' ? 'done' : (n.status === 'in_progress' || n.status === 'learning') ? 'learning' : 'locked'
      return {
        ...n,
        name: n.title || n.name,
        desc: n.description || n.desc || '',
        fullDesc: n.full_desc || n.fullDesc || n.description || '',
        points: n.points || [],
        prerequisites: n.prerequisites || [],
        aiSuggestion: n.ai_suggestion || n.aiSuggestion || '\u5efa\u8bae\u6309\u987a\u5e8f\u5b66\u4e60',
        x: normal.x, y: normal.y,
        _normalX: normal.x, _normalY: normal.y,
        _wideX: wide.x, _wideY: wide.y,
        _color: meta.color,
        _chapterTitle: meta.title,
        _status: status,
      }
    })

    return {
      id: catKey,
      num: meta.num,
      title: meta.title,
      color: meta.color,
      description: cat.description || `${meta.title} — 数据结构核心知识点`,
      x: chX, y: chY,
      nodes: positionedNodes,
    }
  })
}

// ═══ 所有子节点（扁平，用于查找/统计） ═══
const allSubNodes = computed(() => {
  const list = []
  for (const ch of chapters.value) list.push(...ch.nodes)
  return list
})

// ═══ 多智能体个性化路径叠加 ═══
function canonicalLabel(value = '') {
  return String(value).toLowerCase().replace(/[\s·、，,。()（）\-_/]/g, '')
}

function matchPathStep(step) {
  const exactId = step?.node_id || step?.nodeId || step?.id
  if (exactId) {
    const exact = allSubNodes.value.find(node => node.id === exactId)
    if (exact) return exact
  }
  const topic = canonicalLabel(step?.topic || step?.title || step?.name)
  if (!topic) return null
  return allSubNodes.value.find(node => {
    const name = canonicalLabel(node.name)
    return name === topic || name.includes(topic) || topic.includes(name)
  }) || null
}

const personalizedPath = computed(() => {
  const rawPath = learningStore.learningPath || []
  const matched = []
  const seen = new Set()
  rawPath.forEach((step, index) => {
    const node = matchPathStep(step)
    if (!node || seen.has(node.id)) return
    seen.add(node.id)
    matched.push({
      ...step,
      node,
      status: step.status || (node._status === 'done' ? 'completed' : node._status === 'learning' ? 'in_progress' : 'pending'),
      step_id: step.step_id || index + 1,
    })
  })
  if (matched.length) return matched

  const ordered = chapters.value.flatMap(chapter => chapter.nodes)
  if (!ordered.length) return []
  const learningIndex = ordered.findIndex(node => node._status === 'learning')
  const completedCount = ordered.filter(node => node._status === 'done').length
  const start = learningIndex >= 0 ? Math.max(0, learningIndex - 1) : Math.max(0, completedCount - 1)
  return ordered.slice(start, start + 8).map((node, index) => ({
    node,
    step_id: index + 1,
    topic: node.name,
    status: node._status === 'done' ? 'completed' : node._status === 'learning' ? 'in_progress' : 'pending',
    estimated_minutes: 12 + (index % 3) * 3,
    teaching_hint: node.aiSuggestion,
  }))
})

const currentPathIndex = computed(() => {
  const explicit = Number(learningStore.currentStepIndex)
  if (learningStore.learningPath?.length && explicit >= 0) return Math.min(explicit, Math.max(personalizedPath.value.length - 1, 0))
  const active = personalizedPath.value.findIndex(step => step.status === 'in_progress')
  if (active >= 0) return active
  const next = personalizedPath.value.findIndex(step => step.status !== 'completed')
  return next >= 0 ? next : Math.max(personalizedPath.value.length - 1, 0)
})

const personalPathIds = computed(() => new Set(personalizedPath.value.map(step => step.node.id)))
const selectedPathStep = computed(() => personalizedPath.value.find(step => step.node.id === selectedId.value) || null)
const selectedPathPosition = computed(() => {
  const index = personalizedPath.value.findIndex(step => step.node.id === selectedId.value)
  return index >= 0 ? `路径第 ${index + 1} 步` : '拓展知识点'
})
const pathSourceLabel = computed(() => learningStore.learningPath?.length ? '多智能体实时规划' : '基于当前进度推荐')

function isOnPersonalPath(id) { return viewMode.value === 'personal' && personalPathIds.value.has(id) }
function isCurrentPathNode(id) { return personalizedPath.value[currentPathIndex.value]?.node.id === id }
function pathStepNumber(id) {
  if (viewMode.value !== 'personal') return null
  const index = personalizedPath.value.findIndex(step => step.node.id === id)
  return index >= 0 ? index + 1 : null
}

const personalizedLines = computed(() => {
  const visibleIds = new Set(visibleSubNodes.value.map(node => node.id))
  const visiblePath = personalizedPath.value.filter(step => visibleIds.has(step.node.id))
  return visiblePath.slice(0, -1).map((step, index) => {
    const from = step.node
    const to = visiblePath[index + 1].node
    const mx = (from.x + to.x) / 2
    const my = (from.y + to.y) / 2
    const bend = Math.min(80, Math.hypot(to.x - from.x, to.y - from.y) * 0.12)
    return { path: `M ${from.x} ${from.y} Q ${mx} ${my - bend} ${to.x} ${to.y}` }
  })
})

const searchResults = computed(() => {
  const query = canonicalLabel(searchQuery.value)
  if (!query) return []
  return allSubNodes.value.filter(node => canonicalLabel(node.name).includes(query)).slice(0, 7)
})

function focusSearchResult(node) {
  const chapter = chapters.value.find(item => item.nodes.some(child => child.id === node.id))
  if (chapter) {
    const next = new Set(expandedSet.value)
    next.add(chapter.id)
    expandedSet.value = next
    applyExpandedLayout()
    nextTick(() => focusOnChapter(chapter, true))
  }
  selectSubNode(node)
  searchQuery.value = ''
}
function openFirstSearchResult() { if (searchResults.value.length) focusSearchResult(searchResults.value[0]) }
function setViewMode(mode) {
  viewMode.value = mode
  showDeps.value = mode === 'dependencies'
  if (mode === 'personal') focusCurrentPath()
  if (mode === 'mastery') expandAll()
}
function toggleDependencies() {
  showDeps.value = !showDeps.value
  if (showDeps.value) viewMode.value = 'dependencies'
  else if (viewMode.value === 'dependencies') viewMode.value = 'overview'
}
function focusCurrentPath() {
  const current = personalizedPath.value[currentPathIndex.value]?.node
  if (current) focusSearchResult(current)
}

function nodeMastery(node) {
  const raw = node?.mastery ?? node?.mastery_score ?? node?.progress
  if (Number.isFinite(Number(raw))) return Math.max(0, Math.min(100, Math.round(Number(raw))))
  if (node?._status === 'done') return 100
  if (node?._status === 'learning') return 52
  return isOnPersonalPath(node?.id) ? 24 : 0
}
function masteryColor(node) {
  const value = nodeMastery(node)
  if (value >= 80) return '#15803d'
  if (value >= 60) return '#4d7c0f'
  if (value >= 40) return '#c2410c'
  if (value > 0) return '#b91c1c'
  return '#64748b'
}

function masteryClass(node) {
  if (viewMode.value !== 'mastery') return ''
  const value = nodeMastery(node)
  if (value >= 80) return 'mastery-high'
  if (value >= 60) return 'mastery-good'
  if (value >= 40) return 'mastery-mid'
  if (value > 0) return 'mastery-low'
  return 'mastery-empty'
}

const selectedTeachingHint = computed(() => selectedPathStep.value?.teaching_hint || selectedData.value?.aiSuggestion || '建议按照知识依赖顺序学习，并通过练习及时检验理解程度。')
const selectedReasons = computed(() => {
  const reasons = []
  const profile = learningStore.profile || {}
  if (profile.ability_level) reasons.push(`已结合你的「${profile.ability_level}」能力水平调整内容难度`)
  if (profile.learning_style) reasons.push(`优先匹配你的「${profile.learning_style}」学习偏好`)
  if (profile.weakness_summary) reasons.push(`针对薄弱点：${profile.weakness_summary}`)
  if (selectedData.value?.prerequisites?.length) reasons.push('该节点承接已学前置知识，并将解锁后续核心内容')
  if (!reasons.length) reasons.push('依据当前学习进度和知识依赖关系推荐', '建议先建立概念结构，再通过案例与练习巩固', '完成测评后路径会根据掌握情况动态调整')
  return reasons.slice(0, 4)
})
const agentPipeline = computed(() => [
  { icon: '◉', label: '画像分析', done: true },
  { icon: '⌁', label: '行为诊断', done: true },
  { icon: '✦', label: '路径规划', done: personalizedPath.value.length > 0, active: learningStore.isLoading },
  { icon: '▣', label: '资源匹配', done: learningStore.resources?.length > 0, active: !learningStore.isLoading && !learningStore.resources?.length },
  { icon: '✓', label: '质量审核', done: Boolean(learningStore.assessment?.overall_score) },
])
const selectedResources = computed(() => {
  const topic = canonicalLabel(selectedData.value?.name)
  const available = new Set((learningStore.resources || []).filter(resource => {
    const resourceTopic = canonicalLabel(resource.topic || resource.title)
    return !topic || !resourceTopic || resourceTopic.includes(topic) || topic.includes(resourceTopic)
  }).map(resource => resource.resource_type || resource.type))
  return [
    { type: 'notes', icon: '▤', label: '个性化讲义', description: '按能力与学习风格组织', ready: available.has('notes') || available.has('lecture') },
    { type: 'mindmap', icon: '⌘', label: '本节概念导图', description: '梳理概念层级与联系', ready: available.has('mindmap') || available.has('mind_map') },
    { type: 'quiz', icon: '✎', label: '自适应练习', description: '根据掌握度动态调难度', ready: available.has('quiz') || available.has('exercise') },
    { type: 'code_example', icon: '⌨', label: '代码案例', description: '结合专业场景理解实现', ready: available.has('code_example') },
    { type: 'animation', icon: '▶', label: '动画演示', description: '按需生成算法过程', ready: available.has('animation') },
  ]
})

// ═══ 当前可见的子节点（仅已展开的章节的子节点） ═══
const visibleSubNodes = computed(() => {
  const list = []
  for (const ch of chapters.value) {
    if (expandedSet.value.has(ch.id)) list.push(...ch.nodes)
  }
  return list
})

// ═══ 可见依赖连线（仅两端都可见时才绘制） ═══
const depLinesRaw = computed(() => {
  const lines = []
  const posMap = {}
  for (const n of allSubNodes.value) posMap[n.id] = { x: n.x, y: n.y }
  for (const n of allSubNodes.value) {
    if (!n.prerequisites || !n.prerequisites.length) continue
    for (const pid of n.prerequisites) {
      const from = posMap[pid]
      const to = posMap[n.id]
      if (!from || !to) continue
      const mx = (from.x + to.x) / 2
      const my = (from.y + to.y) / 2
      const dx = to.x - from.x
      const dy = to.y - from.y
      const len = Math.sqrt(dx * dx + dy * dy) || 1
      const ox = -dy / len * 35
      const oy = dx / len * 35
      lines.push({
        from: pid,
        to: n.id,
        path: `M ${from.x} ${from.y} Q ${mx + ox} ${my + oy} ${to.x} ${to.y}`,
      })
    }
  }
  return lines
})

const visibleDepLines = computed(() => {
  const visIds = new Set(visibleSubNodes.value.map(n => n.id))
  return depLinesRaw.value.filter(d => visIds.has(d.from) && visIds.has(d.to))
})

// ═══ 展开/收缩操作 ═══
function toggleChapter(ch) {
  const next = new Set(expandedSet.value)
  const isOpen = next.has(ch.id)
  if (isOpen) next.delete(ch.id)
  else next.add(ch.id)
  expandedSet.value = next
  applyExpandedLayout()
  selectChapter(ch)
  nextTick(() => {
    if (!isOpen && next.size === 1) focusOnChapter(ch, true)
    else fitToExpanded()
  })
}

function expandAll() {
  expandedSet.value = new Set(chapters.value.map(c => c.id))
  applyExpandedLayout()
  nextTick(() => fitToExpanded())
}

function collapseAll() {
  expandedSet.value = new Set()
  applyExpandedLayout()
  resetView()
}

function ensureChapterExpanded(node) {
  const chapter = chapters.value.find(item => item.nodes.some(child => child.id === node.id))
  if (!chapter) return
  const next = new Set(expandedSet.value)
  next.add(chapter.id)
  expandedSet.value = next
  applyExpandedLayout()
  nextTick(() => focusOnChapter(chapter, true))
}

/** Focus the camera around a chapter and its visible child nodes. */
function focusOnChapter(ch, expanded) {
  if (!canvasRef.value) return
  const points = expanded && ch.nodes.length
    ? [
        { x: cx, y: cy },
        ...chapters.value.map(chapter => ({ x: chapter.x, y: chapter.y })),
        { x: ch.x, y: ch.y },
        ...ch.nodes.map(node => ({ x: node.x, y: node.y })),
      ]
    : [
        { x: cx, y: cy },
        ...chapters.value.map(chapter => ({ x: chapter.x, y: chapter.y })),
        { x: ch.x, y: ch.y },
      ]

  cameraFit(points, {
    padX: expanded ? 230 : 260,
    padY: expanded ? 240 : 270,
    minScale: expanded ? 0.5 : 0.54,
    maxScale: expanded ? Math.max(0.68, 0.9 - ch.nodes.length * 0.012) : 0.86,
    centerYOffset: expanded ? 6 : -8,
  })
}
// ═══ 选中状态 ═══
const selectedType = ref(null)
const selectedId = ref(null)
const hoverId = ref(null)

const selectedData = computed(() => {
  if (selectedType.value === 'chapter') return chapters.value.find(c => c.id === selectedId.value)
  if (selectedType.value === 'sub') return allSubNodes.value.find(n => n.id === selectedId.value)
  return null
})

function selectCenter() {
  selectedType.value = 'center'
  selectedId.value = null
}
function selectChapter(ch) {
  selectedType.value = 'chapter'
  selectedId.value = ch.id
}
function selectSubNode(n) {
  selectedType.value = 'sub'
  selectedId.value = n.id
  detailTab.value = 'overview'
}
function closePanel() {
  selectedType.value = null
  selectedId.value = null
}
function jumpToNode(id) {
  const n = allSubNodes.value.find(x => x.id === id)
  if (n) {
    selectSubNode(n)
    // 确保所属章节展开
    ensureChapterExpanded(n)
  }
}

// ═══ 高亮链路 ═══
const highlightSet = computed(() => {
  const id = hoverId.value || (selectedType.value === 'sub' ? selectedId.value : null)
  if (!id) return new Set()
  const set = new Set([id])
  const visitUp = (nid) => {
    const n = allSubNodes.value.find(x => x.id === nid)
    if (!n || !n.prerequisites) return
    for (const pid of n.prerequisites) {
      if (!set.has(pid)) { set.add(pid); visitUp(pid) }
    }
  }
  const visitDown = (nid) => {
    for (const n of allSubNodes.value) {
      if (n.prerequisites && n.prerequisites.includes(nid) && !set.has(n.id)) {
        set.add(n.id); visitDown(n.id)
      }
    }
  }
  visitUp(id)
  visitDown(id)
  return set
})

function isHighlighted(id) {
  return highlightSet.value.has(id) && hoverId.value !== null
}
function isDimmed(id) {
  if (!hoverId.value) return false
  return !highlightSet.value.has(id)
}
function isChapterDimmed(ch) {
  if (!hoverId.value) return false
  // 当前 hover 的章节本身不 dim
  if (hoverId.value === ch.id) return false
  // 章节下的任何子节点在 highlightSet 中（即属于当前学习链路），章节就不 dim
  return !ch.nodes.some(n => highlightSet.value.has(n.id))
}
function isLineHighlighted(line) {
  if (!hoverId.value && selectedType.value !== 'sub') return false
  const id = hoverId.value || selectedId.value
  return line.from === id || line.to === id ||
    (highlightSet.value.has(line.from) && highlightSet.value.has(line.to))
}

// ═══ 状态辅助 ═══
function nodeStatusClass(n) {
  return n._status || 'locked'
}
function chapterStatusClass(ch) {
  const done = chapterCompleted(ch)
  const learning = ch.nodes.some(n => n._status === 'learning')
  if (done === ch.nodes.length && ch.nodes.length > 0) return 'done'
  if (learning) return 'learning'
  return 'locked'
}
function chapterCompleted(ch) {
  return ch.nodes.filter(n => n._status === 'done').length
}
function chapterProgress(ch) {
  if (!ch.nodes.length) return 0
  return Math.round(chapterCompleted(ch) / ch.nodes.length * 100)
}
function statusLabel(s) {
  if (s === 'done') return '已掌握'
  if (s === 'learning') return '学习中'
  return '未学习'
}
function nodeName(id) {
  const n = allSubNodes.value.find(x => x.id === id)
  return n ? n.name : id
}
function dependentsOf(id) {
  const result = []
  for (const n of allSubNodes.value) {
    if (n.prerequisites && n.prerequisites.includes(id)) result.push(n.id)
  }
  return result
}

// ═══ 统计 ═══
const totalCompleted = computed(() => allSubNodes.value.filter(n => n._status === 'done').length)
const totalLearning = computed(() => allSubNodes.value.filter(n => n._status === 'learning').length)
const completionRate = computed(() => {
  if (!allSubNodes.value.length) return 0
  return Math.round(totalCompleted.value / allSubNodes.value.length * 100)
})

// ═══ 学习入口 ═══
async function startLearn(node) {
  saveMapState()
  closePanel()
  try {
    await knowledgeApi.startNode(node.id)
    await loadMapData()
  } catch (e) {
    console.warn('[Map] 开始学习失败:', e)
  }
  router.push(`/app/learn/${node.id}`)
}
function goToExam(node) {
  closePanel()
  router.push(`/app/exam/${node.id}`)
}

// ═══ 生命周期 ═══
onMounted(() => {
  window.addEventListener('beforeunload', saveMapState)
  loadMapData()
})
onActivated(() => { if (!chapters.value.length) loadMapData() })
onUnmounted(() => {
  saveMapState()
  entranceContext?.revert()
  window.removeEventListener('beforeunload', saveMapState)
  window.removeEventListener('mousemove', onPanMove)
  window.removeEventListener('mouseup', onPanEnd)
})
</script>

<style lang="scss" scoped>
.map-view {
  height: calc(100vh - var(--topnav-height));
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #f8f9fc;
  position: relative;
}

/* ═══ 顶部栏 ═══ */
.map-topbar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 24px;
  border-bottom: 1px solid rgba(0,0,0,0.06);
  background: rgba(255,255,255,0.92);
  backdrop-filter: blur(12px);
  z-index: 20;
}
.topbar-left {
  display: flex;
  align-items: baseline;
  gap: 12px;
  .map-title { font-size: 19px; font-weight: 700; margin: 0; color: #1e293b; display: flex; align-items: center; }
  .map-subtitle { font-size: 12px; color: #94a3b8; margin: 0; }
}
.topbar-right { display: flex; align-items: center; gap: 12px; }

.action-btn {
  padding: 5px 12px; border: 1px solid rgba(0,0,0,0.08); border-radius: 8px;
  background: #fff; color: #475569; font-size: 12px; font-weight: 600; cursor: pointer;
  display: flex; align-items: center; gap: 4px;
  transition: all 0.2s;
  &:hover { border-color: #b94b5a; color: #b94b5a; background: rgba(59,130,246,0.04); }
}
.legend {
  display: flex; align-items: center; gap: 5px;
  font-size: 11px; color: #64748b;
  span { margin-right: 1px; }
}
.legend-line {
  width: 20px; height: 0; border-top: 2px solid #64748b; display: inline-block;
  &.solid { border-top-style: solid; border-color: #b94b5a; }
  &.dashed { border-top-style: dashed; border-color: #94a3b8; }
}
.legend-dot {
  width: 8px; height: 8px; border-radius: 50%; display: inline-block;
  &.done { background: #22c55e; }
  &.learning { background: #f59e0b; }
}
.toggle-dep-btn {
  padding: 5px 12px; border: 1px solid rgba(0,0,0,0.1); border-radius: 8px;
  background: #fff; color: #64748b; font-size: 12px; font-weight: 600; cursor: pointer;
  transition: all 0.2s;
  &:hover { border-color: #b94b5a; color: #b94b5a; }
  &.active { background: #b94b5a; color: #fff; border-color: #b94b5a; }
}

/* ═══ 画布 ═══ */
.map-canvas {
  flex: 1;
  overflow: hidden;
  position: relative;
  cursor: grab;
  &:active { cursor: grabbing; }
  background:
    radial-gradient(circle at 50% 45%, rgba(59,130,246,0.03) 0%, transparent 55%),
    #f8f9fc;
}
.map-stage {
  position: absolute;
  left: 50%; top: 50%;
  transition: transform 0.05s linear;
}
.map-bg, .map-lines {
  position: absolute;
  left: 0; top: 0;
  pointer-events: none;
}
.map-bg { z-index: 0; }
.map-lines { z-index: 1; }

/* ═══ 中心枢纽 ═══ */
.node-center {
  position: absolute;
  transform: translate(-50%, -50%);
  z-index: 5;
  cursor: pointer;
  .center-inner {
    width: 170px; height: 170px;
    border-radius: 50%;
    background: linear-gradient(135deg, #b94b5a, #c84c5a);
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    box-shadow: 0 8px 32px rgba(59,130,246,0.35), inset 0 2px 12px rgba(255,255,255,0.2);
    border: 3px solid rgba(255,255,255,0.5);
    transition: all 0.3s;
  }
  .center-title { color: #fff; font-size: 22px; font-weight: 800; letter-spacing: 1px; }
  .center-sub { color: rgba(255,255,255,0.86); font-size: 13px; margin-top: 4px; }
  &:hover .center-inner { transform: scale(1.06); box-shadow: 0 12px 40px rgba(59,130,246,0.45); }
  &.selected .center-inner { box-shadow: 0 0 0 4px rgba(59,130,246,0.3), 0 12px 40px rgba(59,130,246,0.5); }
}

/* ═══ 章节节点 ═══ */
.node-chapter {
  position: absolute;
  transform: translate(-50%, -50%);
  z-index: 4;
  cursor: pointer;
  display: flex; flex-direction: column;
  align-items: center; gap: 2px;
  transition: opacity 0.25s, filter 0.25s;
  .chapter-circle {
    width: 98px; height: 98px;
    border-radius: 50%;
    background: #fff;
    border: 2.5px solid var(--ch-color);
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    position: relative;
    transition: all 0.3s;
  }
  .chapter-num { font-size: 25px; font-weight: 800; color: var(--ch-color); }
  .chapter-toggle-icon {
    position: absolute;
    bottom: -2px; right: -2px;
    width: 26px; height: 26px;
    border-radius: 50%;
    background: var(--ch-color);
    color: #fff;
    display: flex; align-items: center; justify-content: center;
    transition: transform 0.3s cubic-bezier(0.34,1.56,0.64,1);
    svg { transform: rotate(-90deg); }
    &.open { svg { transform: rotate(0deg); } }
  }
  .chapter-name { font-size: 15px; font-weight: 700; color: #334155; }
  .chapter-count { font-size: 12px; color: #94a3b8; }
  .chapter-progress { font-size: 12px; font-weight: 700; color: var(--ch-color); }

  &:hover {
    .chapter-circle { transform: scale(1.08); box-shadow: 0 6px 24px rgba(0,0,0,0.12); }
  }
  &.selected .chapter-circle { box-shadow: 0 0 0 4px rgba(200,76,90,0.25), 0 6px 24px rgba(0,0,0,0.12); }
  &.expanded .chapter-circle { border-style: dashed; border-width: 2px; }
  &.done .chapter-circle { background: linear-gradient(135deg, #f0fdf4, #dcfce7); border-color: #22c55e; border-style: solid; .chapter-num { color: #16a34a; } }
  &.learning .chapter-circle { background: linear-gradient(135deg, #fffbeb, #fef3c7); border-color: #f59e0b; border-style: solid; .chapter-num { color: #d97706; } }
  &.dim { opacity: 0.68; filter: saturate(0.9); }
}

/* ═══ 子节点 ═══ */
.node-sub {
  position: absolute;
  transform: translate(-50%, -50%);
  z-index: 3;
  cursor: pointer;
  display: flex; flex-direction: column;
  align-items: center; gap: 3px;
  opacity: 0;
  animation: subFadeIn 0.3s ease forwards;
  transition: opacity 0.25s, transform 0.2s;

  .sub-dot {
    width: 66px; height: 66px;
    border-radius: 50%;
    background: #fff;
    border: 3px solid var(--ch-color);
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 2px 10px rgba(0,0,0,0.07);
    transition: all 0.25s;
  }
  .sub-label {
    font-size: 15px; font-weight: 800; color: #1f2937;
    white-space: nowrap;
    text-shadow: 0 1px 2px rgba(255,255,255,0.8);
    max-width: 150px;
    overflow: hidden; text-overflow: ellipsis;
  }
  .sub-pulse {
    width: 8px; height: 8px; border-radius: 50%;
    background: #f59e0b;
    animation: subPulse 1.8s infinite;
  }
  &:hover { z-index: 6; transform: translate(-50%, -50%) scale(1.18); .sub-dot { box-shadow: 0 4px 16px rgba(0,0,0,0.14); } }
  &.selected { z-index: 6; .sub-dot { box-shadow: 0 0 0 3px rgba(200,76,90,0.3), 0 4px 16px rgba(0,0,0,0.14); } }
  &.done .sub-dot { background: #22c55e; border-color: #16a34a; .sub-label { color: #15803d; } }
  &.learning .sub-dot { background: #fef3c7; border-color: #f59e0b; .sub-label { color: #b45309; } }
  &.locked .sub-dot { background: #eef4fb; border-color: #8fa4bd; .sub-label { color: #334155; } }
  &.hl .sub-dot { box-shadow: 0 0 0 3px rgba(239,68,68,0.3), 0 4px 16px rgba(0,0,0,0.12); }
  &.dim { opacity: 0.66 !important; filter: saturate(0.9); }
}

@keyframes subFadeIn {
  from { opacity: 0; transform: translate(-50%, -50%) scale(0.6); }
  to   { opacity: 1; transform: translate(-50%, -50%) scale(1); }
}
@keyframes subPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(245,158,11,0.5); }
  50% { box-shadow: 0 0 0 6px rgba(245,158,11,0); }
}

/* ═══ 加载/空状态 ═══ */
.map-loading, .map-empty {
  position: absolute; inset: 0; z-index: 10;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 12px;
  background: rgba(248,249,252,0.9);
}
.map-loading-spinner {
  width: 36px; height: 36px;
  border: 3px solid rgba(59,130,246,0.15);
  border-top-color: #b94b5a; border-radius: 50%;
  animation: mapSpin 0.8s linear infinite;
}
@keyframes mapSpin { to { transform: rotate(360deg); } }
.map-empty h3 { font-size: 18px; color: #64748b; margin: 0; }
.map-empty p { font-size: 13px; color: #cbd5e1; margin: 0; }
.map-empty-btn {
  padding: 8px 24px; border: 1px solid rgba(59,130,246,0.3); border-radius: 8px;
  background: rgba(59,130,246,0.08); color: #b94b5a; font-size: 13px; font-weight: 600; cursor: pointer;
  &:hover { background: rgba(59,130,246,0.15); }
}

/* ═══ 缩放控件 ═══ */
.zoom-controls {
  position: absolute;
  bottom: 20px; right: 20px;
  z-index: 15;
  display: flex; flex-direction: column; gap: 4px;
  background: rgba(255,255,255,0.92);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 12px;
  padding: 6px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
  button {
    width: 34px; height: 34px; border: none; border-radius: 8px;
    background: transparent; color: #475569; font-size: 18px; cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    transition: all 0.15s;
    &:hover { background: rgba(59,130,246,0.1); color: #b94b5a; }
  }
  .zoom-level { font-size: 10px; color: #94a3b8; text-align: center; padding: 2px 0; font-weight: 600; }
}

/* ═══ 右侧详情面板 ═══ */
.detail-panel {
  position: absolute;
  top: 56px; right: 0; bottom: 0;
  width: 380px;
  z-index: 30;
  background: rgba(255,255,255,0.98);
  backdrop-filter: blur(20px);
  border-left: 1px solid rgba(0,0,0,0.06);
  box-shadow: -8px 0 32px rgba(0,0,0,0.06);
  padding: 24px 22px;
  overflow-y: auto;
  display: flex; flex-direction: column; gap: 16px;
  &::-webkit-scrollbar { width: 4px; }
  &::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.1); border-radius: 2px; }
}
.detail-close {
  position: absolute; top: 16px; right: 16px;
  width: 28px; height: 28px; border: none; border-radius: 8px;
  background: rgba(0,0,0,0.04); color: #94a3b8; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  &:hover { background: rgba(0,0,0,0.08); color: #475569; }
}
.dp-header { display: flex; flex-direction: column; gap: 6px; }
.dp-badge {
  align-self: flex-start;
  padding: 3px 10px; border-radius: 8px;
  font-size: 11px; font-weight: 700;
  background: rgba(59,130,246,0.1); color: #b94b5a;
  &.center { background: linear-gradient(135deg, rgba(59,130,246,0.15), rgba(200,76,90,0.15)); color: #aa3948; }
}
.dp-title { font-size: 22px; font-weight: 800; color: #1e293b; margin: 0; line-height: 1.2; }
.dp-desc { font-size: 13px; color: #64748b; line-height: 1.6; margin: 0; }
.dp-stats {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px;
  .stat-item {
    display: flex; flex-direction: column; align-items: center; gap: 2px;
    padding: 10px 4px; border-radius: 10px; background: rgba(0,0,0,0.02);
  }
  .stat-num { font-size: 18px; font-weight: 800; color: #1e293b; }
  .stat-label { font-size: 10px; color: #94a3b8; }
}
.dp-section {
  h4 {
    font-size: 11px; color: #94a3b8; text-transform: uppercase;
    letter-spacing: 0.06em; margin: 0 0 10px; font-weight: 700;
  }
}
.chapter-row {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 10px; border-radius: 10px; cursor: pointer;
  transition: background 0.15s;
  margin-bottom: 4px;
  &:hover { background: rgba(59,130,246,0.06); }
  .chapter-row-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
  .chapter-row-name { flex: 1; font-size: 13px; font-weight: 600; color: #334155; }
  .chapter-row-count { font-size: 11px; color: #94a3b8; font-weight: 600; }
  .chapter-row-arrow {
    font-size: 14px; color: #cbd5e1; transition: transform 0.3s;
    &.open { transform: rotate(90deg); color: #b94b5a; }
  }
}
.dp-progress-bar {
  height: 6px; border-radius: 3px; background: rgba(0,0,0,0.06); overflow: hidden;
  .dp-progress-fill { height: 100%; border-radius: 3px; transition: width 0.5s; }
}
.sub-row {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 10px; border-radius: 10px; cursor: pointer;
  transition: all 0.15s; margin-bottom: 4px;
  border: 1px solid transparent;
  &:hover { background: rgba(0,0,0,0.03); border-color: rgba(0,0,0,0.05); }
  .sub-row-idx {
    width: 26px; height: 26px; border-radius: 7px; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 11px; font-weight: 700; background: rgba(0,0,0,0.04); color: #94a3b8;
  }
  .sub-row-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 1px; }
  .sub-row-name { font-size: 13px; font-weight: 600; color: #334155; }
  .sub-row-desc { font-size: 11px; color: #94a3b8; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .sub-row-status { font-size: 10px; font-weight: 600; color: #94a3b8; flex-shrink: 0; }
  &.done { .sub-row-idx { background: #dcfce7; color: #16a34a; } .sub-row-status { color: #16a34a; } }
  &.learning { .sub-row-idx { background: #fef3c7; color: #d97706; } .sub-row-status { color: #d97706; } }
}
.dep-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.dep-chip {
  padding: 5px 12px; border-radius: 8px; font-size: 12px; font-weight: 600;
  background: rgba(239,68,68,0.08); color: #dc2626; cursor: pointer;
  border: 1px solid rgba(239,68,68,0.15);
  transition: all 0.15s;
  &:hover { background: rgba(239,68,68,0.15); }
  &.subsequent { background: rgba(59,130,246,0.08); color: #2563eb; border-color: rgba(59,130,246,0.15); &:hover { background: rgba(59,130,246,0.15); } }
}
.point-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.point-tag {
  padding: 4px 10px; border-radius: 6px; font-size: 12px;
  background: rgba(0,0,0,0.04); color: #64748b; border: 1px solid rgba(0,0,0,0.05);
}
.dp-tip {
  font-size: 12px; color: #64748b; line-height: 1.6;
  padding: 12px 14px; background: rgba(200,76,90,0.05);
  border-radius: 10px; border-left: 3px solid #c84c5a;
}
.dp-actions { display: flex; gap: 10px; margin-top: auto; padding-top: 8px; }
.btn-primary {
  flex: 1; padding: 11px 16px; border: none; border-radius: 10px;
  background: linear-gradient(135deg, #b94b5a, #c84c5a); color: #fff;
  font-size: 13px; font-weight: 700; cursor: pointer; transition: all 0.2s;
  &:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(59,130,246,0.4); }
}
.btn-secondary {
  padding: 11px 16px; border: 1px solid rgba(200,76,90,0.3); border-radius: 10px;
  background: rgba(200,76,90,0.06); color: #c84c5a;
  font-size: 13px; font-weight: 700; cursor: pointer; transition: all 0.2s;
  &:hover { background: rgba(200,76,90,0.12); }
}

/* ═══ 面板动画 ═══ */
.panel-slide-enter-active, .panel-slide-leave-active { transition: all 0.3s cubic-bezier(0.16,1,0.3,1); }
.panel-slide-enter-from, .panel-slide-leave-to { transform: translateX(100%); opacity: 0; }
/* ═══ 知识大脑 2.5D 与个性化路径 ═══ */
.map-view {
  --brain-primary: #6d5dfc;
  --brain-secondary: #22c7d6;
  --brain-ink: #172033;
  --brain-muted: #73809a;
}
.map-topbar { min-height: 64px; padding: 8px 18px; gap: 18px; }
.topbar-left { align-items: center; min-width: 220px; gap: 10px;
  .map-title { font-size: 18px; line-height: 1.1; }
  .map-subtitle { margin-top: 4px; font-size: 11px; }
}
.brain-mark { width: 38px; height: 38px; border-radius: 13px; position: relative; flex-shrink: 0;
  background: linear-gradient(145deg,#7567ff,#5547dc); box-shadow: 0 10px 24px rgba(92,76,231,.26);
  span { position:absolute;width:8px;height:8px;border:2px solid rgba(255,255,255,.92);border-radius:50%;
    &:nth-child(1){left:8px;top:8px}&:nth-child(2){right:7px;top:11px}&:nth-child(3){left:15px;bottom:6px}
  }
  &::before,&::after{content:'';position:absolute;height:1.5px;background:rgba(255,255,255,.8);transform-origin:left center}
  &::before{width:16px;left:12px;top:14px;transform:rotate(14deg)}
  &::after{width:13px;left:13px;top:17px;transform:rotate(55deg)}
}
.view-switch { display:flex; align-items:center; gap:4px; padding:4px; border-radius:12px; background:#f3f4f8; border:1px solid rgba(15,23,42,.05);
  button { border:0;background:transparent;color:#768198;padding:7px 10px;border-radius:9px;font-size:11px;font-weight:650;cursor:pointer;white-space:nowrap;transition:all .2s;display:flex;align-items:center;gap:5px;
    &:hover{color:#aa3948;background:rgba(255,255,255,.7)}
    &.active{color:#aa3948;background:#fff;box-shadow:0 3px 10px rgba(31,41,55,.08)}
  }
}
.topbar-right { margin-left:auto; gap:8px; }
.map-search { position:relative; width:186px;
  .search-icon{position:absolute;left:10px;top:50%;transform:translateY(-50%);font-size:17px;color:#9aa4b6;z-index:1}
  input{width:100%;height:34px;padding:0 12px 0 31px;border:1px solid #e5e8ef;border-radius:10px;background:#f8f9fc;color:#253047;font-size:12px;outline:none;transition:all .2s;
    &:focus{background:#fff;border-color:rgba(200,76,90,.45);box-shadow:0 0 0 3px rgba(200,76,90,.08)}
  }
}
.search-results { position:absolute;top:40px;left:0;right:0;z-index:70;background:#fff;border:1px solid #e8eaf0;border-radius:12px;padding:6px;box-shadow:0 18px 45px rgba(31,41,55,.16);
  button{width:100%;border:0;background:transparent;border-radius:8px;padding:8px 9px;text-align:left;display:flex;justify-content:space-between;gap:8px;cursor:pointer;color:#27324a;font-size:12px;
    small{color:#9aa4b6;font-size:10px}&:hover{background:#f2f0ff;color:#5b4ce3}
  }
}
.icon-action { height:34px;border:1px solid #e5e8ef;border-radius:10px;background:#fff;color:#667189;cursor:pointer;transition:all .2s; }
.icon-action{width:36px;font-size:18px;&.active{color:#5b4ce3;border-color:rgba(200,76,90,.35);background:#f2f0ff}&.wide{width:auto;padding:0 11px;font-size:11px;font-weight:800}}
.map-canvas { background:radial-gradient(circle at 50% 46%,rgba(200,76,90,.11),transparent 31%),radial-gradient(circle at 28% 72%,rgba(34,199,214,.07),transparent 24%),#f7f8fc; }
.map-stage { will-change:transform; transition:transform .12s linear; }
.mode-mastery .node-sub {
  border-color: var(--mastery-color);
  background: #fff;
  box-shadow: 0 10px 26px rgba(15,23,42,.12);
}
.mode-mastery .node-sub .sub-dot {
  background: var(--mastery-color) !important;
  border-color: #fff !important;
  color: #fff;
  box-shadow: 0 0 0 5px rgba(15,23,42,.06), 0 8px 18px rgba(15,23,42,.16);
}
.mode-mastery .node-sub .sub-label { color:#172033; font-weight:850; }
.mastery-dot-score { color:#fff; font-size:17px; font-weight:900; line-height:1; }
.mode-mastery .node-sub::before {
  content: '';
  position:absolute;
  left:6px;
  right:6px;
  bottom:5px;
  height:4px;
  border-radius:999px;
  background:linear-gradient(90deg,var(--mastery-color) var(--mastery),#d6dee8 0);
}
.mode-mastery .node-sub.mastery-empty { opacity:1; }
.personal-path-glow{fill:none;stroke:#6d5dfc;stroke-width:11;stroke-linecap:round;opacity:.14;filter:drop-shadow(0 0 10px rgba(109,93,252,.8))}
.personal-path-flow{fill:none;stroke:#7c6cff;stroke-width:3.5;stroke-linecap:round;stroke-dasharray:5 13;animation:path-flow 1.3s linear infinite;filter:drop-shadow(0 0 4px rgba(109,93,252,.85))}
@keyframes path-flow{to{stroke-dashoffset:-36}}
.node-sub.on-personal-path .sub-dot{border-color:#7465f7;box-shadow:0 0 0 6px rgba(109,93,252,.1),0 0 18px rgba(109,93,252,.45)}
.node-sub.path-current{z-index:12;
  .sub-label{color:#aa3948;font-weight:800}.sub-dot{background:linear-gradient(135deg,#6d5dfc,#32bfd0)!important;border-color:#fff!important}
}
.path-step-badge{position:absolute;left:-13px;top:-13px;min-width:24px;height:24px;border-radius:10px;padding:0 5px;display:flex;align-items:center;justify-content:center;background:#6d5dfc;color:#fff;font-size:12px;font-weight:850;box-shadow:0 4px 10px rgba(79,70,229,.32)}
@keyframes current-node-pulse{50%{transform:scale(1.14);box-shadow:0 0 0 9px rgba(109,93,252,.09),0 0 24px rgba(109,93,252,.5)}}
.map-legend{position:absolute;left:20px;bottom:20px;display:flex;gap:12px;padding:8px 11px;background:rgba(255,255,255,.86);backdrop-filter:blur(12px);border:1px solid rgba(15,23,42,.06);border-radius:10px;font-size:10px;color:#788399;z-index:12;
  span{display:flex;align-items:center;gap:5px}i{width:7px;height:7px;border-radius:50%;display:block}.done{background:#22c55e}.learning{background:#f59e0b}.recommended{background:#6d5dfc;box-shadow:0 0 0 3px rgba(109,93,252,.13)}
}
.mode-personal .detail-panel{bottom:104px}.mode-personal .zoom-controls,.mode-personal .map-legend{bottom:108px}.detail-panel{top:64px;width:410px;padding:22px 22px 18px;gap:14px}.dp-badge.personal{background:#eeecff;color:#5b4ce3}.dp-path{margin:0;color:#9aa4b6;font-size:11px}.detail-tabs{display:grid;grid-template-columns:repeat(3,1fr);gap:4px;background:#f3f4f8;border-radius:10px;padding:4px;
  button{border:0;background:transparent;border-radius:7px;padding:7px 5px;color:#7b8599;font-size:11px;font-weight:700;cursor:pointer;&.active{background:#fff;color:#5b4ce3;box-shadow:0 2px 8px rgba(31,41,55,.07)}}
}
.mastery-card{display:flex;align-items:center;gap:15px;padding:14px;border:1px solid #ebeaf6;border-radius:14px;background:linear-gradient(135deg,#fbfaff,#f4fbfc)}
.mastery-ring{--mastery:0%;width:76px;height:76px;border-radius:50%;flex-shrink:0;display:flex;flex-direction:column;align-items:center;justify-content:center;position:relative;background:conic-gradient(#6d5dfc var(--mastery),#e8eaf1 0);
  &::after{content:'';position:absolute;inset:7px;border-radius:50%;background:#fff}strong,small{position:relative;z-index:1}strong{font-size:17px;color:#302875}small{font-size:9px;color:#929bad}
}
.mastery-copy{display:flex;flex-direction:column;gap:3px;min-width:0;strong{font-size:14px;color:#243047}span{font-size:10px;color:#6d5dfc}p{font-size:11px;color:#7c879a;line-height:1.5;margin:4px 0 0}}
.agent-reason-card{padding:16px;border-radius:15px;background:linear-gradient(145deg,#252451,#30306b);color:#fff;box-shadow:0 16px 30px rgba(43,43,95,.18)}
.agent-reason-head{display:flex;align-items:center;gap:10px;margin-bottom:12px;.agent-orbit{width:36px;height:36px;border:1px solid rgba(255,255,255,.25);border-radius:50%;position:relative;animation:agent-spin 7s linear infinite;i{position:absolute;width:8px;height:8px;border-radius:50%;background:#65e5e7;top:-4px;left:13px;box-shadow:0 0 12px #65e5e7}}div{display:flex;flex-direction:column}strong{font-size:14px}small{font-size:10px;color:#acb6d9}}
.agent-summary{font-size:12px;line-height:1.65;color:#e7eafa;margin:0 0 10px}.agent-reason-card ul{padding-left:17px;margin:0;display:grid;gap:7px}.agent-reason-card li{font-size:11px;line-height:1.45;color:#c9d0ed}
@keyframes agent-spin{to{transform:rotate(360deg)}}
.agent-pipeline{display:grid;grid-template-columns:repeat(5,1fr);gap:5px;position:relative;
  &::before{content:'';position:absolute;left:9%;right:9%;top:15px;height:1px;background:#e0e3ec}
  span{position:relative;z-index:1;display:flex;flex-direction:column;align-items:center;gap:5px;text-align:center;color:#a1a8b6;i{width:30px;height:30px;border-radius:50%;background:#eef0f5;display:flex;align-items:center;justify-content:center;font-style:normal;font-size:11px;border:3px solid #fff}small{font-size:9px;white-space:nowrap}&.done{color:#aa3948} &.done i{background:#eeecff;color:#5b4ce3}&.active i{animation:nl-agent-pulse 1.5s infinite}}
}
@keyframes nl-agent-pulse{50%{box-shadow:0 0 0 7px rgba(109,93,252,.12)}}
.resource-readiness{display:grid;gap:8px}.resource-ready-row{display:flex;align-items:center;gap:10px;padding:11px;border:1px solid #eceef3;border-radius:12px;background:#fff;
  .resource-ready-icon{width:32px;height:32px;border-radius:9px;background:#f1efff;color:#5b4ce3;display:flex;align-items:center;justify-content:center;font-size:15px}div{flex:1;display:flex;flex-direction:column;gap:2px}strong{font-size:12px;color:#2d374c}small{font-size:10px;color:#929bad}.resource-state{font-size:9px;font-weight:700;padding:4px 7px;border-radius:8px;&.ready{background:#eaf9f1;color:#15945a}&.pending{background:#f2f3f6;color:#8791a4}}
}
.path-dock{position:absolute;left:14px;right:14px;bottom:10px;height:84px;z-index:28;display:flex;align-items:center;gap:16px;padding:10px 14px;border:1px solid rgba(200,76,90,.15);border-radius:16px;background:rgba(255,255,255,.94);backdrop-filter:blur(18px);box-shadow:0 16px 45px rgba(42,44,83,.14);transition:all .25s;
  &.collapsed{left:auto;width:245px;height:52px}.path-dock-toggle{position:absolute;right:10px;top:7px;border:0;background:transparent;color:#8b94a5;font-size:9px;cursor:pointer}.path-dock-heading{width:190px;display:flex;align-items:center;gap:9px;flex-shrink:0}.path-dock-heading>div{display:flex;flex-direction:column;gap:2px}.path-dock-heading strong{font-size:12px;color:#263047}.path-dock-heading small{font-size:9px;color:#929bad}.ai-badge{width:34px;height:34px;border-radius:11px;background:linear-gradient(135deg,#6959ec,#29b8c7);color:#fff;font-size:11px;font-weight:850;display:flex;align-items:center;justify-content:center;box-shadow:0 8px 16px rgba(94,78,226,.24)}
}
.path-steps{flex:1;display:flex;align-items:center;gap:22px;min-width:0;overflow-x:auto;padding:3px 26px 3px 3px;&::-webkit-scrollbar{height:3px}&::-webkit-scrollbar-thumb{background:#dfe1e8;border-radius:2px}}
.path-steps button{position:relative;min-width:142px;display:flex;align-items:center;gap:8px;border:0;background:transparent;padding:4px;text-align:left;cursor:pointer;
  &::after{content:'›';position:absolute;right:-16px;color:#c5cad4;font-size:18px}&:last-child::after{display:none}>span{width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:#eef0f5;color:#858fa2;font-size:12px;font-weight:850;flex-shrink:0}div{display:flex;flex-direction:column;gap:1px;min-width:0}strong{font-size:10px;color:#5c6679;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}small{font-size:8px;color:#a4abba}&.completed>span{background:#e5f8ef;color:#17945b}&.current>span{background:#6d5dfc;color:#fff;box-shadow:0 0 0 5px rgba(109,93,252,.12)}&.current strong{color:#aa3948}
}
@media(max-width:1280px){.view-switch button{padding:7px 8px}.view-switch button span{display:none}.map-search{width:150px}.detail-panel{width:380px}.path-dock-heading{width:170px}}
@media(max-width:980px){.view-switch{display:none}.detail-panel{width:min(390px,88vw)}.path-dock{right:8px;left:8px}.path-dock-heading{display:none}}
@media(prefers-reduced-motion:reduce){.brain-atmosphere span,.personal-path-flow,.node-sub.path-current .sub-dot,.agent-orbit{animation:none!important}.map-stage{transition:none}.node-center,.node-chapter,.node-sub{will-change:auto}}
</style>





