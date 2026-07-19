<template>
  <div class="student-detail-page">
    <div class="page-header">
      <div>
        <h2>用户数据中心</h2>
        <el-tag :type="detail?.student?.is_admin ? 'danger' : 'info'" size="small">
          {{ detail?.student?.is_admin ? '管理员' : '学生' }}
        </el-tag>
        <span class="header-meta">ID: {{ userId }} · 模式: {{ detail?.student?.learning_mode_cn || detail?.student?.learning_mode || '基础模式' }}</span>
      </div>
      <div class="header-actions">
        <el-button @click="loadAll" :loading="loading" size="small">刷新</el-button>
        <el-button type="warning" @click="recalcProfile" :loading="recalcLoading" size="small">
          强制重算画像
        </el-button>
        <el-button @click="$router.back()" size="small">返回</el-button>
      </div>
    </div>

    <div v-if="loading" class="loading-wrap"><el-skeleton :rows="8" animated /></div>

    <template v-else>
      <!-- 统计卡片 -->
      <div class="stats-row">
        <div class="stat-card">
          <span class="stat-label">考试次数</span>
          <strong>{{ detail?.stats?.exam_count || 0 }}</strong>
        </div>
        <div class="stat-card">
          <span class="stat-label">平均分</span>
          <strong :class="avgScoreClass">{{ detail?.stats?.avg_exam_score || 0 }}</strong>
        </div>
        <div class="stat-card">
          <span class="stat-label">学习事件</span>
          <strong>{{ detail?.stats?.event_count || 0 }}</strong>
        </div>
        <div class="stat-card">
          <span class="stat-label">AI对话</span>
          <strong>{{ detail?.stats?.chat_sessions || 0 }}</strong>
        </div>
        <div class="stat-card">
          <span class="stat-label">完成节点</span>
          <strong>{{ detail?.stats?.progress_count || 0 }}</strong>
        </div>
      </div>

      <div class="detail-grid">
        <!-- 六维雷达图 -->
        <div class="panel">
          <h4>🧭 六维画像</h4>
          <div ref="radarRef" class="chart-box"></div>
          <div class="radar-legend">
            <el-tag size="small" type="primary">{{ radarData?.ability_level_cn || radarData?.ability_level || '未知' }}</el-tag>
            <el-tag size="small" :type="riskTagType">{{ radarData?.risk_level_cn || radarData?.risk_level || '低风险' }}</el-tag>
            <el-tag size="small" type="info">{{ radarData?.learning_style_cn || radarData?.learning_style || '阅读型' }}</el-tag>
          </div>
        </div>

        <!-- 知识点掌握度 -->
        <div class="panel">
          <h4>📊 知识点掌握度</h4>
          <div v-if="heatmapData?.chapters?.length" class="heatmap-wrap">
            <div v-for="ch in heatmapData.chapters" :key="ch.name" class="heatmap-chapter">
              <div class="chapter-name">{{ ch.name }}</div>
              <div class="node-row">
                <div
                  v-for="node in ch.nodes" :key="node.id"
                  class="node-cell"
                  :class="masteryClass(node.mastery)"
                  :title="`${node.title}: ${node.mastery ?? '未评估'}分`"
                >
                  <span class="node-title">{{ node.title }}</span>
                  <span class="node-score">{{ node.mastery ?? '-' }}</span>
                </div>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无掌握度数据" :image-size="50" />
        </div>

        <!-- 画像详情 -->
        <div class="panel">
          <h4>📋 画像详情</h4>
          <el-descriptions v-if="detail?.profile" :column="2" size="small" border>
            <el-descriptions-item label="能力等级">{{ detail.profile.ability_level_cn || detail.profile.ability_level }}</el-descriptions-item>
            <el-descriptions-item label="学习风格">{{ detail.profile.learning_style_cn || detail.profile.learning_style }}</el-descriptions-item>
            <el-descriptions-item label="活跃度">{{ detail.profile.activity_score }}</el-descriptions-item>
            <el-descriptions-item label="专注度">{{ detail.profile.focus_score }}</el-descriptions-item>
            <el-descriptions-item label="参与度">{{ detail.profile.engagement_score }}</el-descriptions-item>
            <el-descriptions-item label="学习节奏">{{ detail.profile.learning_rhythm || '中等' }}</el-descriptions-item>
            <el-descriptions-item label="总学习时长">{{ detail.profile.total_study_hours || 0 }}h</el-descriptions-item>
            <el-descriptions-item label="掌握趋势">{{ detail.profile.mastery_trend_cn || detail.profile.mastery_trend || '稳定' }}</el-descriptions-item>
            <el-descriptions-item label="风险等级">
              <el-tag :type="riskTagType" size="small">{{ detail.profile.risk_level_cn || detail.profile.risk_level || '低风险' }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="任务完成率">{{ ((detail.profile.task_completion_rate || 0) * 100).toFixed(0) }}%</el-descriptions-item>
            <el-descriptions-item label="认知特征" :span="2">
              <span v-if="detail.profile.cognitive?.mbti_style">MBTI: {{ detail.profile.cognitive.mbti_style }} · </span>
              <span v-if="detail.profile.cognitive?.feynman_adaptation">费曼: {{ (detail.profile.cognitive.feynman_adaptation * 100).toFixed(0) }}% · </span>
              <span v-if="detail.profile.cognitive?.abstract_reasoning">抽象推理: {{ (detail.profile.cognitive.abstract_reasoning * 100).toFixed(0) }}%</span>
            </el-descriptions-item>
            <el-descriptions-item label="强势领域">
              <el-tag v-for="s in (detail.profile.strengths || [])" :key="s" size="small" type="success" style="margin:1px">{{ displayName(s) }}</el-tag>
              <span v-if="!detail.profile.strengths?.length">-</span>
            </el-descriptions-item>
            <el-descriptions-item label="薄弱领域">
              <el-tag v-for="w in (detail.profile.weaknesses || [])" :key="w" size="small" type="danger" style="margin:1px">{{ displayName(w) }}</el-tag>
              <span v-if="!detail.profile.weaknesses?.length">-</span>
            </el-descriptions-item>
            <el-descriptions-item label="资源偏好" :span="2">
              <template v-if="detail.profile.resource_preferences">
                <el-tag v-for="(val, key) in detail.profile.resource_preferences" :key="key" size="small" style="margin:1px">
                  {{ key }}: {{ val?.toFixed?.(0) ?? val }}%
                </el-tag>
              </template>
              <span v-else>-</span>
            </el-descriptions-item>
            <el-descriptions-item label="画像摘要" :span="2">{{ detail.profile.summary || '暂无摘要' }}</el-descriptions-item>
          </el-descriptions>
          <el-empty v-else description="暂无画像数据" :image-size="50" />
        </div>

        <!-- 考试趋势 -->
        <div class="panel">
          <h4>📈 考试趋势</h4>
          <div ref="examRef" class="chart-box"></div>
          <div v-if="!detail?.exams?.length" style="padding:20px;text-align:center;color:#999;">暂无考试记录</div>
        </div>
      </div>

      <!-- ═══════════ 手动数据注入区 ═══════════ -->
      <div class="panel injection-panel" style="margin-top:16px;">
        <h4>🔧 手动注入章节测试成绩</h4>
        <el-form :model="examForm" label-width="100px" size="small" inline style="margin-top:8px;">
          <el-form-item label="知识点">
            <el-select v-model="examForm.node_id" filterable placeholder="搜索选择知识点" style="width:260px" @change="onNodeSelect">
              <el-option v-for="n in knowledgeNodes" :key="n.id" :label="`${n.id} · ${n.title}`" :value="n.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="知识点名">
            <el-input v-model="examForm.node_title" placeholder="自动填入" style="width:160px" />
          </el-form-item>
          <el-form-item label="分数">
            <el-input-number v-model="examForm.score" :min="0" :max="100" />
          </el-form-item>
          <el-form-item label="通过">
            <el-switch v-model="examForm.passed" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="addExam" :loading="examAdding">添加并重算画像</el-button>
          </el-form-item>
        </el-form>
        <div class="form-hint">添加后自动从数据库重新计算全部六维画像数值，雷达图/掌握度将立即刷新。</div>
      </div>

      <!-- 考试记录表 -->
      <div class="panel" style="margin-top:16px;">
        <h4>📝 考试记录</h4>
        <el-table v-if="detail?.exams?.length" :data="detail.exams" size="small" max-height="250">
          <el-table-column prop="node_id" label="知识点" width="120" />
          <el-table-column prop="score" label="分数" width="80" align="center" />
          <el-table-column label="通过" width="70" align="center">
            <template #default="{ row }">{{ row.passed ? '✅' : '❌' }}</template>
          </el-table-column>
          <el-table-column label="时间" width="170">
            <template #default="{ row }">{{ row.completed_at || '-' }}</template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="暂无考试记录" :image-size="50" />
      </div>

      <!-- 学习事件时间轴 -->
      <div class="panel" style="margin-top:16px;">
        <h4>⏱️ 学习事件时间轴</h4>
        <div v-if="timeline?.length" class="timeline-wrap">
          <div v-for="e in timeline" :key="e.id" class="timeline-item">
            <span class="tl-date">{{ e.date }} {{ e.time }}</span>
            <el-tag size="small" :type="eventTypeTag(e.event_type)">{{ e.event_type_cn || e.event_type }}</el-tag>
            <span v-if="e.node_id" class="tl-node">{{ e.node_id }}</span>
            <span v-if="e.score != null" class="tl-score">{{ e.score }}分</span>
          </div>
        </div>
        <el-empty v-else description="暂无事件记录" :image-size="50" />
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import adminApi from '../../api/admin'
import { getNodeNameById } from '../../data/knowledgeMap'

const route = useRoute()
const userId = computed(() => Number(route.params.userId))

const loading = ref(true)
const detail = ref(null)
const radarData = ref(null)
const heatmapData = ref(null)
const timeline = ref([])
const radarRef = ref(null)
const examRef = ref(null)
let radarChart = null
let examChart = null

const avgScoreClass = ref('score-mid')
const riskTagType = ref('success')

// 手动注入表单
const examAdding = ref(false)
const recalcLoading = ref(false)
const knowledgeNodes = ref([])

const examForm = ref({
  node_id: '',
  node_title: '',
  score: 75,
  passed: true,
})

async function loadAll() {
  loading.value = true
  try {
    const [d, r, h, t] = await Promise.all([
      adminApi.getStudentDetail(userId.value),
      adminApi.getStudentRadar(userId.value),
      adminApi.getStudentHeatmap(userId.value),
      adminApi.getStudentTimeline(userId.value, 50),
    ])
    detail.value = d
    radarData.value = r
    heatmapData.value = h
    timeline.value = t.timeline || []

    avgScoreClass.value = (d?.stats?.avg_exam_score || 0) >= 70 ? 'score-high'
      : (d?.stats?.avg_exam_score || 0) >= 40 ? 'score-mid' : 'score-low'
    riskTagType.value = r?.risk_level === 'high' ? 'danger' : (r?.risk_level === 'medium' ? 'warning' : 'success')

    await nextTick()
    renderRadar()
    renderExamChart()
  } catch (e) {
    console.error('加载学生详情失败:', e)
  } finally {
    loading.value = false
  }
}

async function loadKnowledgeNodes() {
  try {
    const res = await adminApi.getKnowledgeNodes()
    knowledgeNodes.value = res.nodes || []
  } catch (e) { console.error('加载知识点列表失败:', e) }
}

function onNodeSelect(nodeId) {
  const found = knowledgeNodes.value.find(n => n.id === nodeId)
  examForm.value.node_title = found ? found.title : ''
}

function renderRadar() {
  if (!radarRef.value || !radarData.value) return
  if (radarChart) radarChart.dispose()
  radarChart = echarts.init(radarRef.value)
  radarChart.setOption({
    tooltip: {},
    radar: {
      indicator: (radarData.value.dimensions || []).map(d => ({ name: d, max: 100 })),
      center: ['50%', '55%'],
      radius: '75%',
    },
    series: [{
      type: 'radar',
      data: [{ value: radarData.value.values || [], name: '画像', areaStyle: { color: 'rgba(100,149,237,0.2)' } }],
      lineStyle: { color: '#6495ED', width: 2 },
      itemStyle: { color: '#6495ED' },
    }],
  })
}

function renderExamChart() {
  if (!examRef.value || !detail.value?.exams?.length) return
  if (examChart) examChart.dispose()
  examChart = echarts.init(examRef.value)
  const exams = [...detail.value.exams].reverse()
  examChart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: exams.map(e => e.completed_at?.slice(0, 10) || ''),
      axisLabel: { rotate: 45, fontSize: 10 },
    },
    yAxis: { min: 0, max: 100 },
    series: [{
      type: 'line',
      data: exams.map(e => e.score),
      smooth: true,
      lineStyle: { color: '#6495ED' },
      itemStyle: { color: '#6495ED' },
      markLine: {
        data: [{ yAxis: 60, name: '及格线', lineStyle: { color: '#e6a23c', type: 'dashed' } }],
        silent: true,
      },
    }],
    grid: { left: 40, right: 20, top: 20, bottom: 40 },
  })
}

