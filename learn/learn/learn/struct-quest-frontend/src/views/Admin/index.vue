<template>
  <div class="admin-page">
    <section class="hero">
      <div>
        <h1>管理员平台</h1>
        <p>知识库管理 · 智能体审核 · 学生画像 · 数据总览</p>
      </div>
      <el-button type="primary" @click="loadAll">刷新数据</el-button>
    </section>

    <el-tabs v-model="activeTab" type="border-card" class="admin-tabs">
      <!-- ═══════════ Tab 1: 总览仪表盘 ═══════════ -->
      <el-tab-pane label="📊 总览仪表盘" name="overview">
        <div class="metrics-grid">
          <div v-for="card in metricCards" :key="card.label" class="metric-card">
            <span class="metric-label">{{ card.label }}</span>
            <strong class="metric-value">{{ card.value }}</strong>
          </div>
        </div>
        <div v-if="agentStats" class="agent-metrics-grid" style="margin-top:16px;">
          <div class="metric-card">
            <span class="metric-label">多智能体会话</span>
            <strong class="metric-value">{{ agentStats.total_sessions }}</strong>
          </div>
          <div class="metric-card">
            <span class="metric-label">平均测评分</span>
            <strong class="metric-value">{{ agentStats.avg_score }}</strong>
          </div>
          <div class="metric-card">
            <span class="metric-label">审核资源总数</span>
            <strong class="metric-value">{{ agentStats.total_reviewed_resources }}</strong>
          </div>
          <div class="metric-card">
            <span class="metric-label">审核通过率</span>
            <strong class="metric-value">{{ agentStats.approval_rate }}%</strong>
          </div>
          <div class="metric-card">
            <span class="metric-label">平均步骤/会话</span>
            <strong class="metric-value">{{ agentStats.avg_steps_per_session }}</strong>
          </div>
          <div class="metric-card">
            <span class="metric-label">完成率</span>
            <strong class="metric-value">{{ agentStats.completion_rate }}%</strong>
          </div>
        </div>
        <!-- Agent 执行分布 -->
        <div v-if="agentStats?.agent_exec_counts" class="panel" style="margin-top:16px;">
          <h3>智能体执行次数分布</h3>
          <div class="agent-bars">
            <div v-for="(count, name) in agentStats.agent_exec_counts" :key="name" class="agent-bar-item">
              <span class="agent-bar-label">{{ name }}</span>
              <el-progress :percentage="Math.min(100, count * 5)" :color="barColor(name)">
                <span class="agent-bar-count">{{ count }} 次</span>
              </el-progress>
            </div>
          </div>
        </div>
        <!-- 最近事件 -->
        <div class="panel" style="margin-top:16px;">
          <h3>最近学习事件</h3>
          <ul class="event-list">
            <li v-for="event in recentEvents" :key="event.id" class="event-item">
              <span class="event-type">{{ event.event_type }}</span>
              <span class="event-meta">用户 {{ event.user_id }} · {{ event.node_id || event.subject || '系统' }}</span>
            </li>
          </ul>
        </div>
      </el-tab-pane>

      <!-- ═══════════ Tab 2: 知识库管理 ═══════════ -->
      <el-tab-pane label="📁 知识库管理" name="knowledge">
        <div class="kb-header">
          <div class="stats-row">
            <div class="stat-card">
              <span class="stat-label">已入库文档</span>
              <strong class="stat-value">{{ kbDocs.length }}</strong>
            </div>
            <div class="stat-card">
              <span class="stat-label">知识切片</span>
              <strong class="stat-value">{{ totalChunks }}</strong>
            </div>
            <div class="stat-card">
              <span class="stat-label">总大小</span>
              <strong class="stat-value">{{ totalSize }}</strong>
            </div>
          </div>
          <el-button type="primary" @click="showUploadDialog = true" :icon="Plus">上传文档</el-button>
        </div>

        <div v-if="kbLoading" class="loading-docs">
          <el-skeleton :rows="3" animated />
        </div>
        <div v-else-if="kbDocs.length === 0" class="empty-state">
          <el-empty description="知识库为空，请上传学习资料" />
        </div>
        <el-table v-else :data="kbDocs" size="small" class="kb-table">
          <el-table-column prop="filename" label="文件名" min-width="280" show-overflow-tooltip />
          <el-table-column prop="chunks" label="切片数" width="90" align="center" />
          <el-table-column label="大小" width="100" align="center">
            <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
          </el-table-column>
          <el-table-column label="上传时间" width="170">
            <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="100" align="center">
            <template #default="{ row }">
              <el-popconfirm title="确认删除该文档？" @confirm="handleKbDelete(row)">
                <template #reference>
                  <el-button link type="danger" size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>

        <PdfUploadDialog v-model="showUploadDialog" @success="onKbUploadSuccess" />
      </el-tab-pane>

      <!-- ═══════════ Tab 3: 智能体审核 ═══════════ -->
      <el-tab-pane label="✅ 智能体审核" name="review">
        <div class="panel-header" style="margin-bottom:12px;">
          <div>
            <h3 style="margin:0;">资源审核列表</h3>
            <span style="color:#909399;font-size:13px;">来自 review_agent 的自动审核结果</span>
          </div>
          <el-select v-model="reviewFilter" size="small" style="width:140px" @change="loadAgentReviews">
            <el-option label="全部" value="" />
            <el-option label="已通过" value="approved" />
            <el-option label="待审核" value="pending" />
            <el-option label="需修订" value="needs_revision" />
          </el-select>
        </div>
        <el-table :data="filteredReviews" size="small" empty-text="暂无智能体审核数据（需先运行多智能体学习会话）">
          <el-table-column label="类型" width="110">
            <template #default="{ row }">
              <el-tag size="small">{{ typeLabel(row.type) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
          <el-table-column label="质量分" width="80" align="center">
            <template #default="{ row }">{{ row.quality_score ?? '-' }}</template>
          </el-table-column>
          <el-table-column label="相关度" width="80" align="center">
            <template #default="{ row }">{{ row.relevance_score ?? '-' }}</template>
          </el-table-column>
          <el-table-column label="推荐分" width="85" align="center">
            <template #default="{ row }">
              <span :style="{ color: (row.recommendation_score >= 70 ? '#22c55e' : '#ef4444'), fontWeight: 'bold' }">
                {{ row.recommendation_score ?? '-' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="审核状态" width="110" align="center">
            <template #default="{ row }">
              <el-tag :type="statusType(row.review_status)" size="small">
                {{ statusLabel(row.review_status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="review_reason" label="审核理由" min-width="180" show-overflow-tooltip />
          <el-table-column label="操作" width="160" align="center">
            <template #default="{ row }">
              <el-button size="small" type="success" @click="adminReview(row, 'approved')" :disabled="row.review_status === 'approved'">通过</el-button>
              <el-button size="small" type="warning" @click="adminReview(row, 'needs_revision')" :disabled="row.review_status === 'needs_revision'">修订</el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 智能体会话列表 -->
        <div class="panel" style="margin-top:16px;">
          <h3>多智能体会话记录</h3>
          <el-table :data="agentSessions" size="small" empty-text="暂无会话">
            <el-table-column prop="plan_id" label="会话ID" width="80" />
            <el-table-column prop="user_id" label="用户" width="80" />
            <el-table-column prop="subject" label="学科" width="120" />
            <el-table-column label="画像" width="150" show-overflow-tooltip>
              <template #default="{ row }">
                {{ row.ability_level }} · {{ row.mbti_style }} · 费曼{{ (row.feynman_adaptation * 100)?.toFixed(0) }}%
              </template>
            </el-table-column>
            <el-table-column label="步骤" width="80" align="center">
              <template #default="{ row }">{{ row.completed_steps }}/{{ row.total_steps }}</template>
            </el-table-column>
            <el-table-column label="测评分" width="85" align="center">
              <template #default="{ row }">
                <span :style="{ color: (row.final_score >= 60 ? '#22c55e' : '#ef4444') }">{{ row.final_score ?? '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="审核/推荐" width="100" align="center">
              <template #default="{ row }">{{ row.reviewed_count }}/{{ row.recommended_count }}</template>
            </el-table-column>
            <el-table-column label="执行Agent" min-width="200" show-overflow-tooltip>
              <template #default="{ row }">
                <el-tag v-for="a in row.agents_executed" :key="a" size="small" style="margin:1px;">{{ a }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="时间" width="160">
              <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <!-- ═══════════ Tab 4: 学生概览 ═══════════ -->
      <el-tab-pane label="👥 学生概览" name="students">
        <el-table :data="students" size="small" empty-text="暂无学生数据">
          <el-table-column prop="username" label="用户名" width="140" />
          <el-table-column label="角色" width="90" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_admin ? 'danger' : 'info'" size="small">{{ row.is_admin ? '管理员' : '学生' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="learning_mode" label="模式" width="110" />
          <el-table-column prop="plan_count" label="计划数" width="90" align="center" />
          <el-table-column prop="event_count" label="事件数" width="90" align="center" />
          <el-table-column prop="latest_profile_summary" label="最新画像摘要" min-width="320" show-overflow-tooltip />
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import adminApi from '../../api/admin'
import { knowledgeApi } from '../../api/knowledge'
import PdfUploadDialog from '../../components/common/PdfUploadDialog.vue'

// ── Tab 状态 ──
const activeTab = ref('overview')

// ── Tab1: 总览 ──
const overview = ref({ metrics: {}, recent_events: [] })
const agentStats = ref(null)
const recentEvents = computed(() => overview.value.recent_events || [])
const metricCards = computed(() => {
  const m = overview.value.metrics || {}
  return [
    { label: '学生数', value: m.total_users || 0 },
    { label: '画像快照', value: m.profile_snapshots || 0 },
    { label: '学习计划', value: m.learning_plans || 0 },
    { label: '学习事件', value: m.learning_events || 0 },
    { label: '资源资产', value: m.resource_assets || 0 },
    { label: '待审核', value: m.pending_assets || 0 },
  ]
})

// ── Tab2: 知识库 ──
const kbDocs = ref([])
const kbLoading = ref(false)
const showUploadDialog = ref(false)
const totalChunks = computed(() => kbDocs.value.reduce((s, d) => s + (d.chunks || 0), 0))
const totalSize = computed(() => {
  const kb = kbDocs.value.reduce((s, d) => s + (d.file_size || 0), 0)
  return kb < 1024 ? `${kb.toFixed(1)} KB` : `${(kb / 1024).toFixed(1)} MB`
})

// ── Tab3: 智能体审核 ──
const agentReviews = ref([])
const agentSessions = ref([])
const reviewFilter = ref('')
const filteredReviews = computed(() => {
  if (!reviewFilter.value) return agentReviews.value
  return agentReviews.value.filter(r => r.review_status === reviewFilter.value)
})

// ── Tab4: 学生 ──
const students = ref([])

// ═══════════════════════════════════
//  数据加载
// ═══════════════════════════════════

async function loadOverview() {
  try { overview.value = await adminApi.getOverview() } catch (e) { /* ignore */ }
}
async function loadAgentStats() {
  try { agentStats.value = await adminApi.getAgentStats() } catch (e) { /* ignore */ }
}
async function loadAgentReviews() {
  try {
    const res = await adminApi.getAgentReviews()
    agentReviews.value = res.items || []
  } catch (e) { /* ignore */ }
}
async function loadAgentSessions() {
  try {
    const res = await adminApi.getAgentSessions()
    agentSessions.value = res.items || []
  } catch (e) { /* ignore */ }
}
async function loadStudents() {
  try {
    const res = await adminApi.getStudents()
    students.value = res.items || []
  } catch (e) { /* ignore */ }
}

// ── 知识库 ──
async function loadKbDocs() {
  kbLoading.value = true
  try {
    kbDocs.value = await knowledgeApi.getDocs()
  } catch (e) {
    kbDocs.value = []
  } finally {
    kbLoading.value = false
  }
}
async function handleKbDelete(doc) {
  try {
    await knowledgeApi.deleteDoc(doc.id)
    ElMessage.success('已删除')
    loadKbDocs()
  } catch (e) {
    ElMessage.error(e?.detail || '删除失败')
  }
}
function onKbUploadSuccess(data) {
  ElMessage.success(`${data.filename || '文档'} 已入库`)
  showUploadDialog.value = false
  loadKbDocs()
}

// ── 审核操作 ──
async function adminReview(row, action) {
  try {
    await adminApi.reviewResource(row.id || 0, {
      action,
      reason: action === 'approved' ? '管理员通过' : '需补充优化',
      score: row.recommendation_score || 70,
    })
    ElMessage.success('审核已更新')
    loadAgentReviews()
  } catch (e) {
    ElMessage.error(e?.detail || '审核失败')
  }
}

async function loadAll() {
  await Promise.all([
    loadOverview(), loadAgentStats(), loadAgentReviews(),
    loadAgentSessions(), loadKbDocs(), loadStudents(),
  ])
}

// ═══════════════════════════════════
//  工具函数
// ═══════════════════════════════════

function typeLabel(t) {
  const map = { notes: '📖 讲义', mindmap: '🧠 导图', quiz: '✏️ 练习', code_example: '💻 代码', animation: '🎬 动画' }
  return map[t] || t || '未知'
}
function statusLabel(s) {
  const map = { approved: '已通过', pending: '待审核', needs_revision: '需修订', rejected: '已驳回' }
  return map[s] || s || '待审核'
}
function statusType(s) {
  const map = { approved: 'success', pending: 'warning', needs_revision: 'danger', rejected: 'info' }
  return map[s] || 'warning'
}
function barColor(name) {
  const colors = {
    profile_agent: '#2196F3', behavior_agent: '#4CAF50',
    profile_update_agent: '#9C27B0', path_agent: '#FF9800',
    resource_agent: '#E91E63', review_agent: '#00BCD4',
    assessment_agent: '#795548',
  }
  return colors[name] || '#607D8B'
}
function formatSize(kb) {
  if (!kb) return '0 KB'
  return kb < 1024 ? `${kb.toFixed(1)} KB` : `${(kb / 1024).toFixed(1)} MB`
}
function formatDate(d) {
  if (!d) return ''
  const dt = new Date(d)
  return `${dt.getMonth() + 1}/${dt.getDate()} ${String(dt.getHours()).padStart(2, '0')}:${String(dt.getMinutes()).padStart(2, '0')}`
}

onMounted(loadAll)
</script>

<style scoped>
.admin-page { padding: 24px; display: flex; flex-direction: column; gap: 20px; }
.hero, .panel, .metric-card, .stat-card {
  background: #fff; border-radius: 16px; border: 1px solid #e5e7eb;
  box-shadow: 0 6px 20px rgba(15, 23, 42, 0.04);
}
.hero { padding: 24px; display: flex; align-items: center; justify-content: space-between; }
.hero h1 { margin: 0 0 8px; font-size: 28px; }
.hero p { margin: 0; color: #64748b; }
.admin-tabs { border-radius: 12px; overflow: hidden; }
.metrics-grid { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 16px; }
.agent-metrics-grid { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 16px; }
.metric-card { padding: 18px; display: flex; flex-direction: column; gap: 8px; }
.metric-label { color: #64748b; font-size: 13px; }
.metric-value { font-size: 28px; color: #111827; }
.panel { padding: 20px; margin-top: 8px; }
.event-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 10px; }
.event-item { padding: 12px 14px; border-radius: 12px; background: #f8fafc; display: flex; flex-direction: column; gap: 4px; }
.event-type { font-weight: 600; color: #111827; }
.event-meta { font-size: 13px; color: #64748b; }
/* 知识库 */
.kb-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.stats-row { display: flex; gap: 24px; }
.stat-card { padding: 12px 20px; display: flex; flex-direction: column; gap: 4px; min-width: 120px; }
.stat-label { font-size: 12px; color: #909399; }
.stat-value { font-size: 24px; color: #111827; font-weight: 700; }
.kb-table { margin-top: 8px; }
.loading-docs { padding: 12px 0; }
.empty-state { padding: 40px 0; }
/* Agent bars */
.agent-bars { display: flex; flex-direction: column; gap: 10px; padding: 8px 0; }
.agent-bar-item { display: flex; align-items: center; gap: 12px; }
.agent-bar-label { width: 160px; font-size: 13px; font-weight: 500; color: #333; text-align: right; flex-shrink: 0; }
.agent-bar-count { font-size: 11px; color: #909399; }
.panel-header { display: flex; justify-content: space-between; align-items: center; }
@media (max-width: 1200px) {
  .metrics-grid, .agent-metrics-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
</style>
