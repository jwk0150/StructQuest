<template>
  <div 
    class="resource-card" 
    :class="[typeClass, { expanded: isExpanded, 'is-loading': loading, 'is-empty': !hasContent && !loading }]"
  >
    <!-- 卡片头部 -->
    <div class="card-header">
      <div class="header-left">
        <span class="type-icon">{{ typeMeta.icon || '📄' }}</span>
        <div class="type-info">
          <span class="type-label">{{ typeMeta.label || '学习资源' }}</span>
          <span v-if="difficulty && hasContent" class="diff-badge" :class="difficulty">{{ difficultyLabel }}</span>
        </div>
      </div>
      <div class="header-right">
        <el-tag v-if="isAI && hasContent" size="small" effect="dark" :color="typeMeta.color" round>
          AI 生成
        </el-tag>
        <el-tag v-else-if="loading" size="small" type="warning" effect="dark" round>
          生成中...
        </el-tag>
        <el-button
          v-if="hasContent"
          link
          size="small"
          class="expand-btn"
          @click.stop="toggleExpand"
        >
          {{ isExpanded ? '收起' : '展开' }}
          <el-icon :class="{ rotated: isExpanded }"><ArrowDown /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 标题区 -->
    <h3 class="card-title">{{ title }}</h3>
    <p v-if="description && !isExpanded" class="card-desc">{{ description }}</p>

    <!-- 空状态：显示生成按钮 -->
    <div v-if="!hasContent && !loading" class="empty-state">
      <div class="empty-icon">{{ typeMeta.icon }}</div>
      <p>点击生成 AI {{ typeMeta.label }}资源</p>
      <el-button 
        type="primary" 
        :color="typeMeta.color"
        round
        @click.stop="$emit('generate')"
        :loading="loading"
      >
        <template #icon><MagicStick /></template>
        立即生成
      </el-button>
    </div>

    <!-- 加载骨架屏 -->
    <div v-if="loading" class="skeleton-loader">
      <div class="sk-line sk-title"></div>
      <div class="sk-line sk-text"></div>
      <div class="sk-line sk-text short"></div>
      <div class="sk-line sk-text"></div>
      <p class="sk-hint">AI 正在生成{{ typeMeta.label }}，请稍候...</p>
    </div>

    <!-- 展开的内容区域 -->
    <transition name="expand">
      <div v-if="isExpanded && hasContent && !loading" class="card-body">
        
        <!-- 📖 讲义 / ✏️ 练习题 / 📋 学习总结 — Markdown 渲染 -->
        <div 
          v-if="isMarkdownLike"
          class="markdown-content"
          v-html="renderedContent"
        ></div>

        <!-- 💻 代码案例 — 高亮代码 -->
        <div v-else-if="type === 'code_example'" class="code-content">
          <div class="markdown-content" v-html="renderedContent"></div>
        </div>

        <!-- 📽️ PPT 大纲 — 支持两种模式：PPTX 文件下载 / Markdown 大纲预览 -->
        <div v-else-if="type === 'ppt_outline'" class="ppt-content">
          <!-- PPTX 文件模式：下载按钮 + 幻灯片信息 -->
          <div v-if="isPptxFile" class="pptx-mode">
            <div class="pptx-banner">
              <div class="banner-icon">📊</div>
              <div class="banner-info">
                <span class="banner-title">PowerPoint 演示文稿已生成</span>
                <span class="banner-meta">
                  {{ pptxSlideCount }} 页幻灯片 · 可直接编辑
                </span>
              </div>
              <el-button type="primary" :color="typeMeta.color" round @click.stop="downloadPptx">
                <template #icon><Download /></template>
                下载 .pptx
              </el-button>
            </div>
            <!-- 大纲预览（可折叠） -->
            <details class="outline-preview" open>
              <summary>📑 大纲内容预览</summary>
              <div class="markdown-content outline-body" v-html="renderedContent"></div>
            </details>
          </div>
          <!-- Markdown 降级模式：JSON 结构化展示 -->
          <div v-else-if="parsedPPT" class="ppt-slides">
            <el-alert
              title="PPTX 引擎不可用，以下为大纲文本预览"
              type="warning"
              :closable="false"
              show-icon
              style="margin-bottom: 12px;"
            />
            <div
              v-for="(slide, idx) in parsedPPT.slides"
              :key="idx"
              class="ppt-slide"
              :class="'layout-' + slide.layout"
            >
              <div class="slide-num">#{{ slide.slide_num }}</div>
              <div class="slide-layout-tag">{{ layoutLabels[slide.layout] || slide.layout }}</div>
              <h4>{{ slide.title }}</h4>
              <ul v-if="slide.content && slide.content.length">
                <li v-for="(item, ci) in slide.content" :key="ci">{{ item }}</li>
              </ul>
              <p v-if="slide.speaker_notes" class="speaker-notes">📝 {{ slide.speaker_notes }}</p>
            </div>
          </div>
          <!-- 纯文本兜底 -->
          <pre v-else class="raw-json"><code>{{ content }}</code></pre>
        </div>

        <!-- 🧠 思维导图 — ECharts 可视化树图 / Mermaid 文本/JSON 降级 -->
        <div v-else-if="type === 'mindmap'" class="mindmap-content">
          <!-- 优先 ECharts 树图渲染 -->
          <div v-if="mindmapTreeData" ref="mindmapChartRef" class="mindmap-echarts"></div>
          <!-- JSON 降级 -->
          <div v-else-if="parsedMindmap" class="mindmap-tree">
            <div 
              v-for="(node, idx) in parsedMindmap.nodes" 
              :key="idx" 
              class="mindmap-node"
              :class="{ highlighted: parsedMindmap.highlight_nodes?.includes(node.id), root: node.type === 'root' }"
              :style="{ paddingLeft: (getDepth(node, parsedMindmap.nodes) * 20) + 'px' }"
            >
              <span class="node-dot"></span>
              <span class="node-label">{{ node.label }}</span>
            </div>
            <p v-if="parsedMindmap.summary" class="mm-summary">{{ parsedMindmap.summary }}</p>
            <p v-if="parsedMindmap.study_tip" class="mm-tip">💡 {{ parsedMindmap.study_tip }}</p>
          </div>
          <!-- Mermaid 文本降级（带语法高亮） -->
          <pre v-else class="raw-mermaid"><code>{{ content }}</code></pre>
        </div>

        <!-- 兜底：原始内容 -->
        <pre v-else class="raw-content"><code>{{ content }}</code></pre>
      </div>
    </transition>

    <!-- 卡片底部操作栏 -->
    <div class="card-footer">
      <div class="footer-left">
        <span v-if="tags && tags.length" class="tag-list">
          <el-tag 
            v-for="tag in tags.slice(0, 3)" 
            :key="tag" 
            size="small" 
            effect="plain" 
            round
          >{{ tag }}</el-tag>
        </span>
        <span v-if="estimatedMinutes" class="time-est">
          ⏱️ 约 {{ estimatedMinutes }} 分钟
        </span>
      </div>
      <div class="footer-actions">
        <el-tooltip v-if="hasContent" content="复制内容">
          <el-button link size="small" :icon="CopyDocument" @click.stop="copyContent" />
        </el-tooltip>
        <el-tooltip v-if="hasContent && isAI" content="重新生成">
          <el-button link size="small" :icon="Refresh" @click.stop="$emit('regenerate')" />
        </el-tooltip>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ArrowDown, CopyDocument, Refresh, MagicStick, Download } from '@element-plus/icons-vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import hljs from 'highlight.js'
