<template>
  <div class="step2-container">
    <!-- 工具栏 -->
    <div class="editor-toolbar">
      <div class="toolbar-left">
        <span class="slide-count">共 {{ slides.length }} 页</span>
        <el-button size="small" type="primary" plain @click="$emit('add-slide')">
          + 添加页面
        </el-button>
      </div>
      <div class="toolbar-right">
        <el-tag size="small" type="info">点击页面可编辑</el-tag>
      </div>
    </div>

    <!-- 编辑区：左侧缩略图 + 右侧详情 -->
    <div class="editor-main" v-if="slides.length > 0">
      <!-- 左侧：页面列表 -->
      <div class="page-list">
        <div
          v-for="(slide, index) in slides"
          :key="index"
          class="page-item"
          :class="{ active: selectedIndex === index }"
          @click="selectedIndex = index"
        >
          <span class="page-num">{{ index + 1 }}</span>
          <span class="page-title">{{ slide.title || '(未命名)' }}</span>
          <span class="page-type" :class="'type-' + slide.layout">
            {{ layoutLabels[slide.layout] || slide.layout }}
          </span>
          <div class="page-actions">
            <button @click.stop="$emit('move-up', index)" :disabled="index === 0" title="上移">↑</button>
            <button @click.stop="$emit('move-down', index)" :disabled="index === slides.length - 1" title="下移">↓</button>
            <button @click.stop="$emit('remove', index)" title="删除" class="btn-danger">×</button>
          </div>
        </div>
      </div>

      <!-- 右侧：编辑详情 -->
      <div class="edit-detail">
        <template v-if="currentSlide">
          <!-- 页面类型选择 -->
          <div class="edit-field">
            <label>页面类型 <el-tag size="small" type="info" style="margin-left:6px;">共10种布局</el-tag></label>
            <div class="layout-grid">
              <div
                v-for="opt in layoutOptions"
                :key="opt.value"
                class="layout-option"
                :class="{ active: currentSlide.layout === opt.value }"
                @click="currentSlide.layout = opt.value"
              >
                <span class="lo-icon">{{ opt.icon }}</span>
                <span class="lo-label">{{ opt.label }}</span>
              </div>
            </div>
            <div class="layout-hint" v-if="currentLayoutMeta">
              {{ currentLayoutMeta.hint }}
            </div>
          </div>

          <!-- 标题编辑 -->
          <div class="edit-field">
            <label>标题</label>
            <el-input v-model="currentSlide.title" placeholder="页面标题" />
          </div>

          <!-- 副标题（仅封面） -->
          <div class="edit-field" v-if="currentSlide.layout === 'title'">
            <label>副标题</label>
            <el-input v-model="currentSlide.subtitle" placeholder="可选的副标题" />
          </div>

          <!-- 要点列表（需要bullet_points的layout类型） -->
          <div class="edit-field" v-if="needsBullets">
            <label>要点列表</label>
            <div class="bullets-list">
              <div
                v-for="(bullet, bIdx) in currentSlide.bullet_points"
                :key="bIdx"
                class="bullet-row"
              >
                <span class="bullet-handle">⠿</span>
                <el-input
                  :model-value="bullet"
                  @update:modelValue="updateBullet(bIdx, $event)"
                  size="small"
                  placeholder="输入要点内容..."
                />
                <button class="btn-remove" @click="removeBullet(bIdx)" title="删除">×</button>
              </div>
            </div>

            <el-button
              size="small"
              plain
              style="margin-top: 8px;"
              @click="addBullet()"
            >
              + 添加要点
            </el-button>
          </div>

          <!-- 视觉建议 -->
          <div class="edit-field">
            <label>视觉建议（给AI的提示）</label>
            <el-input 
              v-model="currentSlide.visual_suggestion" 
              type="textarea"
              :rows="2"
              placeholder="例如：使用卡片式布局、添加流程图等"
            />
          </div>
        </template>

        <div v-else class="no-selection">
          <p>← 选择左侧页面进行编辑</p>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-state">
      <p>没有可编辑的大纲数据</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  outline: {
    type: Object,
    default: () => null,
  },
})

