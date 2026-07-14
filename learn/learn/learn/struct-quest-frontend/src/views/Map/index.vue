<template>
  <div class="map-view">
    <!-- 顶部标题栏 -->
    <div class="map-topbar">
      <div class="topbar-left">
        <h1 class="map-title">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:6px;">
            <circle cx="12" cy="12" r="3"/><circle cx="5" cy="5" r="2"/><circle cx="19" cy="5" r="2"/>
            <circle cx="5" cy="19" r="2"/><circle cx="19" cy="19" r="2"/>
            <line x1="7" y1="7" x2="10" y2="10"/><line x1="17" y1="7" x2="14" y2="10"/>
            <line x1="7" y1="17" x2="10" y2="14"/><line x1="17" y1="17" x2="14" y2="14"/>
          </svg>
          知识图谱
        </h1>
        <p class="map-subtitle">数据结构与算法 · {{ allNodes.length }} 个知识点 · {{ chapters.length }} 大章节</p>
      </div>
      <div class="topbar-right">
        <button class="action-btn" @click="expandAll" title="展开全部章节">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M2 8h12M8 2v12"/></svg>全部展开
        </button>
        <button class="action-btn" @click="collapseAll" title="收缩全部章节">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M2 8h12"/></svg>全部收缩
        </button>
        <div class="legend">
          <span class="legend-line solid"></span><span>包含</span>
          <span class="legend-line dashed"></span><span>依赖</span>
          <span class="legend-dot done"></span><span>已掌握</span>
          <span class="legend-dot learning"></span><span>学习中</span>
        </div>
        <button class="toggle-dep-btn" :class="{ active: showDeps }" @click="showDeps = !showDeps">
          {{ showDeps ? '隐藏' : '显示' }}依赖线
        </button>
      </div>
    </div>

    <!-- 地图画布 -->
    <div class="map-canvas" ref="canvasRef"
      @mousedown="onPanStart" @wheel.prevent="onWheel"
    >
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
              <stop offset="60%" stop-color="rgba(139,92,246,0.02)" />
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
          :class="[chapterStatusClass(ch), { selected: selectedId === ch.id, expanded: expandedSet.has(ch.id), dim: isDimmed(ch.id) }]"
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
            :class="[nodeStatusClass(n), { selected: selectedId === n.id, dim: isDimmed(n.id), hl: isHighlighted(n.id) }]"
            :style="{ left: n.x + 'px', top: n.y + 'px', '--ch-color': n._color }"
            @click.stop="selectSubNode(n)"
            @mouseenter="hoverId = n.id"
            @mouseleave="hoverId = null"
          >
            <div class="sub-dot">
              <svg v-if="n._status === 'done'" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3"><path d="M5 12l5 5L20 7"/></svg>
              <span v-else-if="n._status === 'learning'" class="sub-pulse"></span>
            </div>
            <span class="sub-label">{{ n.name }}</span>
          </div>
        </template>
      </div>

      <!-- 缩放控件 -->
      <div class="zoom-controls">
        <button @click="zoomIn" title="放大">＋</button>
        <button @click="zoomOut" title="缩小">−</button>
        <button @click="resetView" title="重置视图">⟲</button>
        <button @click="fitToExpanded" title="适应视图">⊡</button>
        <span class="zoom-level">{{ Math.round(scale * 100) }}%</span>
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
            <span class="dp-badge" :style="{ background: selectedData._color + '18', color: selectedData._color }">{{ selectedData._chapterTitle }}</span>
            <h2 class="dp-title">{{ selectedData.name }}</h2>
          </div>
          <p class="dp-desc">{{ selectedData.fullDesc || selectedData.desc || '' }}</p>

          <div v-if="selectedData.prerequisites && selectedData.prerequisites.length" class="dp-section">
            <h4>前置知识</h4>
            <div class="dep-chips">
              <span v-for="pid in selectedData.prerequisites" :key="pid"
                class="dep-chip"
                @click="jumpToNode(pid)"
              >{{ nodeName(pid) }}</span>
            </div>
          </div>

          <div v-if="dependentsOf(selectedData.id).length" class="dp-section">
            <h4>后续知识</h4>
            <div class="dep-chips">
              <span v-for="did in dependentsOf(selectedData.id)" :key="did"
                class="dep-chip subsequent"
                @click="jumpToNode(did)"
              >{{ nodeName(did) }}</span>
            </div>
          </div>

          <div class="dp-section">
            <h4>核心知识点</h4>
            <div class="point-tags">
              <span v-for="p in (selectedData.points || [])" :key="p" class="point-tag">{{ p }}</span>
            </div>
          </div>

          <div class="dp-tip">{{ selectedData.aiSuggestion || selectedData.ai_suggestion || '建议按顺序学习' }}</div>

          <div class="dp-actions">
            <button class="btn-primary" @click="startLearn(selectedData)">
              {{ selectedData._status === 'done' ? '复习巩固' : selectedData._status === 'learning' ? '继续学习' : '开始学习' }}
            </button>
            <button class="btn-secondary" @click="goToExam(selectedData)">章节测试</button>
          </div>
        </template>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onActivated, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import knowledgeApi from '@/api/knowledge'