import * as echarts from 'echarts'
import 'highlight.js/styles/github-dark.css'
import { ElMessage } from 'element-plus'
import { parseMindmap } from '../../utils/mindmapParser.js'

const props = defineProps({
  title: { type: String, default: '' },
  description: { type: String, default: '' },
  type: { type: String, default: '' }, // notes/mindmap/quiz/code_example/ppt_outline (旧版兼容: lecture/exercise/summary)
  content: { type: String, default: '' },
  format: { type: String, default: '' },          // "pptx" | "markdown" 等
  difficulty: { type: String, default: '' },
  isAI: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  estimatedMinutes: { type: Number, default: null },
  tags: { type: Array, default: () => [] },
  meta: { type: Object, default: () => ({}) },
  fileUrl: { type: String, default: '' },           // PPTX 文件下载地址
  downloadName: { type: String, default: '' },       // 建议下载文件名
  slideCount: { type: Number, default: 0 },         // 幻灯片页数
})

const emit = defineEmits(['view', 'regenerate', 'copy', 'generate'])

const isExpanded = ref(false)

// ── 类型元信息映射 ──
const TYPE_META = {
  // v4 新类型
  notes:        { icon: '📖', label: '学习讲义', color: '#4F46E5', bg: 'rgba(79,70,229,0.06)' },
  mindmap:      { icon: '🧠', label: '思维导图', color: '#8B5CF6', bg: 'rgba(139,92,246,0.06)' },
  quiz:         { icon: '✏️',  label: '练习题', color: '#EF4444', bg: 'rgba(239,68,68,0.06)' },
  code_example: { icon: '💻', label: '代码案例', color: '#10B981', bg: 'rgba(16,185,129,0.06)' },
  ppt_outline:  { icon: '📽️', label: 'PPT 大纲', color: '#F59E0B', bg: 'rgba(245,158,11,0.06)' },
  // 旧版兼容映射
  lecture:      { icon: '📖', label: '课程讲义', color: '#4F46E5', bg: 'rgba(79,70,229,0.06)' },
  exercise:     { icon: '✏️',  label: '练习题集', color: '#EF4444', bg: 'rgba(239,68,68,0.06)' },
  summary:      { icon: '📋', label: '学习总结', color: '#06B6D4', bg: 'rgba(6,182,212,0.06)' },
  doc:          { icon: '📄', label: '文档', color: '#6B7280', bg: 'rgba(107,114,128,0.06)' },
  diagram:      { icon: '🔷', label: '图解', color: '#EC4899', bg: 'rgba(236,72,153,0.06)' },
}

