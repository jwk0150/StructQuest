<template>
  <div class="ai-lab">
    <!-- ═══════ 顶部标题栏 ═══════ -->
    <header class="lab-header">
      <div class="lab-header-top">
        <div class="lab-brand">
          <span class="lab-brand-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
              <rect x="2" y="2" width="20" height="20" rx="2.18"/>
              <line x1="7" y1="2" x2="7" y2="22"/>
              <line x1="17" y1="2" x2="17" y2="22"/>
              <line x1="2" y1="12" x2="22" y2="12"/>
              <line x1="2" y1="7" x2="7" y2="7"/>
              <line x1="2" y1="17" x2="7" y2="17"/>
              <line x1="17" y1="7" x2="22" y2="7"/>
              <line x1="17" y1="17" x2="22" y2="17"/>
            </svg>
          </span>
          <div>
            <h1 class="lab-title">AI 算法实验室</h1>
            <p class="lab-subtitle">让算法不只会动，更会讲、会问、会思考</p>
          </div>
        </div>
        <div class="lab-mode-badge" v-if="currentPreset || animSource">
          <span class="mode-dot" :class="{ ai: animSource === 'ai' || animSource === 'ai_cached' }"></span>
          {{ animSource === 'ai' ? 'AI 生成' : animSource === 'ai_cached' ? 'AI 缓存' : '预设模式' }}
          <template v-if="currentPreset"> · {{ currentPreset.difficulty }}</template>
        </div>
        <div class="lab-mode-badge loading-badge" v-if="isLoading">
          <span class="loading-spinner"></span>
          {{ loadingMessage }}
        </div>
      </div>
    </header>

    <!-- ═══════ 左中右三栏主体 ═══════ -->
    <div class="lab-main">
      <!-- ▸ 左侧栏折叠按钮 -->
      <button class="collapse-btn left-toggle" :class="{ collapsed: leftCollapsed }" @click="leftCollapsed = !leftCollapsed" title="折叠侧栏">
        {{ leftCollapsed ? '▶' : '◀' }}
      </button>
      <button class="collapse-btn right-toggle" :class="{ collapsed: rightCollapsed }" @click="rightCollapsed = !rightCollapsed" title="折叠侧栏">
        {{ rightCollapsed ? '◀' : '▶' }}
      </button>

      <!-- ▸ 左侧：算法选择器 + 问答输入 -->
      <aside class="lab-left" :class="{ collapsed: leftCollapsed }">
        <div v-if="!leftCollapsed" class="lab-left-inner">
          <!-- 算法选择器：按分类分组 -->
          <div class="algo-section">
            <div class="algo-section-title">算法选择</div>
            <div
              v-for="group in algoGroups"
              :key="group.key"
              class="algo-group"
            >
              <div class="group-label">
                <span class="group-dot" :class="'dot-' + group.key"></span>
                {{ group.label }}
                <span class="group-count">{{ group.items.length }}</span>
              </div>
              <div class="group-chips">
                <button
                  v-for="algo in group.items"
                  :key="algo.id"
                  class="algo-chip"
                  :class="{ active: selectedPresetId === algo.id }"
                  @click="selectPreset(algo)"
                >
                  <span class="chip-icon">{{ algo.icon }}</span>
                  <span class="chip-name">{{ algo.name }}</span>
                  <span class="chip-diff">{{ algo.difficulty }}</span>
                </button>
              </div>
            </div>
          </div>

          <!-- 问答输入区 -->
          <div class="qa-section">
            <div class="qa-input-row">
              <input
                ref="inputRef"
                v-model="userInput"
                @keyup.enter="submitInput"
                placeholder="输入算法名称或描述..."
                class="qa-input"
                :disabled="isLoading"
              />
              <button
                class="qa-send-btn"
                :disabled="!userInput.trim() || isLoading"
                @click="submitInput"
              >
                <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
              </button>
            </div>
            <div class="qa-suggestions">
              <button
                v-for="sug in quickSuggestions"
                :key="sug.id"
                class="qa-chip"
                @click="quickStart(sug.id)"
              >{{ sug.icon }} {{ sug.name }}</button>
            </div>
          </div>
        </div>
      </aside>

      <!-- ▸ 中间：算法动画区域 -->
      <main class="lab-center">
        <div class="canvas-panel" ref="canvasPanel">
          <!-- 空状态 -->
          <div v-if="!hasContent" class="empty-state">
            <div class="empty-icon">
              <svg width="56" height="56" viewBox="0 0 64 64" fill="none">
                <circle cx="32" cy="32" r="28" stroke="var(--color-primary)" stroke-width="1.2" stroke-dasharray="6 3" opacity="0.2"/>
                <path d="M22 44V20l10 7 10-7v24" stroke="var(--color-primary)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" opacity="0.4"/>
                <circle cx="32" cy="32" r="3" fill="var(--color-primary)" opacity="0.3"/>
              </svg>
            </div>
            <h2 class="empty-title">开始你的算法探索</h2>
            <p class="empty-desc">从左侧选择一个预设算法，AI 将逐步讲解每一步的执行过程</p>
            <div class="empty-suggestions">
              <button
                v-for="q in quickQuestions"
                :key="q.id"
                class="empty-chip"
                @click="quickStart(q.id)"
              >{{ q.icon }} {{ q.name }}</button>
            </div>
          </div>

          <!-- 动画舞台 -->
          <div v-else class="animation-stage" ref="animStage">
            <!-- 排序/查找：柱状图 -->
            <div v-if="animType === 'sorting' || animType === 'search'" class="sorting-bars" ref="sortingBars">
              <div
                v-for="(item, idx) in animBars"
                :key="idx"
                class="sort-bar"
                :class="{
                  comparing: item.state === 'comparing',
                  swapping: item.state === 'swapping',
                  sorted: item.state === 'sorted',
                  pivot: item.state === 'pivot'
                }"
                :style="{ height: item.height + '%', backgroundColor: animBarColors[idx % animBarColors.length] }"
              >
                <span class="bar-value" v-if="animBars.length <= 16">{{ item.value }}</span>
                <span class="bar-index">{{ idx }}</span>
              </div>
            </div>

            <!-- 树结构 SVG -->
            <svg v-if="animType === 'tree'" class="tree-svg" viewBox="0 0 800 380" ref="treeSvg">
              <line
                v-for="(edge, ei) in treeEdges"
                :key="'e'+ei"
                :x1="edge.x1" :y1="edge.y1"
                :x2="edge.x2" :y2="edge.y2"
                :stroke="edge.color || '#94a3b8'"
                stroke-width="2"
              />
              <g v-for="(node, ni) in treeNodes" :key="'n'+ni" :transform="`translate(${node.x},${node.y})`">
                <circle :r="20" :fill="treeNodeColor(node)" :stroke="treeNodeStroke(node)" stroke-width="2.5"/>
                <text text-anchor="middle" dy="5"
                  :fill="node.state === 'current' || node.state === 'unbalanced' || node.state === 'pivot' ? '#fff' : '#1e293b'"
                  font-size="13" font-weight="600"
                >{{ node.value }}</text>
              </g>
            </svg>

            <!-- 图结构 SVG -->
            <svg v-if="animType === 'graph'" class="graph-svg" viewBox="0 0 400 380" ref="graphSvg">
              <line
                v-for="(edge, ei) in graphEdges"
                :key="'ge'+ei"
                :x1="edge.x1" :y1="edge.y1"
                :x2="edge.x2" :y2="edge.y2"
                stroke="#cbd5e1" stroke-width="1.5" stroke-dasharray="4 2"
              />
              <g v-for="(node, ni) in graphNodes" :key="'gn'+ni" :transform="`translate(${node.x},${node.y})`">
                <circle :r="22" :fill="graphNodeColor(node)" :stroke="graphNodeStroke(node)" stroke-width="2.5"/>
                <text text-anchor="middle" dy="5"
                  :fill="graphNodeTextColor(node)"
                  font-size="14" font-weight="700"
                >{{ node.label || node.id }}</text>
              </g>
            </svg>

            <!-- 链表 -->
            <div v-if="animType === 'linked_list'" class="linked-list-stage" ref="linkedList">
              <template v-for="(node, ni) in listNodes" :key="'ln'+ni">
                <div class="ll-node" :class="listNodeClass(node)" :style="{ left: node.x + 'px', top: node.y + 'px' }">
                  <span class="ll-val">{{ node.value }}</span>
                </div>
                <svg v-if="node.next && ni < listNodes.length - 1 && node.x < listNodes[ni+1]?.x"
                  class="ll-arrow" :style="{ left: (node.x + 44) + 'px', top: (node.y + 17) + 'px' }">
                  <line x1="0" y1="0" :x2="listNodes[ni+1].x - node.x - 44" y2="0"
                    stroke="#94a3b8" stroke-width="2" marker-end="url(#arrowhead)"/>
                </svg>
              </template>
              <div v-for="(ptr, pi) in listPointers" :key="'lp'+pi"
                class="ll-pointer"
                :style="{ left: (ptr.pos >= 0 ? listNodes[ptr.pos]?.x + 10 : 20) + 'px', top: '20px' }"
              >{{ ptr.name }}</div>
              <svg width="0" height="0"><defs><marker id="arrowhead" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#94a3b8"/></marker></defs></svg>
            </div>
          </div>
        </div>

        <!-- 播放控制栏 -->
        <div class="playback-bar">
          <button class="ctrl-btn" :disabled="!hasContent || currentStep <= 1" @click="stepBack" title="上一步">◀</button>
          <button class="ctrl-btn play-btn" @click="togglePlay" :disabled="!hasContent">
            {{ isPlaying ? '⏸' : '▶' }}
          </button>
          <button class="ctrl-btn" :disabled="!hasContent || currentStep >= totalSteps" @click="stepForward" title="下一步">▶</button>
          <button class="ctrl-btn" :disabled="!hasContent" @click="resetAnimation" title="重置">↺</button>
          <div class="speed-control">
            <span class="speed-label">速度</span>
            <input type="range" v-model.number="playSpeed" min="0.25" max="3" step="0.25" class="speed-slider" />
            <span class="speed-value">{{ playSpeed }}x</span>
          </div>
          <div class="step-indicator" v-if="hasContent">
            <span>{{ currentStep }} / {{ totalSteps }} 步</span>
          </div>
        </div>
      </main>

      <!-- ▸ 右侧：信息面板 + 代码 -->
      <aside class="lab-right" :class="{ collapsed: rightCollapsed }">
        <div v-if="!rightCollapsed" class="lab-right-inner">
          <!-- 数字人头像区 -->
          <div class="tutor-card">
            <div class="tutor-avatar-area">
              <div class="tutor-ring" :class="{ speaking: isPlaying }">
                <div class="tutor-face">
                  <span class="tutor-eyes">{{ isPlaying ? '● ●' : '◉ ◉' }}</span>
                  <span class="tutor-mouth">{{ isPlaying ? '○' : '─' }}</span>
                </div>
              </div>
            </div>
            <div class="tutor-info">
              <h4>StructQuest AI</h4>
              <p>你的算法私教</p>
            </div>
          </div>

          <!-- 进度卡片 -->
          <div class="info-card">
            <div class="card-head">📊 当前进度</div>
            <div class="card-body">
              <template v-if="hasContent">
                <div class="progress-step">
                  <span class="step-label">步骤</span>
                  <span class="step-value">{{ currentStep }}/{{ totalSteps }}</span>
                </div>
                <div class="progress-bar-wrap">
                  <div class="progress-bar-fill" :style="{ width: progressPercent + '%' }"></div>
                </div>
                <div class="progress-algo">
                  <span class="step-label">算法</span>
                  <span class="step-value algo-name">{{ currentAlgorithm }}</span>
                </div>
              </template>
              <div v-else class="card-empty">
                <p>选择一个预设算法开始学习</p>
              </div>
            </div>
          </div>

          <!-- AI 讲解气泡 -->
          <div class="narration-card" v-if="currentNarration">
            <div class="card-head">💬 AI 讲解</div>
            <div class="narration-text">{{ currentNarration }}</div>
          </div>

          <!-- 算法信息 -->
          <div class="info-card" v-if="hasContent">
            <div class="card-head">📋 算法信息</div>
            <div class="card-body">
              <div class="state-row">
                <span>来源</span>
                <span class="state-val">预设算法</span>
              </div>
              <div class="state-row" v-if="currentPreset?.complexity?.time">
                <span>时间复杂度</span>
                <span class="state-val complexity-val">{{ currentPreset.complexity.time }}</span>
              </div>
              <div class="state-row" v-if="currentPreset?.complexity?.space">
                <span>空间复杂度</span>
                <span class="state-val complexity-val">{{ currentPreset.complexity.space }}</span>
              </div>
            </div>
          </div>

          <!-- 代码面板 -->
          <div class="code-panel">
            <div class="panel-head">
              <span class="panel-title">📝 代码</span>
              <span class="code-lang">JavaScript</span>
            </div>
            <div class="panel-body code-body">
              <div v-if="codeLines.length === 0" class="panel-empty">
                <div class="empty-code-icon">
                  <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="var(--text-tertiary)" stroke-width="1.5" stroke-linecap="round">
                    <polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>
                  </svg>
                </div>
                <p>选择算法后显示代码</p>
              </div>
              <div v-else class="code-lines">
                <div
                  v-for="(line, idx) in codeLines"
                  :key="idx"
                  class="code-line"
                  :class="{ highlighted: idx === highlightLine }"
                >
                  <span class="line-num">{{ idx + 1 }}</span>
                  <span class="line-text" v-html="line"></span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { ALGO_PRESETS, CATEGORY_GROUPS } from './algorithms.js'

