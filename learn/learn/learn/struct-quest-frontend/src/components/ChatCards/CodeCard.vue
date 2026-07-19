<template>
  <div class="code-card">
    <!-- 语言标签 -->
    <div class="code-header">
      <span class="lang-tag">{{ langLabel }}</span>
      <div class="code-actions">
        <el-button link size="small" @click="toggleExplain" v-if="hasExplanations">
          {{ showExplain ? '收起解释' : '逐行解释' }}
        </el-button>
        <el-button link size="small" @click="copyCode">
          <el-icon><CopyDocument /></el-icon> 复制
        </el-button>
      </div>
    </div>

    <!-- 代码块（highlight.js 渲染） -->
    <pre class="code-block" :class="{ 'with-explain': showExplain }"><code ref="codeEl" v-html="highlightedCode"></code></pre>

    <!-- 逐行解释 -->
    <div v-if="showExplain && hasExplanations" class="line-explanations">
      <div
        v-for="(exp, lineNum) in data.line_explanations"
        :key="lineNum"
        class="exp-item"
      >
        <span class="exp-line-num">第{{ lineNum }}行</span>
        <span class="exp-text">{{ exp }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { CopyDocument } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import hljs from 'highlight.js'

const props = defineProps({
  data: { type: Object, default: () => ({}) },
})

const showExplain = ref(false)
const codeEl = ref(null)

const langLabel = computed(() => {
  const lang = props.data.language || 'python'
  const map = { python: 'Python', javascript: 'JS', java: 'Java', cpp: 'C++', c: 'C', go: 'Go', rust: 'Rust' }
  return map[lang] || lang
})

const hasExplanations = computed(() => {
  const exp = props.data.line_explanations || {}
  return Object.keys(exp).length > 0
})

const highlightedCode = computed(() => {
  const code = props.data.code || ''
  if (!code) return ''
  const lang = props.data.language || 'python'
  try {
    const result = hljs.highlight(code, { language: lang, ignoreIllegals: true })
    return result.value
  } catch {
    return hljs.highlightAuto(code).value
  }
})

function toggleExplain() {
  showExplain.value = !showExplain.value
}

function copyCode() {
  navigator.clipboard.writeText(props.data.code || '').then(() => {
    ElMessage.success('代码已复制到剪贴板')
  })
}
</script>

<style scoped>
.code-card {
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 14px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.lang-tag {
  font-size: 12px;
  font-weight: 600;
  color: #c84c5a;
  background: #fbf0f1;
  padding: 2px 10px;
  border-radius: 4px;
}

.code-actions {
  display: flex;
  gap: 4px;
}

.code-block {
  margin: 0;
  padding: 14px;
  background: #f0f1f3;
  color: #1f2937;
  font-size: 13px;
  line-height: 1.6;
  overflow-x: auto;
  white-space: pre;
}
.code-block :deep(.hljs-keyword) { color: #7c3aed; }
.code-block :deep(.hljs-string)  { color: #0f766e; }
.code-block :deep(.hljs-comment) { color: #64748b; font-style: italic; }
.code-block :deep(.hljs-number)  { color: #b45309; }
.code-block :deep(.hljs-function) { color: #2563eb; }
.code-block :deep(.hljs-built_in) { color: #be185d; }

.line-explanations {
  background: #f8fafc;
  border-top: 1px solid #e5e7eb;
  padding: 10px 14px;
}

.exp-item {
  display: flex;
  gap: 10px;
  padding: 4px 0;
  font-size: 13px;
}
.exp-line-num {
  flex-shrink: 0;
  color: #c84c5a;
  font-weight: 600;
  min-width: 50px;
}
.exp-text {
  color: #475569;
}
</style>