const typeMeta = computed(() => props.meta?.icon ? {
  ...props.meta,
} : TYPE_META[props.type] || TYPE_META['doc'])

const typeClass = computed(() => `res-type-${props.type}`)

const hasContent = computed(() => !!props.content && props.content.length > 10)
const isMarkdownLike = computed(() => ['notes', 'quiz', 'lecture', 'exercise', 'summary', 'doc', 'ppt_outline'].includes(props.type))

// ── 难度标签 ──
const difficultyMap = { easy: '入门', medium: '中级', hard: '高级' }
const difficultyLabel = computed(() => difficultyMap[props.difficulty] || props.difficulty)

// ── Markdown 渲染 ──
const renderMd = (text) => {
  if (!text) return ''
  try {
    marked.setOptions({
      highlight(code, lang) {
        if (lang && hljs.getLanguage(lang)) return hljs.highlight(code, { language: lang }).value
        return hljs.highlightAuto(code).value
      },
      breaks: true,
    })
    return DOMPurify.sanitize(marked.parse(text))
  } catch {
    return text
  }
}
const renderedContent = computed(() => renderMd(props.content))

// ── PPT 解析 ──
const isPptxFile = computed(() =>
  props.type === 'ppt_outline' && props.format === 'pptx' && !!props.fileUrl
)
const pptxSlideCount = computed(() => props.slideCount || 0)

/** 下载 PPTX 文件 */
function downloadPptx() {
  if (!props.fileUrl) {
    ElMessage.warning('文件地址不可用')
    return
  }
  const link = document.createElement('a')
  link.href = props.fileUrl
  link.download = props.downloadName || '演示文稿.pptx'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  ElMessage.success('开始下载 PPT 文件')
}

const parsedPPT = computed(() => {
  if (props.type !== 'ppt_outline') return null
  try {
    const jsonMatch = props.content.match(/```(?:json)?\s*([\s\S]*?)\s*```/)
    const jsonStr = jsonMatch ? jsonMatch[1].trim() : props.content.trim()
    return JSON.parse(jsonStr)
  } catch {
    return null
  }
})

const layoutLabels = {
  title: '封面', agenda: '目录', section: '章节',
  content: '内容', two_column: '双栏对比', code_page: '代码展示',
  diagram: '图解', exercise: '互动练习', summary: '总结', qa: 'Q&A',
}

// ── 思维导图解析 + ECharts 渲染 ──

const mindmapChartRef = ref(null)
let mindmapChartInstance = null

/** 使用共享解析器 */
const mindmapTreeData = computed(() => {
  if (props.type !== 'mindmap' || !props.content) return null
  return parseMindmap(props.content)
})

