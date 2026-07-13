<template>
  <div class="map-view">
    <!-- 顶部标题栏 -->
    <div class="map-topbar">
      <div class="topbar-left">
        <h1 class="map-title">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:6px;">
            <path d="M1 6v12c0 2 1 3 3 3h16c2 0 3-1 3-3V6c0-2-1-3-3-3H4C2 4 1 5 1 6Z"/>
            <polyline points="1 10 12 4 23 10"/>
            <path d="M12 4v8"/>
          </svg>
          知识地图
        </h1>
        <p class="map-subtitle">数据结构与算法 · 推荐学习路径</p>
      </div>
      <div class="topbar-right">
        <div class="legend">
          <span class="legend-dot done"></span> <span :style="{ color: themeColor }">已完成</span>
          <span class="legend-dot learning-pulse"></span> 学习中
          <span class="legend-dot locked"></span> 未学习
        </div>

        <!-- 模式切换指示 -->
        <div v-if="isExamMode" class="mode-indicator" :style="{ background: themeColor + '12', color: themeColor }">
          {{ currentModeConfig.label }}
        </div>

      </div>
    </div>

    <!-- 地图画布 -->
    <div class="map-canvas">
      <!-- 加载状态 -->
      <div v-if="loading" class="map-loading">
        <div class="map-loading-spinner"></div>
        <p class="map-loading-text">正在加载知识图谱...</p>
      </div>
      
      <!-- 空状态（加载完成但无数据） -->
      <div v-else-if="!modeStages || modeStages.length === 0" class="map-empty">
        <svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="32" cy="32" r="28" stroke="#ddd" stroke-width="2" fill="none" stroke-dasharray="4,4"/>
          <path d="M24 28l8 8 8-8" stroke="#ccc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M32 36v-8" stroke="#ccc" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <h3>暂无知识图谱数据</h3>
        <p>知识图谱数据加载失败或尚未初始化，请初始化课程内容后重试。</p>
        <button class="map-empty-btn" @click="loadMapData">重新加载</button>
      </div>
      
      <!-- 地图内容 -->
      <template v-else>
      <div
        class="map-inner"
        :style="{ transform: 'scale(0.75)' }"
      >
        <!-- 背景装饰 -->
        <svg class="map-terrain" :width="mapW" :height="mapH" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <radialGradient id="tg1" cx="25%" cy="18%" r="45%">
              <stop offset="0%" stop-color="rgba(224,122,95,0.08)" />
              <stop offset="100%" stop-color="transparent" />
            </radialGradient>
            <radialGradient id="tg2" cx="72%" cy="48%" r="42%">
              <stop offset="0%" stop-color="rgba(139,92,246,0.06)" />
              <stop offset="100%" stop-color="transparent" />
            </radialGradient>
            <radialGradient id="tg3" cx="48%" cy="78%" r="38%">
              <stop offset="0%" stop-color="rgba(59,130,246,0.05)" />
              <stop offset="100%" stop-color="transparent" />
            </radialGradient>
          </defs>
          <ellipse cx="260" cy="190" rx="280" ry="180" fill="url(#tg1)" />
          <ellipse cx="740" cy="370" rx="340" ry="220" fill="url(#tg2)" />
          <ellipse cx="480" cy="650" rx="260" ry="200" fill="url(#tg3)" />
          <!-- 网格线 -->
          <g opacity="0.06">
            <line v-for="i in 11" :key="'v'+i" :x1="i*100" y1="0" :x2="i*100" y2="800" stroke="#888" stroke-width="0.5"/>
            <line v-for="i in 8" :key="'h'+i" x1="0" :y1="i*100" x2="1100" :y2="i*100" stroke="#888" stroke-width="0.5"/>
          </g>
        </svg>

        <!-- ═══ 路径连接层（已移除连线，保留占位） ═══ -->
        <svg class="map-roads" :width="mapW" :height="mapH" xmlns="http://www.w3.org/2000/svg"></svg>

        <!-- ═══ 分支连线（已移除） ═══ -->
        <svg class="map-branches" :width="mapW" :height="mapH" xmlns="http://www.w3.org/2000/svg"></svg>

        <!-- ═══ 大类城市节点 ═══ -->
        <div
          v-for="(stage, idx) in modeStages"
          :key="stage.id"
          class="map-city"
          :class="{
            'is-expanded': expandedStage === stage.id,
            'is-mastered': stage.status === 'mastered',
            'is-active': stage.status === 'learning',
            'is-locked': !stage.status && !stage.recommended,
            'is-highlight': highlightStage === stage.id,
            [`status-${getNodeStatusClass(stage)}`]: true
          }"
          :style="{ left: stage.x - stageRadius + 'px', top: stage.y - stageRadius + 'px', opacity: getNodeStatusClass(stage) === 'locked' ? 0.7 : 1 }"
          @click="selectStage(stage)"
          @mouseenter="highlightStage = stage.id"
          @mouseleave="highlightStage = null"
        >
          <div class="city-shadow"></div>
          <div class="city-outer-ring"></div>
          <div class="city-inner">
            <div class="city-icon">
              <svg width="26" height="26" viewBox="0 0 28 28" fill="none" v-html="stage.icon"></svg>
            </div>
            <span class="city-num">{{ stage.num }}</span>
            <span class="city-name">{{ stage.title }}</span>
            <span class="city-count">{{ stage.nodes.length }}个知识点</span>
            <!-- ★ 已完成大章节的状态标语 -->
            <span v-if="stage.status === 'mastered'" class="city-mastered-label">✅ 已完成</span>
            <span v-else-if="stage.status === 'learning'" class="city-mastered-label learning-label">📖 学习中</span>
          </div>
          <!-- 三种状态徽章 -->
          <div v-if="stage.status === 'mastered'" class="city-badge done">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3"><path d="M5 12l5 5L20 7"/></svg>
          </div>
          <div v-else-if="stage.status === 'learning'" class="city-badge learning-pulse">●</div>
          <div v-else class="city-badge locked">🔒</div>
          <!-- 考试模式频率标注 -->
          <div v-if="isExamMode && stage._examMeta" class="exam-freq-badge" :title="stage._examMeta.examCount">
            {{ stage._examMeta.frequency }}
          </div>
        </div>

        <!-- ═══ 展开面板 ═══ -->
        <transition name="panel-zoom">
          <div
            v-if="expandedStage"
            class="sub-panel"
            :style="panelStyle"
          >
            <div class="panel-header">
              <div class="panel-title-row">
                <span class="panel-stage-num">{{ expandedData.num }}</span>
                <h3 class="panel-title">{{ expandedData.title }}</h3>
              </div>
              <p class="panel-desc">{{ expandedData.description }}</p>
              <button class="panel-close" @click.stop="expandedStage = null">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M3 3L13 13M13 3L3 13" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                </svg>
                关闭
              </button>
            </div>
            <div class="panel-list">
              <div
                v-for="(node, idx) in expandedData.nodes"
                :key="node.id"
                class="sub-item"
                :class="[getNodeStatusClass(node), { 'has-exam': !!node._examMeta }]"
                @click.stop="onNodeClick(node)"
              >
                <div class="sub-item-index" :class="getNodeStatusClass(node)">{{ String(idx + 1).padStart(2, '0') }}</div>
                <div class="sub-item-body">
                  <div class="sub-item-head">
                    <span class="sub-item-name">{{ node.name }}</span>
                    <!-- 考试频率标签 -->
                    <span v-if="node._examMeta" class="exam-freq-tag">{{ node._examMeta.frequency }}</span>
                    <span v-if="node.recommended" class="sub-item-rec">AI推荐</span>
                    <span v-if="getNodeStatusClass(node) === 'done'" class="sub-item-status done">✅ 已完成</span>
                    <span v-else-if="getNodeStatusClass(node) === 'learning'" class="sub-item-status learning">📖 学习中 {{ node.progress }}%</span>
                    <span v-else class="sub-item-status locked">⬜ 未学习</span>
                  </div>
                  <p class="sub-item-desc">{{ node.desc }}</p>
                  <div v-if="node.status === 'learning' && node.progress" class="sub-item-bar">
                    <div class="sub-item-fill" :style="{ width: node.progress + '%' }"></div>
                  </div>
                </div>
                <div class="sub-item-arrow">
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M6 4L10 8L6 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </div>
              </div>
            </div>
          </div>
        </transition>

        <!-- 指南针 -->
        <div class="map-compass">
          <svg width="46" height="46" viewBox="0 0 46 46" fill="none">
            <circle cx="23" cy="23" r="21" stroke="rgba(0,0,0,0.08)" stroke-width="1.5" />
            <path d="M23 5L27 21L23 41L19 21Z" fill="rgba(0,0,0,0.06)" />
            <path d="M23 5L19 21H27Z" fill="#E07A5F" opacity="0.5" />
            <text x="23" y="14" text-anchor="middle" fill="rgba(0,0,0,0.2)" font-size="6" font-weight="700">N</text>
          </svg>
        </div>
      </div>
    </template>
    </div>

    <!-- 节点详情弹窗 -->
    <transition name="detail-slide">
      <div v-if="selectedNode" class="detail-bar" @click.self="selectedNode = null">
        <div class="detail-bar-inner">
          <button class="detail-close" @click="selectedNode = null">
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M4 4L14 14M14 4L4 14" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
            </svg>
          </button>
          <div class="detail-left">
            <span class="detail-tag" :class="selectedNode.status">{{ statusLabel(selectedNode.status) }}</span>
            <h2 class="detail-name">{{ selectedNode.name }}</h2>
            <p class="detail-desc">{{ selectedNode.fullDesc }}</p>
          </div>
          <div class="detail-mid">
            <h4>包含知识点</h4>
            <div class="detail-tags">
              <span v-for="p in selectedNode.points" :key="p" class="detail-chip">{{ p }}</span>
            </div>
          </div>
          <div class="detail-right">
            <p class="detail-tip">{{ selectedNode.aiSuggestion }}</p>
            <button
              class="detail-action"
              @click="startLearn(selectedNode)"
            >
              {{ selectedNode.status === 'completed' || selectedNode.status === 'mastered' ? '复习巩固' : selectedNode.status === 'learning' || selectedNode.status === 'in_progress' ? '继续学习' : '开始学习' }}
            </button>
            <button
              class="detail-action exam-action"
              @click="goToExam(selectedNode)"
            >
              📝 章节测试
            </button>
            <div v-if="selectedNode.status === 'completed' || selectedNode.status === 'mastered'" class="chapter-badge">✅ 已完结</div>
            <div v-else-if="selectedNode.status === 'learning' || selectedNode.status === 'in_progress'" class="chapter-badge learning-badge">📖 学习中</div>
            <div v-else class="chapter-badge available-badge">📚 未学习</div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onActivated, watch } from 'vue'
