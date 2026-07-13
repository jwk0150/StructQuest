/** 全局在线计时器 —— 追踪用户在任何页面的活跃时间（非学习页面也统计） */
import { ref, onMounted, onUnmounted } from 'vue'

const GLOBAL_KEY = 'learn-global-activity'
const HEARTBEAT_INTERVAL = 5000  // 每5秒记录一次心跳

function getTodayKey() {
  return new Date().toISOString().slice(0, 10)
}

function getGlobalLog() {
  try {
    return JSON.parse(localStorage.getItem(GLOBAL_KEY) || '[]')
  } catch { return [] }
}

function saveGlobalLog(log) {
  try {
    localStorage.setItem(GLOBAL_KEY, JSON.stringify(log))
  } catch {}
}

/** 获取今日全局在线秒数 */
export function getTodayGlobalSeconds() {
  const log = getGlobalLog()
  const today = getTodayKey()
  const record = log.find(r => r.date === today)
  return record ? (record.totalSeconds || 0) : 0
}

/** 格式化秒数为 "X小时Y分钟" */
export function formatStudyDuration(totalSeconds) {
  const h = Math.floor(totalSeconds / 3600)
  const m = Math.floor((totalSeconds % 3600) / 60)
  if (h > 0) return `${h}小时${m}分钟`
  return `${m}分钟`
}

/** 全局计时器：在 App 根组件挂载，追踪全天在线时长 */
export function useGlobalTimer() {
  const todaySeconds = ref(0)
  let heartbeatTimer = null
  let lastHeartbeat = Date.now()   // 上次心跳时间（用于计算经过秒数）
  let lastUserActivity = Date.now() // 上次用户操作时间（用于判断是否离开）
  let paused = false

  function onActivity() {
    lastUserActivity = Date.now()
    if (paused) {
      // 用户回来了，重新开始计时
      paused = false
      lastHeartbeat = Date.now()
    }
  }

  function onVisibilityChange() {
    if (document.hidden) {
      // 标签页隐藏 → 先 flush 已累积时间，再暂停
      heartbeat()
      paused = true
    } else {
      // 标签页恢复 → 重新开始计时
      lastUserActivity = Date.now()
      lastHeartbeat = Date.now()
      paused = false
    }
  }

  function heartbeat() {
    if (paused) return

    const now = Date.now()

    // 用户超过60秒无操作 → 自动暂停
    if (now - lastUserActivity > 60000) {
      paused = true
      return
    }

    // 计算从上次心跳到现在的间隔（固定累加，不受频繁 mousemove 干扰）
    const elapsed = Math.floor((now - lastHeartbeat) / 1000)
    if (elapsed > 0) {
      const log = getGlobalLog()
      const today = getTodayKey()
      const idx = log.findIndex(r => r.date === today)
      if (idx >= 0) {
        log[idx].totalSeconds += elapsed
      } else {
        log.push({ date: today, totalSeconds: elapsed })
      }
      saveGlobalLog(log)
      todaySeconds.value = getTodayGlobalSeconds()
    }

    lastHeartbeat = now
  }

  onMounted(() => {
    // 初始化
    todaySeconds.value = getTodayGlobalSeconds()

    // 监听用户活动
    const events = ['mousemove', 'keydown', 'scroll', 'click', 'touchstart']
    events.forEach(e => window.addEventListener(e, onActivity, { passive: true }))
    document.addEventListener('visibilitychange', onVisibilityChange)

    // 定时心跳
    heartbeatTimer = setInterval(heartbeat, HEARTBEAT_INTERVAL)
  })

  onUnmounted(() => {
    if (heartbeatTimer) clearInterval(heartbeatTimer)
    const events = ['mousemove', 'keydown', 'scroll', 'click', 'touchstart']
    events.forEach(e => window.removeEventListener(e, onActivity))
    document.removeEventListener('visibilitychange', onVisibilityChange)
    // 最后记录一次
    heartbeat()
  })

  return { todaySeconds }
}
