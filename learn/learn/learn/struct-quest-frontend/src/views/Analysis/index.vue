<template>
  <div class="analysis-container">
    <header class="analysis-header">
      <div class="header-left">
        <h1>学习数据分析</h1>
        <p>基于 AI 的全方位学习状态评估</p>
      </div>
      <div class="header-right">
        <el-button type="primary" :icon="Download">导出分析报告</el-button>
      </div>
    </header>

    <div class="analysis-grid">
      <!-- 核心指标 -->
      <section class="card-container mastery-card">
        <h3>知识掌握度</h3>
        <div class="chart-wrapper">
          <v-chart class="chart" :option="radarOption" autoresize />
        </div>
      </section>

      <!-- 学习趋势 -->
      <section class="card-container trend-card">
        <h3>学习趋势</h3>
        <div class="chart-wrapper">
          <v-chart class="chart" :option="lineOption" autoresize />
        </div>
      </section>

      <!-- 模块分布 -->
      <section class="card-container distribution-card">
        <h3>学习时长分布</h3>
        <div class="chart-wrapper">
          <v-chart class="chart" :option="pieOption" autoresize />
        </div>
      </section>

      <!-- 学习热力图 -->
      <section class="card-container heatmap-card">
        <h3>学习活跃度</h3>
        <div class="chart-wrapper heatmap-wrapper">
          <v-chart class="chart" :option="heatmapOption" autoresize />
        </div>
      </section>

      <!-- AI 总结报告 -->
      <section class="card-container ai-report-card">
        <div class="card-header">
          <div class="title-with-icon">
            <el-icon class="ai-icon"><MagicStick /></el-icon>
            <h3>AI 总结与建议</h3>
          </div>
        </div>
        <div class="report-content">
          <!-- ★ 实时学习统计 -->
          <div class="report-stats-row">
            <div class="stat-card">
              <span class="stat-label">本日学习时长</span>
              <span class="stat-value">{{ todayDisplay || '0分钟' }}</span>
            </div>
            <div class="stat-card">
              <span class="stat-label">本周累计学习</span>
              <span class="stat-value">{{ weekDisplay || '0小时' }}</span>
            </div>
            <div class="stat-card">
              <span class="stat-label">总学习时长</span>
              <span class="stat-value">{{ totalDisplay || '0小时' }}</span>
            </div>
            <div class="stat-card">
              <span class="stat-label">已完成章节</span>
              <span class="stat-value">{{ completedChapters }}/{{ totalChapters }}</span>
            </div>
            <div class="stat-card">
              <span class="stat-label">章节完成率</span>
              <span class="stat-value" :style="{ color: chapterRateColor }">{{ chapterCompletionRate }}%</span>
            </div>
            <div class="stat-card">
              <span class="stat-label">活跃度</span>
              <span class="stat-value" :style="{ color: activityColor }">{{ activity }}%</span>
            </div>
          </div>

          <!-- ★ 最近完成章节 -->
          <div v-if="recentChapters.length > 0" class="report-section">
            <h4>🏆 最近完成</h4>
            <div class="recent-chips">
              <span v-for="ch in recentChapters" :key="ch.node_id" class="recent-chip">{{ ch.title }}</span>
            </div>
          </div>

          <!-- ★ 激励文案 -->
          <div v-if="dailyEncouragement" class="report-section">
            <h4>💪 每日激励</h4>
            <p class="encouragement-text">{{ dailyEncouragement }}</p>
          </div>
          <div v-if="weeklyEncouragement" class="report-section">
            <h4>📊 每周总结</h4>
            <p class="encouragement-text">{{ weeklyEncouragement }}</p>
          </div>

          <div class="report-section">
            <h4>🎯 弱项分析</h4>
            <p v-if="weakAnalysisText" v-html="weakAnalysisText"></p>
            <p v-else>正在分析你的学习数据...</p>
          </div>
          <div class="report-section recommendation" v-if="suggestionsList.length > 0">
            <h4>💡 个性化建议</h4>
            <ul>
              <li v-for="(suggestion, idx) in suggestionsList" :key="idx">{{ suggestion }}</li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, provide, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { RadarChart, LineChart, PieChart, HeatmapChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  VisualMapComponent,
  CalendarComponent,
  GridComponent
} from 'echarts/components'
import VChart, { THEME_KEY } from 'vue-echarts'
import { MagicStick, Download } from '@element-plus/icons-vue'
import { http } from '../../utils/request'
import { getStorage, STORAGE_KEYS } from '../../utils/storage'