import { useRouter } from 'vue-router'
import knowledgeApi from '@/api/knowledge'
import { useSessionStore } from '../../store/session'
import { getModeKnowledgeMap, modeConfigs } from '../../data/knowledgeModes'

const router = useRouter()
const session = useSessionStore()

// ═══ 当前学习模式 ═══
const currentMode = computed(() => session.learningMode || 'beginner')
const currentModeConfig = computed(() => modeConfigs[currentMode.value] || modeConfigs.beginner)

// ═══ 地图尺寸 ═══
const mapW = 1100
const mapH = 800

// ═══ 数据 ═══
const stageRadius = 64
const stages = ref([])
const modeStages = ref([])   // 模式过滤后的stages
const themeColor = ref('#3b82f6')
const isExamMode = ref(false)
const loading = ref(true)

// 监听模式变化，重新过滤图谱
watch(currentMode, () => {
  applyModeFilter()
})

// ★ 调试：监控 modeStages 状态变化
watch(modeStages, (stages) => {
  if (stages && stages.length > 0) {
    console.log(`[Watch] 共 ${stages.length} 个大章节:`, stages.map(s => `${s.id}(${s.title})`))
    stages.forEach(s => {
      console.log(`  [Watch] stage ${s.id} "${s.title}": status="${s.status}", nodes:`, s.nodes.map(n => `${n.name}:${n.status}`))
    })
  }
}, { deep: true })

