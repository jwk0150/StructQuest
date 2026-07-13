<template>
  <div class="step1-container">
    <!-- 输入源选择 -->
    <div class="source-selector">
      <h3>选择输入来源</h3>
      <p class="sub-hint">PPT内容的数据来源</p>

      <div class="source-cards">
        <!-- 选项1: 使用已有思维导图 -->
        <div
          class="source-card"
          :class="{ active: inputData.source === 'existing', disabled: !inputData.mindmapAvailable }"
          @click="selectSource('existing')"
        >
          <div class="card-icon">🗺️</div>
          <h4>使用当前思维导图</h4>
          <p>从本节点的思维导图中提取内容</p>
          <span v-if="inputData.mindmapAvailable" class="status-badge ok">可用</span>
          <span v-else class="status-badge none">无思维导图</span>
        </div>

        <!-- 选项2: 粘贴Markdown -->
        <div
          class="source-card"
          :class="{ active: inputData.source === 'markdown' }"
          @click="selectSource('markdown')"
        >
          <div class="card-icon">📝</div>
          <h4>粘贴 Markdown 文本</h4>
          <p>支持层级标题、列表等格式</p>
          <span class="status-badge">手动输入</span>
        </div>

        <!-- 选项3: 粘贴JSON -->
        <div
          class="source-card"
          :class="{ active: inputData.source === 'mindmap' || inputData.source === 'json' }"
          @click="selectSource('json')"
        >
          <div class="card-icon">{ }</div>
          <h4>粘贴思维导图 JSON</h4>
          <p>标准树形结构 JSON 数据</p>
          <span class="status-badge">手动输入</span>
        </div>
      </div>
    </div>

    <!-- 内容输入区（当不是 existing 模式时显示） -->
    <div v-if="inputData.source !== 'existing'" class="content-input-area">
      <label>输入内容：</label>
      <el-input
        v-model="inputData.content"
        type="textarea"
        :rows="8"
        :placeholder="textareaPlaceholder"
        resize="vertical"
      />
    </div>

    <!-- 页数设置 -->
    <div class="pages-setting">
      <label>目标页数：</label>
      <el-slider
        v-model="inputData.targetPages"
        :min="5"
        :max="25"
        :step="1"
        show-input
        :show-input-controls="false"
        input-size="small"
      />
      <span class="pages-hint">建议 8-15 页，包含封面和结尾</span>
    </div>

    <!-- 预览已有思维导图的内容 -->
    <div v-if="inputData.source === 'existing' && inputData.existingMindmap" class="mindmap-preview">
      <div class="preview-header">
        <span>📊 思维导图预览</span>
        <el-tag size="small" type="success">将用于生成大纲</el-tag>
      </div>
      <div class="preview-content">
        {{ getMindmapPreviewText() }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, toRefs } from 'vue'

const props = defineProps({
  inputData: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['update:inputData'])

const { inputData } = toRefs(props)

const textareaPlaceholder = computed(() => {
  const placeholders = {
    markdown: `# 标题

## 第一章 概述
- 要点1
- 要点2

## 第二章 详细内容
- 核心概念A
- 核心概念B`,
    json: `{
  "name": "主题",
  "children": [
    {
      "name": "章节一",
      "children": [
        {"name": "要点1"},
        {"name": "要点2"}
      ]
    }
  ]
}`,
    raw_text: `请粘贴你的文本内容...`,
  }
  return placeholders[props.inputData.source] || placeholders.markdown
})

function selectSource(source) {
  // 如果选择existing但不可用，阻止切换
  if (source === 'existing' && !inputData.value.mindmapAvailable) {
    return
  }
  
  emit('update:inputData', { ...inputData.value, source })
}

function getMindmapPreviewText() {
  try {
    const data = typeof props.inputData.existingMindmap === 'string'
      ? JSON.parse(props.inputData.existingMindmap)
      : props.inputData.existingMindmap
    
    if (!data) return '(空数据)'
    
    return JSON.stringify(data).substring(0, 500) + 
      (JSON.stringify(data).length > 500 ? '\n...(更多内容)' : '')
  } catch {
    return String(props.inputData.existingMindmap || '').substring(0, 300)
  }
}
</script>

<style scoped>
.step1-container {
  padding: 8px 0;
}

/* 来源选择卡片 */
.source-selector h3 {
  margin: 0 0 6px;
  font-size: 16px;
  color: #303133;
}

.sub-hint {
  color: #909399;
  font-size: 13px;
  margin-bottom: 20px;
}

.source-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.source-card {
  padding: 20px 16px;
  border: 2px solid #e4e7ed;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.25s ease;
  text-align: center;
  background: #fafafa;
}

.source-card:hover:not(.disabled) {
  border-color: #409eff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.12);
  transform: translateY(-2px);
}

.source-card.active {
  border-color: #409eff;
  background: #ecf5ff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.18);
}

.source-card.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.card-icon {
  font-size: 32px;
  margin-bottom: 10px;
}

.source-card h4 {
  font-size: 14px;
  color: #303133;
  margin: 0 0 6px;
}

.source-card p {
  font-size: 12px;
  color: #909399;
  margin: 0 0 10px;
  line-height: 1.5;
}

.status-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 11px;
  background: #f0f0f0;
  color: #666;
}

.status-badge.ok {
  background: #f0f9eb;
  color: #67c23a;
}

.status-badge.none {
  background: #fef0f0;
  color: #f56c6c;
}

/* 内容输入 */
.content-input-area {
  margin-bottom: 24px;
}

.content-input-area label {
  display: block;
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
  font-weight: 500;
}

/* 页数设置 */
.pages-setting {
  margin-bottom: 24px;
  padding: 16px 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.pages-setting label {
  display: inline-block;
  font-size: 14px;
  color: #606266;
  min-width: 80px;
  vertical-align: middle;
}

.pages-setting .el-slider {
  display: inline-block;
  width: calc(100% - 200px);
  vertical-align: middle;
}

.pages-hint {
  display: block;
  font-size: 12px;
  color: #b0b0b0;
  margin-top: 6px;
  padding-left: 80px;
}

/* 思维导图预览 */
.mindmap-preview {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  background: #f5f7fa;
  font-size: 13px;
  font-weight: 500;
}

.preview-content {
  padding: 14px 16px;
  max-height: 180px;
  overflow-y: auto;
  font-family: 'Fira Code', Consolas, monospace;
  font-size: 12px;
  line-height: 1.7;
  color: #555;
  white-space: pre-wrap;
  word-break: break-all;
  background: white;
}

@media (max-width: 600px) {
  .source-cards {
    grid-template-columns: 1fr;
  }
}
</style>
