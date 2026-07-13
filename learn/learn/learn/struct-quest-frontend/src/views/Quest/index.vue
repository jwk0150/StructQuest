<template>
  <div class="quest-view">
    <!-- 顶部栏 -->
    <div class="quest-topbar">
      <div class="topbar-left">
        <h1 class="quest-title">🎯 今日任务</h1>
        <p class="quest-subtitle">每天3个任务，轻松掌握数据结构</p>
      </div>
      <div class="topbar-right">
        <span class="refresh-count">今日可刷新 {{ 3 - refreshCount }} 次</span>
        <button class="refresh-btn" :disabled="refreshCount >= 3 || loading" @click="refreshTasks">
          🔄 刷新今日任务
        </button>
      </div>
    </div>

    <!-- 今日概览 -->
    <div class="quest-summary">
      <div class="summary-item">
        <span class="summary-value">{{ completedCount }}</span>
        <span class="summary-label">已完成</span>
      </div>
      <div class="summary-item">
        <span class="summary-value">{{ inProgressCount }}</span>
        <span class="summary-label">进行中</span>
      </div>
      <div class="summary-item">
        <span class="summary-value">{{ pendingCount }}</span>
        <span class="summary-label">待开始</span>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="quest-loading">加载今日任务中...</div>

    <!-- 空状态 -->
    <div v-else-if="tasks.length === 0" class="quest-empty">
      <p>暂无今日任务</p>
      <button @click="refreshTasks">生成今日任务</button>
    </div>

    <!-- 任务列表 -->
    <div v-else class="quest-list">
      <!-- 今日在线时长 -->
      <div class="study-time-card">
        <span class="time-label">📊 今日学习</span>
        <span class="time-value">{{ formatTime(todaySeconds) }}</span>
      </div>

      <div v-for="task in tasks" :key="task.id" class="task-card"
        :class="[`task-${task.status}`, `type-${task.task_type}`]">
        <div class="task-left">
          <div class="task-icon-wrapper">
            <span class="task-icon">{{ taskIcons[task.task_type] || '📋' }}</span>
          </div>
        </div>
        <div class="task-body">
          <div class="task-header">
            <span class="task-type-tag" :class="task.task_type">{{ typeLabels[task.task_type] || task.task_type }}</span>
            <span class="task-time">⏱ {{ task.estimated_time || '5分钟' }}</span>
          </div>
          <h3 class="task-title">{{ task.task_title }}</h3>
          <p class="task-desc">{{ task.task_description }}</p>
          <div v-if="task.status === 'in_progress'" class="task-progress-bar">
            <div class="task-progress-fill" :style="{ width: (task.progress || 0) + '%' }"></div>
          </div>
        </div>
        <div class="task-right">
          <div v-if="task.status === 'completed'" class="task-completed-badge">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="#22c55e" stroke-width="2" fill="rgba(34,197,94,0.1)"/>
              <path d="M8 12l3 3 5-5" stroke="#22c55e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>已完成</span>
          </div>
          <button v-else class="task-action-btn" :class="task.task_type" @click="goToTask(task)">
            {{ task.status === 'in_progress' ? '继续完成' : '去完成' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import dailyTaskApi from '../../api/dailyTask'
import { useTaskStore } from '../../store/task'

const router = useRouter()
const taskStore = useTaskStore()

const tasks = ref([])
const loading = ref(true)
const refreshCount = ref(0)
const todaySeconds = ref(0)
let timer = null

const taskIcons = { simple: '📖', advanced: '✏️', review: '🔄' }
const typeLabels = { simple: '基础学习', advanced: '拔高练习', review: '错题复习' }

const completedCount = computed(() => tasks.value.filter(t => t.status === 'completed').length)
const inProgressCount = computed(() => tasks.value.filter(t => t.status === 'in_progress').length)
const pendingCount = computed(() => tasks.value.filter(t => t.status === 'pending').length)

onMounted(async () => {
  await loadTasks()
  // 每5秒更新在线时长
  timer = setInterval(() => {
    todaySeconds.value += 5
  }, 5000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

async function loadTasks() {
  loading.value = true
  try {
    const res = await dailyTaskApi.getTodayTasks()
    tasks.value = res.tasks || []
  } catch (e) {
    console.warn('[Quest] 加载任务失败:', e)
    // fallback 使用旧接口
    try {
      const { default: studyApi } = await import('../../api/study')
      const res = await studyApi.getDailyTasks()
      if (res?.tasks) tasks.value = res.tasks
    } catch (e2) {
      console.warn('[Quest] Fallback也失败:', e2)
    }
  } finally {
    loading.value = false
  }
}

async function refreshTasks() {
  if (refreshCount.value >= 3) return
  refreshCount.value++
  loading.value = true
  try {
    const res = await dailyTaskApi.refreshTasks()
    tasks.value = res.tasks || []
  } catch (e) {
    console.warn('[Quest] 刷新失败:', e)
  } finally {
    loading.value = false
  }
}

async function goToTask(task) {
  if (task.status === 'pending') {
    try {
      await dailyTaskApi.updateTaskStatus(task.id, { status: 'in_progress' })
    } catch (e) { /* 忽略 */ }
    task.status = 'in_progress'
  }

  if (task.task_type === 'simple') {
    const nodeId = task.target_node_id || 'ch01_data_concept'
    router.push(`/app/learn/${nodeId}`)
  } else if (task.task_type === 'advanced') {
    router.push('/app/daily-practice')
  } else if (task.task_type === 'review') {
    router.push('/app/review')
  }
}

function formatTime(seconds) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h > 0) return `${h}时${m}分${s}秒`
  if (m > 0) return `${m}分${s}秒`
  return `${s}秒`
}
</script>

<style lang="scss" scoped>
.quest-view { max-width: 720px; margin: 0 auto; padding: 24px 28px; }
.quest-topbar { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 20px; }
.quest-title { font-size: 24px; font-weight: 700; color: #333; margin: 0 0 4px; }
.quest-subtitle { font-size: 14px; color: #999; margin: 0; }
.topbar-right { display: flex; align-items: center; gap: 12px; }
.refresh-count { font-size: 12px; color: #bbb; }
.refresh-btn { padding: 7px 16px; border: 1px solid rgba(59,130,246,0.25); border-radius: 8px; background: rgba(59,130,246,0.06); color: #3b82f6; font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s; white-space: nowrap; }
.refresh-btn:hover:not(:disabled) { background: rgba(59,130,246,0.12); border-color: rgba(59,130,246,0.4); }
.refresh-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.quest-summary { display: flex; gap: 12px; margin-bottom: 20px; }
.summary-item { flex: 1; text-align: center; padding: 16px; background: #fff; border-radius: 12px; border: 1px solid rgba(0,0,0,0.06); }
.summary-value { display: block; font-size: 28px; font-weight: 700; color: #333; }
.summary-label { display: block; font-size: 12px; color: #999; margin-top: 2px; }
.quest-loading { text-align: center; padding: 80px 0; color: #999; font-size: 15px; }
.quest-empty { text-align: center; padding: 80px 0; color: #999; }
.quest-empty button { margin-top: 12px; padding: 8px 24px; border-radius: 8px; border: 1px solid rgba(59,130,246,0.3); background: rgba(59,130,246,0.08); color: #3b82f6; cursor: pointer; }
.quest-list { display: flex; flex-direction: column; gap: 16px; }
.study-time-card { display: flex; align-items: center; justify-content: space-between; padding: 14px 20px; background: linear-gradient(135deg, #f0fdf4, #dcfce7); border-radius: 12px; border: 1px solid rgba(34,197,94,0.2); }
.time-label { font-size: 14px; font-weight: 600; color: #16a34a; }
.time-value { font-size: 16px; font-weight: 700; color: #15803d; font-variant-numeric: tabular-nums; }
.task-card { display: flex; align-items: center; gap: 16px; padding: 20px 24px; background: #fff; border-radius: 16px; border: 1px solid rgba(0,0,0,0.06); transition: all 0.3s; }
.task-card.task-completed { opacity: 0.75; background: #fafafa; }
.task-card.type-simple { border-left: 4px solid #3b82f6; }
.task-card.type-advanced { border-left: 4px solid #f97316; }
.task-card.type-review { border-left: 4px solid var(--color-primary); }
.task-left { flex-shrink: 0; }
.task-icon-wrapper { width: 48px; height: 48px; border-radius: 14px; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,0.03); font-size: 24px; }
.type-simple .task-icon-wrapper { background: rgba(59,130,246,0.08); }
.type-advanced .task-icon-wrapper { background: rgba(249,115,22,0.08); }
.type-review .task-icon-wrapper { background: rgba(139,92,246,0.08); }
.task-body { flex: 1; min-width: 0; }
.task-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.task-type-tag { font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 6px; }
.task-type-tag.simple { background: rgba(59,130,246,0.1); color: #3b82f6; }
.task-type-tag.advanced { background: rgba(249,115,22,0.1); color: #f97316; }
.task-type-tag.review { background: rgba(139,92,246,0.1); color: var(--color-primary); }
.task-time { font-size: 12px; color: #bbb; }
.task-title { font-size: 16px; font-weight: 700; color: #333; margin: 0 0 4px; }
.task-desc { font-size: 13px; color: #999; margin: 0; line-height: 1.5; }
.task-progress-bar { height: 4px; background: rgba(0,0,0,0.06); border-radius: 2px; margin-top: 10px; overflow: hidden; }
.task-progress-fill { height: 100%; background: linear-gradient(90deg, #3b82f6, #6366f1); border-radius: 2px; transition: width 0.5s; }
.task-right { flex-shrink: 0; }
.task-completed-badge { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.task-completed-badge svg { width: 28px; height: 28px; }
.task-completed-badge span { font-size: 11px; color: #22c55e; font-weight: 600; }
.task-action-btn { padding: 9px 20px; border: none; border-radius: 10px; font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s; white-space: nowrap; }
.task-action-btn.simple { background: linear-gradient(135deg, #3b82f6, #6366f1); color: #fff; }
.task-action-btn.advanced { background: linear-gradient(135deg, #f97316, #fb923c); color: #fff; }
.task-action-btn.review { background: linear-gradient(135deg, var(--color-primary), #a78bfa); color: #fff; }
.task-action-btn:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.12); }
</style>
