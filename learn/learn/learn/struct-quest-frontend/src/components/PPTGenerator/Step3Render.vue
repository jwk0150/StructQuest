<template>
  <div class="step3-container">
    <!-- 模板选择 -->
    <div class="template-section">
      <h3>🎨 选择模板风格</h3>
      
      <div class="template-cards" v-if="templatesList.length > 0">
        <div
          v-for="tpl in templatesList"
          :key="tpl.name"
          class="template-card"
          :class="{ active: renderConfig.template === tpl.name }"
          @click="selectTemplate(tpl.name)"
        >
          <!-- 预览色块 -->
          <div class="tpl-preview" :style="{ 
            background: `linear-gradient(135deg, ${tpl.preview_colors?.primary || '#667eea'}, ${tpl.preview_colors?.accent || '#764ba2'})`
          }">
            <div class="preview-mockup">
              <div class="mock-title"></div>
              <div class="mock-bar"></div>
              <div class="mock-content">
                <div class="mock-card" v-for="i in 3" :key="i"></div>
              </div>
            </div>
          </div>

          <!-- 信息 -->
          <div class="tpl-info">
            <h4>{{ tpl.display_name }}</h4>
            <p>{{ tpl.description?.split('\n')[0] || '' }}</p>
          </div>
          
          <!-- 选中标记 -->
          <div v-if="renderConfig.template === tpl.name" class="selected-badge">✓</div>
        </div>
      </div>
    </div>

    <!-- 输出格式选择 -->
    <div class="format-section">
      <h3>📁 输出格式</h3>
      
      <el-radio-group v-model="renderConfig.format" size="large">
        <el-radio-button value="html">
          🌐 HTML（浏览器预览/打印PDF）
        </el-radio-button>
        <el-radio-button value="pptx">
          📊 PPTX文件（PowerPoint可编辑）
        </el-radio-button>
      </el-radio-group>
    </div>

    <!-- 大纲摘要确认 -->
    <div class="summary-section">
      <h3>📋 最终大纲确认</h3>
      
      <div class="outline-summary">
        <div class="summary-header">
          <strong>{{ outline.topic || '演示文稿' }}</strong>
          <span class="page-count">{{ outline.total_pages || outline.slides?.length }} 页</span>
        </div>
        
        <div class="summary-slides">
          <div 
            v-for="(slide, i) in (outline.slides || [])" 
            :key="i" 
            class="summary-slide-item"
          >
            <span class="ss-num">{{ i + 1 }}</span>
            <span class="ss-type" :class="'type-' + slide.layout">{{ layoutIcons[slide.layout] || '●' }}</span>
            <span class="ss-title">{{ slide.title }}</span>
            <span class="ss-bullets">{{ slide.bullet_points?.length || 0 }} 个要点</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 渲染进度 -->
    <div v-if="renderProgress.generating" class="progress-overlay">
      <div class="progress-box">
        <el-progress 
          :percentage="renderProgress.percentage" 
          :stroke-width="10"
          status="success"
        />
        <p class="status-text">{{ renderProgress.statusText }}</p>
      </div>
    </div>

    <!-- 渲染结果 -->
    <div v-if="renderResult && !renderProgress.generating" class="result-section">
      <el-result icon="success" title="生成成功！" :sub-title="`耗时 ${renderResult.render_time}秒 · 格式: ${formatLabel}`">
        <template #extra>
          <el-button type="primary" size="large" @click="$emit('open-preview')">
            {{ isHtmlFormat ? '🌐 预览/播放' : '👀 查看文件' }}
          </el-button>
          <el-button size="large" @click="$emit('download')">
            ⬇️ 下载 {{ isHtmlFormat ? 'HTML' : 'PPTX' }}
          </el-button>
          <el-button size="large" plain @click="$emit('back-to-edit')">返回编辑</el-button>
        </template>
        <div v-if="isHtmlFormat" class="result-hint">
          <p>💡 HTML 格式支持浏览器直接打开、全屏演示（按 F11）、以及打印为 PDF</p>
        </div>
        <div v-else class="result-hint">
          <p>💡 PPTX 文件可下载后用 PowerPoint / WPS 打开编辑，支持进一步自定义样式和动画</p>
        </div>
      </el-result>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  renderConfig: { type: Object, required: true },
  outline: { type: Object, required: true },
  renderProgress: { type: Object, required: true },
  renderResult: { type: Object, default: null },
  templatesList: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:render-config', 'render'])

