/** 学习计时器 composable——追踪用户在节点学习页的停留时长 */
import { ref, onUnmounted } from 'vue'

const ACTIVITY_KEY = 'learn-activity-log'

/** 从 localStorage 读写活跃度日志 */
function getActivityLog() {
  try {
    return JSON.parse(localStorage.getItem(ACTIVITY_KEY) || '[]')
  } catch { return [] }
}

function saveActivityLog(log) {
  localStorage.setItem(ACTIVITY_KEY, JSON.stringify(log))
}

function getTodayKey() {
  return new Date().toISOString().slice(0, 10)
}

/** 获取今日累计学习秒数（从 localStorage） */
export function getTodayStudySeconds() {
  const log = getActivityLog()
  const today = getTodayKey()
  const record = log.find(r => r.date === today)
  return record ? (record.totalSeconds || 0) : 0
}

/** 获取本周累计学习小时数 */
export function getWeekStudyHours() {
  const log = getActivityLog()
  const today = new Date()
  const weekStart = new Date(today)
  weekStart.setDate(today.getDate() - today.getDay() + (today.getDay() === 0 ? -6 : 1))
  weekStart.setHours(0, 0, 0, 0)
  let totalSeconds = 0
  for (const r of log) {
    const d = new Date(r.date)
    if (d >= weekStart) {
      totalSeconds += r.totalSeconds
    }
  }
  return Math.floor(totalSeconds / 3600)
}

/** 格式化秒数为 "X小时Y分钟" */
export function formatStudyDuration(totalSeconds) {
  const h = Math.floor(totalSeconds / 3600)
  const m = Math.floor((totalSeconds % 3600) / 60)
  if (h > 0) return `${h}小时${m}分钟`
  return `${m}分钟`
}

/**
 * 使用学习计时器——在组件 mounted 时开始计时，unmounted 时结束
 * 返回 { startTimer, stopTimer, elapsedSeconds }
 */
export function useStudyTimer() {
  const startTime = ref(null)
  const elapsedSeconds = ref(0)
  let interval = null

  function startTimer() {
    if (startTime.value !== null) return
    startTime.value = Date.now()
    elapsedSeconds.value = 0
    interval = setInterval(() => {
      if (startTime.value) {
        elapsedSeconds.value = Math.floor((Date.now() - startTime.value) / 1000)
      }
    }, 1000)
  }

  function stopTimer() {
    if (interval) {
      clearInterval(interval)
      interval = null
    }
    if (startTime.value === null) return 0
    const seconds = Math.floor((Date.now() - startTime.value) / 1000)
    startTime.value = null
    elapsedSeconds.value = 0

    // 写入 localStorage 活跃度日志
    if (seconds > 5) {
      const log = getActivityLog()
      const today = getTodayKey()
      const idx = log.findIndex(r => r.date === today)
      if (idx >= 0) {
        log[idx].totalSeconds += seconds
        log[idx].sessions += 1
      } else {
        log.push({ date: today, totalSeconds: seconds, sessions: 1 })
      }
      saveActivityLog(log)
    }

    return seconds
  }

  onUnmounted(() => {
    stopTimer()
  })

  return { startTimer, stopTimer, elapsedSeconds }
}