// 注册 ECharts 必须的组件
use([
  CanvasRenderer, RadarChart, LineChart, PieChart, HeatmapChart,
  TitleComponent, TooltipComponent, LegendComponent, VisualMapComponent,
  CalendarComponent, GridComponent
])

provide(THEME_KEY, 'light')

// ══════════════════════════════════════════
// ★ 真实学习统计（从后端加载，降级到 localStorage）
// ══════════════════════════════════════════
const todayDisplay = ref('')
const weekDisplay = ref('')
const totalDisplay = ref('')
const activity = ref(0)
const dailyEncouragement = ref('')
const weeklyEncouragement = ref('')
const completedChapters = ref(0)
const totalChapters = ref(0)
const chapterCompletionRate = ref(0)
const recentChapters = ref([])
const weakAnalysisText = ref('')
const suggestionsList = ref([])

/** 从 localStorage 读取今日学习秒数 */
function getLocalTodaySeconds() {
  try {
    const log = JSON.parse(localStorage.getItem('learn-activity-log') || '[]')
    const today = new Date().toISOString().slice(0, 10)
    const record = log.find(function(r) { return r.date === today })
    return record?.totalSeconds || 0
  } catch { return 0 }
}

/** 格式化秒数 */
function formatDur(sec) {
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  if (h > 0) return `${h}小时${m}分钟`
  return `${m}分钟`
}

/** 活跃度颜色 */
const activityColor = computed(() => {
  if (activity.value >= 80) return '#22c55e'
  if (activity.value >= 60) return '#3b82f6'
  if (activity.value >= 40) return '#f59e0b'
  return '#ef4444'
})
/** 章节完成率颜色 */
const chapterRateColor = computed(() => {
  if (chapterCompletionRate.value >= 80) return '#22c55e'
  if (chapterCompletionRate.value >= 50) return '#3b82f6'
  if (chapterCompletionRate.value >= 20) return '#f59e0b'
  return '#ef4444'
})

onMounted(async () => {
  // 先从 localStorage 获取基础数据
  const localSecs = getLocalTodaySeconds()
  todayDisplay.value = formatDur(localSecs)

  try {
    // 加载基础统计数据
    const statsRes = await http.get('/study/stats')
    todayDisplay.value = statsRes.today_display
    weekDisplay.value = statsRes.week_display
    totalDisplay.value = statsRes.total_display || ''
    activity.value = statsRes.activity
    completedChapters.value = statsRes.completed_chapters || 0
    totalChapters.value = statsRes.total_chapters || 0
    chapterCompletionRate.value = statsRes.chapter_completion_rate || 0
    recentChapters.value = statsRes.recent_chapters || []
    dailyEncouragement.value = statsRes.daily_encouragement
    weeklyEncouragement.value = statsRes.weekly_encouragement

    // ★ 加载图表数据（新接口）
    const chartRes = await http.get('/study/chart-data')

    // 更新雷达图
    if (chartRes.radar) {
      radarOption.value.radar.indicator = chartRes.radar.categories.map(cat => ({
        name: cat,
        max: 100,
      }))
      radarOption.value.series[0].data = [{
        value: chartRes.radar.values,
        name: '当前水平',
        itemStyle: { color: '#10A37F' },
        areaStyle: { color: 'rgba(16, 163, 127, 0.2)' }
      }]
    }

    // 更新折线图
    if (chartRes.trend) {
      lineOption.value.xAxis.data = chartRes.trend.labels
      lineOption.value.series[0].data = chartRes.trend.data
    }

    // 更新饼图
    if (chartRes.pie) {
      pieOption.value.series[0].data = chartRes.pie.map((item, idx) => ({
        value: item.value,
        name: item.name,
        itemStyle: {
          color: ['#10A37F', '#6366F1', '#2563EB', '#F59E0B'][idx]
        }
      }))
    }

    // 更新热力图
    if (chartRes.heatmap && chartRes.heatmap.length > 0) {
      heatmapOption.value.series.data = chartRes.heatmap
    }

    // 更新弱项分析和建议
    weakAnalysisText.value = chartRes.weak_analysis || ''
    suggestionsList.value = chartRes.suggestions || []

  } catch (e) {
    console.error('[Analysis] 数据加载失败:', e)

    // 降级：仅用 localStorage 数据，计算简单的激励文案
    const h = Math.floor(localSecs / 3600)
    if (h < 0.5) dailyEncouragement.value = '今天已经开始学习，继续保持。'
    else if (h < 1) dailyEncouragement.value = '不错，你已经超过很多普通学习者。'
    else if (h < 2) dailyEncouragement.value = '学习状态很好，正在持续积累知识。'
    else if (h < 4) dailyEncouragement.value = '优秀的学习习惯正在形成。'
    else dailyEncouragement.value = '今天的投入非常出色，坚持下去会有巨大收获。'
    activity.value = Math.min(100, Math.floor(localSecs / 36))

    // 图表保持默认Mock数据作为fallback
    console.warn('[Analysis] 使用默认图表数据降级显示')
  }
})