// ============================================================
// 状态
// ============================================================
const leftCollapsed = ref(false)
const rightCollapsed = ref(false)
const userInput = ref('')

// 预设
const selectedPresetId = ref(null)
const currentPreset = ref(null)

// 动画
const hasContent = ref(false)
const animType = ref('sorting')
const animBars = ref([])
const animBarColors = ref([
  '#d97982', '#ec4899', '#f43f5e', '#f97316', '#eab308',
  '#22c55e', '#14b8a6', '#06b6d4', '#b94b5a', '#c84c5a'
])
const currentStep = ref(0)
const totalSteps = ref(0)
const isPlaying = ref(false)
const playSpeed = ref(1)
const currentNarration = ref('')
const currentAlgorithm = ref('')

// 树动画
const treeNodes = ref([])
const treeEdges = ref([])

// 图动画
const graphNodes = ref([])
const graphEdges = ref([])

// 链表动画
const listNodes = ref([])
const listPointers = ref([])

// 代码面板
const codeLines = ref([])
const highlightLine = ref(-1)
const codeExplanation = ref('')

// 动画引擎
let animGenerator = null
let animTimer = null

// AI 生成模式
const isLoading = ref(false)
const loadingMessage = ref('')
const animSource = ref('')
let algoWs = null
let aiComplexity = ref({ time: '', space: '' })

// Refs
const inputRef = ref(null)

// ============================================================
// 算法分组
// ============================================================
const algoGroups = computed(() => {
  return CATEGORY_GROUPS.map(group => ({
    ...group,
    items: ALGO_PRESETS.filter(p => p.category === group.key)
  })).filter(g => g.items.length > 0)
})