// 手动注入：添加考试
async function addExam() {
  examAdding.value = true
  try {
    const res = await adminApi.addExam(userId.value, {
      node_id: examForm.value.node_id,
      node_title: examForm.value.node_title,
      score: examForm.value.score,
      passed: examForm.value.passed,
    })
    ElMessage.success(res.message || '章节测试记录已添加，画像已更新')
    examForm.value = { node_id: '', node_title: '', score: 75, passed: true }
    await loadAll()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '添加失败')
  } finally {
    examAdding.value = false
  }
}

// 强制重算画像
async function recalcProfile() {
  recalcLoading.value = true
  try {
    const res = await adminApi.recalculateProfile(userId.value)
    ElMessage.success('画像已重新计算')
    await loadAll()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '重算失败')
  } finally {
    recalcLoading.value = false
  }
}

function masteryClass(val) {
  if (val == null) return 'no-data'
  if (val >= 70) return 'high'
  if (val >= 40) return 'mid'
  return 'low'
}

/** 将 ID 翻译为中文名 */
function displayName(id) {
  return getNodeNameById(id) || id
}

function eventTypeTag(t) {
  const map = { ai_chat: '', exam_completed: 'success', study_start: 'warning', quiz_completed: 'info', node_completed: '', view_notes: 'info', video_watched: '' }
  return map[t] || ''
}