const router = useRouter()

// ═══ 画布尺寸（足够大以容纳所有展开的节点） ═══
const stageW = 2200
const stageH = 1800
const cx = stageW / 2
const cy = stageH / 2
const R1 = 280           // 章节环半径

// ═══ 章节配色 ═══
const CHAPTER_META = {
  ch01_intro:        { num: '01', title: '绪论',         color: '#3b82f6' },
  ch02_linear_list:  { num: '02', title: '线性表',       color: '#22c55e' },
  ch03_stack_queue:  { num: '03', title: '栈和队列',     color: '#06b6d4' },
  ch04_string_array: { num: '04', title: '串数组广义表', color: '#6366f1' },
  ch05_tree:         { num: '05', title: '树和二叉树',   color: '#14b8a6' },
  ch06_graph:        { num: '06', title: '图',           color: '#8b5cf6' },
  ch07_search:       { num: '07', title: '查找',         color: '#f97316' },
  ch08_sort:         { num: '08', title: '排序',         color: '#ec4899' },
}

// ═══ 数据 ═══
const loading = ref(true)
const chapters = ref([])          // 含位置和子节点位置
const allNodes = ref([])          // 扁平节点列表（原始数据）
const showDeps = ref(true)

// ═══ 展开/收缩状态 ═══
const expandedSet = ref(new Set()) // 已展开的章节 ID 集合

// ═══ 平移缩放 ═══
const scale = ref(0.65)
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
function zoomIn() { scale.value = Math.min(2.5, scale.value + 0.15) }
function zoomOut() { scale.value = Math.max(0.2, scale.value - 0.15) }
function resetView() {
  scale.value = 0.65
  panX.value = 0
  panY.value = 0
}

/** 根据当前展开状态自适应缩放 */
function fitToExpanded() {
  const expCount = expandedSet.value.size
  if (expCount === 0) {
    scale.value = 0.65
    panX.value = 0
    panY.value = 0
    return
  }
  // 展开越多，需要越小的 scale 以容纳所有内容
  const targetScale = Math.max(0.28, 0.65 - expCount * 0.06)
  animateScale(scale.value, targetScale)
}

/** 平滑过渡到目标缩放 */
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
async function loadMapData() {
  loading.value = true
  try {
    const res = await knowledgeApi.getMap()
    allNodes.value = res.nodes || []
    chapters.value = buildLayout(res.categories || [], res.nodes || [])
  } catch (e) {
    console.warn('[Map] 后端加载失败，使用本地 fallback:', e)
    const { stages: fallback } = await import('@/data/knowledgeMap.js')
    const flatNodes = []
    const cats = fallback.map(s => {
      const ns = s.nodes.map(n => ({ ...n, category: s.id }))
      flatNodes.push(...ns)
      return { id: s.id, title: s.title, nodes: ns }
    })
    allNodes.value = flatNodes
    chapters.value = buildLayout(cats, flatNodes)
  } finally {
    loading.value = false
  }
}

