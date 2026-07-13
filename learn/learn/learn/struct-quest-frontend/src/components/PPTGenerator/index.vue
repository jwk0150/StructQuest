<template>
  <el-dialog
    v-model="dialogVisible"
    title="🎯 AI PPT 智能生成器"
    width="920px"
    :close-on-click-modal="false"
    :close-on-press-escape="!renderProgress.generating"
    :show-close="!renderProgress.generating"
    class="ppt-generator-dialog"
    destroy-on-close
    @closed="onClosed"
  >
    <!-- 步骤指示器 -->
    <div class="steps-indicator">
      <div
        v-for="(step, i) in stepLabels"
        :key="i"
        class="step-item"
        :class="{ 
          active: currentStep === i, 
          done: currentStep > i,
          clickable: currentStep > i || (i === 1 && outlineData)
        }"
        @click="goToStep(i)"
      >
        <div class="step-circle">
          <span v-if="currentStep > i">✓</span>
          <span v-else>{{ i + 1 }}</span>
        </div>
        <span class="step-text">
          <strong>{{ step.title }}</strong>
          <small>{{ step.desc }}</small>
        </span>
      </div>
      <!-- 连接线 -->
      <div class="step-line" v-for="i in 2" :key="'line-' + i" :class="{ active: currentStep > i - 1 }"></div>
    </div>

    <!-- 错误提示 -->
    <el-alert
      v-if="errorMessage"
      :title="errorMessage"
      type="error"
      show-icon
      closable
      @close="errorMessage = ''"
      style="margin-bottom: 16px;"
    />

    <!-- 步骤内容区 -->
    <div class="steps-content" v-loading="loading" element-loading-text="AI正在生成大纲...">

      <!-- Step 1: 输入源选择 -->
      <div v-show="currentStep === 0" class="step-content step1-content">
        <Step1Input
          :input-data="inputData"
          @update:inputData="inputData = $event"
        />
      </div>

      <!-- Step 2: 大纲编辑 -->
      <div v-show="currentStep === 1" class="step-content step2-content">
        <Step2Editor
          v-if="editedOutline"
          :outline="editedOutline"
          @add-slide="addSlide"
          @remove="removeSlide"
          @move-up="moveSlideUp"
          @move-down="moveSlideDown"
        />
        <div v-else class="empty-outline-hint">
          <p>⚠️ 请先完成第一步，生成初始大纲</p>
        </div>
      </div>

      <!-- Step 3: 模板 + 渲染 -->
      <div v-show="currentStep === 2" class="step-content step3-content">
        <Step3Render
          v-if="editedOutline"
          :render-config="renderConfig"
          :outline="editedOutline"
          :render-progress="renderProgress"
          :render-result="renderResult"
          :templates-list="renderConfig.templatesList"
          @update:render-config="updateRenderConfig"
          @open-preview="openPreview"
          @download="downloadFile"
          @back-to-edit="prevStep"
        />
      </div>

    </div>

    <!-- 底部操作栏 -->
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="close" :disabled="renderProgress.generating">取消</el-button>
        
        <el-button 
          v-if="currentStep > 0" 
          @click="prevStep"
          :disabled="renderProgress.generating"
        >
          ← 上一步
        </el-button>

        <el-button
          v-if="currentStep < totalSteps - 1"
          type="primary"
          @click="nextStep"
          :loading="loading && currentStep === 0"
          :disabled="!canGoNext || renderProgress.generating"
        >
          {{ currentStep === 0 ? '✨ 生成大纲' : '下一步 →' }}
        </el-button>

        <el-button
          v-if="currentStep === totalSteps - 1 && !renderResult"
          type="primary"
          size="large"
          @click="handleRender"
          :loading="loading"
          :disabled="renderProgress.generating"
        >
          🎨 开始渲染 PPT
        </el-button>

        <el-button
          v-if="currentStep === totalSteps - 1 && renderResult"
          type="success"
          size="large"
          @click="close; openPreview()"
        >
          ✓ 完成，预览 PPT
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { watch } from 'vue'
import { usePPTGenerator } from '@/composables/usePPTGenerator'
import Step1Input from './Step1Input.vue'
import Step2Editor from './Step2Editor.vue'
import Step3Render from './Step3Render.vue'

const {
  // 状态
  currentStep,
  dialogVisible,
  loading,
  renderProgress,
  inputData,
  outlineData,
  editedOutline,
  renderConfig,
  renderResult,
  errorMessage,

  // 计算属性
  totalSteps,
  canGoNext,
  canGoPrev,
  stepLabels,

  // 方法
  open,
  close,
  nextStep,
  prevStep,
  goToStep,
  generateOutline,
  renderPPT,
  openPreview,
  downloadFile,

  // 编辑器
  addSlide,
  removeSlide,
  moveSlideUp,
  moveSlideDown,
} = usePPTGenerator()

// 暴露 open 方法供外部调用
defineExpose({ open })

function updateRenderConfig(val) {
  Object.assign(renderConfig, val)
}

function handleRender() {
  renderPPT()
}

function onClosed() {
  // 对话框关闭后的清理（可选）
}
</script>

<style scoped>
/* ── 对话框整体样式 ── */
.ppt-generator-dialog :deep(.el-dialog__header) {
  padding: 18px 24px;
  border-bottom: 1px solid #ebeef5;
}

.ppt-generator-dialog :deep(.el-dialog__title) {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.ppt-generator-dialog :deep(.el-dialog__body) {
  padding: 20px 24px;
  max-height: 70vh;
  overflow-y: auto;
}

.ppt-generator-dialog :deep(.el-dialog__footer) {
  padding: 14px 24px;
  border-top: 1px solid #ebeef5;
}

/* ── 步骤指示器 ── */
.steps-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
  padding: 16px 0;
}

.step-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  z-index: 1;
  cursor: default;
  opacity: 0.45;
  transition: all 0.35s ease;
  min-width: 100px;
}

.step-item.active {
  opacity: 1;
}

.step-item.done {
  opacity: 0.8;
}

.step-item.clickable:not(.active):not(:hover) {
  cursor: pointer;
}
.step-item.clickable:hover {
  opacity: 0.9;
}

.step-circle {
  width: 36px; height: 36px;
  border-radius: 50%;
  background: #e4e7ed;
  color: #909399;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  transition: all 0.3s;
  margin-bottom: 6px;
}

.step-item.active .step-circle {
  background: linear-gradient(135deg, #409eff, #337ecc);
  color: white;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
  transform: scale(1.08);
}

.step-item.done .step-circle {
  background: #67c23a;
  color: white;
}

.step-text {
  text-align: center;
  line-height: 1.3;
}

.step-text strong {
  font-size: 13px;
  color: #303133;
  display: block;
}

.step-text small {
  font-size: 11px;
  color: #909399;
  display: block;
}

.step-item.active .step-text strong { color: #409eff; }

.step-line {
  width: 60px;
  height: 3px;
  background: #e4e7ed;
  border-radius: 2px;
  margin: 0 10px;
  margin-bottom: 28px;
  transition: background 0.3s;
}

.step-line.active {
  background: #67c23a;
}

/* ── 步骤内容 ── */
.steps-content {
  min-height: 380px;
  position: relative;
}

.step-content {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.empty-outline-hint {
  text-align: center;
  padding: 80px 0;
  color: #c0c4cc;
  font-size: 15px;
}

/* ── 底部操作栏 ── */
.dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dialog-footer .el-button + .el-button {
  margin-left: 8px;
}
</style>
