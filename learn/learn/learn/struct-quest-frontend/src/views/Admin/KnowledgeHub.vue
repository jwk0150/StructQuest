<template>
  <div class="knowledge-hub">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>📚 知识库大管家</h2>
      <p class="subtitle">管理所有 AI 生成的内容、上传文档和向量库缓存</p>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card chroma-card">
          <div class="stat-icon">🧬</div>
          <div class="stat-body">
            <div class="stat-value">{{ overview.chromadb.total_chunks || 0 }}</div>
            <div class="stat-label">ChromaDB 向量数</div>
          </div>
          <div class="stat-sub">{{ overview.chromadb.status }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card doc-card">
          <div class="stat-icon">📄</div>
          <div class="stat-body">
            <div class="stat-value">{{ overview.uploaded_docs.total || 0 }}</div>
            <div class="stat-label">上传文档</div>
          </div>
          <div class="stat-sub">有效 {{ overview.uploaded_docs.active || 0 }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card ai-card">
          <div class="stat-icon">🤖</div>
          <div class="stat-body">
            <div class="stat-value">{{ overview.ai_resources.total || 0 }}</div>
            <div class="stat-label">AI 生成资源</div>
          </div>
          <div class="stat-sub">待审 {{ overview.ai_resources.pending || 0 }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card content-card">
          <div class="stat-icon">💾</div>
          <div class="stat-body">
            <div class="stat-value">{{ overview.generated_content.total || 0 }}</div>
            <div class="stat-label">用户保存内容</div>
          </div>
          <div class="stat-sub">&nbsp;</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Tab 切换 -->
    <el-card class="main-content">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="AI 生成资源" name="ai_resources">
          <!-- 工具栏 -->
          <div class="toolbar">
            <el-select v-model="aiFilter" placeholder="按状态筛选" clearable size="small" style="width:150px" @change="loadTabData">
              <el-option label="全部" value="all" />
              <el-option label="已审核" value="approved" />
              <el-option label="待审核" value="pending" />
              <el-option label="已拒绝" value="rejected" />
            </el-select>
            <el-button type="primary" size="small" @click="showAddDialog = true">
              <el-icon><Plus /></el-icon> 手动添加
            </el-button>
          </div>

          <!-- 类型分布 -->
          <div class="type-tags" v-if="typeStats.length > 0">
            <el-tag v-for="t in typeStats" :key="t.type" :type="t.tagType" effect="plain" size="small">
              {{ t.icon }} {{ t.label }}: {{ t.count }}
            </el-tag>
          </div>

          <!-- 资源列表 -->
          <el-table :data="aiResources" stripe v-loading="loading" empty-text="暂无 AI 生成资源" max-height="500">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column label="类型" width="120">
              <template #default="{ row }">
                <span>{{ row.type_meta?.icon || '📄' }} {{ row.type_meta?.label || row.asset_type }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="topic" label="主题" min-width="140" show-overflow-tooltip />
            <el-table-column prop="subject" label="学科" width="100" />
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="statusType(row.review_status)" size="small">{{ statusLabel(row.review_status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="quality_score" label="质量分" width="80" align="center">
              <template #default="{ row }">
                <span :style="{ color: scoreColor(row.quality_score) }">{{ row.quality_score || '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="内容预览" min-width="200" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="preview-text">{{ row.content_preview }}</span>
                <el-tag v-if="row.content_length" size="small" type="info" class="length-tag">{{ row.content_length }}字</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="创建时间" width="160">
              <template #default="{ row }">
                {{ formatTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="240" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="viewDetail(row)">查看</el-button>
                <el-button link type="success" size="small" @click="approveItem(row)" v-if="row.review_status !== 'approved'">审核</el-button>
                <el-button link type="danger" size="small" @click="deleteItem(row, 'ai_resources')">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="用户保存内容" name="generated_content">
          <el-table :data="generatedContents" stripe v-loading="loading" empty-text="暂无保存内容" max-height="500">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column label="类型" width="100">
              <template #default="{ row }">
                <el-tag size="small">{{ row.content_type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="title" label="标题" min-width="160" show-overflow-tooltip />
            <el-table-column prop="topic_tag" label="标签" width="120" />
            <el-table-column label="内容预览" min-width="200" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="preview-text">{{ row.content_preview || row.description }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="view_count" label="查看" width="70" align="center" />
            <el-table-column label="创建时间" width="160">
              <template #default="{ row }">
                {{ formatTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="viewGenDetail(row)">查看</el-button>
                <el-button link type="danger" size="small" @click="deleteItem(row, 'generated_content')">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="上传文档" name="uploaded">
          <el-table :data="uploadedDocs" stripe v-loading="loading" empty-text="暂无上传文档" max-height="500">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="filename" label="文件名" min-width="200" show-overflow-tooltip />
            <el-table-column label="类型" width="80">
              <template #default="{ row }">
                <el-tag size="small">{{ row.file_type || '-' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.status === 'active' ? 'success' : 'warning'" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="大小" width="80" align="right">
              <template #default="{ row }">
                {{ formatSize(row.file_size) }}
              </template>
            </el-table-column>
            <el-table-column label="上传时间" width="160">
              <template #default="{ row }">
                {{ formatTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="{ row }">
                <el-button link type="danger" size="small" @click="deleteItem(row, 'uploaded')">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="ChromaDB 向量库" name="chromadb">
          <el-empty v-if="!chromaDetails" description="ChromaDB 未连接或为空" />
          <el-descriptions v-else :column="2" border>
            <el-descriptions-item label="总向量数">{{ chromaDetails.total_chunks }}</el-descriptions-item>
            <el-descriptions-item label="文档数">{{ chromaDetails.document_count }}</el-descriptions-item>
            <el-descriptions-item label="状态">{{ chromaDetails.status }}</el-descriptions-item>
            <el-descriptions-item label="模型">{{ chromaDetails.model }}</el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 查看详情弹窗 -->
    <el-dialog v-model="detailVisible" title="资源详情" width="700px" top="5vh">
      <div v-if="detailItem" class="detail-body">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="类型">{{ detailItem.type_meta?.icon }} {{ detailItem.type_meta?.label || detailItem.asset_type }}</el-descriptions-item>
          <el-descriptions-item label="主题">{{ detailItem.topic }}</el-descriptions-item>
          <el-descriptions-item label="学科">{{ detailItem.subject }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusType(detailItem.review_status)" size="small">{{ statusLabel(detailItem.review_status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="质量分">{{ detailItem.quality_score || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatTime(detailItem.created_at) }}</el-descriptions-item>
        </el-descriptions>
        <div class="content-section">
          <h4>内容</h4>
          <div class="content-box" v-html="renderedContent"></div>
        </div>
      </div>
    </el-dialog>

    <!-- 手动添加弹窗 -->
    <el-dialog v-model="showAddDialog" title="手动添加资源到知识库" width="550px" top="5vh">
      <el-form :model="addForm" label-width="80px" size="small">
        <el-form-item label="存储位置">
          <el-radio-group v-model="addForm.type">
            <el-radio value="ai_resources">AI 资源库</el-radio>
            <el-radio value="generated_content">用户内容库</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="资源类型">
          <el-select v-model="addForm.asset_type" style="width:100%">
            <el-option v-for="(meta, key) in typeMeta" :key="key" :label="`${meta.icon} ${meta.label}`" :value="key" />
          </el-select>
        </el-form-item>
        <el-form-item label="主题">
          <el-input v-model="addForm.topic" placeholder="如：链表、二叉树" />
        </el-form-item>
        <el-form-item label="学科">
          <el-input v-model="addForm.subject" placeholder="数据结构" />
        </el-form-item>
        <el-form-item label="标题">
          <el-input v-model="addForm.title" placeholder="资源标题" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="addForm.content_text" type="textarea" :rows="8" placeholder="请输入 Markdown 格式的内容" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="doAddItem" :loading="adding">添加到知识库</el-button>
      </template>
    </el-dialog>

    <!-- 查看生成内容详情 -->
    <el-dialog v-model="genDetailVisible" title="生成内容详情" width="700px" top="5vh">
      <div v-if="genDetailItem" class="detail-body">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="类型">{{ genDetailItem.content_type }}</el-descriptions-item>
          <el-descriptions-item label="标题">{{ genDetailItem.title }}</el-descriptions-item>
          <el-descriptions-item label="标签">{{ genDetailItem.topic_tag }}</el-descriptions-item>
          <el-descriptions-item label="格式">{{ genDetailItem.format }}</el-descriptions-item>
          <el-descriptions-item label="查看次数">{{ genDetailItem.view_count }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatTime(genDetailItem.created_at) }}</el-descriptions-item>
        </el-descriptions>
        <div class="content-section" v-if="genDetailItem.content_text">
          <h4>内容</h4>
          <div class="content-box">{{ genDetailItem.content_text }}</div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import request from '../../utils/request'

// ════════════════════════ 数据 ════════════════════════
const loading = ref(false)
const activeTab = ref('ai_resources')
const aiFilter = ref('all')

const overview = ref({
  chromadb: { total_chunks: 0, document_count: 0, status: '加载中...', model: '' },
  uploaded_docs: { total: 0, active: 0, items: [] },
  ai_resources: { total: 0, approved: 0, pending: 0, by_type: {}, items: [] },
  generated_content: { total: 0, by_type: {}, items: [] },
})

const typeMeta = {
  notes: { icon: '📖', label: '学习讲义' },
  mindmap: { icon: '🧠', label: '思维导图' },
  quiz: { icon: '✏️', label: '练习题' },
  code_example: { icon: '💻', label: '代码案例' },
  animation: { icon: '🎬', label: '动画演示' },
  ppt_outline: { icon: '📊', label: 'PPT大纲' },
}

// AI 资源列表
const aiResources = computed(() => overview.value.ai_resources.items || [])
const uploadedDocs = computed(() => overview.value.uploaded_docs.items || [])
const generatedContents = computed(() => overview.value.generated_content.items || [])
const chromaDetails = computed(() => overview.value.chromadb)

const typeStats = computed(() => {
  const byType = overview.value.ai_resources.by_type || {}
  const colors = ['', 'success', 'warning', 'danger', 'info']
  return Object.entries(byType).map(([type, count], i) => ({
    type,
    count,
    icon: typeMeta[type]?.icon || '📄',
    label: typeMeta[type]?.label || type,
    tagType: colors[i % colors.length],
  }))
})

// 详情弹窗
const detailVisible = ref(false)
const detailItem = ref(null)
const renderedContent = computed(() => {
  if (!detailItem.value?.content_text) return ''
  const text = detailItem.value.content_text || ''
  // 简单 Markdown 转 HTML（只转换代码块和换行）
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code class="language-$1">$2</code></pre>')
    .replace(/\n/g, '<br>')
})

// 生成内容详情
const genDetailVisible = ref(false)
const genDetailItem = ref(null)

// 手动添加
const showAddDialog = ref(false)
const adding = ref(false)
const addForm = ref({
  type: 'ai_resources',
  asset_type: 'notes',
  topic: '',
  subject: '数据结构',
  title: '',
  content_text: '',
  description: '',
})

// ════════════════════════ 方法 ════════════════════════

async function loadOverview() {
  loading.value = true
  try {
    const res = await request.get('/admin/knowledge-hub')
    overview.value = res
  } catch (e) {
    ElMessage.error('加载知识库数据失败: ' + (e?.detail || e?.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

async function loadTabData() {
  loading.value = true
  try {
    if (activeTab.value === 'ai_resources') {
      const params = { limit: 100 }
      if (aiFilter.value && aiFilter.value !== 'all') params.status = aiFilter.value
      const res = await request.get(`/admin/knowledge-hub/ai_resources`, params)
      overview.value.ai_resources.items = res.items || []
      overview.value.ai_resources.total = res.total || 0
    } else if (activeTab.value === 'generated_content') {
      const res = await request.get('/admin/knowledge-hub/generated_content', { limit: 100 })
      overview.value.generated_content.items = res.items || []
      overview.value.generated_content.total = res.total || 0
    } else if (activeTab.value === 'uploaded') {
      const res = await request.get('/admin/knowledge-hub/uploaded', { limit: 100 })
      overview.value.uploaded_docs.items = res.items || []
      overview.value.uploaded_docs.total = res.total || 0
    }
  } catch (e) {
    // 加载失败用 overview 里的数据兜底
  } finally {
    loading.value = false
  }
}

function handleTabChange() {
  aiFilter.value = 'all'
  loadTabData()
}

async function viewDetail(row) {
  try {
    const res = await request.get(`/admin/knowledge-hub/ai_resources/${row.id}`)
    detailItem.value = res
    detailVisible.value = true
  } catch (e) {
    // 兜底：直接用行数据
    detailItem.value = row
    detailVisible.value = true
  }
}

async function viewGenDetail(row) {
  try {
    const res = await request.get(`/admin/knowledge-hub/generated_content/${row.id}`)
    genDetailItem.value = res
  } catch (e) {
    genDetailItem.value = row
  }
  genDetailVisible.value = true
}

async function approveItem(row) {
  try {
    await request.post(`/admin/resources/${row.id}/review`, { action: 'approved', reason: '管理员审核通过', score: 85 })
    ElMessage.success('已审核通过')
    loadOverview()
  } catch (e) {
    ElMessage.error('审核失败: ' + (e?.detail || e?.message || ''))
  }
}

async function deleteItem(row, hubType) {
  try {
    await ElMessageBox.confirm(`确定要删除这条记录吗？此操作不可恢复。`, '确认删除', { type: 'warning' })
    await request.delete(`/admin/knowledge-hub/${hubType}/${row.id}`)
    ElMessage.success('已删除')
    loadOverview()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败: ' + (e?.detail || e?.message || ''))
    }
  }
}

async function doAddItem() {
  if (!addForm.value.content_text.trim()) {
    ElMessage.warning('请输入内容')
    return
  }
  adding.value = true
  try {
    await request.post('/admin/knowledge-hub', { ...addForm.value })
    ElMessage.success('已添加到知识库')
    showAddDialog.value = false
    resetAddForm()
    loadOverview()
  } catch (e) {
    ElMessage.error('添加失败: ' + (e?.detail || e?.message || ''))
  } finally {
    adding.value = false
  }
}

function resetAddForm() {
  addForm.value = {
    type: 'ai_resources',
    asset_type: 'notes',
    topic: '',
    subject: '数据结构',
    title: '',
    content_text: '',
    description: '',
  }
}

// ════════════════════════ 工具函数 ════════════════════════

function statusType(status) {
  const map = { approved: 'success', pending: 'warning', needs_revision: 'warning', rejected: 'danger' }
  return map[status] || 'info'
}

function statusLabel(status) {
  const map = { approved: '已审核', pending: '待审核', needs_revision: '需修改', rejected: '已拒绝' }
  return map[status] || status
}

function scoreColor(score) {
  if (!score) return '#999'
  if (score >= 80) return '#22c55e'
  if (score >= 60) return '#f59e0b'
  return '#ef4444'
}

function formatTime(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  return d.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function formatSize(bytes) {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// ════════════════════════ 初始化 ════════════════════════
onMounted(() => {
  loadOverview()
})
</script>

<style scoped>
.knowledge-hub {
  max-width: 1400px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0 0 4px 0;
  font-size: 22px;
  color: #1e293b;
}

.subtitle {
  margin: 0;
  color: #64748b;
  font-size: 13px;
}

/* 统计卡片 */
.stats-row {
  margin-bottom: 16px;
}

.stat-card {
  border-radius: 12px;
  cursor: default;
}

.stat-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  gap: 14px;
}

.stat-icon {
  font-size: 32px;
  flex-shrink: 0;
}

.stat-body {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: #64748b;
}

.stat-sub {
  font-size: 11px;
  color: #94a3b8;
  text-align: right;
  align-self: flex-end;
}

.stat-card.chroma-card { border-left: 3px solid #d97982; }
.stat-card.doc-card { border-left: 3px solid #b94b5a; }
.stat-card.ai-card { border-left: 3px solid #10b981; }
.stat-card.content-card { border-left: 3px solid #f59e0b; }

/* 主内容 */
.main-content {
  border-radius: 12px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
}

.type-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.preview-text {
  color: #64748b;
  font-size: 12px;
}

.length-tag {
  margin-left: 8px;
  font-size: 11px;
}

/* 详情弹窗 */
.detail-body {
  max-height: 70vh;
  overflow-y: auto;
}

.content-section {
  margin-top: 16px;
}

.content-section h4 {
  margin: 0 0 8px 0;
  color: #334155;
}

.content-box {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 16px;
  font-size: 13px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 400px;
  overflow-y: auto;
  color: #334155;
}

.content-box :deep(pre) {
  background: #1e293b;
  color: #e2e8f0;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
}

.content-box :deep(code) {
  font-family: 'Fira Code', monospace;
  font-size: 12px;
}
</style>