// 从后端加载知识图谱数据（原始全量数据）
async function loadMapData() {
  try {
    const res = await knowledgeApi.getMap()
    // 将后端数据映射到 stages 格式（保留原有位置坐标）
    stages.value = buildStagesFromBackend(res.categories || [], res.nodes || [])
  } catch (e) {
    console.warn('[Map] 后端加载失败，使用本地数据:', e)
    // fallback
    const { stages: fallbackStages } = await import('@/data/knowledgeMap.js')
    stages.value = fallbackStages
  } finally {
    loading.value = false
    applyModeFilter()
  }
}

// 根据当前模式过滤/重组知识图谱
function applyModeFilter() {
  const mode = currentMode.value
  const config = currentModeConfig.value

  if (!stages.value.length) return

  const mapResult = getModeKnowledgeMap(mode)
  
  // 如果后端返回了完整数据，使用后端数据 + 模式配置做筛选/覆盖
  if (mapResult.isExamMode) {
    // 考试模式：使用重组后的分类
    modeStages.value = mapResult.stages.map(s => ({
      ...s,
      nodes: s.nodes.map(n => enrichNodeWithModeInfo(n, mode, config)),
      _modeConfig: config,
    }))
  } else {
    // 基础/入门模式：基于原始stages做筛选
    const filtered = []
    
    for (const stage of stages.value) {
      const includedNodeIds = config.includedNodeIds
      let filteredNodes = stage.nodes
      
      // 如果有节点ID限制，只保留包含的节点
      if (includedNodeIds) {
        filteredNodes = stage.nodes.filter(n => includedNodeIds.includes(n.id))
      }
      
      // 应用描述覆盖
      filteredNodes = filteredNodes.map(n => enrichNodeWithModeInfo(n, mode, config))
      
      // 类别级别限制 - 兼容后端返回的 stage_xxx 和本地数据的 xxx 两种格式
      if (config.includedCategories) {
        const stageIdRaw = stage.id
        const stageIdClean = stage.id.replace(/^stage_/, '')
        const matches = config.includedCategories.includes(stageIdRaw) || config.includedCategories.includes(stageIdClean)
        if (!matches) continue
      }
      
      if (filteredNodes.length > 0 || !includedNodeIds) {
        // ★ 基于过滤后（当前模式可见）的节点重新计算大章节状态
        const finalNodes = includedNodeIds ? filteredNodes : filteredNodes.map(n => enrichNodeWithModeInfo(n, mode, config))
        let recalcStatus = 'locked'
        const allMastered = finalNodes.length > 0 && finalNodes.every(n => n.status === 'completed' || n.status === 'mastered')
        const someLearning = finalNodes.some(n => n.status === 'in_progress' || n.status === 'learning')
        if (allMastered) recalcStatus = 'mastered'
        else if (someLearning) recalcStatus = 'learning'
        else recalcStatus = null  // available/dormant

        filtered.push({
          ...stage,
          status: recalcStatus,  // ★ 覆盖：基于可见节点重新计算的真实状态
          nodes: finalNodes,
          recommended: finalNodes.some(n => (n.status === 'available' || n.status === null) && (n.difficulty ?? 99) <= 2),
          _modeConfig: config,
        })
      }
    }
    
    modeStages.value = filtered
  }

  themeColor.value = mapResult.themeColor
  isExamMode.value = mapResult.isExamMode
}

// 用模式信息丰富节点（描述覆盖、考试频率等）
function enrichNodeWithModeInfo(node, mode, config) {
  const enriched = { ...node }
  
  // 描述覆盖
  if (config.nodeDescOverrides?.[node.id]) {
    Object.assign(enriched, config.nodeDescOverrides[node.id])
  }
  
  // 考试元信息
  if (config.nodeExamMeta?.[node.id]) {
    enriched._examMeta = config.nodeExamMeta[node.id]
  }
  
  // 确保状态映射一致
  if (node.status === 'completed') { enriched.status = 'mastered' }
  if (node.status === 'in_progress') { enriched.status = 'learning' }
  if (node.status === 'available' && node.status !== 'locked') { enriched.status = null }  // 可学习但未开始
  
  return enriched
}

// 使用modeStages作为渲染源（兼容旧的computed引用）
// 在后续computed中，将 stages 引用替换为 modeStages