const emit = defineEmits(['add-slide', 'remove', 'move-up', 'move-down'])

const selectedIndex = ref(0)

const slides = computed(() => props.outline?.slides || [])

const currentSlide = computed(() => {
  if (!props.outline?.slides) return null
  return props.outline.slides[selectedIndex.value] || null
})

const layoutLabels = {
  title: '封面',
  section: '章节',
  content: '内容',
  summary: '总结',
  chart: '图表',
  comparison: '对比',
  timeline: '时间线',
  quote: '引用',
  two_column: '双栏',
  cards_grid: '卡片网格',
}

const layoutOptions = [
  { value: 'title', icon: '📄', label: '封面', hint: '大标题+副标题，用于PPT首页' },
  { value: 'section', icon: '📑', label: '章节', hint: '章节分隔页，简洁醒目的大标题' },
  { value: 'content', icon: '📋', label: '内容', hint: '标准内容页，标题+3-5条详细要点列表（最常用）' },
  { value: 'summary', icon: '✅', label: '总结', hint: '总结回顾页，核心要点提炼+展望' },
  { value: 'chart', icon: '📊', label: '图表', hint: '数据展示页，配合柱状图/饼图/趋势图等可视化组件' },
  { value: 'comparison', icon: '⚖️', label: '对比', hint: '对比分析页，左右双栏或多维度对比展示' },
  { value: 'timeline', icon: '⏱️', label: '时间线', hint: '流程/时间轴页，步骤或阶段按顺序排列' },
  { value: 'quote', icon: '💬', label: '引用', hint: '金句/引用页，突出显示核心观点或名言' },
  { value: 'two_column', icon: '📑', label: '双栏', hint: '双栏图文页，左右分栏展示两个相关侧面' },
  { value: 'cards_grid', icon: '🃏', label: '卡片', hint: '卡片网格页，多个并列卡片展示并列要点' },
]

const currentLayoutMeta = computed(() => {
  if (!currentSlide.value) return null
  return layoutOptions.find(o => o.value === currentSlide.value.layout) || null
})

// 需要编辑 bullet_points 的 layout 类型
const BULLET_LAYOUTS = ['content', 'summary', 'chart', 'comparison', 'timeline', 'quote', 'two_column', 'cards_grid']
const needsBullets = computed(() => {
  return currentSlide.value ? BULLET_LAYOUTS.includes(currentSlide.value.layout) : false
})

function updateBullet(index, val) {
  if (currentSlide.value?.bullet_points) {
    currentSlide.value.bullet_points[index] = val
  }
}

function removeBullet(index) {
  if (currentSlide.value?.bullet_points) {
    currentSlide.value.bullet_points.splice(index, 1)
  }
}

function addBullet() {
  if (currentSlide.value) {
    if (!currentSlide.value.bullet_points) {
      currentSlide.value.bullet_points = []
    }
    currentSlide.value.bullet_points.push('新要点')
  }
}
</script>

<style scoped>
.step2-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* 工具栏 */
.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  background: #f8f9fa;
  border-bottom: 1px solid #ebeef5;
  border-radius: 8px 8px 0 0;
}

.slide-count {
  font-size: 13px;
  color: #909399;
  margin-right: 12px;
}

/* 主编辑区 */
.editor-main {
  display: flex;
  flex: 1;
  border: 1px solid #e4e7ed;
  border-top: none;
  border-radius: 0 0 8px 8px;
  overflow: hidden;
  min-height: 400px;
}

/* 左侧页面列表 */
.page-list {
  width: 260px;
  min-width: 220px;
  background: #fafbfc;
  overflow-y: auto;
  border-right: 1px solid #e4e7ed;
}