// 快捷入口
const quickQuestions = computed(() => ALGO_PRESETS.slice(0, 4).map(p => ({ id: p.id, icon: p.icon, name: p.name })))
const quickSuggestions = computed(() => ALGO_PRESETS.slice(4, 10).map(p => ({ id: p.id, icon: p.icon, name: p.name })))

// ============================================================
// 计算属性
// ============================================================
const progressPercent = computed(() => {
  if (totalSteps.value === 0) return 0
  return Math.round((currentStep.value / totalSteps.value) * 100)
})

// ============================================================
// 树/图/链表渲染辅助
// ============================================================
function treeNodeColor(node) {
  const map = {
    'current': '#c84c5a', 'unbalanced': '#ef4444', 'pivot': '#f59e0b',
    'inserting': '#22c55e', 'sorted': '#22c55e'
  }
  return map[node.state] || '#f8fafc'
}

function treeNodeStroke(node) {
  if (node.state === 'sorted') return '#16a34a'
  if (node.state === 'current' || node.state === 'unbalanced') return '#aa3948'
  if (node.state === 'pivot') return '#d97706'
  if (node.state === 'inserting') return '#16a34a'
  return '#cbd5e1'
}

function graphNodeColor(node) {
  const map = { 'current': '#c84c5a', 'visited': '#e7b9bd', 'queue': '#fbbf24', 'visiting': '#d86b76' }
  return map[node.state] || '#f1f5f9'
}

function graphNodeStroke(node) {
  const map = { 'current': '#aa3948', 'visited': '#c84c5a', 'queue': '#d97706', 'visiting': '#c84c5a' }
  return map[node.state] || '#cbd5e1'
}

function graphNodeTextColor(node) {
  return node.state === 'current' ? '#fff' : '#1e293b'
}

function listNodeClass(node) {
  const map = {
    'current': 'll-current', 'next': 'll-next', 'inserting': 'll-inserting',
    'deleting': 'll-deleting', 'done': 'll-done', 'visited': 'll-visited',
    'reversed': 'll-reversed'
  }
  return map[node.state] || ''
}

// ============================================================
// 方法
// ============================================================

function selectPreset(preset) {
  stopAndClear()
  selectedPresetId.value = preset.id
  currentPreset.value = preset
  currentAlgorithm.value = preset.name
  animSource.value = 'preset'

  codeLines.value = (preset.code || '').split('\n').map(line => escapeHtml(line.trimEnd()))
  highlightLine.value = -1
  codeExplanation.value = ''

  let steps = []
  if (preset.generator) {
    steps = preset.generator(typeof preset.defaultData === 'object' && !Array.isArray(preset.defaultData)
      ? preset.defaultData
      : (preset.defaultData || [5, 3, 8, 2, 1, 4]))
  }

  if (steps.length === 0) return

  initAnimType(steps[0], preset)
  hasContent.value = true
  totalSteps.value = steps.length
  animGenerator = { steps, index: 0 }

  isPlaying.value = true
  nextTick(() => runStep())
}

function initAnimType(firstStep, preset) {
  currentStep.value = 0
  currentNarration.value = ''
  highlightLine.value = -1
  codeExplanation.value = ''

  if (firstStep.type === 'graph') {
    animType.value = 'graph'
    animBars.value = []
  } else if (firstStep.type === 'tree') {
    animType.value = 'tree'
    animBars.value = []
  } else if (firstStep.type === 'linked_list') {
    animType.value = 'linked_list'
    animBars.value = []
  } else {
    if (preset?.category === 'search') animType.value = 'search'
    else animType.value = 'sorting'
    animBars.value = firstStep.bars || []
  }
}

function stopAndClear() {
  isPlaying.value = false
  clearTimeout(animTimer)
  animGenerator = null
  currentStep.value = 0
  currentNarration.value = ''
  highlightLine.value = -1
  codeExplanation.value = ''
  animBars.value = []
  graphNodes.value = []
  graphEdges.value = []
  treeNodes.value = []
  treeEdges.value = []
  listNodes.value = []
  listPointers.value = []
}

function runStep() {
  if (!animGenerator || animGenerator.index >= animGenerator.steps.length) {
    isPlaying.value = false
    return
  }

  const step = animGenerator.steps[animGenerator.index]
  currentStep.value = step.step
  currentNarration.value = step.narration || ''

  if (step.type === 'graph') {
    renderGraphStep(step)
  } else if (step.type === 'tree') {
    renderTreeStep(step)
  } else if (step.type === 'linked_list') {
    renderListStep(step)
  } else {
    animBars.value = step.bars || []
  }

  if (step.codeLine !== undefined && step.codeLine >= 0) {
    highlightLine.value = step.codeLine
    codeExplanation.value = step.codeExplanation || ''
  }

  animGenerator.index++

  if (isPlaying.value && animGenerator.index < animGenerator.steps.length) {
    const delay = Math.max(60, Math.floor(1000 / playSpeed.value))
    animTimer = setTimeout(runStep, delay)
  } else if (animGenerator.index >= animGenerator.steps.length) {
    isPlaying.value = false
  }
}

function renderGraphStep(step) {
  if (!step.graphState) return
  graphNodes.value = step.graphState.nodes || []
  const edges = []
  const adjList = step.graphState.adjList || {}
  const drawnEdges = new Set()
  for (const [from, neighbors] of Object.entries(adjList)) {
    for (const to of neighbors) {
      const key = [from, to].sort().join('-')
      if (drawnEdges.has(key)) continue
      drawnEdges.add(key)
      const fn = graphNodes.value.find(n => n.id === from)
      const tn = graphNodes.value.find(n => n.id === to)
      if (fn && tn) {
        edges.push({ x1: fn.x, y1: fn.y, x2: tn.x, y2: tn.y })
      }
    }
  }
  graphEdges.value = edges
}

function renderTreeStep(step) {
  if (!step.treeState) return
  treeNodes.value = step.treeState.nodes || []
  const edges = step.treeState.edges || []
  treeEdges.value = edges.map(e => {
    const fn = treeNodes.value.find(n => n.value === e.from)
    const tn = treeNodes.value.find(n => n.value === e.to)
    if (!fn || !tn) return { x1: 0, y1: 0, x2: 0, y2: 0 }
    return {
      x1: fn.x, y1: fn.y + 20,
      x2: tn.x, y2: tn.y - 20,
      color: e.side === 'left' ? '#d97982' : e.side === 'right' ? '#f59e0b' : '#94a3b8'
    }
  })
}

function renderListStep(step) {
  if (!step.listState) return
  listNodes.value = step.listState.nodes || []
  listPointers.value = step.listState.pointers || []
}

function togglePlay() {
  if (!hasContent.value) return
  isPlaying.value = !isPlaying.value
  if (isPlaying.value) {
    runStep()
  } else {
    clearTimeout(animTimer)
  }
}

function stepBack() {
  if (!animGenerator || animGenerator.index <= 0) return
  isPlaying.value = false
  clearTimeout(animTimer)
  animGenerator.index = Math.max(0, animGenerator.index - 2)
  const step = animGenerator.steps[Math.max(0, animGenerator.index)]
  if (step) {
    currentStep.value = step.step
    currentNarration.value = step.narration || ''
    if (step.type === 'graph') renderGraphStep(step)
    else if (step.type === 'tree') renderTreeStep(step)
    else if (step.type === 'linked_list') renderListStep(step)
    else animBars.value = step.bars || []
    if (step.codeLine !== undefined && step.codeLine >= 0) {
      highlightLine.value = step.codeLine
      codeExplanation.value = step.codeExplanation || ''
    }
  }
  animGenerator.index++
}

function stepForward() {
  if (!animGenerator || animGenerator.index >= animGenerator.steps.length) return
  isPlaying.value = false
  clearTimeout(animTimer)
  runStep()
}