// 雷达图配置：知识掌握度
const radarOption = ref({
  radar: {
    indicator: [
      { name: '线性表', max: 100 },
      { name: '栈与队列', max: 100 },
      { name: '树形结构', max: 100 },
      { name: '图论', max: 100 },
      { name: '查找算法', max: 100 },
      { name: '排序算法', max: 100 }
    ],
    shape: 'circle',
    splitNumber: 5,
    axisName: { color: '#6B7280' },
    splitLine: { lineStyle: { color: ['#F3F4F6'] } },
    splitArea: { show: false },
    axisLine: { lineStyle: { color: '#F3F4F6' } }
  },
  series: [
    {
      type: 'radar',
      data: [
        {
          value: [85, 70, 45, 20, 30, 40],
          name: '当前水平',
          itemStyle: { color: '#10A37F' },
          areaStyle: { color: 'rgba(16, 163, 127, 0.2)' }
        }
      ]
    }
  ]
})

// 折线图配置：学习趋势
const lineOption = ref({
  grid: { top: 40, bottom: 40, left: 40, right: 20 },
  xAxis: {
    type: 'category',
    data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    axisLine: { lineStyle: { color: '#E5E7EB' } },
    axisTick: { show: false }
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { type: 'dashed', color: '#F3F4F6' } }
  },
  tooltip: { trigger: 'axis' },
  series: [
    {
      data: [120, 200, 150, 80, 70, 110, 130],
      type: 'line',
      smooth: true,
      itemStyle: { color: '#6366F1' },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [{ offset: 0, color: 'rgba(99, 102, 241, 0.3)' }, { offset: 1, color: 'rgba(99, 102, 241, 0)' }]
        }
      }
    }
  ]
})

// 饼图配置：时长分布
const pieOption = ref({
  tooltip: { trigger: 'item' },
  legend: { bottom: '0%', left: 'center', icon: 'circle', textStyle: { fontSize: 12 } },
  series: [
    {
      name: '时长分布',
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      emphasis: { label: { show: true, fontSize: '14', fontWeight: 'bold' } },
      data: [
        { value: 40, name: '阅读讲解', itemStyle: { color: '#10A37F' } },
        { value: 30, name: '动手练习', itemStyle: { color: '#6366F1' } },
        { value: 20, name: 'AI 交流', itemStyle: { color: '#2563EB' } },
        { value: 10, name: '视频观看', itemStyle: { color: '#F59E0B' } }
      ]
    }
  ]
})

// 热力图配置：活跃度
function getVirtualData(year) {
  const date = +new Date(year, 0, 1);
  const end = +new Date(year + 1, 0, 1);
  const dayTime = 3600 * 24 * 1000;
  const data = [];
  for (let time = date; time < end; time += dayTime) {
    data.push([
      new Intl.DateTimeFormat('en-US').format(new Date(time)),
      Math.floor(Math.random() * 1000)
    ]);
  }
  return data;
}

