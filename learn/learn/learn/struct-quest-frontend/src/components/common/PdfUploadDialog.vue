<template>
  <el-dialog
    v-model="visible"
    title="上传文档"
    width="560px"
    :close-on-click-modal="false"
    :close-on-press-escape="!isUploading"
    :show-close="!isUploading"
    class="pdf-upload-dialog"
    @open="onDialogOpen"
    @closed="onDialogClosed"
  >
    <!-- 步骤条 -->
    <div class="steps-bar">
      <div class="step" :class="{ active: currentStep >= 1, done: currentStep > 1 }">
        <div class="step-num">1</div>
        <span>选择文件</span>
      </div>
      <div class="step-line" :class="{ active: currentStep > 1 }"></div>
      <div class="step" :class="{ active: currentStep >= 2, done: currentStep > 2 }">
        <div class="step-num">2</div>
        <span>处理中</span>
      </div>
      <div class="step-line" :class="{ active: currentStep > 2 }"></div>
      <div class="step" :class="{ active: currentStep >= 3 }">
        <div class="step-num">3</div>
        <span>完成</span>
      </div>
    </div>

    <!-- Step 1: 拖拽上传区域 -->
    <div v-if="currentStep === 1" class="upload-step">
      <el-upload
        ref="uploadRef"
        drag
        action="#"
        :auto-upload="false"
        :show-file-list="true"
        :on-change="handleFileChange"
        :on-remove="handleFileRemove"
        :file-list="selectedFiles"
        accept=".pdf,.pptx"
        :limit="1"
        :disabled="isUploading"
        class="pdf-drag-uploader"
      >
        <template v-if="!hasSelectedFile">
          <div class="upload-placeholder">
            <div class="upload-icon-wrap">
              <el-icon :size="48"><UploadFilled /></el-icon>
            </div>
            <p class="upload-text">
              将 PDF/PPTX 文件拖到此处，或<em>点击选择</em>
            </p>
            <p class="upload-hint">
              支持教材、讲义、论文等 PDF/PPTX 格式文件，最大支持 50MB
            </p>
          </div>
        </template>
      </el-upload>

      <!-- 已选文件信息 -->
      <div v-if="hasSelectedFile && selectedFileRaw" class="selected-file-info">
        <div class="file-preview-card">
          <div class="file-icon-box">
            <el-icon :size="32" color="#F56C6C"><Document /></el-icon>
          </div>
          <div class="file-detail">
            <h4 class="file-name">{{ selectedFileRaw.name }}</h4>
            <p class="file-meta">{{ formatFileSize(selectedFileRaw.size) }} · {{ formatFileType(selectedFileRaw.name) }}</p>
          </div>
          <el-button type="primary" size="default" @click="startUpload" :disabled="isUploading">
            <el-icon><Top /></el-icon>
            开始处理
          </el-button>
        </div>
      </div>
    </div>

    <!-- Step 2: 处理进度 -->
    <div v-if="currentStep === 2" class="process-step">
      <div class="processing-animation">
        <div class="processing-circle">
          <el-progress type="circle" :percentage="uploadProgress" color="#10A37F" :width="120" :stroke-width="8">
            <template #default>
              <span class="progress-label">{{ uploadProgress.toFixed(2) }}%</span>
            </template>
          </el-progress>
        </div>
      </div>
      <div class="processing-info">
        <h4>{{ processStatusText.title }}</h4>
        <p class="process-desc">{{ processStatusText.desc }}</p>
        <div class="process-steps-timeline">
          <div class="timeline-item" :class="{ done: uploadProgress >= 15 }">
            <div class="timeline-dot"></div>
            <span>读取 PDF 内容</span>
          </div>
          <div class="timeline-item" :class="{ done: uploadProgress >= 45 }">
            <div class="timeline-dot"></div>
            <span>智能文本切分</span>
          </div>
          <div class="timeline-item" :class="{ done: uploadProgress >= 75 }">
            <div class="timeline-dot"></div>
            <span>向量化嵌入</span>
          </div>
          <div class="timeline-item" :class="{ done: uploadProgress >= 95 }">
            <div class="timeline-dot"></div>
            <span>存入知识库</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Step 3: 完成结果 -->
    <div v-if="currentStep === 3" class="result-step">
      <div class="result-content" :class="{ success: uploadSuccess, error: !uploadSuccess }">
        <div class="result-icon-wrap">
          <el-icon v-if="uploadSuccess" :size="64" color="#10A37F"><CircleCheckFilled /></el-icon>
          <el-icon v-else :size="64" color="#F56C6C"><CircleCloseFilled /></el-icon>
        </div>
        <h4>{{ uploadSuccess ? '文档入库成功！' : '处理失败' }}</h4>
        <p v-if="uploadSuccess" class="result-summary">
          已将 <strong>{{ selectedFileName }}</strong> 切分为
          <strong style="color:#10A37F">{{ resultChunks }} 个</strong> 知识片段并成功存入向量数据库。
        </p>
        <p v-else class="result-error-msg">{{ resultError }}</p>
        
        <div v-if="uploadSuccess" class="result-stats-cards">
          <div class="stat-card">
            <div class="stat-value">{{ resultChunks }}</div>
            <div class="stat-label">知识切片</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ resultSize || '-' }}</div>
            <div class="stat-label">文件大小</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ resultDocId?.slice(0,8) || '-' }}</div>
            <div class="stat-label">文档ID</div>
          </div>
        </div>
      </div>
      
      <!-- 操作按钮 -->
      <div class="result-actions">
        <el-button v-if="uploadSuccess" type="primary" @click="uploadAnother">
          继续上传其他文档
        </el-button>
        <el-button v-else type="primary" @click="retryUpload">
          重试
        </el-button>
        <el-button @click="visible = false">关闭窗口</el-button>
      </div>
    </div>

    <!-- 底部按钮（仅 step1 显示） -->
    <template v-if="currentStep === 1" #footer>
      <el-button @click="visible = false">取消</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { getStorage, STORAGE_KEYS } from '../../utils/storage'