function resetAnimation() {
  isPlaying.value = false
  clearTimeout(animTimer)
  currentStep.value = 0
  currentNarration.value = ''
  highlightLine.value = -1
  codeExplanation.value = ''
  animBars.value = []
  graphNodes.value = []
  graphEdges.value = []
  treeNodes.value = []
  treeEdges.value = []
  listNodes.value = []
  listPointers.value = []

  if (currentPreset.value) {
    const p = currentPreset.value
    let steps = []
    if (p.generator) {
      steps = p.generator(typeof p.defaultData === 'object' && !Array.isArray(p.defaultData)
        ? p.defaultData : (p.defaultData || [5, 3, 8, 2, 1, 4]))
    }
    animGenerator = { steps, index: 0 }
    totalSteps.value = steps.length
    isPlaying.value = true
    nextTick(() => runStep())
  }
}

function quickStart(algoId) {
  const preset = ALGO_PRESETS.find(p => p.id === algoId)
  if (preset) selectPreset(preset)
}

// ============================================================
//  AI 生成模式 — 本地匹配 + WebSocket 智能体
// ============================================================

const LOCAL_KEYWORDS = {
  "bubble_sort":    ["冒泡", "bubble", "气泡"],
  "quick_sort":     ["快排", "快速排序", "quick", "partition"],
  "merge_sort":     ["归并", "merge"],
  "insertion_sort": ["插入排序", "insertion"],
  "selection_sort": ["选择排序", "selection"],
  "heap_sort":      ["堆排序", "heap"],
  "binary_search":  ["二分", "binary search", "折半"],
  "bst_insert":     ["BST", "二叉搜索树插入", "二叉查找树"],
  "avl_rotate_left":  ["AVL左旋", "左单旋", "LL旋转"],
  "avl_rotate_right": ["AVL右旋", "右单旋", "RR旋转"],
  "graph_bfs":      ["BFS", "广度优先"],
  "graph_dfs":      ["DFS", "深度优先"],
  "linked_list_reverse": ["链表反转", "反转链表"],
  "linked_list_insert":  ["链表插入"],
  "linked_list_delete":  ["链表删除"],
}

function localMatch(text) {
  const t = text.toLowerCase()
  for (const [algoId, keywords] of Object.entries(LOCAL_KEYWORDS)) {
    for (const kw of keywords) {
      if (t.includes(kw.toLowerCase())) return algoId
    }
  }
  return null
}

function submitInput() {
  const prompt = userInput.value.trim()
  if (!prompt || isLoading.value) return

  const matched = localMatch(prompt)
  if (matched) {
    const preset = ALGO_PRESETS.find(p => p.id === matched)
    if (preset) {
      selectPreset(preset)
      userInput.value = ''
      return
    }
  }

  startAIGeneration(prompt)
}

function startAIGeneration(prompt) {
  stopAndClear()
  isLoading.value = true
  loadingMessage.value = '正在分析你的请求...'
  animSource.value = ''
  selectedPresetId.value = null
  currentPreset.value = null
  hasContent.value = false

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  const wsUrl = import.meta.env.DEV
    ? `${protocol}//${host}/ws/algo-lab`
    : `${protocol}//${host}/ws/algo-lab`

  if (algoWs) {
    try { algoWs.close() } catch (_) {}
  }

  algoWs = new WebSocket(wsUrl)
  let aiSteps = []
  let aiMeta = null

  algoWs.onopen = () => {
    algoWs.send(JSON.stringify({
      type: 'generate',
      prompt: prompt,
      user_level: 'beginner'
    }))
  }

  algoWs.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)

      switch (data.type) {
        case 'matching':
          loadingMessage.value = data.message
          break

        case 'matched_preset':
          loadingMessage.value = data.message
          const p = ALGO_PRESETS.find(p => p.id === data.algo_id)
          if (p) {
            isLoading.value = false
            loadingMessage.value = ''
            selectPreset(p)
            userInput.value = ''
          }
          break

        case 'generating':
          loadingMessage.value = data.message
          break

        case 'ai_meta':
          aiMeta = data
          animSource.value = data.source || 'ai'
          currentAlgorithm.value = data.algorithm
          codeLines.value = (data.code || '// AI 生成的代码').split('\n').map(line => escapeHtml(line))
          if (data.complexity) {
            aiComplexity.value = data.complexity
          }
          totalSteps.value = data.total_steps
          hasContent.value = true
          const cat = data.category || 'sorting'
          if (cat === 'graph') animType.value = 'graph'
          else if (cat === 'tree') animType.value = 'tree'
          else if (cat === 'linked_list') animType.value = 'linked_list'
          else animType.value = 'sorting'
          aiSteps = []
          loadingMessage.value = `AI 生成中... 0/${data.total_steps} 步`
          break

        case 'ai_step':
          const step = data.step
          aiSteps.push(step)
          loadingMessage.value = `AI 生成中... ${data.index + 1}/${data.total} 步`
          break

        case 'ai_done':
          isLoading.value = false
          loadingMessage.value = ''
          userInput.value = ''

          console.log('[AlgoLab] AI 生成的 steps:', aiSteps.length, '条')
          if (aiSteps[0]) {
            console.log('[AlgoLab] 第一条 commands:', JSON.stringify(aiSteps[0].commands, null, 2))
          }

          if (aiSteps.length > 0) {
            if (animType.value === 'sorting' || animType.value === 'search') {
              aiSteps = convertAItoBars(aiSteps, data.total_steps)
            } else if (animType.value === 'tree') {
              aiSteps = convertAItoTree(aiSteps, data.total_steps)
            } else if (animType.value === 'graph') {
              aiSteps = convertAItoGraph(aiSteps, data.total_steps)
            } else if (animType.value === 'linked_list') {
              aiSteps = convertAItoList(aiSteps, data.total_steps)
            }
          }

          if (aiSteps.length === 0) {
            console.warn('[AlgoLab] AI 转换后无步骤')
            hasContent.value = false
            currentNarration.value = 'AI 生成的动画步骤无法渲染。请尝试更具体的描述。'
            break
          }

          if (animType.value === 'tree' || animType.value === 'graph' || animType.value === 'linked_list') {
            const hasStructure = aiSteps.some(s =>
              (s.treeState?.nodes?.length > 0) ||
              (s.graphState?.nodes?.length > 0) ||
              (s.listState?.nodes?.length > 0)
            )
            if (!hasStructure) {
              console.warn('[AlgoLab] AI 生成的动画缺少结构数据，尝试降级为柱状图渲染')
              animType.value = 'sorting'
              aiSteps = convertAItoBars(aiSteps.filter(s => s.commands?.length > 0).map(s => ({
                step: s.step, narration: s.narration,
                code_line: s.codeLine, code_explanation: s.codeExplanation,
                commands: s.commands
              })), data.total_steps)
            }
          }

          animGenerator = { steps: aiSteps, index: 0 }
          totalSteps.value = aiSteps.length
          hasContent.value = true
          isPlaying.value = true
          if (aiMeta?.summary) {
            currentNarration.value = ''
          }
          nextTick(() => runStep())

          try { algoWs.close() } catch (_) {}
          algoWs = null
          break

        case 'error':
          isLoading.value = false
          loadingMessage.value = ''
          hasContent.value = false
          alert('AI 生成失败：' + (data.message || '未知错误') + '\n请尝试从预设算法开始体验')
          break
      }
    } catch (e) {
      console.error('[AlgoLab] WS 消息解析失败:', e)
    }
  }

  algoWs.onerror = () => {
    isLoading.value = false
    loadingMessage.value = ''
    hasContent.value = false
    alert('连接 AI 服务失败，请确认后端已启动。\n您可以先从左侧的预设算法开始体验。')
  }

  algoWs.onclose = () => {
    if (isLoading.value) {
      isLoading.value = false
      loadingMessage.value = ''
    }
  }
}

