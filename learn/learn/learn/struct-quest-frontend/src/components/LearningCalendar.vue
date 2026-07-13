<template>
  <div class="learning-calendar">
    <div class="calendar-header">
      <div class="calendar-title-row">
        <span class="calendar-icon">📅</span>
        <h3 class="calendar-title">学习日历</h3>
        <span class="calendar-mode-tag" :style="{ background: modeColor + '15', color: modeColor }">{{ modeLabel }}</span>
      </div>
      <div class="calendar-nav">
        <button class="nav-btn" @click="prevMonth">‹</button>
        <span class="month-label">{{ currentYear }}年 {{ currentMonth }}月</span>
        <button class="nav-btn" @click="nextMonth">›</button>
        <button class="today-btn" @click="goToday">今</button>
      </div>
    </div>

    <!-- 星期标题 -->
    <div class="week-header">
      <span v-for="d in weekDays" :key="d" class="weekday">{{ d }}</span>
    </div>

    <!-- 日历格子 -->
    <div class="calendar-grid">
      <div
        v-for="(day, idx) in calendarDays"
        :key="idx"
        class="cal-cell"
        :class="getCellClass(day)"
        @click="day.date && selectDay(day)"
      >
        <span class="cell-date">{{ day.date || '' }}</span>
        <span v-if="day.isToday" class="today-marker">今</span>
        <div
          v-if="day.hasData"
          class="cell-heatmap"
          :style="{ background: getHeatmapColor(day) }"
          :title="'学习 ' + (day.minutes || 0) + ' 分钟'"
        ></div>
      </div>
    </div>

    <!-- 今日概览 -->
    <div class="daily-summary">
      <div class="summary-item">
        <span class="summary-label">今日</span>
        <span class="summary-value">{{ todayData.minutes || 0 }}分钟</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">完成</span>
        <span class="summary-value">{{ todayData.completedCount || 0 }}章节</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">本周活跃</span>
        <span class="summary-value highlight">{{ weekActiveDays }}天 🔥</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">连续学习</span>
        <span class="summary-value streak">{{ currentStreak }}天</span>
      </div>
    </div>

    <!-- 本周柱状图 -->
    <div class="week-chart">
      <h4 class="chart-label">本周趋势</h4>
      <div class="chart-bars">
        <div
          v-for="(bar, i) in weekBars"
          :key="i"
          class="chart-bar-col"
        >
          <div class="bar-wrapper">
            <div class="bar-fill" :style="{ height: bar.height + '%', background: bar.minutes > 0 ? modeColor : '#eee' }"></div>
          </div>
          <span class="bar-day">{{ bar.label }}</span>
          <span v-if="bar.minutes > 0" class="bar-minutes">{{ bar.minutes }}m</span>
        </div>
      </div>
    </div>

    <!-- 选中日期的详情弹窗 -->
    <transition name="fade">
      <div v-if="selectedDate" class="day-detail-popover" :style="popoverStyle">
        <div class="popover-arrow"></div>
        <div class="popover-content">
          <h4 class="popover-title">{{ selectedDateDisplay }}</h4>
          
          <div v-if="selectedDayData.hasData" class="popover-body">
            <div class="detail-section" v-if="selectedDayData.completedNodes?.length">
              <span class="section-icon done">✅</span>
              <div class="section-body">
                <span class="section-label">已完成</span>
                <div class="node-chips">
                  <span v-for="(n, i) in selectedDayData.completedNodes" :key="i" class="node-chip done">{{ n }}</span>
                </div>
              </div>
            </div>
            
            <div class="detail-section" v-if="selectedDayData.learningNodes?.length">
              <span class="section-icon learning">📖</span>
              <div class="section-body">
                <span class="section-label">学习中</span>
                <div class="node-chips">
                  <span v-for="(n, i) in selectedDayData.learningNodes" :key="i" class="node-chip learning">{{ n }}</span>
                </div>
              </div>
            </div>

            <div class="detail-section" v-if="selectedDayData.examResults?.length">
              <span class="section-icon exam">📝</span>
              <div class="section-body">
                <span class="section-label">测试记录</span>
                <div v-for="(er, i) in selectedDayData.examResults" :key="i" class="exam-row">
                  <span class="exam-node">{{ er.node }}</span>
                  <span class="exam-score" :class="er.passed ? 'pass' : 'fail'">{{ er.score }}分</span>
                </div>
              </div>
            </div>

            <div class="detail-time">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#999" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
              总时长：<strong>{{ selectedDayData.minutes || 0 }} 分钟</strong>
            </div>

            <div v-if="selectedDayData.aiComment" class="ai-comment">
              💡 <strong>AI点评：</strong>{{ selectedDayData.aiComment }}
            </div>
          </div>
          
          <div v-else class="popover-empty">
            {{ selectedDate.isFuture ? '未来日期' : (selectedDate.isPast ? '当日无记录' : '') }}
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onActivated } from 'vue'
import { useSessionStore } from '../store/session'
import { http } from '../utils/request'