import {
  UploadFilled, Document, Top,
  CircleCheckFilled, CircleCloseFilled,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'success'])

// ===== 状态 =====
const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const currentStep = ref(1)
const isUploading = ref(false)
const uploadProgress = ref(0)
const uploadSuccess = ref(false)

const uploadRef = ref(null)
const selectedFiles = ref([])
const selectedFileRaw = ref(null)

// 结果数据
const resultChunks = ref(0)
const resultSize = ref('')
const resultDocId = ref('')
const resultError = ref('')

// ===== 计算属性 =====

const hasSelectedFile = computed(() => selectedFiles.value.length > 0)
const selectedFileName = computed(() => selectedFileRaw.value?.name || '')

const processStatusText = computed(() => {
  if (uploadProgress.value < 20) return { title: '正在读取 PDF 文件...', desc: '解析文档结构与文本内容' }
  if (uploadProgress.value < 50) return { title: '正在智能切分文本...', desc: '按语义边界拆分为可检索的知识片段' }
  if (uploadProgress.value < 80) return { title: '正在生成向量嵌入...', desc: '使用语义模型将文本转化为高维向量' }
  if (uploadProgress.value < 98) return { title: '正在写入向量数据库...', desc: '将向量与元数据持久化到 ChromaDB' }
  return { title: '即将完成...', desc: '最后整理与确认' }
})

// ===== 方法 =====

const getBaseUrl = () => {
  // 开发环境走 Vite 代理，不需要指定端口
  return ''
}

const formatFileSize = (bytes) => {
  if (!bytes) return '-'
  const kb = bytes / 1024
  if (kb < 1024) return `${kb.toFixed(1)} KB`
  return `${(kb / 1024).toFixed(1)} MB`
}

const formatFileType = (name) => name.split('.').pop().toUpperCase()

function onDialogOpen() {
  resetState()
}

function onDialogClosed() {
  resetState()
}

function resetState() {
  currentStep.value = 1
  isUploading.value = false
  uploadProgress.value = 0
  uploadSuccess.value = false
  selectedFiles.value = []
  selectedFileRaw.value = null
  resultChunks.value = 0
  resultSize.value = ''
  resultDocId.value = ''
  resultError.value = ''
}

function handleFileChange(uploadFile) {
  const file = uploadFile.raw
  if (!file) return
  
  // 校验文件类型
  const nameLower = file.name.toLowerCase()
  const isPdf = file.type === 'application/pdf' || nameLower.endsWith('.pdf')
  const isPptx = file.type === 'application/vnd.openxmlformats-officedocument.presentationml.presentation' || nameLower.endsWith('.pptx')
  if (!isPdf && !isPptx) {
    ElMessage.warning('仅支持 PDF 和 PPTX 格式文件')
    selectedFiles.value = []
    selectedFileRaw.value = null
    return
  }

  // 校验大小 (50MB)
  if (file.size > 50 * 1024 * 1024) {
    ElMessage.warning('文件大小不能超过 50MB')
    selectedFiles.value = []
    selectedFileRaw.value = null
    return
  }

  selectedFiles.value = [uploadFile]
  selectedFileRaw.value = file
}