// AI 转换函数
function convertAItoBars(steps, total) {
  const result = []
  let currentBars = null

  for (const step of steps) {
    const commands = step.commands || []

    const setDataCmd = commands.find(c => c.op === 'set_data')
    if (setDataCmd && setDataCmd.data) {
      currentBars = setDataCmd.data.map((v, i) => ({
        value: v, state: 'normal', color: animBarColors.value[i % animBarColors.value.length], height: 0
      }))
      const maxVal = Math.max(...currentBars.map(d => d.value), 1)
      currentBars.forEach(d => d.height = Math.round((d.value / maxVal) * 88) + 10)
      result.push({
        step: result.length + 1, narration: step.narration || '',
        bars: JSON.parse(JSON.stringify(currentBars)),
        codeLine: step.code_line, codeExplanation: step.code_explanation || ''
      })
      continue
    }

    if (!currentBars) {
      currentBars = [8, 3, 9].map((v, i) => ({
        value: v, state: 'normal', color: animBarColors.value[i % animBarColors.value.length], height: 30 + v * 10
      }))
    }

    currentBars.forEach(b => b.state = 'normal')

    for (const cmd of commands) {
      switch (cmd.op) {
        case 'swap':
          if (cmd.i >= 0 && cmd.j >= 0 && cmd.i < currentBars.length && cmd.j < currentBars.length) {
            currentBars[cmd.i].state = 'swapping'; currentBars[cmd.j].state = 'swapping'
            ;[currentBars[cmd.i], currentBars[cmd.j]] = [currentBars[cmd.j], currentBars[cmd.i]]
          }
          break
        case 'compare':
          if (cmd.i >= 0) currentBars[cmd.i] && (currentBars[cmd.i].state = 'comparing')
          if (cmd.j >= 0) currentBars[cmd.j] && (currentBars[cmd.j].state = 'comparing')
          break
        case 'mark':
          if (cmd.indices) {
            for (const idx of cmd.indices) { if (currentBars[idx]) currentBars[idx].state = 'comparing' }
          }
          break
        case 'pivot':
          if (cmd.index >= 0 && currentBars[cmd.index]) { currentBars[cmd.index].state = 'pivot' }
          break
        case 'partition':
          if (cmd.low >= 0 && currentBars[cmd.low]) currentBars[cmd.low].state = 'comparing'
          if (cmd.high >= 0 && currentBars[cmd.high]) currentBars[cmd.high].state = 'comparing'
          break
      }
    }

    result.push({
      step: result.length + 1, narration: step.narration || '',
      bars: JSON.parse(JSON.stringify(currentBars)),
      codeLine: step.code_line, codeExplanation: step.code_explanation || ''
    })
  }

  if (result.length > 0 && currentBars) {
    currentBars.forEach(b => b.state = 'normal')
    result.push({
      step: result.length + 1, narration: 'AI 生成的动画播放完毕 ✅',
      bars: JSON.parse(JSON.stringify(currentBars)), codeLine: -1, codeExplanation: 'AI 生成的算法演示结束'
    })
  }

  return result
}

function convertAItoTree(steps, total) {
  const result = []
  let treeState = { nodes: [], edges: [] }

  function autoLayout(nodes, edges) {
    if (nodes.length === 0) return { nodes: [], edges: [] }
    const children = {}
    edges.forEach(e => {
      if (!children[e.from]) children[e.from] = []
      children[e.from].push({ to: e.to, side: e.side })
    })
    const childSet = new Set(edges.map(e => e.to))
    const root = nodes.find(n => !childSet.has(n.value))
    if (!root) return { nodes, edges }
    const positions = new Map()
    const queue = [{ value: root.value, depth: 0 }]
    positions.set(root.value, { x: 400, y: 50 })
    let maxDepth = 0
    const nodesByLevel = { 0: [root.value] }
    while (queue.length > 0) {
      const { value, depth } = queue.shift()
      maxDepth = Math.max(maxDepth, depth)
      const kids = children[value] || []
      for (const k of kids) {
        if (!nodesByLevel[depth + 1]) nodesByLevel[depth + 1] = []
        nodesByLevel[depth + 1].push(k.to)
        queue.push({ value: k.to, depth: depth + 1 })
      }
    }
    for (let d = 0; d <= maxDepth; d++) {
      const levelNodes = nodesByLevel[d] || []
      const spacing = 800 / (levelNodes.length + 1)
      levelNodes.forEach((val, i) => { positions.set(val, { x: spacing * (i + 1), y: 50 + d * 110 }) })
    }
    return {
      nodes: nodes.map(n => ({ ...n, x: positions.get(n.value)?.x || 400, y: positions.get(n.value)?.y || 50 })),
      edges
    }
  }

  for (const step of steps) {
    const commands = step.commands || []
    for (const cmd of commands) {
      switch (cmd.op) {
        case 'tree_build': {
          let nodes = [], edges = []
          if (cmd.structure) {
            nodes = (cmd.structure.nodes || []).map(n => ({ value: n.value, x: 0, y: 0, state: n.state || 'normal' }))
            edges = cmd.structure.edges || []
          } else if (cmd.nodes) {
            nodes = cmd.nodes.map(n => ({ value: n.value || n, x: 0, y: 0, state: 'normal' }))
            edges = cmd.edges || []
          }
          const laid = autoLayout(nodes, edges)
          treeState = { nodes: laid.nodes, edges: laid.edges }
          break
        }
        case 'tree_insert': {
          if (cmd.value !== undefined) {
            const existingNodes = treeState.nodes.map(n => n.value)
            if (!existingNodes.includes(cmd.value)) {
              treeState.nodes.push({ value: cmd.value, x: 0, y: 0, state: 'inserting' })
              if (cmd.parent !== undefined) treeState.edges.push({ from: cmd.parent, to: cmd.value, side: cmd.side || 'left' })
              const laid = autoLayout(treeState.nodes, treeState.edges)
              treeState.nodes = laid.nodes
            }
          }
          break
        }
        case 'tree_mark': {
          if (cmd.node !== undefined) {
            const n = treeState.nodes.find(x => x.value === cmd.node)
            if (n) {
              treeState.nodes.forEach(x => { if (x.state !== 'inserting' && x.state !== 'sorted') x.state = 'normal' })
              n.state = cmd.color === '#ef4444' || cmd.color === '#dc2626' ? 'current' : cmd.color === '#f59e0b' ? 'pivot' : cmd.color === '#22c55e' || cmd.color === '#16a34a' ? 'sorted' : 'current'
            }
          }
          break
        }
        case 'tree_rotate_left':
        case 'tree_rotate_right': {
          if (cmd.node !== undefined) { const n = treeState.nodes.find(x => x.value === cmd.node); if (n) n.state = 'pivot' }
          break
        }
        case 'mark': {
          if (cmd.indices) {
            treeState.nodes.forEach(x => x.state = 'normal')
            cmd.indices.forEach(idx => { const n = treeState.nodes[idx]; if (n) n.state = 'current' })
          }
          break
        }
      }
    }
    treeState.nodes.forEach(n => { if (!n.state) n.state = 'normal' })
    result.push({
      step: result.length + 1, type: 'tree', narration: step.narration || '',
      treeState: JSON.parse(JSON.stringify(treeState)), codeLine: step.code_line, codeExplanation: step.code_explanation || ''
    })
  }
  if (result.length > 0) {
    result.push({
      step: result.length + 1, type: 'tree', narration: 'AI 生成的动画播放完毕 ✅',
      treeState: JSON.parse(JSON.stringify(treeState)), codeLine: -1, codeExplanation: 'AI 生成的算法演示结束'
    })
  }
  return result
}