// 后端数据 → 地图 stages 格式
function buildStagesFromBackend(categories, allNodes) {
  // ★ 位置定义（与 knowledgeMap.js 对齐）
  const stagePositions = {
    'stage_ch01_intro':        { x: 180, y: 200, title: '绪论', icon: '' },
    'stage_ch02_linear_list':  { x: 440, y: 200, title: '线性表', icon: '' },
    'stage_ch03_stack_queue':  { x: 700, y: 200, title: '栈和队列', icon: '' },
    'stage_ch04_string_array': { x: 960, y: 200, title: '串数组广义表', icon: '' },
    'stage_ch05_tree':         { x: 180, y: 550, title: '树和二叉树', icon: '' },
    'stage_ch06_graph':        { x: 440, y: 550, title: '图', icon: '' },
    'stage_ch07_search':       { x: 700, y: 550, title: '查找', icon: '' },
    'stage_ch08_sort':         { x: 960, y: 550, title: '排序', icon: '' },
  }

  return categories.map(cat => {
    // ★ 从 category id 提取 key（格式：stage_xxx 或直接 xxx）
    const catKey = cat.id.replace(/^stage_/, '')
    let pos = stagePositions[cat.id] || stagePositions[`stage_${catKey}`]

    // 如果找不到精确位置，用 fallback
    if (!pos) {
      const fallbackMap = {
        ch01_intro: { x: 180, y: 200 },
        ch02_linear_list: { x: 440, y: 200 },
        ch03_stack_queue: { x: 700, y: 200 },
        ch04_string_array: { x: 960, y: 200 },
        ch05_tree: { x: 180, y: 550 },
        ch06_graph: { x: 440, y: 550 },
        ch07_search: { x: 700, y: 550 },
        ch08_sort: { x: 960, y: 550 },
      }
      pos = fallbackMap[catKey] || { x: 200, y: 400 }
    }

    // ★ 只用后端 category.nodes（已正确排除 parent_id=null 的顶级分类节点），
    // 避免把顶级节点（category==catKey 但 parent_id==null）也算进来导致大章节状态永远不变成 mastered
    const catNodes = (cat.nodes && cat.nodes.length > 0)
      ? cat.nodes
      : allNodes.filter(n => n.category === catKey)

    // 判断大类状态
    console.log(`[Debug] 大章节 ${cat.id}: catNodes=${catNodes.length}, statuses=`, catNodes.map(n => `${n.id}:${n.status}`))
    const allCompleted = catNodes.length > 0 && catNodes.every(n => n.status === 'completed')
    console.log(`[Debug] 大章节 ${cat.id}: allCompleted=${allCompleted}, catNodes.len=${catNodes.length}`)
    const hasLearning = catNodes.some(n => n.status === 'in_progress')
    const hasAvailable = catNodes.some(n => n.status === 'available')
    const hasRecommended = catNodes.some(n => n.status === 'available' && n.difficulty <= 2)

    let stageStatus = 'locked'
    if (allCompleted) stageStatus = 'mastered'
    else if (hasLearning) stageStatus = 'learning'
    else if (hasAvailable) stageStatus = null

    return {
      id: cat.id,
      num: `S${catNodes.length || '?'}`,
      title: pos.title || cat.title,
      icon: pos.icon || '',
      x: pos.x,
      y: pos.y,
      status: stageStatus,
      recommended: hasRecommended,
      nodes: catNodes.map((n, i) => ({
        id: n.id,
        name: n.title,
        desc: n.description || '',
        fullDesc: n.full_desc || n.description || '',
        points: n.points || [],
        aiSuggestion: n.ai_suggestion || '建议按顺序学习',
        status: n.status,
        progress: n.progress || 0,
        recommended: n.status === 'available' && n.difficulty <= 2,
      })),
      description: pos.title || cat.title,
    }
  })
}

// ═══ 生命周期 ═══
onMounted(() => {
  loadMapData()
})

// ★ keep-alive 激活时重新拉取数据
onActivated(() => {
  loadMapData()
})

// ═══ 节点状态颜色映射（三种状态） ═══
function getNodeStatusClass(node) {
  if (!node) return 'locked'
  
  // 已完成（通过章节测试点亮）
  if (node.status === 'mastered' || node.status === 'completed') return 'done'
  // 学习中（有进度 > 0）
  if (node.status === 'learning' || node.status === 'in_progress') return 'learning'
  // 未学习（暗）
  return 'locked'
}

// 节点的状态颜色
const nodeStatusColors = computed(() => ({
  done:      { border: 'rgba(34,197,94,0.45)', bg: 'linear-gradient(145deg, #f0fdf4, #dcfce7)', text: '#16a34a', icon: '#22c55e', shadow: 'rgba(34,197,94,0.18)' },
  learning: { border: 'rgba(224,122,95,0.45)', bg: 'linear-gradient(145deg, #fff7ed, #ffedd5)', text: '#E07A5F', icon: '#E07A5F', shadow: 'rgba(224,122,95,0.18)' },
  locked:   { border: 'rgba(150,150,150,0.5)', bg: '#f5f5f5', text: '#555', icon: '#888', shadow: 'transparent', opacity: 0.7 },
}))


// ═══ 展开/选中 ═══
const expandedStage = ref(null)
const highlightStage = ref(null)
const selectedNode = ref(null)

const expandedData = computed(() => {
  return modeStages.value.find(s => s.id === expandedStage.value) || null
})

const panelStyle = computed(() => {
  if (!expandedData.value) return {}
  const d = expandedData.value
  const panelW = 440
  const rightSpace = mapW - d.x - stageRadius - 30
  if (rightSpace >= panelW) {
    return {
      left: (d.x + stageRadius + 24) + 'px',
      top: Math.max(10, d.y - 180) + 'px',
    }
  }
  return {
    left: Math.max(10, d.x - panelW - stageRadius - 24) + 'px',
    top: Math.max(10, d.y - 180) + 'px',
  }
})

function selectStage(stage) {
  expandedStage.value = expandedStage.value === stage.id ? null : stage.id
}

