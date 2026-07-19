<template>
  <div class="debug-card">
    <!-- 错误描述 -->
    <div v-if="data.error_description" class="debug-section">
      <div class="debug-label">🐛 错误信息</div>
      <pre class="debug-error">{{ data.error_description }}</pre>
    </div>

    <!-- 根因分析 -->
    <div v-if="data.root_cause" class="debug-section">
      <div class="debug-label">🔍 错误原因</div>
      <div class="debug-text">{{ data.root_cause }}</div>
    </div>

    <!-- 原始代码 vs 修复代码 -->
    <div v-if="data.original_code && data.fix_code" class="debug-diff">
      <div class="debug-label">⚡ 修复对比</div>
      <div class="diff-container">
        <div class="diff-pane">
          <div class="diff-pane-header wrong">❌ 修改前</div>
          <pre class="diff-code wrong-code">{{ data.original_code }}</pre>
        </div>
        <div class="diff-pane">
          <div class="diff-pane-header correct">✅ 修改后</div>
          <pre class="diff-code correct-code">{{ data.fix_code }}</pre>
        </div>
      </div>
    </div>

    <!-- 单个修复代码 -->
    <div v-else-if="data.fix_code" class="debug-section">
      <div class="debug-label">✅ 修复代码</div>
      <pre class="fix-code">{{ data.fix_code }}</pre>
      <el-button link size="small" @click="copyFix" style="margin-top:4px">
        <el-icon><CopyDocument /></el-icon> 复制修复代码
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { CopyDocument } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  data: { type: Object, default: () => ({}) },
})

function copyFix() {
  navigator.clipboard.writeText(props.data.fix_code || '').then(() => {
    ElMessage.success('已复制')
  })
}
</script>

<style scoped>
.debug-card {
  font-size: 14px;
}

.debug-section {
  margin-bottom: 12px;
}

.debug-label {
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 6px;
  font-size: 13px;
}

.debug-error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
  padding: 10px;
  font-size: 13px;
  color: #991b1b;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
}

.debug-text {
  color: #475569;
  line-height: 1.7;
}

.diff-container {
  display: flex;
  gap: 10px;
}
.diff-pane {
  flex: 1;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
}
.diff-pane-header {
  padding: 6px 10px;
  font-size: 12px;
  font-weight: 700;
}
.diff-pane-header.wrong { background: #fef2f2; color: #991b1b; }
.diff-pane-header.correct { background: #ecfdf5; color: #065f46; }

.diff-code {
  margin: 0;
  padding: 10px;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
}
.wrong-code { background: #fff5f5; color: #991b1b; }
.correct-code { background: #f0fdf4; color: #065f46; }

.fix-code {
  background: #1e293b;
  color: #e2e8f0;
  padding: 12px;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.5;
  overflow-x: auto;
  margin: 0;
}
</style>