function convertAItoGraph(steps, total) {
  const result = []
  let graphState = { nodes: [], adjList: {} }
  for (const step of steps) {
    const commands = step.commands || []
    for (const cmd of commands) {
      switch (cmd.op) {
        case 'graph_build': {
          if (cmd.nodes) {
            graphState.nodes = cmd.nodes.map(n => ({ id: n.id || n.value, label: n.label || String(n.id || n.value), x: n.x || 100 + Math.random() * 600, y: n.y || 50 + Math.random() * 300, state: 'normal' }))
            graphState.adjList = cmd.adjList || {}
          } else if (cmd.adjList) {
            graphState.adjList = cmd.adjList
            graphState.nodes = Object.keys(cmd.adjList).map((id, i) => { const angle = (i / Object.keys(cmd.adjList).length) * Math.PI * 2; return { id, label: id, x: 200 + Math.cos(angle) * 120, y: 180 + Math.sin(angle) * 120, state: 'normal' } })
          }
          break
        }
        case 'graph_visit': {
          if (cmd.node !== undefined) { graphState.nodes.forEach(n => n.state = n.state === 'visited' ? 'visited' : 'normal'); const node = graphState.nodes.find(n => n.id == cmd.node || n.label == cmd.node); if (node) node.state = 'current' }
          break
        }
        case 'mark': {
          if (cmd.indices) { graphState.nodes.forEach(n => n.state = 'normal'); cmd.indices.forEach(idx => { const n = graphState.nodes[idx]; if (n) n.state = 'current' }) }
          break
        }
      }
    }
    result.push({ step: result.length + 1, type: 'graph', narration: step.narration || '', graphState: JSON.parse(JSON.stringify(graphState)), codeLine: step.code_line, codeExplanation: step.code_explanation || '' })
  }
  if (result.length > 0) { result.push({ step: result.length + 1, type: 'graph', narration: 'AI 生成的动画播放完毕 ✅', graphState: JSON.parse(JSON.stringify(graphState)), codeLine: -1, codeExplanation: 'AI 生成的算法演示结束' }) }
  return result
}

function convertAItoList(steps, total) {
  const result = []
  let listState = { nodes: [], pointers: [] }
  function layoutList(values) { const startX = 80; const gap = 110; return values.map((v, i) => ({ value: v, x: startX + i * gap, y: 100, state: 'normal', next: i < values.length - 1 })) }
  for (const step of steps) {
    const commands = step.commands || []
    for (const cmd of commands) {
      switch (cmd.op) {
        case 'list_build': { if (cmd.values) { listState.nodes = layoutList(cmd.values); listState.pointers = [] } break }
        case 'list_insert': { if (cmd.values) { listState.nodes = layoutList(cmd.values); if (cmd.position !== undefined && listState.nodes[cmd.position]) listState.nodes[cmd.position].state = 'inserting' } break }
        case 'list_delete': { if (cmd.values) { listState.nodes = layoutList(cmd.values); if (cmd.position !== undefined && listState.nodes[cmd.position]) listState.nodes[cmd.position].state = 'deleting' } break }
        case 'list_mark': { if (cmd.position !== undefined && listState.nodes[cmd.position]) { listState.nodes.forEach(n => n.state = 'normal'); listState.nodes[cmd.position].state = 'current' } break }
        case 'mark': { if (cmd.indices) { listState.nodes.forEach(n => n.state = 'normal'); cmd.indices.forEach(idx => { const n = listState.nodes[idx]; if (n) n.state = 'current' }) } break }
      }
    }
    result.push({ step: result.length + 1, type: 'linked_list', narration: step.narration || '', listState: JSON.parse(JSON.stringify(listState)), codeLine: step.code_line, codeExplanation: step.code_explanation || '' })
  }
  if (result.length > 0) { result.push({ step: result.length + 1, type: 'linked_list', narration: 'AI 生成的动画播放完毕 ✅', listState: JSON.parse(JSON.stringify(listState)), codeLine: -1, codeExplanation: 'AI 生成的算法演示结束' }) }
  return result
}

function escapeHtml(text) {
  if (!text) return ''
  let escaped = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  escaped = escaped
    .replace(/\b(function|const|let|var|if|else|for|while|return|new)\b/g, '<span class="kw">$1</span>')
    .replace(/\b([a-zA-Z_]\w*)(?=\s*\()/g, '<span class="fn">$1</span>')
    .replace(/(\/\/.+)$/g, '<span class="cm">$1</span>')
  return escaped
}

watch(playSpeed, () => {
  if (isPlaying.value) { clearTimeout(animTimer); runStep() }
})
</script>

<style lang="scss" scoped>
/* ============================================
   AI 算法实验室 - 左中右三栏布局
   ============================================ */

.ai-lab {
  height: calc(100vh - var(--topnav-height));
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg-page);
}