/** 渲染 ECharts mindmap — 专业 Markmap 级配置 */
function renderMindmapChart() {
  nextTick(() => {
    if (!mindmapChartRef.value || !mindmapTreeData.value) return
    const chartData = mindmapTreeData.value
    if (!chartData.children || chartData.children.length === 0) return

    if (mindmapChartInstance) {
      mindmapChartInstance.dispose()
      mindmapChartInstance = null
    }

    mindmapChartInstance = echarts.init(mindmapChartRef.value)

    // 按深度着色的色板
    const depthColors = [
      '#E63946', '#F4A261', '#457B9D', '#2A9D8F', '#7209B7',
    ]

    const option = {
      tooltip: {
        trigger: 'item',
        triggerOn: 'mousemove',
        backgroundColor: 'rgba(29,53,87,0.9)',
        borderColor: '#457B9D',
        textStyle: { color: '#fff', fontSize: 13 },
        formatter: (p) => {
          const depth = p.treeAncestors ? p.treeAncestors.length : 0
          return `<b>${p.name}</b><br/><span style="font-size:11px;opacity:0.7">层级 L${depth}</span>`
        },
      },
      series: [{
        type: 'tree',
        data: [chartData],
        top: '3%',
        left: '6%',
        bottom: '3%',
        right: '10%',
        orient: 'LR',
        symbol: 'circle',
        symbolSize: (value, params) => {
          if (!params || params.treeAncestors == null) return [14, 14]
          const depth = params.treeAncestors.length
          return depth === 0 ? [14, 14] : depth <= 2 ? [9, 9] : [6, 6]
        },
        edgeShape: 'curve',
        edgeForkPosition: '63%',
        initialTreeDepth: 2,
        roam: true,
        scaleLimit: { min: 0.4, max: 3 },
        label: {
          position: 'right',
          verticalAlign: 'middle',
          align: 'left',
          fontSize: 13,
          fontWeight: 'bold',
          color: '#1D3557',
          borderRadius: 4,
          padding: [4, 10],
          distance: 10,
          overflow: 'truncate',
          ellipsis: '...',
          width: 130,
        },
        leaves: {
          label: {
            position: 'right',
            verticalAlign: 'middle',
            align: 'left',
            fontSize: 12,
            fontWeight: 'normal',
            color: '#455A64',
            distance: 8,
            padding: [2, 8],
          },
        },
        itemStyle: {
          borderWidth: 0,
        },
        lineStyle: {
          color: '#B0BEC5',
          width: 1.8,
          curveness: 0.5,
        },
        emphasis: {
          focus: 'descendant',
          lineStyle: { color: '#E63946', width: 3 },
          itemStyle: { shadowBlur: 10, shadowColor: 'rgba(230,57,70,0.3)' },
        },
        expandAndCollapse: true,
        animationDuration: 550,
        animationDurationUpdate: 750,
        animationEasingUpdate: 'cubicInOut',
      }],
    }

    mindmapChartInstance.setOption(option)
  })
}
}

// 监听 mindmapTreeData 变化自动渲染
watch(mindmapTreeData, (val) => {
  if (val) renderMindmapChart()
})

// 监听展开状态，展开时才渲染（避免隐藏 dom 尺寸为 0）
watch(isExpanded, (val) => {
  if (val && mindmapTreeData.value) {
    setTimeout(() => renderMindmapChart(), 100)
  }
})

onMounted(() => {
  if (isExpanded.value && mindmapTreeData.value) {
    setTimeout(() => renderMindmapChart(), 200)
  }
})

/** 销毁图表实例 */
function destroyMindmapChart() {
  if (mindmapChartInstance) {
    mindmapChartInstance.dispose()
    mindmapChartInstance = null
  }
}

onBeforeUnmount(() => destroyMindmapChart())

/** 旧的 JSON 格式降级解析 */
const parsedMindmap = computed(() => {
  if (props.type !== 'mindmap') return null
  if (mindmapTreeData.value) return null  // 优先用 ECharts 渲染
  try {
    const jsonMatch = props.content.match(/```(?:json)?\s*([\s\S]*?)\s*```/)
    const jsonStr = jsonMatch ? jsonMatch[1].trim() : props.content.trim()
    const parsed = JSON.parse(jsonStr)
    return parsed.nodes ? parsed : null
  } catch {
    return null
  }
})