function handleFileRemove() {
  selectedFiles.value = []
  selectedFileRaw.value = null
}

async function startUpload() {
  if (!selectedFileRaw.value) return

  isUploading.value = true
  currentStep.value = 2
  uploadProgress.value = 0
  uploadSuccess.value = false

  const formData = new FormData()
  formData.append('file', selectedFileRaw.value)

  // 模拟渐进式进度
  let progressInterval = null
  try {
    progressInterval = setInterval(() => {
      if (uploadProgress.value < 92) {
        uploadProgress.value += Math.random() * 8 + 2
        if (uploadProgress.value > 92) uploadProgress.value = 92
      }
    }, 400)

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 120000) // 120秒超时

    const token = getStorage(STORAGE_KEYS.TOKEN) || ''
    const response = await fetch(`${getBaseUrl()}/api/upload-pdf`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
      signal: controller.signal,
    })

    clearTimeout(timeoutId)
    clearInterval(progressInterval)
    progressInterval = null

    const data = await response.json()

    if (data.error || !response.ok) {
      throw new Error(data.detail || data.error || `服务器返回 ${response.status}`)
    }

    // 成功
    uploadProgress.value = 100
    uploadSuccess.value = true
    resultChunks.value = data.chunks || 0
    resultSize.value = formatFileSize(selectedFileRaw.value?.size)
    resultDocId.value = data.doc_id || ''

    setTimeout(() => {
      currentStep.value = 3
      emit('success', data)
    }, 600)

  } catch (error) {
    clearInterval(progressInterval)
    uploadSuccess.value = false
    
    let errorMsg = '网络错误或后端服务未启动'
    if (error.name === 'AbortError') {
      errorMsg = '处理超时（>120秒），可能是首次加载嵌入模型耗时较长或文件过大'
    } else if (error.message) {
      errorMsg = error.message
    }
    
    resultError.value = errorMsg

    setTimeout(() => {
      currentStep.value = 3
    }, 300)
  } finally {
    isUploading.value = false
  }
}

function retryUpload() {
  resetState()
  currentStep.value = 1
}

function uploadAnother() {
  resetState()
  currentStep.value = 1
}
</script>