.page-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 12px;
  cursor: pointer;
  border-left: 3px solid transparent;
  transition: all 0.15s;
  border-bottom: 1px solid #f0f0f0;
}

.page-item:hover {
  background: #ecf5ff;
}

.page-item.active {
  background: #d9ecff;
  border-left-color: #409eff;
}

.page-num {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  line-height: 22px;
  text-align: center;
  border-radius: 50%;
  background: #e4e7ed;
  font-size: 11px;
  color: #606266;
  font-weight: 600;
}

.page-item.active .page-num {
  background: #409eff;
  color: white;
}

.page-title {
  flex: 1;
  font-size: 13px;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.page-type {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 3px;
  background: #f0f0f0;
  color: #888;
}

.type-title { background: #fdf6ec; color: #e6a23c; }
.type-section { background: #fef0f0; color: #f56c6c; }
.type-content { background: #ecf5ff; color: #409eff; }
.type-summary { background: #f0f9eb; color: #67c23a; }
.type-chart { background: #f3e8ff; color: #9b59b6; }
.type-comparison { background: #fef5e7; color: #e67e22; }
.type-timeline { background: #e8f8f5; color: #1abc9c; }
.type-quote { background: #f0f3f5; color: #34495e; }
.type-two_column { background: #eaf2f8; color: #2980b9; }
.type-cards_grid { background: #f5eef8; color: #8e44ad; }

/* Layout 选择器网格 */
.layout-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 6px;
}

.layout-option {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: 1.5px solid #e4e7ed;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  color: #606266;
  transition: all 0.15s ease;
  background: white;
}

.layout-option:hover {
  border-color: #409eff;
  background: #ecf5ff;
}

.layout-option.active {
  border-color: #409eff;
  background: #409eff;
  color: white;
}

.lo-icon {
  font-size: 14px;
}

.lo-label {
  font-size: 12px;
  font-weight: 500;
}

.layout-hint {
  margin-top: 6px;
  padding: 8px 12px;
  background: #f0f9ff;
  border-left: 3px solid #409eff;
  border-radius: 0 6px 6px 0;
  font-size: 12px;
  color: #409eff;
  line-height: 1.5;
}

.page-actions {
  opacity: 0;
  transition: opacity 0.2s;
  display: flex;
  gap: 2px;
}

.page-item:hover .page-actions {
  opacity: 1;
}

.page-actions button {
  width: 20px; height: 20px;
  border: none; border-radius: 3px;
  background: transparent;
  cursor: pointer;
  font-size: 12px;
  color: #999;
  transition: all 0.15s;
}
.page-actions button:hover:not(:disabled) {
  background: #409eff; color: white;
}
.page-actions button:disabled {
  opacity: 0.3; cursor: not-allowed;
}
.btn-danger:hover {
  background: #f56c6c !important; color: white !important;
}

/* 右侧编辑详情 */
.edit-detail {
  flex: 1;
  padding: 20px 24px;
  overflow-y: auto;
  background: white;
}

.edit-field {
  margin-bottom: 18px;
}

.edit-field label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #606266;
  margin-bottom: 6px;
}

/* 要点行样式 */
.bullet-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.bullet-handle {
  cursor: grab;
  color: #bfbfbf;
  font-size: 14px;
  user-select: none;
}

.bullet-row .el-input {
  flex: 1;
}

.btn-remove {
  width: 24px; height: 24px;
  border: 1px solid #fbc4c4;
  border-radius: 50%;
  background: #fef0f0;
  color: #f56c6c;
  cursor: pointer;
  font-size: 14px;
  line-height: 22px;
  text-align: center;
  transition: all 0.15s;
}
.btn-remove:hover {
  background: #f56c6c; color: white;
  border-color: #f56c6c;
}

.no-selection {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #c0c4cc;
  font-size: 14px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: #c0c4cc;
  border: 2px dashed #e4e7ed;
  border-radius: 8px;
}
</style>