// ═══ 布局计算 ═══
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
    const dynamicR2 = 170 + Math.min(N * 11, 200)
    const half = (N - 1) / 2
    // 步长 = 总扇形角度 / (N-1)
    const step = N > 1 ? (2 * spreadRad) / (N - 1) : 0

    const positionedNodes = catNodes.map((n, j) => {
      const subAngle = angle + (j - half) * step
      const nx = chX + dynamicR2 * Math.cos(subAngle)
      const ny = chY + dynamicR2 * Math.sin(subAngle)
      const status = n.status === 'completed' ? 'done' : (n.status === 'in_progress' || n.status === 'learning') ? 'learning' : 'locked'
      return {
        ...n,
        name: n.title || n.name,
        desc: n.description || n.desc || '',
        fullDesc: n.full_desc || n.fullDesc || n.description || '',
        points: n.points || [],
        prerequisites: n.prerequisites || [],
        aiSuggestion: n.ai_suggestion || n.aiSuggestion || '建议按顺序学习',
        x: nx, y: ny,
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
  const newSet = new Set(expandedSet.value)
  if (newSet.has(ch.id)) {
    newSet.delete(ch.id)
  } else {
    newSet.add(ch.id)
  }
  expandedSet.value = newSet
  selectChapter(ch)

  // 自动聚焦到展开的章节
  nextTick(() => focusOnChapter(ch, newSet.has(ch.id)))
}

function expandAll() {
  expandedSet.value = new Set(chapters.value.map(c => c.id))
  nextTick(() => fitToExpanded())
}

function collapseAll() {
  expandedSet.value = new Set()
  resetView()
}

function ensureChapterExpanded(node) {
  // 从 node 的 _chapterTitle 反查 chapter id
  for (const ch of chapters.value) {
    if (ch.title === node._chapterTitle && !expandedSet.value.has(ch.id)) {
      toggleChapter(ch)
      break
    }
  }
}

/** 将视图平移+缩放到指定章节区域 */
function focusOnChapter(ch, expanded) {
  if (!canvasRef.value) return
  const rect = canvasRef.value.getBoundingClientRect()
  const viewCx = rect.width / 2
  const viewCy = rect.height / 2

  // 目标：将章节节点移到视野中央附近
  // 如果展开了，目标点取章节和子节点之间的中间位置
  let targetX = ch.x
  let targetY = ch.y
  if (expanded && ch.nodes.length) {
    // 计算该章节所有节点的包围盒中心
    const xs = [ch.x, ...ch.nodes.map(n => n.x)]
    const ys = [ch.y, ...ch.nodes.map(n => n.y)]
    targetX = (Math.min(...xs) + Math.max(...xs)) / 2
    targetY = (Math.min(...ys) + Math.max(...ys)) / 2
  }

  // 当前画布中心在屏幕坐标中的位置
  const currentScreenX = cx * scale.value + panX.value
  const currentScreenY = cy * scale.value + panY.value

  // 目标在屏幕坐标中应该的位置
  const targetScreenX = targetX * scale.value + panX.value
  const targetScreenY = targetY * scale.value + panY.value

  // 需要的偏移量
  const dx = viewCx - targetScreenX
  const dy = viewCy - targetScreenY

  // 如果展开了且节点较多，适当缩小
  const targetScale = expanded ? Math.max(0.38, 0.65 - ch.nodes.length * 0.018) : 0.65

  // 动画过渡
  const startPanX = panX.value
  const startPanY = panY.value
  const startScale = scale.value
  const endPanX = panX.value + dx
  const endPanY = panY.value + dy
  const steps = 15
  let step = 0
  const tick = () => {
    step++
    const t = step / steps
    const ease = t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2
    scale.value = startScale + (targetScale - startScale) * ease
    panX.value = startPanX + (endPanX - startPanX) * ease
    panY.value = startPanY + (endPanY - startPanY) * ease
    if (step < steps) requestAnimationFrame(tick)
  }
  tick()
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
onMounted(() => { loadMapData() })
onActivated(() => { loadMapData() })
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
  &:hover { border-color: #3b82f6; color: #3b82f6; background: rgba(59,130,246,0.04); }
}
.legend {
  display: flex; align-items: center; gap: 5px;
  font-size: 11px; color: #64748b;
  span { margin-right: 1px; }
}
.legend-line {
  width: 20px; height: 0; border-top: 2px solid #64748b; display: inline-block;
  &.solid { border-top-style: solid; border-color: #3b82f6; }
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
  &:hover { border-color: #3b82f6; color: #3b82f6; }
  &.active { background: #3b82f6; color: #fff; border-color: #3b82f6; }
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
    width: 130px; height: 130px;
    border-radius: 50%;
    background: linear-gradient(135deg, #3b82f6, #6366f1);
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    box-shadow: 0 8px 32px rgba(59,130,246,0.35), inset 0 2px 12px rgba(255,255,255,0.2);
    border: 3px solid rgba(255,255,255,0.5);
    transition: all 0.3s;
  }
  .center-title { color: #fff; font-size: 17px; font-weight: 800; letter-spacing: 1px; }
  .center-sub { color: rgba(255,255,255,0.8); font-size: 11px; margin-top: 4px; }
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
    width: 72px; height: 72px;
    border-radius: 50%;
    background: #fff;
    border: 2.5px solid var(--ch-color);
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    position: relative;
    transition: all 0.3s;
  }
  .chapter-num { font-size: 18px; font-weight: 800; color: var(--ch-color); }
  .chapter-toggle-icon {
    position: absolute;
    bottom: -2px; right: -2px;
    width: 20px; height: 20px;
    border-radius: 50%;
    background: var(--ch-color);
    color: #fff;
    display: flex; align-items: center; justify-content: center;
    transition: transform 0.3s cubic-bezier(0.34,1.56,0.64,1);
    svg { transform: rotate(-90deg); }
    &.open { svg { transform: rotate(0deg); } }
  }
  .chapter-name { font-size: 13px; font-weight: 700; color: #334155; }
  .chapter-count { font-size: 10px; color: #94a3b8; }
  .chapter-progress { font-size: 10px; font-weight: 700; color: var(--ch-color); }

  &:hover {
    .chapter-circle { transform: scale(1.08); box-shadow: 0 6px 24px rgba(0,0,0,0.12); }
  }
  &.selected .chapter-circle { box-shadow: 0 0 0 4px rgba(99,102,241,0.25), 0 6px 24px rgba(0,0,0,0.12); }
  &.expanded .chapter-circle { border-style: dashed; border-width: 2px; }
  &.done .chapter-circle { background: linear-gradient(135deg, #f0fdf4, #dcfce7); border-color: #22c55e; border-style: solid; .chapter-num { color: #16a34a; } }
  &.learning .chapter-circle { background: linear-gradient(135deg, #fffbeb, #fef3c7); border-color: #f59e0b; border-style: solid; .chapter-num { color: #d97706; } }
  &.dim { opacity: 0.25; }
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
    width: 36px; height: 36px;
    border-radius: 50%;
    background: #fff;
    border: 2px solid var(--ch-color);
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 2px 10px rgba(0,0,0,0.07);
    transition: all 0.25s;
  }
  .sub-label {
    font-size: 11px; font-weight: 600; color: #475569;
    white-space: nowrap;
    text-shadow: 0 1px 2px rgba(255,255,255,0.8);
    max-width: 80px;
    overflow: hidden; text-overflow: ellipsis;
  }
  .sub-pulse {
    width: 8px; height: 8px; border-radius: 50%;
    background: #f59e0b;
    animation: subPulse 1.8s infinite;
  }
  &:hover { z-index: 6; transform: translate(-50%, -50%) scale(1.18); .sub-dot { box-shadow: 0 4px 16px rgba(0,0,0,0.14); } }
  &.selected { z-index: 6; .sub-dot { box-shadow: 0 0 0 3px rgba(99,102,241,0.3), 0 4px 16px rgba(0,0,0,0.14); } }
  &.done .sub-dot { background: #22c55e; border-color: #16a34a; .sub-label { color: #15803d; } }
  &.learning .sub-dot { background: #fef3c7; border-color: #f59e0b; .sub-label { color: #b45309; } }
  &.locked .sub-dot { background: #f1f5f9; border-color: #cbd5e1; .sub-label { color: #94a3b8; } }
  &.hl .sub-dot { box-shadow: 0 0 0 3px rgba(239,68,68,0.3), 0 4px 16px rgba(0,0,0,0.12); }
  &.dim { opacity: 0.2 !important; }
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
  border-top-color: #3b82f6; border-radius: 50%;
  animation: mapSpin 0.8s linear infinite;
}
@keyframes mapSpin { to { transform: rotate(360deg); } }
.map-empty h3 { font-size: 18px; color: #64748b; margin: 0; }
.map-empty p { font-size: 13px; color: #cbd5e1; margin: 0; }
.map-empty-btn {
  padding: 8px 24px; border: 1px solid rgba(59,130,246,0.3); border-radius: 8px;
  background: rgba(59,130,246,0.08); color: #3b82f6; font-size: 13px; font-weight: 600; cursor: pointer;
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
    &:hover { background: rgba(59,130,246,0.1); color: #3b82f6; }
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
  background: rgba(59,130,246,0.1); color: #3b82f6;
  &.center { background: linear-gradient(135deg, rgba(59,130,246,0.15), rgba(99,102,241,0.15)); color: #4f46e5; }
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
    &.open { transform: rotate(90deg); color: #3b82f6; }
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
  padding: 12px 14px; background: rgba(99,102,241,0.05);
  border-radius: 10px; border-left: 3px solid #6366f1;
}
.dp-actions { display: flex; gap: 10px; margin-top: auto; padding-top: 8px; }
.btn-primary {
  flex: 1; padding: 11px 16px; border: none; border-radius: 10px;
  background: linear-gradient(135deg, #3b82f6, #6366f1); color: #fff;
  font-size: 13px; font-weight: 700; cursor: pointer; transition: all 0.2s;
  &:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(59,130,246,0.4); }
}
.btn-secondary {
  padding: 11px 16px; border: 1px solid rgba(99,102,241,0.3); border-radius: 10px;
  background: rgba(99,102,241,0.06); color: #6366f1;
  font-size: 13px; font-weight: 700; cursor: pointer; transition: all 0.2s;
  &:hover { background: rgba(99,102,241,0.12); }
}

/* ═══ 面板动画 ═══ */
.panel-slide-enter-active, .panel-slide-leave-active { transition: all 0.3s cubic-bezier(0.16,1,0.3,1); }
.panel-slide-enter-from, .panel-slide-leave-to { transform: translateX(100%); opacity: 0; }
</style>