/* ── 顶部标题栏 ── */
.lab-header {
  flex-shrink: 0;
  padding: 14px 24px;
  border-bottom: 1px solid var(--border-light);
  background: var(--bg-color);
}
.lab-header-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.lab-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}
.lab-brand-icon {
  width: 38px; height: 38px;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #d97982, #c84c5a);
  border-radius: 9px; color: #fff; flex-shrink: 0;
}
.lab-title {
  font-size: 18px; font-weight: 800; color: var(--text-main);
  letter-spacing: -0.02em; margin: 0;
}
.lab-subtitle {
  font-size: 12px; color: var(--text-tertiary); margin: 2px 0 0;
}
.lab-mode-badge {
  display: flex; align-items: center; gap: 6px;
  font-size: 12px; font-weight: 600; color: var(--text-secondary);
  padding: 5px 12px; border-radius: 999px;
  background: var(--bg-secondary); border: 1px solid var(--border-light);
}
.mode-dot {
  width: 7px; height: 7px; border-radius: 50%; background: var(--color-success);
  &.ai { background: #d97982; animation: aiPulse 1.5s ease-in-out infinite; }
}
@keyframes aiPulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

.loading-badge {
  background: rgba(217,121,130, 0.08); border-color: rgba(217,121,130, 0.2); color: #d97982;
}
.loading-spinner {
  width: 12px; height: 12px; border: 2px solid rgba(217,121,130, 0.2);
  border-top-color: #d97982; border-radius: 50%; animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── 三栏主体 ── */
.lab-main {
  flex: 1; display: flex; min-height: 0; position: relative;
}

/* 折叠按钮 */
.collapse-btn {
  position: absolute; z-index: 10; top: 50%; transform: translateY(-50%);
  width: 22px; height: 44px; border: 1px solid var(--border-light);
  background: var(--bg-color); border-radius: 6px; cursor: pointer;
  font-size: 10px; color: var(--text-tertiary);
  display: flex; align-items: center; justify-content: center;
  transition: all var(--transition-fast);
  &:hover { color: var(--color-primary); border-color: var(--color-primary); }
}
.left-toggle { left: 268px; &.collapsed { left: 10px; } }
.right-toggle { right: 328px; &.collapsed { right: 10px; } }

/* ═══════ 左侧栏：算法选择 + 问答输入 ═══════ */
.lab-left {
  width: 280px; flex-shrink: 0;
  border-right: 1px solid var(--border-light);
  background: var(--bg-color); overflow: hidden;
  transition: width var(--transition-normal);
  &.collapsed { width: 0; }
}
.lab-left-inner {
  display: flex; flex-direction: column; height: 100%;
}

/* 算法选择器 */
.algo-section {
  flex: 1; overflow-y: auto; padding: 8px 12px 4px;
  &::-webkit-scrollbar { width: 3px; }
  &::-webkit-scrollbar-thumb { background: var(--border-light); border-radius: 3px; }
}
.algo-section-title {
  padding: 6px 4px 8px;
  font-size: 11px; font-weight: 700; color: var(--text-tertiary);
  letter-spacing: 0.04em;
}
.algo-group { margin-bottom: 6px; }
.group-label {
  display: flex; align-items: center; gap: 5px;
  padding: 4px; font-size: 10px; font-weight: 700;
  color: var(--text-tertiary); letter-spacing: 0.03em;
}
.group-dot {
  width: 5px; height: 5px; border-radius: 50%; flex-shrink: 0;
  &.dot-sorting { background: #d97982; }
  &.dot-search { background: #f59e0b; }
  &.dot-tree { background: #22c55e; }
  &.dot-graph { background: #06b6d4; }
  &.dot-linked_list { background: #8b5cf6; }
}
.group-count { margin-left: auto; font-size: 9px; color: var(--text-tertiary); opacity: 0.5; }
.group-chips { display: flex; flex-direction: column; gap: 2px; }
.algo-chip {
  display: flex; align-items: center; gap: 7px;
  width: 100%; padding: 6px 8px; border-radius: 7px;
  border: 1px solid transparent; background: transparent;
  cursor: pointer; text-align: left; transition: all 0.15s ease;

  &:hover { background: var(--bg-secondary); border-color: var(--border-light); }
  &.active {
    background: linear-gradient(135deg, rgba(217,121,130, 0.08), rgba(200,76,90, 0.04));
    border-color: rgba(200,76,90, 0.18);
  }
}
.chip-icon { font-size: 14px; flex-shrink: 0; width: 20px; text-align: center; }
.chip-name { font-size: 12px; font-weight: 600; color: var(--text-main); flex: 1; }
.algo-chip.active .chip-name { color: var(--color-primary); }
.chip-diff {
  font-size: 9px; padding: 1px 5px; border-radius: 999px;
  background: rgba(200,76,90, 0.06); color: var(--color-primary); font-weight: 600;
}
.algo-chip.active .chip-diff { background: rgba(200,76,90, 0.12); }

/* 问答输入区 */
.qa-section {
  flex-shrink: 0; padding: 10px 12px; border-top: 1px solid var(--border-light);
  background: var(--bg-color);
}
.qa-input-row { display: flex; gap: 6px; align-items: center; }
.qa-input {
  flex: 1; height: 34px; padding: 0 10px; border-radius: 8px;
  border: 1px solid var(--border-light); background: var(--bg-secondary);
  font-size: 12px; color: var(--text-main); outline: none;
  transition: border 0.15s ease;
  &::placeholder { color: var(--text-tertiary); font-size: 11px; }
  &:focus { border-color: var(--color-primary); }
  &:disabled { opacity: 0.5; cursor: not-allowed; }
}
.qa-send-btn {
  width: 34px; height: 34px; border-radius: 8px; border: none;
  background: linear-gradient(135deg, #d97982, #c84c5a); color: #fff;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: all 0.15s ease; flex-shrink: 0;
  &:hover:not(:disabled) { box-shadow: 0 4px 14px rgba(200,76,90, 0.35); }
  &:disabled { opacity: 0.4; cursor: not-allowed; }
}
.qa-suggestions { display: flex; gap: 4px; margin-top: 6px; flex-wrap: wrap; }
.qa-chip {
  padding: 2px 7px; border-radius: 999px; border: 1px solid var(--border-light);
  background: var(--bg-color); cursor: pointer; font-size: 10px; font-weight: 600;
  color: var(--text-tertiary); transition: all 0.15s ease; white-space: nowrap;
  &:hover { border-color: var(--color-primary); color: var(--color-primary); background: rgba(200,76,90, 0.04); }
}

/* ═══════ 中间：动画区域 ═══════ */
.lab-center {
  flex: 1; display: flex; flex-direction: column; min-width: 0; background: var(--bg-page);
}
.canvas-panel {
  flex: 1; min-height: 0; position: relative; overflow: hidden; padding: 20px;
}

/* 空状态 */
.empty-state {
  position: absolute; inset: 0; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 10px;
}
.empty-icon { opacity: 0.45; margin-bottom: 4px; }
.empty-title { font-size: 20px; font-weight: 800; color: var(--text-main); margin: 0; }
.empty-desc { font-size: 13px; color: var(--text-secondary); margin: 0; text-align: center; max-width: 320px; }
.empty-suggestions { display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; margin-top: 8px; }
.empty-chip {
  padding: 7px 14px; border-radius: 10px; border: 1px solid var(--border-light);
  background: var(--bg-color); cursor: pointer; font-size: 13px; font-weight: 600;
  color: var(--text-secondary); transition: all 0.15s ease;
  &:hover { border-color: var(--color-primary); color: var(--color-primary); box-shadow: 0 2px 8px rgba(200,76,90, 0.1); }
}

/* 动画舞台 */
.animation-stage { width: 100%; height: 100%; display: flex; align-items: flex-end; justify-content: center; }

/* 排序柱状图 */
.sorting-bars {
  display: flex; align-items: flex-end; justify-content: center;
  gap: 3px; height: 100%; width: 100%; padding: 0 10px 40px;
}
.sort-bar {
  flex: 1; max-width: 58px; border-radius: 6px 6px 2px 2px;
  transition: height 0.25s ease, background-color 0.25s ease, transform 0.2s ease;
  position: relative; display: flex; flex-direction: column;
  align-items: center; justify-content: flex-start; padding-top: 6px; min-width: 24px;

  &.comparing { box-shadow: 0 0 0 3px rgba(200,76,90, 0.3); transform: translateY(-4px); }
  &.swapping { box-shadow: 0 0 0 3px rgba(245,158,11,0.5); transform: translateY(-6px); animation: swapBounce 0.3s ease; }
  &.sorted { opacity: 0.65; filter: grayscale(0.3); }
  &.pivot { box-shadow: 0 0 0 3px rgba(239,68,68,0.5); transform: translateY(-4px); animation: pivotGlow 1s ease-in-out infinite; }
}
@keyframes swapBounce { 0% { transform: translateY(-6px); } 50% { transform: translateY(-12px); } 100% { transform: translateY(-6px); } }
@keyframes pivotGlow { 0%,100% { box-shadow: 0 0 0 3px rgba(239,68,68,0.5); } 50% { box-shadow: 0 0 0 8px rgba(239,68,68,0.15); } }
.bar-value { font-size: 11px; font-weight: 700; color: rgba(255,255,255,0.9); text-shadow: 0 1px 2px rgba(0,0,0,0.2); }
.bar-index { position: absolute; bottom: -22px; font-size: 10px; color: var(--text-tertiary); }

/* 树/图 SVG */
.tree-svg, .graph-svg { width: 100%; height: 100%; }
line { transition: all 0.3s ease; }
circle { transition: all 0.3s ease; }

/* 链表 */
.linked-list-stage { position: relative; width: 100%; height: 360px; margin: 20px 0; }
.ll-node {
  position: absolute; width: 48px; height: 48px; border-radius: 10px;
  border: 2px solid #cbd5e1; background: #f8fafc;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.3s ease; transform: translate(-50%, -50%);
  &.ll-current { border-color: #c84c5a; background: #fbf0f1; }
  &.ll-next { border-color: #f59e0b; }
  &.ll-inserting { border-color: #22c55e; background: #f0fdf4; animation: nodePopIn 0.4s ease; }
  &.ll-deleting { border-color: #ef4444; background: #fef2f2; opacity: 0.5; }
  &.ll-done { border-color: #22c55e; }
  &.ll-visited { border-color: #e7b9bd; }
  &.ll-reversed { border-color: #d97982; background: #fbf2f3; }
}
@keyframes nodePopIn { 0% { transform: translate(-50%,-50%) scale(0.5); opacity: 0; } 100% { transform: translate(-50%,-50%) scale(1); opacity: 1; } }
.ll-val { font-size: 15px; font-weight: 700; color: #1e293b; }
.ll-arrow { position: absolute; width: 60px; height: 10px; overflow: visible; }
.ll-pointer { position: absolute; font-size: 11px; font-weight: 700; color: #c84c5a; background: rgba(200,76,90,0.08); padding: 2px 8px; border-radius: 999px; white-space: nowrap; pointer-events: none; }

/* 播放控制栏 */
.playback-bar {
  display: flex; align-items: center; justify-content: center; gap: 8px;
  padding: 10px 20px; border-top: 1px solid var(--border-light);
  background: var(--bg-color); flex-shrink: 0;
}
.ctrl-btn {
  width: 36px; height: 36px; border-radius: 10px;
  border: 1px solid var(--border-light); background: var(--bg-color);
  cursor: pointer; font-size: 15px; color: var(--text-secondary);
  display: flex; align-items: center; justify-content: center;
  transition: all 0.15s ease;
  &:hover:not(:disabled) { border-color: var(--color-primary); color: var(--color-primary); background: rgba(200,76,90,0.04); }
  &:disabled { opacity: 0.35; cursor: not-allowed; }
}
.play-btn {
  width: 42px; height: 42px; font-size: 18px;
  background: linear-gradient(135deg, #d97982, #c84c5a); color: #fff; border-color: transparent;
  &:hover:not(:disabled) { color: #fff; box-shadow: 0 4px 14px rgba(200,76,90,0.35); }
}
.speed-control { display: flex; align-items: center; gap: 6px; margin-left: 10px; }
.speed-label { font-size: 11px; color: var(--text-tertiary); font-weight: 600; }
.speed-slider { width: 70px; height: 4px; accent-color: var(--color-primary); cursor: pointer; }
.speed-value { font-size: 11px; font-weight: 700; color: var(--color-primary); min-width: 26px; }
.step-indicator {
  margin-left: 14px; font-size: 12px; font-weight: 600;
  color: var(--text-secondary); padding: 4px 12px; border-radius: 999px; background: var(--bg-secondary);
}

/* ═══════ 右侧栏：信息面板 + 代码 ═══════ */
.lab-right {
  width: 340px; flex-shrink: 0;
  border-left: 1px solid var(--border-light);
  background: var(--bg-color); overflow-y: auto;
  transition: width var(--transition-normal);
  &.collapsed { width: 0; overflow: hidden; }
}
.lab-right-inner {
  display: flex; flex-direction: column; gap: 12px; padding: 14px;
}

/* 数字人 */
.tutor-card {
  padding: 14px; border-radius: var(--radius-md);
  background: var(--bg-secondary); border: 1px solid var(--border-light);
  display: flex; align-items: center; gap: 12px;
}
.tutor-ring {
  width: 48px; height: 48px; border-radius: 50%;
  background: linear-gradient(135deg, #d97982, #c84c5a);
  display: flex; align-items: center; justify-content: center;
  transition: all var(--transition-normal);
  &.speaking { box-shadow: 0 0 0 4px rgba(200,76,90,0.2); animation: tutorPulse 2s ease-in-out infinite; }
}
@keyframes tutorPulse { 0%,100% { box-shadow: 0 0 0 4px rgba(200,76,90,0.2); } 50% { box-shadow: 0 0 0 10px rgba(200,76,90,0.05); } }
.tutor-face { color: #fff; font-size: 10px; text-align: center; line-height: 1.2; }
.tutor-eyes { display: block; letter-spacing: 3px; }
.tutor-mouth { display: block; font-size: 13px; }
.tutor-info {
  h4 { font-size: 13px; font-weight: 700; color: var(--text-main); margin: 0; }
  p { font-size: 11px; color: var(--text-tertiary); margin: 2px 0 0; }
}

/* 信息卡片 */
.info-card {
  border-radius: var(--radius-sm); background: var(--bg-secondary);
  border: 1px solid var(--border-light); overflow: hidden;
}
.card-head {
  padding: 8px 12px; font-size: 11px; font-weight: 700;
  color: var(--text-secondary); border-bottom: 1px solid var(--border-light);
}
.card-body { padding: 8px 12px; display: flex; flex-direction: column; gap: 6px; }
.card-empty { padding: 6px 0; p { font-size: 11px; color: var(--text-tertiary); margin: 0; text-align: center; } }
.progress-step { display: flex; justify-content: space-between; align-items: center; }
.step-label { font-size: 11px; color: var(--text-tertiary); }
.step-value { font-size: 12px; font-weight: 700; color: var(--text-main); }
.algo-name { color: var(--color-primary); }
.progress-bar-wrap { height: 4px; border-radius: 999px; background: var(--bg-tertiary); overflow: hidden; }
.progress-bar-fill { height: 100%; border-radius: 999px; background: linear-gradient(90deg, #d97982, #c84c5a); transition: width 0.3s ease; }
.progress-algo { display: flex; justify-content: space-between; }
.state-row { display: flex; justify-content: space-between; align-items: center; font-size: 11px; color: var(--text-tertiary); }
.state-val { font-weight: 600; color: var(--text-main); font-size: 11px; }
.complexity-val { font-family: var(--font-mono); color: var(--color-accent-teal); }

/* 讲解气泡 */
.narration-card {
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, rgba(217,121,130,0.06), rgba(200,76,90,0.03));
  border: 1px solid rgba(200,76,90,0.1); overflow: hidden;
}
.narration-text { padding: 10px 12px; font-size: 12px; line-height: 1.6; color: var(--text-main); }

/* 代码面板 */
.code-panel {
  border-radius: var(--radius-sm); background: var(--bg-secondary);
  border: 1px solid var(--border-light); overflow: hidden;
}
.panel-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 12px; border-bottom: 1px solid var(--border-light); background: var(--bg-tertiary);
}
.panel-title { font-size: 11px; font-weight: 700; color: var(--text-secondary); }
.code-lang {
  font-size: 10px; font-weight: 600; color: var(--text-tertiary);
  padding: 1px 6px; border-radius: 999px; background: var(--bg-secondary);
}
.panel-body { overflow-y: auto; max-height: 260px; }
.panel-empty { padding: 20px 12px; text-align: center; p { font-size: 11px; color: var(--text-tertiary); margin: 6px 0 0; } }
.empty-code-icon { display: flex; justify-content: center; opacity: 0.35; }
.code-lines { font-family: var(--font-mono); font-size: 11px; line-height: 1.7; }
.code-line {
  display: flex; align-items: baseline; padding: 1px 12px;
  transition: background 0.2s ease; position: relative;
  &.highlighted { background: rgba(200,76,90,0.08); border-left: 3px solid var(--color-primary); }
}
.line-num {
  width: 24px; text-align: right; color: var(--text-tertiary);
  font-size: 10px; margin-right: 10px; user-select: none; flex-shrink: 0;
}
.line-text {
  color: var(--text-main); white-space: pre; flex: 1;
  :deep(.kw) { color: #d946ef; font-weight: 600; }
  :deep(.fn) { color: #c84c5a; }
  :deep(.cm) { color: #94a3b8; font-style: italic; }
}

/* ── 响应式 ── */
@media (max-width: 1100px) {
  .lab-left { width: 240px; }
  .lab-right { width: 280px; }
  .left-toggle { left: 228px; &.collapsed { left: 10px; } }
  .right-toggle { right: 268px; &.collapsed { right: 10px; } }
}
@media (max-width: 860px) {
  .lab-left { width: 0; overflow: hidden; }
  .lab-right { width: 0; overflow: hidden; }
  .collapse-btn { display: none; }
}
</style>
