<template>
  <div class="knowledge-container">
    <header class="page-header">
      <div class="header-left">
        <h1>专属知识库</h1>
        <p>上传 PDF 教材、课件或笔记，StructQuest AI 将学习这些内容并为您提供专属解答。</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="openUploadDialog" :icon="Plus">
          上传文档
        </el-button>
      </div>
    </header>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon doc-icon"><el-icon><Document /></el-icon></div>
        <div class="stat-body">
          <div class="stat-value">{{ documents.length }}</div>
          <div class="stat-label">已入库文档</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon chunk-icon"><el-icon><DataLine /></el-icon></div>
        <div class="stat-body">
          <div class="stat-value">{{ totalChunks }}</div>
          <div class="stat-label">知识切片</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon size-icon"><el-icon><Coin /></el-icon></div>
        <div class="stat-body">
          <div class="stat-value">{{ totalSize }}</div>
          <div class="stat-label">总大小</div>
        </div>
      </div>
    </div>

    <!-- 文档列表区域 -->
    <section class="documents-section">
      <div class="section-header">
        <h3>已学习的文档</h3>
        <el-button :icon="Refresh" text @click="fetchDocuments" :loading="loadingDocs">
          刷新
        </el-button>
      </div>

      <div v-if="loadingDocs" class="loading-docs">
        <el-skeleton :rows="3" animated />
      </div>

      <div v-else-if="documents.length === 0" class="empty-state">
        <el-empty description="您的知识库还是空的">
          <el-button type="primary" @click="openUploadDialog" :icon="UploadFilled">
            上传第一份学习资料
          </el-button>
        </el-empty>
      </div>

      <div v-else class="doc-grid">
        <el-card
          v-for="doc in documents"
          :key="doc.id"
          class="doc-card"
          shadow="hover"
        >
          <div class="doc-card-inner">
            <div class="doc-icon">
              <el-icon :size="28"><Document /></el-icon>
            </div>
            <div class="doc-info">
              <h4 class="doc-name" :title="doc.filename">{{ doc.filename }}</h4>
              <div class="doc-meta">
                <span class="meta-item"><el-icon><DataLine /></el-icon> {{ doc.chunks }} 个切片</span>
                <span v-if="doc.file_size" class="meta-item">{{ formatSize(doc.file_size) }} KB</span>
              </div>
              <span class="doc-time">{{ formatDate(doc.created_at) }}</span>
            </div>
            <div class="doc-actions">
              <el-tag size="small" type="success" effect="light" round>已入库</el-tag>
              <el-popconfirm
                title="确认从知识库中删除该文档？"
                confirm-button-text="删除"
                cancel-button-text="取消"
                confirm-button-type="danger"
                @confirm="handleDelete(doc)"
              >
                <template #reference>
                  <el-button link type="danger" size="small" :icon="Delete" />
                </template>
              </el-popconfirm>
            </div>
          </div>
        </el-card>
      </div>
    </section>

    <!-- ========== 独立上传弹窗 ========== -->
    <PdfUploadDialog v-model="showUploadDialog" @success="onUploadSuccess" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  Plus, UploadFilled, Document, DataLine,
  Refresh, Delete, Coin,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import PdfUploadDialog from '../../components/common/PdfUploadDialog.vue'

// ===== 数据 =====
const documents = ref([])
const loadingDocs = ref(false)
const showUploadDialog = ref(false)

const totalChunks = computed(() => documents.value.reduce((sum, d) => sum + (d.chunks || 0), 0))
const totalSize = computed(() => {
  const kb = documents.value.reduce((sum, d) => sum + (d.file_size || 0), 0)
  if (kb < 1024) return `${kb.toFixed(1)}KB`
  return `${(kb / 1024).toFixed(1)}MB`
})

// ===== API =====
const getBaseUrl = () => {
  // 开发环境走 Vite 代理，不需要指定端口
  return ''
}

const fetchDocuments = async () => {
  loadingDocs.value = true
  try {
    const response = await fetch(`${getBaseUrl()}/api/knowledge-docs`)
    if (response.ok) {
      const data = await response.json()
      documents.value = Array.isArray(data) ? data : (data.documents || data.items || [])
    } else if (response.status === 404) {
      documents.value = []
    }
  } catch (error) {
    // 后端未启动或网络错误时静默处理，不阻塞页面
    documents.value = []
  } finally {
    loadingDocs.value = false
  }
}