watch(() => userId.value, () => { loadKnowledgeNodes(); loadAll(); }, { immediate: true })

onUnmounted(() => {
  radarChart?.dispose()
  examChart?.dispose()
})
</script>

<style scoped>
.student-detail-page { max-width: 1400px; }
.page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; padding-bottom:12px; border-bottom:1px solid #e5e7eb; flex-wrap:wrap; gap:12px; }
.page-header h2 { margin:0 0 4px; font-size:22px; color:#1e293b; }
.header-meta { font-size:12px; color:#909399; margin-left:12px; }
.header-actions { display:flex; gap:8px; }
.stats-row { display:grid; grid-template-columns:repeat(5,1fr); gap:12px; margin-bottom:16px; }
.stat-card { background:#fff; border-radius:10px; padding:12px 16px; border:1px solid #e5e7eb; display:flex; flex-direction:column; gap:4px; }
.stat-label { font-size:12px; color:#909399; }
.stat-card strong { font-size:24px; color:#111827; }
.score-high { color:#22c55e; }
.score-mid { color:#e6a23c; }
.score-low { color:#ef4444; }
.detail-grid { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
.panel { background:#fff; border-radius:12px; padding:16px; border:1px solid #e5e7eb; }
.panel h4 { margin:0 0 12px; font-size:14px; color:#374151; }
.chart-box { width:100%; height:260px; }
.radar-legend { display:flex; gap:6px; margin-top:8px; justify-content:center; }
.heatmap-wrap { display:flex; flex-direction:column; gap:10px; }
.heatmap-chapter { display:flex; flex-direction:column; gap:4px; }
.chapter-name { font-size:12px; font-weight:600; color:#6b7280; }
.node-row { display:flex; flex-wrap:wrap; gap:4px; }
.node-cell { border-radius:6px; padding:4px 8px; display:flex; flex-direction:column; align-items:center; min-width:50px; cursor:default; }
.node-cell.high { background:#d4edda; color:#155724; }
.node-cell.mid { background:#fff3cd; color:#856404; }
.node-cell.low { background:#f8d7da; color:#721c24; }
.node-cell.no-data { background:#f3f4f6; color:#9ca3af; }
.node-title { font-size:10px; white-space:nowrap; }
.node-score { font-size:12px; font-weight:700; }
.timeline-wrap { display:flex; flex-direction:column; gap:6px; max-height:300px; overflow-y:auto; }
.timeline-item { display:flex; align-items:center; gap:8px; padding:6px 10px; background:#f8fafc; border-radius:8px; font-size:12px; }
.tl-date { color:#6b7280; white-space:nowrap; min-width:120px; }
.tl-node { color:#b94b5a; }
.tl-score { color:#f59e0b; font-weight:600; }
.loading-wrap { padding:20px 0; }
.injection-panel { border-left:3px solid #38bdf8; }
.form-hint { margin-top:8px; font-size:12px; color:#909399; }
.field-tip { font-size:11px; color:#909399; margin-top:2px; line-height:1.3; }
@media (max-width:900px) {
  .detail-grid { grid-template-columns:1fr; }
  .stats-row { grid-template-columns:repeat(2, 1fr); }
}
</style>