<style lang="scss" scoped>
.pdf-upload-dialog {
  :deep(.el-dialog__header) {
    padding: 24px 28px 12px;
    border-bottom: 1px solid var(--border-light, #f0f0f0);

    .el-dialog__title {
      font-size: 20px;
      font-weight: 700;
      color: var(--text-main, #1a1a1a);
    }
  }

  :deep(.el-dialog__body) {
    padding: 20px 28px 16px;
  }

  :deep(.el-dialog__footer) {
    padding: 12px 28px 24px;
    border-top: none;
  }
}

/* ========== 步骤条 ========== */
.steps-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 28px;
  padding: 0 20px;

  .step {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;

    .step-num {
      width: 30px;
      height: 30px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 13px;
      font-weight: 700;
      background: #e8e8e8;
      color: #999;
      transition: all 0.3s ease;
    }

    span {
      font-size: 12px;
      color: #999;
      transition: color 0.3s;
    }

    &.active .step-num {
      background: #10A37F;
      color: white;
      box-shadow: 0 2px 8px rgba(16, 163, 127, 0.35);
    }

    &.active span {
      color: var(--text-main, #333);
      font-weight: 500;
    }

    &.done .step-num {
      background: #10A37F;
      position: relative;

      &::after {
        content: '\2713';
        position: absolute;
        color: white;
        font-size: 14px;
        line-height: 30px;
        text-align: center;
        left: 0; right: 0;
      }
    }
  }

  .step-line {
    width: 48px;
    height: 2.5px;
    background: #e8e8e8;
    border-radius: 2px;
    margin-bottom: 22px;
    transition: background 0.3s;

    &.active {
      background: #10A37F;
    }
  }
}

/* ========== Step 1: 上传区域 ========== */
.upload-step {
  min-height: 220px;

  .pdf-drag-uploader {
    :deep(.el-upload) {
      width: 100%;

      .el-upload-dragger {
        width: 100%;
        background-color: #fafbfc;
        border: 2px dashed #dcdfe6;
        border-radius: 16px;
        padding: 40px 20px;
        transition: all 0.3s ease;

        &:hover {
          border-color: #10A37F;
          background: rgba(16, 163, 127, 0.03);
        }
      }
    }
  }

  .upload-placeholder {
    text-align: center;

    .upload-icon-wrap {
      margin-bottom: 14px;
      color: #10A37F;
      opacity: 0.85;
    }

    .upload-text {
      font-size: 16px;
      color: var(--text-main, #303133);
      margin-bottom: 8px;

      em {
        color: #10A37F;
        font-style: normal;
        font-weight: 600;
        text-decoration: underline;
        cursor: pointer;
      }
    }

    .upload-hint {
      font-size: 13px;
      color: var(--text-tertiary, #909399);
    }
  }

  /* 已选文件卡片 */
  .selected-file-info {
    margin-top: 16px;
  }

  .file-preview-card {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px 20px;
    background: white;
    border: 1px solid #e8e8e8;
    border-radius: 14px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    transition: box-shadow 0.2s;

    &:hover {
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
    }

    .file-icon-box {
      width: 52px;
      height: 52px;
      background: rgba(245, 108, 108, 0.08);
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }

    .file-detail {
      flex: 1;
      min-width: 0;

      .file-name {
        margin: 0 0 4px 0;
        font-size: 15px;
        font-weight: 600;
        color: var(--text-main);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .file-meta {
        margin: 0;
        font-size: 13px;
        color: var(--text-tertiary);
      }
    }
  }
}

/* ========== Step 2: 处理进度 ========== */
.process-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 0;

  .processing-animation {
    margin-bottom: 24px;

    .processing-circle {
      animation: pulse-glow 2s ease-in-out infinite;
    }
  }

  .processing-info {
    text-align: center;
    width: 100%;
    max-width: 380px;

    h4 {
      font-size: 17px;
      color: var(--text-main);
      margin: 0 0 6px 0;
    }

    .process-desc {
      font-size: 13px;
      color: var(--text-tertiary);
      margin: 0 0 20px 0;
    }
  }

  .process-steps-timeline {
    display: flex;
    justify-content: space-between;
    gap: 8px;

    .timeline-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      opacity: 0.35;
      transition: all 0.4s ease;

      &.done {
        opacity: 1;
      }

      .timeline-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #dcdfe6;
        transition: all 0.3s;
      }

      &.done .timeline-dot {
        background: #10A37F;
        box-shadow: 0 0 8px rgba(16, 163, 127, 0.4);
      }

      span {
        font-size: 11px;
        color: var(--text-secondary);
        white-space: nowrap;
      }
    }
  }
}

/* ========== Step 3: 结果展示 ========== */
.result-step {
  .result-content {
    text-align: center;
    padding: 24px 0 16px;

    h4 {
      font-size: 19px;
      margin: 16px 0 8px;
    }

    .result-summary {
      font-size: 14px;
      color: var(--text-secondary);
      line-height: 1.7;
      max-width: 400px;
      margin: 0 auto 20px;
    }

    .result-error-msg {
      font-size: 14px;
      color: #F56C6C;
      background: rgba(245, 108, 108, 0.06);
      padding: 12px 20px;
      border-radius: 10px;
      display: inline-block;
      max-width: 380px;
      margin: 12px auto 0;
    }

    .result-stats-cards {
      display: flex;
      justify-content: center;
      gap: 16px;
      margin-top: 20px;
    }

    .stat-card {
      padding: 14px 22px;
      background: rgba(16, 163, 127, 0.05);
      border: 1px solid rgba(16, 163, 127, 0.15);
      border-radius: 12px;
      min-width: 90px;

      .stat-value {
        font-size: 22px;
        font-weight: 700;
        color: #10A37F;
      }

      .stat-label {
        font-size: 12px;
        color: var(--text-tertiary);
        margin-top: 4px;
      }
    }

    &.error .result-stats-cards {
      display: none;
    }
  }

  .result-actions {
    display: flex;
    justify-content: center;
    gap: 12px;
    margin-top: 8px;
  }
}

.progress-label {
  font-size: 18px;
  font-weight: 700;
  color: #10A37F;
}

@keyframes pulse-glow {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.04); }
}
</style>