function getDepth(node, nodes) {
  let depth = 0
  let current = node
  while (current?.parent) {
    depth++
    current = nodes.find(n => n.id === current.parent)
  }
  return Math.min(depth, 4)
}

// ── 操作方法 ──

/** 切换展开/收起 — 有内容才能展开 */
function toggleExpand() {
  if (!hasContent.value) {
    // 没有内容时，触发生成
    emit('generate')
    return
  }
  isExpanded.value = !isExpanded.value
  if (isExpanded.value) emit('view')
}

function copyContent() {
  navigator.clipboard.writeText(props.content).then(() => {
    ElMessage.success('已复制到剪贴板')
    emit('copy')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

defineExpose({ 
  expand: () => { isExpanded.value = true },
  collapse: () => { isExpanded.value = false },
})
</script>

<style lang="scss" scoped>
.resource-card {
  border-radius: 16px;
  border: 2px solid var(--border-color);
  background: white;
  transition: all 0.35s cubic-bezier(.4, 0, .2, 1);
  cursor: pointer;
  overflow: hidden;
  display: flex;
  flex-direction: column;

  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 40px rgba(0,0,0,0.08);
    border-color: v-bind('typeMeta.color');
  }

  &.is-loading {
    pointer-events: none;
    border-style: dashed;
    opacity: 0.85;
  }

  &.is-empty {
    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(0,0,0,0.06);
    }
    .card-header .type-icon {
      background: var(--accent-bg, rgba(0,0,0,0.04));
      opacity: 0.6;
    }
    .card-title { color: var(--text-secondary); font-weight: 600; }
  }

  &.expanded {
    cursor: default;
  }

  // ── 每种类型的主题色 ──
  .res-type-notes        { --accent: #4F46E5; --accent-bg: rgba(79,70,229,0.05); }
  .res-type-mindmap      { --accent: #8B5CF6; --accent-bg: rgba(139,92,246,0.05); }
  .res-type-quiz         { --accent: #EF4444; --accent-bg: rgba(239,68,68,0.05); }
  .res-type-code_example { --accent: #10B981; --accent-bg: rgba(16,185,129,0.05); }
  .res-type-ppt_outline  { --accent: #F59E0B; --accent-bg: rgba(245,158,11,0.05); }
  // 旧版兼容
  .res-type-lecture       { --accent: #4F46E5; --accent-bg: rgba(79,70,229,0.05); }
  .res-type-exercise      { --accent: #EF4444; --accent-bg: rgba(239,68,68,0.05); }
  .res-type-summary       { --accent: #06B6D4; --accent-bg: rgba(6,182,212,0.05); }
  .res-type-doc           { --accent: #6B7280; --accent-bg: rgba(107,114,128,0.05); }
  .res-type-diagram       { --accent: #EC4899; --accent-bg: rgba(236,72,153,0.05); }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px 0;

  .header-left {
    display: flex;
    align-items: center;
    gap: 10px;

    .type-icon {
      font-size: 24px;
      width: 42px;
      height: 42px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--accent-bg, var(--bg-secondary));
      border-radius: 10px;
      transition: all 0.25s;
    }

    .type-info {
      display: flex;
      flex-direction: column;
      gap: 2px;

      .type-label {
        font-size: 13px;
        font-weight: 700;
        color: var(--accent, var(--text-main));
      }

      .diff-badge {
        font-size: 10px;
        padding: 1px 8px;
        border-radius: 4px;
        font-weight: 600;
        display: inline-block;
        width: fit-content;

        &.easy   { background: #DCFCE7; color: #166534; }
        &.medium { background: #FEF3C7; color: #92400E; }
        &.hard   { background: #FEE2E2; color: #991B1B; }
      }
    }
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 8px;

    .expand-btn {
      font-size: 12px;
      color: var(--text-tertiary);

      .el-icon {
        transition: transform 0.25s;
        margin-left: 2px;

        &.rotated { transform: rotate(180deg); }
      }
    }
  }
}

.card-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-main);
  margin: 14px 20px 6px;
  line-height: 1.3;
}

.card-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.55;
  padding: 0 20px;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

// ── 空状态（无内容时的生成入口） ──
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 20px;
  gap: 14px;
  text-align: center;

  .empty-icon {
    font-size: 44px;
    opacity: 0.45;
    filter: grayscale(0.3);
  }

  p {
    font-size: 13px;
    color: var(--text-tertiary);
    margin: 0;
  }
}

// ── 骨架屏 ──
.skeleton-loader {
  padding: 20px;
  .sk-line {
    background: linear-gradient(90deg, var(--bg-secondary) 25%, var(--border-light) 50%, var(--bg-secondary) 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: 6px;
    height: 14px;
    margin-bottom: 10px;
    &.sk-title { height: 20px; width: 60%; }
    &.short { width: 40%; }
  }
  .sk-hint {
    text-align: center;
    font-size: 12px;
    color: var(--text-tertiary);
    margin-top: 12px;
    animation: pulse-text 2s ease-in-out infinite;
  }
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
@keyframes pulse-text {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

// ── 展开内容区 ──
.card-body {
  padding: 0 20px 20px;
  border-top: 1px solid var(--border-light);
  margin-top: 12px;
  max-height: 60vh;
  overflow-y: auto;
  animation: fadeIn 0.3s ease;

  .markdown-content {
    font-size: 14px;
    line-height: 1.75;
    color: var(--text-main);

    :deep(h1), :deep(h2), :deep(h3), :deep(h4) {
      color: var(--text-main);
      margin-top: 1.2em;
      margin-bottom: 0.5em;
      font-weight: 700;
    }
    :deep(h1) { font-size: 1.5em; border-bottom: 2px solid var(--accent, var(--color-primary)); padding-bottom: 0.3em; }
    :deep(h2) { font-size: 1.25em; }
    :deep(h3) { font-size: 1.1em; }

    :deep(p) { margin: 0.7em 0; }

    :deep(blockquote) {
      border-left: 4px solid var(--accent, var(--color-primary));
      background: var(--accent-bg, var(--bg-secondary));
      padding: 12px 16px;
      border-radius: 0 8px 8px 0;
      margin: 1em 0;
      color: var(--text-secondary);
    }

    :deep(ul), :deep(ol) { padding-left: 1.5em; margin: 0.7em 0; }

    :strong, :deep(strong) { color: var(--text-main); }

    :deep(table) {
      width: 100%;
      border-collapse: collapse;
      margin: 1em 0;
      font-size: 13px;
      th, td {
        border: 1px solid var(--border-color);
        padding: 8px 12px;
        text-align: left;
      }
      th { background: var(--accent-bg, var(--bg-secondary)); font-weight: 600; }
    }

    :deep(pre) {
      background: #1e1e2e;
      border-radius: 10px;
      padding: 16px;
      overflow-x: auto;
      margin: 1em 0;

      code {
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        font-size: 13px;
        color: #cdd6f4;
      }
    }

    :deep(details) {
      margin: 0.7em 0;
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 10px 14px;
      summary { cursor: pointer; font-weight: 600; color: var(--accent, var(--color-primary)); }
      p { margin-top: 8px; }
    }

    :deep(hr) { border: none; border-top: 1px dashed var(--border-color); margin: 1.5em 0; }
  }
}

.expand-enter-active { transition: all 0.35s ease-out; }
.expand-leave-active { transition: all 0.2s ease-in; }
.expand-enter-from, .expand-leave-to { opacity: 0; max-height: 0; margin-top: 0; }

@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }

// ── PPT 展示样式 ──
.ppt-content {
  .pptx-mode {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .pptx-banner {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 16px 20px;
    background: linear-gradient(135deg, #FFF7ED 0%, #FEF3C7 100%);
    border-radius: 12px;
    border: 1px solid #FDE68A;

    .banner-icon {
      font-size: 36px;
      width: 56px; height: 56px;
      display: flex; align-items: center; justify-content: center;
      background: white; border-radius: 12px;
      box-shadow: 0 2px 8px rgba(245,158,11,0.15);
    }

    .banner-info {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 3px;

      .banner-title {
        font-size: 15px;
        font-weight: 700;
        color: #92400E;
      }

      .banner-meta {
        font-size: 12px;
        color: #B45309;
      }
    }

    .el-button { white-space: nowrap; }
  }

  .outline-preview {
    border: 1px solid var(--border-color);
    border-radius: 10px;
    overflow: hidden;

    summary {
      padding: 10px 16px;
      font-size: 13px;
      font-weight: 600;
      color: var(--accent, var(--color-primary));
      background: var(--bg-secondary);
      cursor: pointer;

      &::-webkit-details-marker { display: none; }
    }

    .outline-body {
      padding: 12px 16px;
      max-height: 40vh;
      overflow-y: auto;
      font-size: 13px;
    }
  }
  .ppt-slides {
    display: grid;
    gap: 14px;
  }
  .ppt-slide {
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 14px 16px;
    position: relative;
    transition: all 0.2s;

    &:hover { border-color: var(--accent); box-shadow: 0 2px 12px var(--accent-bg); }

    .slide-num {
      position: absolute;
      top: 10px;
      right: 14px;
      font-size: 11px;
      font-weight: 700;
      color: var(--text-tertiary);
      background: var(--bg-secondary);
      padding: 2px 8px;
      border-radius: 6px;
    }

    .slide-layout-tag {
      font-size: 10px;
      font-weight: 700;
      color: var(--accent);
      background: var(--accent-bg);
      padding: 2px 8px;
      border-radius: 4px;
      display: inline-block;
      margin-bottom: 6px;
    }

    h4 { margin: 0 0 8px; font-size: 15px; }
    
    ul { margin: 0; padding-left: 1.2em;
      li { font-size: 13px; color: var(--text-secondary); line-height: 1.6; margin-bottom: 3px; }
    }

    .speaker-notes {
      margin-top: 10px;
      padding: 8px 10px;
      background: var(--bg-secondary);
      border-radius: 6px;
      font-size: 12px;
      color: var(--text-tertiary);
    }
  }
}

// ── 思维导图样式 ──
.mindmap-content {
  .mindmap-echarts {
    width: 100%;
    min-height: 420px;
    height: 55vh;
    max-height: 650px;
    border: 1px solid var(--border-light);
    border-radius: 12px;
    background: linear-gradient(135deg, #F8F9FA 0%, #FFFFFF 100%);
    overflow: hidden;
  }

  .raw-mermaid {
    background: #1e1e2e;
    border-radius: 10px;
    padding: 16px;
    font-size: 12px;
    line-height: 1.6;
    overflow-x: auto;
    white-space: pre-wrap;

    code {
      font-family: 'JetBrains Mono', monospace;
      color: #cdd6f4;
    }
  }

  .mindmap-tree {
    padding: 8px 0;
  }
  .mindmap-node {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 0;
    font-size: 14px;
    transition: all 0.2s;

    &.root {
      font-weight: 800;
      font-size: 17px;
      color: var(--accent);
      padding: 10px 0 14px;
      .node-dot { width: 12px; height: 12px; background: var(--accent); }
    }

    &.highlighted .node-label {
      color: #DC2626;
      font-weight: 700;
      background: #FEE2E2;
      padding: 1px 8px;
      border-radius: 4px;
    }

    .node-dot {
      width: 8px; height: 8px;
      border-radius: 50%;
      background: var(--accent);
      flex-shrink: 0;
      opacity: 0.6;
    }

    .node-label {
      color: var(--text-secondary);
    }

    &:hover .node-dot { opacity: 1; transform: scale(1.3); }
  }

  .mm-summary, .mm-tip {
    margin-top: 14px;
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 13px;
  }
  .mm-summary { background: var(--accent-bg); color: var(--text-secondary); }
  .mm-tip     { background: #FEF3C7; color: #92400E; }
}

// ── 原始代码兜底 ──
.raw-json, .raw-content {
  background: #1e1e2e;
  border-radius: 10px;
  padding: 16px;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.6;

  code {
    font-family: 'JetBrains Mono', monospace;
    color: #cdd6f4;
  }
}

// ── 底部操作栏 ──
.card-footer {
  margin-top: auto;
  padding: 12px 20px;
  border-top: 1px solid var(--border-light);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(250,250,252,0.6);

  .footer-left {
    display: flex;
    align-items: center;
    gap: 10px;

    .tag-list {
      display: flex;
      gap: 4px;
    }

    .time-est {
      font-size: 11px;
      color: var(--text-tertiary);
    }
  }

  .footer-actions {
    display: flex;
    gap: 2px;

    .el-button { color: var(--text-tertiary); &:hover { color: var(--accent); } }
  }
}
</style>