function onNodeClick(node) {
  if (node.status === 'locked') return
  selectedNode.value = node
}

function statusLabel(s) {
  if (s === 'mastered' || s === 'completed') return '已完结'
  if (s === 'learning' || s === 'in_progress') return '学习中'
  return '可学习'
}

function goToExam(node) {
  selectedNode.value = null
  router.push(`/app/exam/${node.id}`)
}

async function startLearn(node) {
  selectedNode.value = null
  try {
    await knowledgeApi.startNode(node.id)
    // 刷新地图数据
    await loadMapData()
  } catch (e) {
    console.warn('[Map] 开始学习失败:', e)
  }
  router.push(`/app/learn/${node.id}`)
}

</script>

<style lang="scss" scoped>
.map-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #f7f5f2;
}

/* ═══ 顶部栏 ═══ */
.map-topbar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 28px;
  border-bottom: 1px solid rgba(0,0,0,0.08);
  z-index: 10;
  backdrop-filter: blur(12px);
  background: rgba(255,255,255,0.85);
}

.topbar-left {
  display: flex;
  align-items: baseline;
  gap: 12px;
  .map-title {
    font-size: 22px;
    font-weight: 700;
    margin: 0;
    color: #333;
    display: flex;
    align-items: center;
    letter-spacing: -0.5px;
  }
  .map-subtitle {
    font-size: 12px;
    color: var(--text-tertiary);
    margin: 0;
  }
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.legend {
  display: flex;
  align-items: center;
  gap: 14px;
  font-size: 12px;
  color: var(--text-tertiary);
}

.legend-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  display: inline-block;
  &.done { background: #22c55e; box-shadow: 0 0 6px rgba(34,197,94,0.4); }
  &.active { background: #E07A5F; }
  &.rec { background: linear-gradient(135deg, var(--color-primary-light), #a78bfa); }
  &.lock { background: #d4d4d4; }
  &.learning-pulse {
    background: #E07A5F;
    animation: legendPulse 2s infinite;
    box-shadow: 0 0 8px rgba(224,122,95,0.5);
  }
}
@keyframes legendPulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.4); opacity: 0.7; }
}

/* 模式指示器 */
.mode-indicator {
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 700;
}

/* ═══ 加载状态 ═══ */
.map-loading {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  z-index: 10;
  background: rgba(247,245,242,0.8);
}
.map-loading-spinner {
  width: 36px; height: 36px;
  border: 3px solid rgba(59,130,246,0.15);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: mapSpin 0.8s linear infinite;
}
@keyframes mapSpin {
  to { transform: rotate(360deg); }
}
.map-loading-text {
  font-size: 14px;
  color: var(--text-tertiary);
  margin: 0;
}

/* ═══ 空状态 ═══ */
.map-empty {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  z-index: 10;
  background: rgba(247,245,242,0.9);
}
.map-empty h3 {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-tertiary);
  margin: 0;
}
.map-empty p {
  font-size: 13px;
  color: #bbb;
  margin: 0;
  max-width: 320px;
  text-align: center;
  line-height: 1.5;
}
.map-empty-btn {
  margin-top: 8px;
  padding: 8px 24px;
  border: 1px solid rgba(59,130,246,0.3);
  border-radius: 8px;
  background: rgba(59,130,246,0.08);
  color: #3b82f6;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.map-empty-btn:hover {
  background: rgba(59,130,246,0.15);
  border-color: rgba(59,130,246,0.5);
}

/* ═══ 画布 ═══ */
.map-canvas {
  flex: 1;
  overflow: auto;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  background:
    radial-gradient(circle at 28% 18%, rgba(224,122,95,0.06) 0%, transparent 50%),
    radial-gradient(circle at 70% 48%, rgba(139,92,246,0.05) 0%, transparent 50%),
    #f7f5f2;
}

.map-inner {
  position: relative;
  width: 1100px;
  height: 800px;
}

/* ═══ 地形层 ═══ */
.map-terrain {
  position: absolute;
  top: 0; left: 0;
  pointer-events: none;
  z-index: 0;
}

/* ═══ 路径层 ═══ */
.map-roads {
  position: absolute;
  top: 0; left: 0;
  pointer-events: none;
  z-index: 1;
}

.map-branches {
  position: absolute;
  top: 0; left: 0;
  pointer-events: none;
  z-index: 1;
}

/* ═══ 城市节点 ═══ */
.map-city {
  position: absolute;
  z-index: 3;
  cursor: pointer;
  transition: filter 0.3s;

  &:hover { filter: drop-shadow(0 4px 16px rgba(0,0,0,0.12)); }
}

.city-shadow {
  position: absolute;
  inset: 4px;
  border-radius: 50%;
  background: transparent;
  box-shadow: 0 4px 24px rgba(0,0,0,0.12);
  pointer-events: none;
}

.city-outer-ring {
  position: absolute;
  inset: -8px;
  border-radius: 50%;
  border: 2px solid rgba(0,0,0,0.05);
  transition: all 0.3s;
  pointer-events: none;
}

.city-inner {
  width: 128px;
  height: 128px;
  border-radius: 50%;
  background: var(--bg-color);
  border: 1.5px solid rgba(0,0,0,0.08);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  transition: all 0.4s cubic-bezier(0.16,1,0.3,1);
  position: relative;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);

  &::after {
    content: '';
    position: absolute;
    width: 58%;
    height: 58%;
    border-radius: 50%;
    border: 1px dashed rgba(0,0,0,0.06);
    pointer-events: none;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
  }
}

.city-icon {
  color: var(--text-tertiary);
  transition: all 0.3s;
}