const props = defineProps({
  mode: { type: String, default: 'beginner' },
})

const session = useSessionStore()
const weekDays = ['一', '二', '三', '四', '五', '六', '日']

// 当前月份状态
const now = new Date()
const currentYear = ref(now.getFullYear())
const currentMonth = ref(now.getMonth() + 1)

// 选中的日期（用于展示详情）
const selectedDate = ref(null)
const selectedCellRect = ref({ x: 0, y: 0 })

// ═══ 模式颜色映射 ═══
const modeColorMap = {
  basic: '#22c55e',
  beginner: '#3b82f6',
  exam: '#f97316',
}
const modeLabelMap = {
  basic: '基础模式',
  beginner: '入门模式',
  exam: '考试模式',
}
const modeColor = computed(() => modeColorMap[props.mode] || modeColorMap.beginner)
const modeLabel = computed(() => modeLabelMap[props.mode] || modeLabelMap.beginner)

// ═══ 日历数据（从后端加载）═══
const calendarRecords = ref({})
const calendarLoading = ref(false)

/** 从后端加载指定月份的日历数据 */
async function loadCalendarData(year, month) {
  calendarLoading.value = true

  try {
    const params = {}
    if (year) params.year = year
    if (month) params.month = month

    const res = await http.get('/study/calendar', params)

    if (res && res.records) {
      // 后端返回的records是对象，直接使用
      calendarRecords.value = res.records
      console.log(`[Calendar] 加载了 ${res.total_days_with_activity || Object.keys(res.records).length} 天的学习记录`)
    } else {
      calendarRecords.value = {}
    }
  } catch (e) {
    console.error('[Calendar] 加载失败:', e)

    // 降级：使用空数据（不显示模拟数据）
    console.warn('[Calendar] API加载失败，显示空白')
    calendarRecords.value = {}
  } finally {
    calendarLoading.value = false
  }
}

