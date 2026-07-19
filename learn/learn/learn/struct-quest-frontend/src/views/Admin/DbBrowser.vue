<template>
  <div class="db-browser-page">
    <div class="page-header">
      <h2>数据库管理</h2>
      <el-button type="primary" size="small" @click="refresh">刷新</el-button>
    </div>

    <!-- 表选择器 -->
    <div class="db-toolbar">
      <div class="toolbar-left">
        <span class="toolbar-label">选择表：</span>
        <el-select v-model="activeTable" size="small" style="width:220px" @change="onTableChange">
          <el-option v-for="t in tables" :key="t.name" :label="`${t.name} (${t.rows})`" :value="t.name" />
        </el-select>
        <span v-if="browseData" class="row-count">
          共 {{ browseData.total_rows }} 行，当前 {{ browseData.rows?.length || 0 }} 条
        </span>
      </div>
      <div class="toolbar-right">
        <el-button size="small" type="success" @click="showInsertDialog">插入行</el-button>
        <el-button size="small" :disabled="offset === 0" @click="goPage(-1)">上一页</el-button>
        <el-button size="small" :disabled="!hasMore" @click="goPage(1)">下一页</el-button>
        <span class="page-info">第 {{ pageNum }} 页</span>
      </div>
    </div>

    <!-- 数据表格 -->
    <div v-if="browseLoading" class="loading-wrap"><el-skeleton :rows="6" animated /></div>
    <div v-else-if="browseData" class="table-wrap">
      <el-table :data="browseData.rows" size="small" border stripe max-height="500" style="width:100%">
        <el-table-column
          v-for="col in browseData.columns"
          :key="col"
          :prop="col"
          :label="col"
          :min-width="colWidth(col)"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            <template v-if="isJsonVal(row[col])">
              <el-popover placement="right" :width="400" trigger="click">
                <template #reference>
                  <el-button link size="small" type="primary">{{ formatJsonPreview(row[col]) }}</el-button>
                </template>
                <pre class="json-preview">{{ formatJsonFull(row[col]) }}</pre>
              </el-popover>
            </template>
            <span v-else>{{ formatCell(row[col]) }}</span>
          </template>
        </el-table-column>
        <!-- 操作列 -->
        <el-table-column label="操作" width="140" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
            <el-popconfirm title="确认删除此行？" @confirm="handleDelete(row)">
              <template #reference>
                <el-button link type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </div>
    <el-empty v-else description="选择一个表开始浏览" :image-size="60" />

    <!-- 编辑/插入对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      :title="editMode === 'edit' ? `编辑 ${activeTable} #${editRowId}` : `插入 ${activeTable}`"
      width="600px"
      :destroy-on-close="true"
    >
      <el-form label-width="150px" size="small">
        <el-form-item
          v-for="col in editableColumns"
          :key="col.name"
        >
          <template #label>
            <el-tooltip v-if="fieldInfo(col.name)" :content="fieldInfo(col.name)" placement="top-start" effect="dark">
              <span>{{ fieldLabel(col.name) }}</span>
            </el-tooltip>
            <span v-else>{{ col.name }}</span>
          </template>
          <el-input
            v-if="getInputType(col) === 'string'"
            v-model="editFormData[col.name]"
            :placeholder="getColPlaceholder(col)"
          />
          <el-input-number
            v-else-if="getInputType(col) === 'number'"
            v-model="editFormData[col.name]"
            style="width:100%"
          />
          <el-switch
            v-else-if="getInputType(col) === 'bool'"
            v-model="editFormData[col.name]"
          />
          <el-input
            v-else
            v-model="editFormData[col.name]"
            type="textarea"
            :rows="4"
            :placeholder="getColPlaceholder(col)"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEdit" :loading="editSubmitting">
          {{ editMode === 'edit' ? '保存' : '插入' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import adminApi from '../../api/admin'

const tables = ref([])
const activeTable = ref('')
const browseData = ref(null)
const browseLoading = ref(false)
const offset = ref(0)
const pageSize = 50

const hasMore = computed(() => browseData.value && (offset.value + pageSize) < browseData.value.total_rows)
const pageNum = computed(() => Math.floor(offset.value / pageSize) + 1)

// 编辑/插入
const editDialogVisible = ref(false)
const editMode = ref('edit') // 'edit' | 'insert'
const editRowId = ref(null)
const editFormData = ref({})
const editSubmitting = ref(false)
const tableColumns = ref([])

const editableColumns = computed(() =>
  tableColumns.value.filter(c => c.name !== 'id' || editMode.value === 'edit')
)

function getInputType(col) {
  const t = (col.type || '').toLowerCase()
  if (['integer', 'int', 'float', 'real', 'number', 'numeric'].some(k => t.includes(k))) return 'number'
  if (['bool', 'boolean'].some(k => t.includes(k))) return 'bool'
  return 'string'
}

function getColPlaceholder(col) {
  if (col.pk) return '（主键，新建时可留空自动生成）'
  return col.type || ''
}

async function loadTables() {
  try {
    const res = await adminApi.getDbTables()
    tables.value = res.tables || []
    if (tables.value.length && !activeTable.value) {
      activeTable.value = tables.value[0].name
      await Promise.all([loadTable(), loadColumns()])
    }
  } catch (e) { console.error(e) }
}

async function loadTable() {
  if (!activeTable.value) return
  browseLoading.value = true
  try {
    browseData.value = await adminApi.getDbBrowse(activeTable.value, pageSize, offset.value)
  } catch (e) {
    console.error(e)
    browseData.value = null
  } finally {
    browseLoading.value = false
  }
}

async function loadColumns() {
  if (!activeTable.value) return
  try {
    const res = await adminApi.getTableColumns(activeTable.value)
    tableColumns.value = res.columns || []
  } catch (e) {
    tableColumns.value = []
  }
}

function onTableChange() {
  offset.value = 0
  Promise.all([loadTable(), loadColumns()])
}

function goPage(dir) {
  offset.value = Math.max(0, offset.value + dir * pageSize)
  loadTable()
}

function refresh() { loadTable() }

// CRUD 操作
async function handleDelete(row) {
  try {
    await adminApi.deleteDbRow(activeTable.value, row.id)
    ElMessage.success(`已删除 ${activeTable}.id=${row.id}`)
    loadTable()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}

function openEdit(row) {
  editMode.value = 'edit'
  editRowId.value = row.id
  editFormData.value = {}
  for (const col of tableColumns.value) {
    let val = row[col.name]
    // JSON 字段转字符串
    if (typeof val === 'object' && val !== null) {
      val = JSON.stringify(val, null, 2)
    } else if (val === null || val === undefined) {
      val = ''
    }
    editFormData.value[col.name] = val
  }
  editDialogVisible.value = true
}

function showInsertDialog() {
  editMode.value = 'insert'
  editRowId.value = null
  editFormData.value = {}
  for (const col of tableColumns.value) {
    if (col.pk) {
      editFormData.value[col.name] = null // 主键留空
    } else {
      const t = getInputType(col)
      if (t === 'number') editFormData.value[col.name] = 0
      else if (t === 'bool') editFormData.value[col.name] = false
      else editFormData.value[col.name] = ''
    }
  }
  editDialogVisible.value = true
}

async function submitEdit() {
  editSubmitting.value = true
  try {
    // 过滤掉空的 id（插入时）
    const data = { ...editFormData.value }
    if (editMode.value === 'insert' && !data.id) {
      delete data.id
    }
    // 尝试解析 JSON 字符串
    for (const key in data) {
      const val = data[key]
      if (typeof val === 'string' && (val.trim().startsWith('{') || val.trim().startsWith('['))) {
        try { data[key] = JSON.parse(val) } catch (e) { /* 保持字符串 */ }
      }
    }

    if (editMode.value === 'edit') {
      await adminApi.updateDbRow(activeTable.value, editRowId.value, data)
      ElMessage.success(`已更新 ${activeTable}.id=${editRowId.value}`)
    } else {
      await adminApi.insertDbRow(activeTable.value, data)
      ElMessage.success(`已插入新行到 ${activeTable}`)
    }
    editDialogVisible.value = false
    loadTable()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '操作失败')
  } finally {
    editSubmitting.value = false
  }
}

// 工具函数
function isJsonVal(val) {
  return typeof val === 'object' && val !== null
}
function formatJsonPreview(val) {
  if (typeof val === 'object') {
    const s = JSON.stringify(val).slice(0, 80)
    return s.length >= 80 ? s + '...' : s
  }
  return String(val || '')
}
function formatJsonFull(val) {
  return JSON.stringify(val, null, 2)
}
function formatCell(val) {
  if (val === null || val === undefined) return '-'
  if (val === true) return '✅'
  if (val === false) return '❌'
  return String(val)
}
function colWidth(col) {
  if (col === 'id') return 60
  if (['created_at', 'updated_at', 'completed_at'].includes(col)) return 160
  if (['event_type', 'role', 'status', 'review_status'].includes(col)) return 100
  return 120
}

// 字段说明字典（hover 显示用途和可选值）
const FIELD_INFO = {
  // ── 通用字段 ──
  id:           { label: 'ID', desc: '主键（自动生成，编辑时不要改）' },
  user_id:      { label: '用户ID', desc: '对应 users 表的 id' },
  created_at:   { label: '创建时间', desc: '格式: 2026-07-15 10:30:00' },
  updated_at:   { label: '更新时间', desc: '格式: 2026-07-15 10:30:00' },
  completed_at: { label: '完成时间', desc: '记录完成的时间' },
  source:       { label: '数据来源', desc: 'agent(AI生成) / manual(手动) / event(事件触发) / admin_recalc(管理员重算)' },
  subject:      { label: '学科', desc: '例: 数据结构' },

  // ── users 表 ──
  username:            { label: '用户名', desc: '登录账号（不要乱改）' },
  email:               { label: '邮箱', desc: '用户邮箱（可空）' },
  hashed_password:     { label: '密码哈希', desc: '⚠️ 加密后的密码，乱改会导致无法登录！' },
  is_admin:            { label: '是否管理员', desc: 'true=管理员, false=普通用户' },
  has_completed_onboarding: { label: '是否完成引导', desc: 'true=已走完新手指引' },
  completed_onboarding:{ label: '是否完成引导', desc: 'true=已走完新手指引' },
  learning_mode:       { label: '学习模式', desc: 'basic(基础模式) / beginner(入门模式) / exam(考试模式)' },
  learning_mode_set_at:{ label: '模式设置时间', desc: '学习模式最后被设置的时间' },
  profile_data:        { label: '画像数据', desc: 'JSON 格式，存用户的画像快照' },
  major:               { label: '专业', desc: '例: 计算机科学与技术' },
  grade:               { label: '年级', desc: '例: 大二 / 研一' },
  course:              { label: '课程', desc: '例: 数据结构' },
  learning_goal:       { label: '学习目标', desc: '例: 期末考90分 / 考研 / 找工作' },
  target_score:        { label: '目标分数', desc: '想达到的考试分数' },
  daily_study_time:    { label: '每日学习时长', desc: '例: 2小时' },
  exam_date:           { label: '考试日期', desc: '如果有考试的话' },
  learning_purpose:    { label: '学习目的', desc: 'course_preview(预习) / exam(考试) / research(研究)' },
  preferred_styles:    { label: '偏好风格', desc: 'JSON数组, 例: ["visual","hands_on"]' },
  diagnostic_results:  { label: '诊断结果', desc: 'JSON对象, 存冷启动诊断数据' },

  // ── learning_events 表 ──
  event_type:         { label: '事件类型', desc: 'study_start(开始学习) / ai_chat(AI对话) / exam_completed(考试完成) / quiz_completed(练习完成) / node_completed(节点完成) / view_notes(查看讲义) / video_watched(视频观看)' },
  node_id:            { label: '知识点ID', desc: '对应 knowledge_nodes 表的id, 例: ch02_linked_list(链表)' },
  score:              { label: '分数', desc: '0-100' },
  duration_seconds:   { label: '时长(秒)', desc: '这次学习持续了多少秒' },
  event_data:         { label: '事件详情', desc: 'JSON对象, 存额外信息' },

  // ── exam_results 表 ──
  passed:             { label: '是否通过', desc: 'true=及格, false=不及格' },
  details:            { label: '考试详情', desc: 'JSON, 存每道题的得分' },

  // ── study_sessions 表 ──
  started_at:         { label: '开始时间', desc: '学习会话开始时间' },
  ended_at:           { label: '结束时间', desc: '学习会话结束时间' },
  focus_score:        { label: '专注度', desc: '0-100, 系统自动评估' },

  // ── learning_progress 表 ──
  status:             { label: '状态', desc: 'in_progress(进行中) / completed(已完成) / paused(暂停)' },
  progress:           { label: '进度', desc: '0-100 百分比' },
  mastery_level:      { label: '掌握度', desc: '0-100 分' },
  resource_progress:  { label: '资源进度', desc: 'JSON, 记录每个资源的完成情况' },

  // ── chat_sessions 表 ──
  title:              { label: '标题', desc: '聊天窗口的标题' },
  session_id:         { label: '会话ID', desc: '对应 chat_sessions 表的 id' },

  // ── chat_messages 表 ──
  role:               { label: '角色', desc: 'user(用户) / assistant(AI) / system(系统)' },
  content:            { label: '内容', desc: '消息正文' },

  // ── knowledge_nodes 表 ──
  description:        { label: '简介', desc: '一句话描述' },
  full_desc:          { label: '完整说明', desc: '详细的文字说明' },
  category:           { label: '分类', desc: '所属章节ID, 例: ch02_linear_list' },
  difficulty:         { label: '难度', desc: '1-5, 1=最简单, 5=最难' },
  order_index:        { label: '排序', desc: '数字越小越靠前' },
  parent_id:          { label: '父节点ID', desc: '子节点填大类ID, 大类填空' },
  prerequisites:      { label: '前置知识点', desc: 'JSON数组, 例: ["ch02_seq_list"]' },
  icon:               { label: '图标', desc: 'emoji表情, 例: 🔗' },
  points:             { label: '要点', desc: 'JSON数组, 存该知识点的子要点' },
  ai_suggestion:      { label: 'AI建议', desc: 'AI给的学习建议文本' },

  // ── learning_plans 表 ──
  goal:               { label: '学习目标', desc: '例: 掌握链表相关算法' },
  plan_data:          { label: '计划数据', desc: 'JSON, 存完整的学习计划内容(含路径/资源/智能体消息)' },

  // ── student_profiles 表 ──
  ability_level:      { label: '能力等级', desc: 'beginner(初级) / intermediate(中级) / advanced(高级)' },
  learning_style:     { label: '学习风格', desc: 'visual(视觉型) / auditory(听觉型) / reading(阅读型) / hands_on(动手型)' },
  pace:               { label: '学习节奏', desc: 'fast(快) / moderate(中等) / slow(慢)' },
  learning_rhythm:    { label: '学习习惯', desc: '持续型 / 突击型 / 碎片型' },
  knowledge_mastery:  { label: '知识掌握', desc: 'JSON, 例: {"链表":85, "树":60}' },
  activity_score:     { label: '活跃度', desc: '0-100' },
  engagement_score:   { label: '参与度', desc: '0-100' },
  total_study_hours:  { label: '总学习时长', desc: '单位: 小时' },
  task_completion_rate:{ label: '任务完成率', desc: '0-1的数字, 0.8=80%' },
  resource_preferences:{ label: '资源偏好', desc: 'JSON, 例: {"视频":85, "PPT":60}' },
  error_patterns:     { label: '错误模式', desc: 'JSON数组, 例: ["概念混淆","计算错误"]' },
  primary_error_type: { label: '主要错误', desc: '错误模式中出现最多的' },
  mastery_trend:      { label: '掌握趋势', desc: 'improving(进步中) / stable(稳定) / declining(下滑)' },
  growth_history:     { label: '成长历史', desc: 'JSON数组, 存每日画像快照' },
  risk_level:         { label: '风险等级', desc: 'low(低风险) / medium(中风险) / high(高风险)' },
  risk_factors:       { label: '风险因素', desc: 'JSON数组, 描述具体风险' },
  strengths:          { label: '强项', desc: 'JSON数组, 存知识点ID' },
  weaknesses:         { label: '弱项', desc: 'JSON数组, 存知识点ID' },
  interests:          { label: '兴趣', desc: 'JSON数组' },
  cognitive_profile:  { label: '认知特征', desc: 'JSON, 含MBTI/费曼/抽象推理等' },
  confidence_score:   { label: '自信度', desc: '0-100' },
  daily_strategy:     { label: '每日策略', desc: 'AI生成的每日学习策略文本' },
  summary:            { label: '摘要', desc: '一段话总结' },
  profile_version:    { label: '画像版本', desc: '数字, 越大越新' },
}
function fieldInfo(colName) {
  return FIELD_INFO[colName]?.desc || ''
}
function fieldLabel(colName) {
  return FIELD_INFO[colName]?.label || colName
}

onMounted(loadTables)
</script>

<style scoped>
.db-browser-page { max-width: 1400px; }
.page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; }
.page-header h2 { margin:0; font-size:22px; color:#1e293b; }
.db-toolbar { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; flex-wrap:wrap; gap:8px; }
.toolbar-left { display:flex; align-items:center; gap:8px; }
.toolbar-right { display:flex; align-items:center; gap:8px; }
.toolbar-label { font-size:13px; color:#6b7280; }
.row-count { font-size:12px; color:#909399; }
.page-info { font-size:12px; color:#909399; }
.table-wrap { border-radius:10px; overflow:hidden; border:1px solid #e5e7eb; }
.json-preview { max-height:400px; overflow:auto; font-size:11px; background:#f5f5f5; padding:8px; border-radius:6px; margin:0; white-space:pre-wrap; word-break:break-all; }
.loading-wrap { padding:12px 0; }
</style>