.city-num {
  font-size: 11px;
  font-weight: 700;
  color: #bbb;
  letter-spacing: 0.08em;
  margin-top: -2px;
}

.city-name {
  font-size: 13px;
  font-weight: 700;
  color: #555;
  letter-spacing: 0.03em;
}

.city-count {
  font-size: 10px;
  color: #bbb;
  margin-top: 1px;
}

/* ★ 已完成/学习中 状态标语 */
.city-mastered-label {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 8px;
  border-radius: 10px;
  margin-top: 2px;
  line-height: 1.4;
  &.learning-label {
    background: rgba(224,122,95,0.12);
    color: #E07A5F;
  }
}
.map-city.status-done .city-mastered-label {
  background: rgba(34,197,94,0.15);
  color: #15803d;
}

.city-badge {
  position: absolute;
  top: -2px;
  right: 8px;
  min-width: 22px;
  height: 22px;
  border-radius: 11px;
  font-size: 10px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 6px;

  &.done {
    background: linear-gradient(135deg, #22c55e, #16a34a);
    color: #fff;
    box-shadow: 0 2px 12px rgba(34,197,94,0.5);
    animation: badgePopIn 0.5s cubic-bezier(0.34,1.56,0.64,1);
    min-width: 24px;
    height: 24px;
    svg { width: 14px; height: 14px; }
  }
  &.active {
    background: #E07A5F; color: #fff;
    animation: pulse-dot 2s infinite;
  }
  &.learning-pulse {
    background: linear-gradient(135deg, #E07A5F, #f97316);
    color: #fff;
    box-shadow: 0 2px 8px rgba(224,122,95,0.45);
    animation: pulse-dot 2s infinite;
  }
  &.locked {
    background: #b0b0b0;
    color: var(--text-secondary);
    font-size: 9px;
  }
  &.rec { background: linear-gradient(135deg, var(--color-primary-light), #a78bfa); color: #fff; font-size: 9px; }
}

/* 考试频率标签 */
.exam-freq-badge {
  position: absolute;
  bottom: -6px;
  left: 50%;
  transform: translateX(-50%);
  padding: 1px 8px;
  border-radius: 8px;
  background: linear-gradient(135deg, #f97316, #fb923c);
  color: #fff;
  font-size: 9px;
  font-weight: 700;
  white-space: nowrap;
  z-index: 2;
}

@keyframes pulse-dot {
  0%, 100% { box-shadow: 0 0 0 0 rgba(224,122,95,0.5); }
  50% { box-shadow: 0 0 0 8px rgba(224,122,95,0); }
}

@keyframes badgePopIn {
  0%   { transform: scale(0); opacity: 0; }
  60%  { transform: scale(1.25); opacity: 1; }
  100% { transform: scale(1); opacity: 1; }
}

/* 已掌握 - 基础样式(优先级较低) */
.map-city.is-mastered {
  .city-outer-ring { border-color: rgba(34,197,94,0.4); box-shadow: 0 0 20px rgba(34,197,94,0.12); }
  .city-inner { border-color: rgba(34,197,94,0.35); background: linear-gradient(145deg, #f0fdf4, #fff); }
  .city-name { color: #16a34a; }
  .city-icon { color: #4ade80; }
}

/* 学习中 */
.map-city.is-active {
  .city-outer-ring { border-color: rgba(224,122,95,0.35); box-shadow: 0 0 20px rgba(224,122,95,0.1); }
  .city-inner { border-color: rgba(224,122,95,0.35); background: linear-gradient(145deg, #fff7ed, #fff); }
  .city-name { color: #E07A5F; }
  .city-icon { color: #E07A5F; }
}

/* ═══ 三种状态通用样式（优先级高于 is-mastered/is-active） ═══ */
.map-city.status-done {
  .city-shadow { 
    box-shadow: 0 6px 32px rgba(34,197,94,0.25), 0 2px 8px rgba(34,197,94,0.15) !important; 
  }
  .city-outer-ring {
    border-color: rgba(34,197,94,0.55) !important;
    border-width: 2.5px !important;
    box-shadow: 0 0 30px rgba(34,197,94,0.2), inset 0 0 25px rgba(34,197,94,0.06);
    animation: glowPulseDone 2.5s ease-in-out infinite;
  }
  .city-inner {
    border-color: rgba(34,197,94,0.5);
    border-width: 2px;
    background: linear-gradient(145deg, #ecfdf5, #d1fae5) !important;
    box-shadow: inset 0 3px 16px rgba(34,197,94,0.12), 0 0 0 2px rgba(34,197,94,0.08);
  }
  &::after { border-color: rgba(34,197,94,0.35); }
  .city-name { color: #15803d; font-weight: 800; text-shadow: 0 0 8px rgba(34,197,94,0.15); }
  .city-icon { color: #22c55e; filter: drop-shadow(0 0 6px rgba(34,197,94,0.5)); }
  .city-num { color: #22c55e; font-weight: 800; }
  .city-count { color: #4ade80; font-weight: 600; }
}
@keyframes glowPulseDone {
  0%, 100% { box-shadow: 0 0 24px rgba(34,197,94,0.15); }
  50% { box-shadow: 0 0 36px rgba(34,197,94,0.25); }
}

.map-city.status-learning {
  .city-outer-ring {
    border-color: rgba(224,122,95,0.45);
    box-shadow: 0 0 24px rgba(224,122,95,0.15);
  }
  .city-inner {
    border-color: rgba(224,122,95,0.4);
    background: linear-gradient(145deg, #fff7ed, #fffafcc);
  }
  &::after { border-color: rgba(224,122,95,0.25); }
  .city-name { color: #D2654B; }
  .city-icon { color: #E07A5F; }
}

.map-city.status-locked {
  .city-inner {
    background: #f0f0f0 !important;
    border-color: rgba(0,0,0,0.15) !important;
    box-shadow: none !important;
    filter: saturate(0.7) brightness(0.95);
  }
  .city-icon { color: var(--text-tertiary) !important; }
  .city-name { color: #555 !important; font-weight: 600; }
  .city-count { color: #aaa !important; }
}

/* hover */
.map-city:hover:not(.is-expanded) {
  .city-inner {
    transform: scale(1.08);
    border-color: rgba(0,0,0,0.15);
    box-shadow: 0 8px 30px rgba(0,0,0,0.1);
  }
  .city-outer-ring {
    border-color: rgba(0,0,0,0.1);
    transform: scale(1.15);
  }
  .city-name { color: #333; }
}

/* 高亮 */
.map-city.is-highlight:not(.is-expanded) {
  .city-outer-ring { border-color: rgba(139,92,246,0.35); transform: scale(1.12); box-shadow: 0 0 24px rgba(139,92,246,0.18); }
}

/* 展开态 */
.map-city.is-expanded {
  .city-outer-ring {
    border-color: rgba(139,92,246,0.5);
    box-shadow: 0 0 28px rgba(139,92,246,0.22);
    transform: scale(1.15);
  }
  .city-inner {
    border-color: rgba(139,92,246,0.45);
    background: linear-gradient(145deg, #f5f3ff, #fff);
    box-shadow: 0 0 40px rgba(139,92,246,0.18);
  }
  .city-name { color: var(--color-primary); }
  .city-icon { color: rgba(139,92,246,0.85); }
}

/* ★ 展开态 + 已完成：绿色优先于紫色（3级选择器 > 2级，自动胜出） */
.map-city.is-expanded.status-done {
  .city-outer-ring {
    border-color: rgba(34,197,94,0.55);
    box-shadow: 0 0 32px rgba(34,197,94,0.24);
    transform: scale(1.15);
    animation: glowPulseDone 2.5s ease-in-out infinite;
  }
  .city-inner {
    border-color: rgba(34,197,94,0.5);
    background: linear-gradient(145deg, #ecfdf5, #d1fae5) !important;
    box-shadow: 0 0 40px rgba(34,197,94,0.2), inset 0 3px 16px rgba(34,197,94,0.1);
  }
  .city-name { color: #15803d; font-weight: 800; }
  .city-icon { color: #22c55e; filter: drop-shadow(0 0 6px rgba(34,197,94,0.5)); }
  .city-count, .city-num { color: #22c55e; }
}

/* ═══ 展开面板 ═══ */
.sub-panel {
  position: absolute;
  z-index: 5;
  width: 440px;
  max-height: 520px;
  background: rgba(255,255,255,0.97);
  backdrop-filter: blur(24px);
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 20px;
  box-shadow: 0 16px 48px rgba(0,0,0,0.12);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  padding: 18px 20px 14px;
  border-bottom: 1px solid rgba(0,0,0,0.06);
  flex-shrink: 0;
  position: relative;
}

.panel-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.panel-stage-num {
  width: 28px; height: 28px;
  border-radius: 8px;
  background: rgba(139,92,246,0.12);
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.panel-title {
  font-size: 18px;
  font-weight: 700;
  color: #333;
  margin: 0;
}

.panel-desc {
  font-size: 12px;
  color: var(--text-tertiary);
  margin: 8px 0 0;
  line-height: 1.5;
  padding-right: 50px;
}

.panel-close {
  position: absolute;
  top: 14px; right: 14px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 10px;
  border: 1px solid rgba(0,0,0,0.1);
  border-radius: 8px;
  background: #f9f8f6;
  color: var(--text-tertiary);
  font-size: 11px;
  cursor: pointer;
  transition: all 0.15s;
  &:hover { background: #f0eee9; color: #555; border-color: rgba(0,0,0,0.18); }
}

.panel-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;

  &::-webkit-scrollbar { width: 4px; }
  &::-webkit-scrollbar-track { background: transparent; }
  &::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.1); border-radius: 2px; }
}

.sub-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 14px;
  background: #faf9f7;
  border: 1px solid rgba(0,0,0,0.05);
  cursor: pointer;
  transition: all 0.25s;

  &:hover {
    background: #f5f3f0;
    border-color: rgba(0,0,0,0.12);
    transform: translateX(4px);
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  }

  &.done {
    background: linear-gradient(135deg, #f0fdf4, #dcfce7);
    border-color: rgba(34,197,94,0.35);
    box-shadow: 0 2px 8px rgba(34,197,94,0.08);
    &:hover { background: #bbf7d0; border-color: rgba(34,197,94,0.5); }
  }

  &.learning {
    background: linear-gradient(135deg, #fff7ed, #ffedd5);
    border-color: rgba(224,122,95,0.3);
    &:hover { background: #ffecd5; border-color: rgba(224,122,95,0.45); }
  }

  &.locked {
    opacity: 0.75;
    cursor: not-allowed;
    background: #f2f2f2 !important;
    border-color: rgba(0,0,0,0.08) !important;
    &:hover { transform: none; background: #f2f2f2; }
    
    .sub-item-index { background: #ddd; color: #777; }
    .sub-item-name { color: var(--text-secondary) !important; }
    .sub-item-desc { color: #aaa !important; }
  }
}

.sub-item-index {
  width: 28px; height: 28px;
  border-radius: 8px;
  background: rgba(0,0,0,0.04);
  color: #bbb;
  font-size: 11px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  .done & { background: #dcfce7; color: #16a34a; }
  .learning & { background: var(--bg-color)7ed; color: #E07A5F; }
}

/* 考试频率标签 */
.exam-freq-tag {
  padding: 1px 7px;
  border-radius: 5px;
  font-size: 9px;
  font-weight: 700;
  background: linear-gradient(135deg, #f97316, #fb923c);
  color: #fff;
  white-space: nowrap;
  margin-left: 4px;
}

.sub-item-body { flex: 1; min-width: 0; }

.sub-item-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 3px;
}

.sub-item-name {
  font-size: 14px;
  font-weight: 600;
  color: #444;
}

.sub-item-rec {
  font-size: 10px; font-weight: 700;
  padding: 1px 6px;
  border-radius: 6px;
  background: rgba(139,92,246,0.12);
  color: var(--color-primary);
}

.sub-item-status {
  font-size: 10px; padding: 1px 6px; border-radius: 6px;
  &.done { background: rgba(34,197,94,0.12); color: #16a34a; }
  &.active { background: rgba(224,122,95,0.12); color: #E07A5F; }
  &.locked { background: rgba(0,0,0,0.08); color: #888; }
}

.sub-item-desc {
  font-size: 11px;
  color: #aaa;
  margin: 0;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sub-item-bar {
  height: 3px;
  background: rgba(0,0,0,0.06);
  border-radius: 2px;
  margin-top: 6px;
}

.sub-item-fill {
  height: 100%;
  border-radius: 2px;
  background: linear-gradient(90deg, #E07A5F, #f08a5d);
  transition: width 0.6s ease;
}

.sub-item-arrow {
  color: #ddd;
  flex-shrink: 0;
  transition: all 0.2s;
  .sub-item:hover & { color: var(--text-tertiary); transform: translateX(3px); }
  .sub-item.locked:hover & { transform: none; }
}

/* ═══ 指南针 ═══ */
.map-compass {
  position: absolute;
  bottom: 24px; left: 24px;
  z-index: 2;
  pointer-events: none;
  opacity: 0.45;
}

/* ═══ 面板动画 ═══ */
.panel-zoom-enter-active { transition: all 0.35s cubic-bezier(0.16,1,0.3,1); }
.panel-zoom-leave-active { transition: all 0.25s cubic-bezier(0.4,0,0.2,1); }
.panel-zoom-enter-from { opacity: 0; transform: scale(0.85) translateY(-12px); }
.panel-zoom-leave-to { opacity: 0; transform: scale(0.9); }

/* ═══ 底部详情浮层 ═══ */
.detail-bar {
  position: fixed;
  bottom: 0; left: 0; right: 0;
  z-index: 100;
  background: rgba(255,255,255,0.97);
  backdrop-filter: blur(20px);
  border-top: 1px solid rgba(0,0,0,0.08);
  padding: 18px 28px;
  box-shadow: 0 -4px 24px rgba(0,0,0,0.06);
}

.detail-bar-inner {
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  align-items: flex-start;
  gap: 28px;
}

.detail-close {
  position: absolute;
  top: 10px; right: 18px;
  width: 30px; height: 30px;
  border: none;
  background: rgba(0,0,0,0.04);
  border-radius: 8px;
  color: #aaa;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
  &:hover { background: rgba(0,0,0,0.08); color: #555; }
}

.detail-left { flex: 2; min-width: 0; }

.detail-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 600;
  margin-bottom: 6px;
  &.mastered { background: rgba(34,197,94,0.12); color: #16a34a; }
  &.learning { background: rgba(224,122,95,0.15); color: #E07A5F; }
  &.locked   { background: rgba(0,0,0,0.07); color: #777; }
}

.detail-name {
  font-size: 19px;
  font-weight: 700;
  margin: 0 0 4px;
  color: #333;
}

.detail-desc {
  font-size: 13px;
  color: #888;
  line-height: 1.5;
  margin: 0;
}

.detail-mid {
  flex: 1.5; min-width: 0;
  h4 {
    font-size: 11px;
    color: #bbb;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin: 0 0 8px;
  }
}

.detail-tags { display: flex; flex-wrap: wrap; gap: 6px; }

.detail-chip {
  padding: 3px 10px;
  border-radius: 6px;
  background: rgba(0,0,0,0.04);
  font-size: 12px;
  color: #888;
  border: 1px solid rgba(0,0,0,0.06);
}

.detail-right { flex: 1.5; display: flex; flex-direction: column; gap: 10px; }

.detail-tip {
  font-size: 12px;
  color: #888;
  line-height: 1.5;
  margin: 0;
  padding: 10px 12px;
  background: rgba(139,92,246,0.06);
  border-radius: 10px;
  border-left: 2px solid var(--color-primary-light);
}

.detail-action {
  align-self: flex-start;
  padding: 9px 24px;
  border: none;
  border-radius: 10px;
  background: linear-gradient(135deg, #E07A5F, #D2654B);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
  &:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(224,122,95,0.35); }
  &:disabled { opacity: 0.3; cursor: not-allowed; transform: none; }
}
.exam-action {
  background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
  margin-top: 8px;
  &:hover { filter: brightness(0.92); transform: scale(1.03) !important; }
}
.chapter-badge {
  margin-top: 16px;
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 700;
  text-align: center;
  width: 100%;
}
.chapter-badge.learning-badge { background: rgba(59,130,246,0.1); color: #3b82f6; }
.chapter-badge.available-badge { background: rgba(107,114,128,0.08); color: var(--text-tertiary); }

/* ═══ 过渡 ═══ */
.detail-slide-enter-active,
.detail-slide-leave-active { transition: all 0.3s cubic-bezier(0.16,1,0.3,1); }
.detail-slide-enter-from,
.detail-slide-leave-to { transform: translateY(100%); opacity: 0; }
</style>