// ═══ 计算属性：日历网格 ═══
const calendarDays = computed(() => {
  const year = currentYear.value
  const month = currentMonth.value
  const firstDay = new Date(year, month - 1, 1)
  const lastDay = new Date(year, month, 0)
  const daysInMonth = lastDay.getDate()
  
  // 获取周一为起始的偏移量（JS中周日=0，我们用周一=0）
  let startWeekday = firstDay.getDay() - 1
  if (startWeekday < 0) startWeekday = 6
  
  const days = []
  const today = new Date()
  const todayStr = formatDateKey(today)
  
  // 前置空白
  for (let i = 0; i < startWeekday; i++) {
    days.push({})
  }
  
  // 当月天数
  for (let d = 1; d <= daysInMonth; d++) {
    const dateKey = `${year}-${String(month).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    const isToday = dateKey === todayStr
    const data = calendarRecords.value[dateKey]
    const recordDate = new Date(year, month - 1, d)
    const isFuture = recordDate > today
    
    days.push({
      date: d,
      dateKey,
      isToday,
      hasData: !!data && !isFuture,
      isPast: !isToday && !isFuture,
      isFuture,
      minutes: data?.minutes || 0,
      completedCount: data?.completedCount || 0,
      ...(data || {}),
    })
  }
  
  return days
})

// ═══ 今日数据 ═══
const todayData = computed(() => {
  const key = formatDateKey(new Date())
  return calendarRecords.value[key] || {}
})

// ═══ 本周统计 ═══
const weekActiveDays = computed(() => {
  const today = new Date()
  let count = 0
  const dayOfWeek = today.getDay() || 7
  
  for (let i = 0; i < dayOfWeek; i++) {
    const d = new Date(today)
    d.setDate(today.getDate() - i)
    const key = formatDateKey(d)
    if (calendarRecords.value[key]?.minutes > 0) count++
  }
  return count
})

const weekBars = computed(() => {
  const today = new Date()
  const dayOfWeek = today.getDay() || 7
  const bars = []
  
  for (let i = dayOfWeek - 1; i >= 0; i--) {
    const d = new Date(today)
    d.setDate(today.getDate() - i)
    const key = formatDateKey(d)
    const data = calendarRecords.value[key]
    bars.push({
      label: weekDays[d.getDay() === 0 ? 6 : d.getDay() - 1],
      minutes: data?.minutes || 0,
      height: data ? Math.min(100, (data.minutes / 90) * 100) : 0,
    })
  }
  
  while (bars.length < 7) bars.push({ label: '', minutes: 0, height: 0 })
  return bars.slice(0, 7)
})

// 连续学习天数
const currentStreak = computed(() => {
  const today = new Date()
  let streak = 0
  
  // 从昨天开始往前数
  for (let i = 1; i < 365; i++) {
    const d = new Date(today)
    d.setDate(today.getDate() - i)
    const key = formatDateKey(d)
    if (calendarRecords.value[key]?.minutes > 0) streak++
    else break
  }
  
  // 如果今天也有记录，+1
  if (calendarRecords.value[formatDateKey(today)]?.minutes > 0) streak++
  return streak
})

// ═══ 选中日期详情 ═══
const selectedDayData = computed(() => {
  if (!selectedDate.value) return {}
  const key = selectedDate.value.dateKey
  return calendarRecords.value[key] || {}
})

const selectedDateDisplay = computed(() => {
  if (!selectedDate.value) return ''
  const d = selectedDate.value
  return `${currentYear.value}年${currentMonth.value}月${d.date || ''}日`
})

const popoverStyle = computed(() => ({
  left: selectedCellRect.value.x + 'px',
  top: selectedCellRect.value.y + 'px',
}))

// ═══ 方法 ═══
function prevMonth() {
  if (currentMonth.value === 1) {
    currentMonth.value = 12
    currentYear.value--
  } else {
    currentMonth.value--
  }
  selectedDate.value = null
  onMonthChanged()
}

function nextMonth() {
  if (currentMonth.value === 12) {
    currentMonth.value = 1
    currentYear.value++
  } else {
    currentMonth.value++
  }
  selectedDate.value = null
  onMonthChanged()
}

function goToday() {
  const now = new Date()
  currentYear.value = now.getFullYear()
  currentMonth.value = now.getMonth() + 1
}

function selectDay(day) {
  if (!day.date) return
  if (day.isFuture) return
  
  // 如果点击同一个，取消选中
  if (selectedDate.value?.dateKey === day.dateKey) {
    selectedDate.value = null
    return
  }
  
  selectedDate.value = day
  // 获取元素位置来定位弹窗
  setTimeout(() => {
    const el = document.querySelector(`.cal-cell.selected`)
    if (el) {
      const rect = el.getBoundingClientRect()
      selectedCellRect.value = {
        x: rect.left + rect.width / 2 - 140,
        y: rect.bottom + 8,
      }
    }
  }, 10)
}

function getCellClass(day) {
  const cls = []
  if (!day.date) cls.push('empty')
  else if (day.isToday) cls.push('today', 'selected')
  else if (day.isFuture) cls.push('future')
  else if (day.hasData) cls.push('has-data')
  else if (day.isPast) cls.push('past')
  
  if (selectedDate.value?.dateKey === day.dateKey) cls.push('selected')
  return cls.join(' ')
}

function getHeatmapColor(day) {
  if (!day.minutes) return ''
  if (day.minutes > 60) return `rgba(${hexToRgb(modeColor.value)}, 0.85)`
  if (day.minutes > 30) return `rgba(${hexToRgb(modeColor.value)}, 0.55)`
  return `rgba(${hexToRgb(modeColor.value)}, 0.25)`
}

function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  return result 
    ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}`
    : '59, 130, 246' // default blue
}

function formatDateKey(date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

// 点击外部关闭弹窗
onMounted(() => {
  // 加载当前月份数据
  loadCalendarData(currentYear.value, currentMonth.value)

  document.addEventListener('click', (e) => {
    if (!e.target.closest('.learning-calendar')) {
      selectedDate.value = null
    }
  })
})

// keep-alive 激活时自动刷新当天数据
onActivated(() => {
  loadCalendarData(currentYear.value, currentMonth.value)
})

// 监听月份变化，重新加载数据
function onMonthChanged() {
  loadCalendarData(currentYear.value, currentMonth.value)
}
</script>

<style lang="scss" scoped>
.learning-calendar {
  background: #fff;
  border-radius: 14px;
  border: 1px solid #eee;
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* ── 头部 ── */
.calendar-header {
  padding: 14px 16px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.calendar-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.calendar-icon { font-size: 18px; }
.calendar-title {
  font-size: 15px;
  font-weight: 700;
  color: #333;
  margin: 0;
}
.calendar-mode-tag {
  padding: 2px 8px;
  border-radius: 8px;
  font-size: 10px;
  font-weight: 600;
}

.calendar-nav {
  display: flex;
  align-items: center;
  gap: 4px;
}
.nav-btn {
  width: 26px; height: 26px;
  border: 1px solid #e5e5e5;
  border-radius: 6px;
  background: #fafafa;
  color: #666;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  transition: all 0.15s;
  &:hover { background: #f0f0f0; border-color: #ccc; }
}
.month-label {
  font-size: 13px;
  font-weight: 600;
  color: #333;
  min-width: 85px;
  text-align: center;
}
.today-btn {
  padding: 2px 8px;
  border: 1px solid var(--mode-color, #3b82f6);
  border-radius: 6px;
  background: transparent;
  color: var(--mode-color, #3b82f6);
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s;
  &:hover { background: rgba(var(--mode-color-rgb), 0.08); }
}

/* ── 星期头 ── */
.week-header {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  padding: 6px 8px 4px;
  border-bottom: 1px solid #f5f5f5;
}
.weekday {
  text-align: center;
  font-size: 11px;
  color: #aaa;
  font-weight: 600;
  padding: 4px 0;
}

/* ── 日历格子 ── */
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
  padding: 6px 8px 8px;
}
.cal-cell {
  aspect-ratio: 1;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  min-height: 36px;

  &.empty { cursor: default; }

  &.past {
    .cell-date { color: #bbb; }
    &:hover { background: #f9f9f9; }
  }

  &.future {
    .cell-date { color: #ddd; }
    cursor: default;
  }

  &.has-data {
    &:hover {
      transform: scale(1.05);
      box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
  }

  &.today {
    background: transparent;
    border: 2px solid var(--mode-color, #3b82f6);
    .cell-date { color: var(--mode-color, #3b82f6); font-weight: 800; }
  }

  &.selected {
    border-color: var(--mode-color, #3b82f6);
    box-shadow: 0 0 0 3px rgba(var(--mode-color-rgb), 0.15);
  }
}
.cell-date {
  font-size: 12px;
  font-weight: 500;
  color: #444;
  z-index: 1;
}
.today-marker {
  position: absolute;
  bottom: 2px;
  right: 3px;
  font-size: 7px;
  font-weight: 700;
  background: var(--mode-color, #3b82f6);
  color: #fff;
  padding: 0 3px;
  border-radius: 3px;
  line-height: 1.2;
}
.cell-heatmap {
  position: absolute;
  bottom: 3px;
  left: 50%;
  transform: translateX(-50%);
  width: 20px;
  height: 4px;
  border-radius: 2px;
  z-index: 0;
}

/* ── 今日概览 ── */
.daily-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 4px;
  padding: 12px 14px;
  border-top: 1px solid #f0f0f0;
  background: #fafbfc;
}
.summary-item {
  text-align: center;
  .summary-label {
    display: block;
    font-size: 10px;
    color: #aaa;
    margin-bottom: 2px;
  }
  .summary-value {
    font-size: 13px;
    font-weight: 700;
    color: #555;
    &.highlight { color: var(--mode-color, #3b82f6); }
    &.streak { color: #E07A5F; }
  }
}

/* ── 周图表 ── */
.week-chart {
  padding: 12px 14px 14px;
  border-top: 1px solid #f0f0f0;
}
.chart-label {
  font-size: 11px;
  color: #999;
  margin: 0 0 8px;
  font-weight: 600;
}
.chart-bars {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
  height: 60px;
  align-items: flex-end;
}
.chart-bar-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}
.bar-wrapper {
  width: 22px;
  height: 48px;
  background: #f5f5f5;
  border-radius: 3px;
  display: flex;
  align-items: flex-end;
  overflow: hidden;
}
.bar-fill {
  width: 100%;
  border-radius: 3px;
  transition: height 0.4s ease;
  min-height: 2px;
}
.bar-day {
  font-size: 9px;
  color: #bbb;
}
.bar-minutes {
  font-size: 8px;
  color: #999;
  font-weight: 600;
}

/* ── 详情弹窗 ── */
.day-detail-popover {
  position: fixed;
  z-index: 200;
  width: 280px;
  background: #fff;
  border: 1px solid #e5e5e5;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.12);
  animation: popoverIn 0.2s ease;
}
@keyframes popoverIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}
.popover-arrow {
  position: absolute;
  top: -6px;
  left: 40%;
  width: 10px;
  height: 10px;
  background: #fff;
  border-left: 1px solid #e5e5e5;
  border-top: 1px solid #e5e5e5;
  transform: rotate(45deg);
}
.popover-content {
  padding: 14px 14px 12px;
}
.popover-title {
  font-size: 13px;
  font-weight: 700;
  margin: 0 0 10px;
  color: #333;
  padding-bottom: 8px;
  border-bottom: 1px solid #f5f5f5;
}
.popover-body { display: flex; flex-direction: column; gap: 8px; }
.detail-section {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}
.section-icon { font-size: 14px; flex-shrink: 0; margin-top: 1px; }
.section-body { flex: 1; min-width: 0; }
.section-label {
  display: block;
  font-size: 10px;
  color: #999;
  margin-bottom: 3px;
  font-weight: 600;
}
.node-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
}
.node-chip {
  padding: 1px 7px;
  border-radius: 5px;
  font-size: 10px;
  font-weight: 600;
  &.done { background: #dcfce7; color: #16a34a; }
  &.learning { background: #fff7ed; color: #E07A5F; }
  &.exam { background: #eff6ff; color: #2563eb; }
}
.exam-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 2px 0;
  font-size: 11px;
  .exam-node { color: #555; }
  .exam-score { font-weight: 700; &.pass { color: #22c55e; } &.fail { color: #ef4444; } }
}
.detail-time {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #888;
  margin-top: 4px;
  strong { color: #555; }
}
.ai-comment {
  margin-top: 8px;
  padding: 8px 10px;
  background: linear-gradient(135deg, rgba(139,92,246,0.06), rgba(59,130,246,0.06));
  border-radius: 8px;
  border-left: 2.5px solid #8b5cf6;
  font-size: 11px;
  color: #666;
  line-height: 1.45;
}
.popover-empty {
  text-align: center;
  padding: 16px 0;
  color: #bbb;
  font-size: 12px;
}

.fade-enter-active, .fade-leave-active { transition: all 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateY(-4px); }
</style>