const handleDelete = async (doc) => {
  try {
    const response = await fetch(
      `${getBaseUrl()}/api/knowledge-docs/${doc.doc_id || doc.id}`,
      { method: 'DELETE' }
    )
    const data = await response.json()

    if (response.ok) {
      ElMessage.success(data.message || '删除成功')
      fetchDocuments()
    } else {
      ElMessage.error(data.detail || '删除失败')
    }
  } catch (error) {
    ElMessage.error('删除请求失败')
  }
}

// ===== 操作 =====

function openUploadDialog() {
  showUploadDialog.value = true
}

function onUploadSuccess(data) {
  // 弹窗内部已经显示成功信息，这里只需刷新列表
  ElMessage.success(`${data.filename || '文档'} 已成功入库`)
  fetchDocuments()
}

// ===== 工具函数 =====

function formatSize(kb) {
  if (!kb) return '0'
  if (kb < 1024) return kb.toFixed(1)
  return (kb / 1024).toFixed(1)
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}月${date.getDate()}日 ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

onMounted(() => {
  fetchDocuments()
})
</script>

<style lang="scss" scoped>
.knowledge-container {
  padding: 36px 40px;
  max-width: 1200px;
  margin: 0 auto;
}

/* ========== 页头 ========== */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;

  h1 { font-size: 28px; margin: 0 0 8px 0; font-weight: 700; }
  p { color: var(--text-secondary); margin: 0; font-size: 15px; max-width: 560px; line-height: 1.6; }

  .header-right {
    flex-shrink: 0;
  }
}

/* ========== 统计卡片 ========== */
.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 36px;

  .stat-card {
    background: white;
    border-radius: 16px;
    padding: 20px 24px;
    display: flex;
    align-items: center;
    gap: 16px;
    border: 1px solid var(--border-color);
    transition: box-shadow 0.25s;

    &:hover {
      box-shadow: 0 4px 16px rgba(0,0,0,0.06);
    }

    .stat-icon {
      width: 48px;
      height: 48px;
      border-radius: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 22px;
      color: white;
      flex-shrink: 0;

      &.doc-icon   { background: linear-gradient(135deg, #10a37f, #1a7f64); }
      &.chunk-icon { background: linear-gradient(135deg, #F1C40F, #D4AC0D); color: #333; }
      &.size-icon  { background: linear-gradient(135deg, #9B59B6, #8E44AD); }
    }

    .stat-body {
      .stat-value {
        font-size: 26px;
        font-weight: 800;
        color: var(--text-main);
        line-height: 1.2;
      }

      .stat-label {
        font-size: 13px;
        color: var(--text-tertiary);
        margin-top: 2px;
      }
    }
  }
}

/* ========== 文档列表区域 ========== */
.documents-section {
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    h3 { font-size: 18px; margin: 0; font-weight: 600; color: var(--text-main); }
  }
}

.loading-docs {
  padding: 12px 0;
}

.empty-state {
  padding: 60px 0;
}

.doc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 18px;
}

.doc-card {
  border-radius: 14px;
  border: 1px solid var(--border-color);
  transition: all 0.25s ease;

  &:hover {
    border-color: rgba(16, 163, 127, 0.35);
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06);
  }

  :deep(.el-card__body) {
    padding: 18px 22px;
  }
}

.doc-card-inner {
  display: flex;
  align-items: center;
  gap: 14px;

  .doc-icon {
    width: 46px;
    height: 46px;
    background: rgba(16, 163, 127, 0.08);
    color: #10A37F;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .doc-info {
    flex: 1;
    min-width: 0;

    .doc-name {
      margin: 0 0 6px 0;
      font-size: 15px;
      font-weight: 600;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      color: var(--text-main);
    }

    .doc-meta {
      display: flex;
      gap: 12px;
      margin-bottom: 2px;

      .meta-item {
        display: flex;
        align-items: center;
        gap: 3px;
        font-size: 12px;
        color: var(--text-tertiary);

        .el-icon { font-size: 13px; }
      }
    }

    .doc-time {
      font-size: 11px;
      color: var(--text-quaternary, #c0c4cc);
    }
  }

  .doc-actions {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 6px;
    flex-shrink: 0;
  }
}

/* ========== 响应式 ========== */
@media (max-width: 768px) {
  .page-header { flex-direction: column; gap: 16px; }
  .stats-row { grid-template-columns: 1fr; }
  .doc-grid { grid-template-columns: 1fr; }
}
</style>