function selectTemplate(name) {
  emit('update:render-config', { ...props.renderConfig, template: name })
}

const isHtmlFormat = computed(() => {
  return props.renderResult?.format?.includes('html') ?? true
})

const formatLabel = computed(() => {
  const fmt = props.renderResult?.format || 'html'
  if (fmt.includes('pptx')) return 'PPTX (PowerPoint)'
  if (fmt.includes('html')) {
    return fmt.includes('降级') ? 'HTML (已降级)' : 'HTML (网页)'
  }
  return fmt
})

const layoutIcons = {
  title: '📄',
  section: '📑',
  content: '📋',
  summary: '✅',
  chart: '📊',
  comparison: '⚖️',
  timeline: '⏱️',
  quote: '💬',
  two_column: '📑',
  cards_grid: '🃏',
}
</script>

<style scoped>
.step3-container {
  padding: 8px 0;
}

/* 模板选择 */
.template-section h3,
.format-section h3,
.summary-section h3 {
  font-size: 16px;
  color: #303133;
  margin-bottom: 14px;
}

.template-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
  margin-bottom: 28px;
}

.template-card {
  border: 2px solid #e4e7ed;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.25s ease;
  position: relative;
  background: white;
}

.template-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.template-card.active {
  border-color: #409eff;
  box-shadow: 0 8px 24px rgba(64, 158, 255, 0.2);
}

.tpl-preview {
  height: 140px;
  padding: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-mockup {
  width: 100%;
  height: 100%;
  background: rgba(255,255,255,0.9);
  border-radius: 6px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.mock-title {
  width: 60%; height: 12px;
  background: rgba(0,0,0,0.15);
  border-radius: 2px;
}
.mock-bar {
  width: 100%; height: 8px;
  background: rgba(255,255,255,0.7);
  border-radius: 2px;
  margin-top: 4px;
}
.mock-content {
  display: flex; gap: 5px; flex: 1; margin-top: 6px;
}
.mock-card {
  flex: 1; background: rgba(0,0,0,0.08); border-radius: 3px;
}

.tpl-info {
  padding: 12px 14px;
}

.tpl-info h4 {
  font-size: 15px; margin: 0 0 4px; color: #303133;
}
.tpl-info p {
  font-size: 12px; margin: 0; color: #909399; line-height: 1.4;
}

.selected-badge {
  position: absolute; top: 10px; right: 10px;
  width: 26px; height: 26px;
  background: #409eff; color: white;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-weight: bold; font-size: 14px;
}

/* 格式选择 */
.format-section {
  margin-bottom: 24px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 10px;
}

/* 大纲摘要 */
.summary-outline .summary-section {
  margin-bottom: 24px;
}

.outline-summary {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
}

.summary-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px;
  background: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
}

.page-count {
  font-size: 13px; color: #909399;
}

.summary-slides {
  max-height: 240px;
  overflow-y: auto;
}

.summary-slide-item {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 16px;
  border-bottom: 1px solid #f5f5f5;
  font-size: 13px;
}

.ss-num {
  width: 22px; height: 22px;
  line-height: 22px; text-align: center;
  background: #f0f0f0; border-radius: 50%;
  font-size: 11px; font-weight: 600;
  color: #666; flex-shrink: 0;
}

.ss-type { font-size: 14px; }
.ss-title { flex: 1; color: #303133; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ss-bullets { color: #909399; font-size: 12px; flex-shrink: 0; }

/* 渲染进度 */
.progress-overlay {
  position: fixed; inset: 0;
  background: rgba(255,255,255,0.9);
  backdrop-filter: blur(4px);
  z-index: 200;
  display: flex; align-items: center; justify-content: center;
}

.progress-box {
  text-align: center;
  padding: 36px 48px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 12px 48px rgba(0,0,0,0.12);
  min-width: 320px;
}

.status-text {
  margin-top: 14px; color: #606266; font-size: 14px;
}

/* 结果区域 */
.result-section {
  margin-top: 20px;
  padding: 20px;
  background: #f0f9eb;
  border-radius: 10px;
  border: 1px solid #e1f3d8;
}

.result-hint {
  margin-top: 12px;
  padding: 10px 16px;
  background: #f4f4f5;
  border-radius: 8px;
  font-size: 13px;
  color: #909399;
}

.result-hint p {
  margin: 0;
}

@media (max-width: 700px) {
  .template-cards {
    grid-template-columns: 1fr;
  }
}
</style>