const heatmapOption = ref({
  tooltip: { position: 'top' },
  visualMap: {
    min: 0, max: 1000, type: 'piecewise', orient: 'horizontal', left: 'center', top: 0,
    pieces: [
      { min: 0, max: 200, color: '#ebedf0' },
      { min: 201, max: 400, color: '#9be9a8' },
      { min: 401, max: 600, color: '#40c463' },
      { min: 601, max: 800, color: '#30a14e' },
      { min: 801, color: '#216e39' }
    ]
  },
  calendar: {
    top: 60, left: 30, right: 30, cellSize: ['auto', 13], range: '2026',
    itemStyle: { borderWidth: 0.5 }, yearLabel: { show: false },
    dayLabel: { firstDay: 1, nameMap: 'cn' }
  },
  series: {
    type: 'heatmap', coordinateSystem: 'calendar', data: getVirtualData(2026)
  }
})
</script>

<style lang="scss" scoped>
.analysis-container {
  padding: 40px;
  max-width: 1400px;
  margin: 0 auto;
}

.analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 40px;
  h1 { font-size: 32px; margin: 0 0 8px 0; }
  p { color: var(--text-secondary); margin: 0; }
}

.analysis-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

.card-container {
  background: white;
  border-radius: 24px;
  padding: 24px;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
  
  h3 { font-size: 18px; margin: 0 0 24px 0; color: var(--text-main); }
}

.chart-wrapper {
  height: 300px;
  width: 100%;
  .chart { height: 100%; width: 100%; }
}

.mastery-card, .trend-card, .distribution-card {
  grid-column: span 1;
}

.heatmap-card {
  grid-column: span 3;
  .heatmap-wrapper { height: 200px; }
}

.ai-report-card {
  grid-column: span 3;
  background: linear-gradient(145deg, #ffffff 0%, #f7fcf9 100%);
  border-left: 6px solid var(--color-primary);
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    .title-with-icon {
      display: flex; align-items: center; gap: 12px;
      .ai-icon { font-size: 24px; color: var(--color-primary); }
      h3 { margin: 0; }
    }
  }
  
  .report-content {
    display: grid;
    grid-template-columns: 1fr 1fr 1.2fr;
    gap: 40px;
    
    .report-section {
      h4 { margin: 0 0 12px 0; font-size: 16px; color: var(--text-main); }
      p { font-size: 14px; line-height: 1.6; color: var(--text-secondary); margin: 0; }
      strong { color: var(--color-primary); }
    }
    
    .recommendation {
      background: white;
      padding: 20px;
      border-radius: 16px;
      border: 1px solid var(--border-light);
      ul {
        margin: 0; padding-left: 18px;
        li { font-size: 14px; color: var(--text-secondary); margin-bottom: 8px; line-height: 1.4; }
      }
    }
  }
}

/* ★ 统计卡片行 */
.report-stats-row {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}
.stat-card {
  flex: 1;
  background: var(--bg-secondary);
  border-radius: 16px;
  padding: 20px 16px;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 8px;
  .stat-label {
    font-size: 13px;
    color: var(--text-tertiary);
    font-weight: 500;
  }
  .stat-value {
    font-size: 20px;
    font-weight: 800;
    color: var(--text-main);
    font-family: var(--font-display);
  }
}
.encouragement-text {
  font-size: 15px !important;
  color: var(--color-primary) !important;
  font-weight: 600;
  padding: 12px 16px;
  background: rgba(16, 163, 127, 0.06);
  border-radius: 12px;
  border-left: 3px solid var(--color-primary);
}
.recent-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.recent-chip {
  padding: 6px 14px;
  background: rgba(16, 163, 127, 0.08);
  color: var(--color-primary);
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
}

@media (max-width: 1200px) {
  .analysis-grid { grid-template-columns: 1fr 1fr; }
  .heatmap-card, .ai-report-card { grid-column: span 2; }
  .report-content { grid-template-columns: 1fr !important; gap: 24px !important; }
}
</style>
