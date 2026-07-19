<template>
  <div class="evaluation-page">
    <!-- ═══ 顶部：标题 + 时间筛选 + 导出 ═══ -->
    <header class="page-header">
      <div class="header-left">
        <div class="breadcrumb-row">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/home' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>AI学习效果评估</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <h1 class="page-title">AI学习效果评估中心</h1>
        <p class="page-subtitle">AI 根据你的学习行为，持续分析效果、动态调整资源、优化学习方案</p>
      </div>
      <div class="header-right">
        <el-radio-group v-model="daysRange" size="small" @change="fetchData">
          <el-radio-button :value="7">近7天</el-radio-button>
          <el-radio-button :value="14">近14天</el-radio-button>
          <el-radio-button :value="30">近30天</el-radio-button>
        </el-radio-group>
        <el-button type="primary" :icon="Download" @click="exportReport" class="export-btn">
          导出评估报告
        </el-button>
      </div>
    </header>

    <div class="loading-overlay" v-if="loading">
      <el-icon class="loading-icon"><Loading /></el-icon>
      <span>AI 正在分析你的学习数据...</span>
    </div>

    <template v-else>
      <!-- ═══ ① AI综合评估总评 ═══ -->
      <section class="section-ai-summary">
        <div class="summary-hero">
          <div class="score-ring-area">
            <div class="score-ring">
              <svg viewBox="0 0 140 140" class="ring-svg">
                <circle cx="70" cy="70" r="60" fill="none" stroke="var(--border-light)" stroke-width="10"/>
                <circle cx="70" cy="70" r="60" fill="none" stroke="url(#scoreGradient)" stroke-width="10"
                  stroke-linecap="round" :stroke-dasharray="circumference"
                  :stroke-dashoffset="scoreOffset" class="ring-progress"/>
                <defs>
                  <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#c84c5a"/>
                    <stop offset="100%" stop-color="#d97982"/>
                  </linearGradient>
                </defs>
              </svg>
              <div class="score-inner">
                <span class="score-number">{{ summary.composite_score }}</span>
                <span class="score-total">/100</span>
              </div>
            </div>
            <div class="score-stars">
              <span v-for="i in 5" :key="i" class="star" :class="{ active: i <= summary.stars }">★</span>
            </div>
          </div>
          <div class="summary-content">
            <div class="summary-status-row">
              <span class="status-badge" :class="statusClass">{{ summary.status_label }}</span>
              <span v-if="summary.trend_label" class="trend-badge">{{ summary.trend_label }}</span>
            </div>
            <p class="summary-text">{{ summary.summary_text }}</p>
            <div class="summary-highlights" v-if="summary.highlight || summary.concern">
              <span v-if="summary.highlight" class="highlight-green">{{ summary.highlight }}</span>
              <span v-if="summary.concern" class="highlight-amber">{{ summary.concern }}</span>
            </div>
          </div>
          <div class="today-recommend" v-if="summary.today_recommendation && summary.today_recommendation.topic">
            <div class="recommend-label">今日推荐</div>
            <div class="recommend-topic">《{{ displayTopic(summary.today_recommendation) }}》</div>
            <div class="recommend-meta">
              预计 {{ summary.today_recommendation.estimated_minutes }} 分钟 ·
              {{ bloomLabel(summary.today_recommendation.bloom_level) }}
            </div>
            <el-button size="small" type="primary" @click="$router.push('/app/quest')">
              开始学习
            </el-button>
          </div>
        </div>
      </section>

      <!-- ═══ ② 学习效果评估（四个评分卡）═══ -->
      <section class="section-score-cards">
        <h2 class="section-title">学习效果评估</h2>
        <div class="score-cards-grid">
          <div class="score-card" v-for="card in scoreCards" :key="card.key">
            <div class="card-icon" :style="{ background: card.gradient }">
              <el-icon :size="20"><component :is="card.icon" /></el-icon>
            </div>
            <div class="card-info">
              <span class="card-label">{{ card.label }}</span>
              <div class="card-bar-wrap">
                <div class="card-bar" :style="{ width: card.barWidth + '%', background: card.barColor }"></div>
              </div>
              <div class="card-value-row">
                <span class="card-score" :style="{ color: card.barColor }">{{ card.score }}%</span>
                <span v-if="card.delta !== undefined" class="card-delta" :class="card.delta > 0 ? 'up' : card.delta < 0 ? 'down' : ''">
                  {{ card.deltaLabel }}
                </span>
              </div>
            </div>
            <p class="card-desc">{{ card.description }}</p>
          </div>
        </div>
      </section>

      <!-- ═══ ③ 学习行为分析 ═══ -->
      <section class="section-behavior">
        <h2 class="section-title">学习行为分析</h2>
        <div class="behavior-grid">
          <!-- 学习活跃度热力图 -->
          <div class="behavior-card heatmap-area">
            <h3>学习活跃度</h3>
            <div class="mini-heatmap">
              <div class="week-row" v-for="(day, idx) in behavior.week_days" :key="idx">
                <span class="day-label">{{ day.day_name }}</span>
                <div class="day-bar-wrap">
                  <div class="day-bar" :style="{ width: Math.min(100, day.minutes / 2) + '%' }"
                    :class="{ today: day.is_today }"></div>
                </div>
                <span class="day-value">{{ day.minutes > 0 ? day.minutes + '分' : '—' }}</span>
              </div>
            </div>
            <div class="behavior-total">
              近{{ daysRange }}天累计学习 <strong>{{ behavior.total_hours }} 小时</strong> · {{ behavior.session_count }} 次学习会话
            </div>
          </div>

          <!-- 学习时段分布 -->
          <div class="behavior-card">
            <h3>学习时段</h3>
            <div class="time-slots">
              <div class="time-slot" v-for="slot in behavior.time_distribution" :key="slot.label">
                <span class="slot-label">{{ slot.label }}</span>
                <div class="slot-bar-wrap">
                  <div class="slot-bar" :style="{ width: slot.percent + '%' }"></div>
                </div>
                <span class="slot-value">{{ slot.hours }}h</span>
              </div>
            </div>
            <div class="slot-peak" v-if="behavior.peak_hour_slot">
              高峰时段：<strong>{{ behavior.peak_hour_slot }}</strong>
            </div>
          </div>

          <!-- 资源使用占比 -->
          <div class="behavior-card">
            <h3>资源使用占比</h3>
            <div class="resource-tags" v-if="behavior.resource_usage.length > 0">
              <div class="resource-tag" v-for="res in behavior.resource_usage" :key="res.key">
                <span class="rt-label">{{ res.type }}</span>
                <span class="rt-bar-wrap">
                  <span class="rt-bar" :style="{ width: res.percent + '%' }"></span>
                </span>
                <span class="rt-percent">{{ res.percent }}%</span>
              </div>
            </div>
            <div v-else class="empty-hint">暂无资源使用数据</div>
          </div>
        </div>
      </section>

      <!-- ═══ ④ AI智能诊断 ═══ -->
      <section class="section-diagnosis">
        <h2 class="section-title">AI智能诊断</h2>
        <div class="diagnosis-grid">
          <div class="diagnosis-card" v-for="card in diagnosis.cards" :key="card.id"
            :class="[card.type, 'diag-' + card.id]">
            <div class="diag-header">
              <span class="diag-icon">{{ card.icon }}</span>
              <span class="diag-title">{{ card.title }}</span>
              <el-tag v-if="card.id === 'risk' && card.risk_level" size="small"
                :type="card.risk_level === 'high' ? 'danger' : card.risk_level === 'medium' ? 'warning' : 'success'"
                effect="plain">
                {{ card.risk_level === 'high' ? '高风险' : card.risk_level === 'medium' ? '中等' : '低风险' }}
              </el-tag>
            </div>
            <p class="diag-content">{{ card.content }}</p>
          </div>
        </div>
      </section>

      <!-- ═══ ⑤⑥ 资源优化 + 学习计划优化（双栏）═══ -->
      <section class="section-bottom">
        <div class="bottom-grid">
          <!-- ⑤ AI资源优化记录 -->
          <div class="bottom-card">
            <div class="bottom-card-header">
              <h2>AI资源优化记录</h2>
              <el-tag size="small" effect="plain" type="info">{{ optimization.total }} 条记录</el-tag>
            </div>
            <div class="optimization-timeline" v-if="optimization.items.length > 0">
              <div class="timeline-item" v-for="item in optimization.items.slice(0, 4)" :key="item.id">
                <div class="tl-dot"></div>
                <div class="tl-content">
                  <div class="tl-date">{{ item.date }}</div>
                  <div class="tl-change">
                    <span class="tl-from">{{ item.from_desc }}</span>
                    <el-icon class="tl-arrow"><Right /></el-icon>
                    <span class="tl-to">{{ item.to_desc }}</span>
                  </div>
                  <div class="tl-reason">{{ item.reason }}</div>
                  <div class="tl-effect" v-if="item.improvement !== null">
                    效果提升 <span class="effect-up">{{ item.improvement > 0 ? '+' : '' }}{{ item.improvement }}%</span>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="empty-state">
              <el-icon :size="32"><Timer /></el-icon>
              <p>AI 将持续记录每次资源调整</p>
              <span class="empty-sub">完成学习后，AI 会根据效果自动优化资源推荐</span>
            </div>
            <el-button v-if="optimization.has_more" text type="primary" class="view-all-btn">
              查看全部优化记录
            </el-button>
          </div>

          <!-- ⑥ 学习计划优化 -->
          <div class="bottom-card">
            <div class="bottom-card-header">
              <h2>学习计划优化</h2>
              <div class="plan-stats">
                <span>总 {{ plan.total_minutes }} 分钟</span>
                <span class="stat-sep">·</span>
                <span>掌握度预估提升 +{{ plan.mastery_improvement }}%</span>
              </div>
            </div>
            <div class="plan-flow" v-if="plan.steps.length > 0">
              <div class="plan-step" v-for="(step, idx) in plan.steps" :key="idx">
                <div class="step-index" :class="step.status">{{ step.step_no }}</div>
                <div class="step-body">
                  <div class="step-topic">{{ displayTopic(step) }}</div>
                  <div class="step-meta">
                    <el-tag size="small" effect="plain">{{ bloomLabel(step.bloom_level) }}</el-tag>
                    <span class="step-time">{{ step.estimated_minutes }}分钟</span>
                  </div>
                </div>
                <div class="step-connector" v-if="idx < plan.steps.length - 1">
                  <el-icon><Bottom /></el-icon>
                </div>
              </div>
            </div>
            <div class="plan-rationale" v-if="plan.rationale">
              <el-icon><InfoFilled /></el-icon>
              <span>{{ plan.rationale }}</span>
            </div>
            <div class="plan-footer">
              <div class="plan-diff">
                计划难度：
                <span v-for="i in 5" :key="i" class="diff-star" :class="{ active: i <= plan.difficulty_stars }">★</span>
              </div>
              <el-button size="small" type="primary" plain @click="$router.push('/app/quest')">
                开始执行计划
              </el-button>
            </div>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Download, Loading, Timer, Right, Bottom, InfoFilled,
  TrendCharts, DataAnalysis, MagicStick, Coin,
} from '@element-plus/icons-vue'
import { evaluationApi } from '../../api/evaluation'
import { stepKnowledgeTitle } from '../../utils/knowledgeNames'

const router = useRouter()
const loading = ref(true)
const daysRange = ref(7)

// ═══ 数据 ═══
const summary = ref({ composite_score: 0, stars: 0, status_label: '—', trend_label: '', summary_text: '', highlight: '', concern: '', today_recommendation: null })
const scoreCards = ref([])
const behavior = ref({ total_hours: 0, session_count: 0, heatmap: [], time_distribution: [], resource_usage: [], week_days: [], peak_hour_slot: '' })
const diagnosis = ref({ cards: [] })
const optimization = ref({ total: 0, items: [], has_more: false })
const plan = ref({ steps: [], total_minutes: 0, difficulty_stars: 3, rationale: '', mastery_improvement: 10 })

// ═══ 计算属性 ═══
const circumference = 2 * Math.PI * 60 // 圆环周长

const scoreOffset = computed(() => {
  const pct = Math.min(100, Math.max(0, summary.value.composite_score || 0))
  return circumference - (pct / 100) * circumference
})

const statusClass = computed(() => {
  const s = summary.value.status_label
  if (s === '优秀') return 'status-excellent'
  if (s === '良好') return 'status-good'
  if (s === '一般') return 'status-normal'
  return 'status-warning'
})

// 评分卡图标映射
const cardIconMap = {
  knowledge_mastery: TrendCharts,
  practice_effect: DataAnalysis,
  knowledge_retention: MagicStick,
  learning_efficiency: Coin,
}
const cardGradientMap = {
  knowledge_mastery: 'linear-gradient(135deg, #c84c5a, #d97982)',
  practice_effect: 'linear-gradient(135deg, #14b8a6, #0d9488)',
  knowledge_retention: 'linear-gradient(135deg, #f59e0b, #d97706)',
  learning_efficiency: 'linear-gradient(135deg, #22c55e, #16a34a)',
}
const cardBarColorMap = {
  knowledge_mastery: '#c84c5a',
  practice_effect: '#14b8a6',
  knowledge_retention: '#f59e0b',
  learning_efficiency: '#22c55e',
}

function bloomLabel(level) {
  const map = { '记忆': '记忆', '理解': '理解', '应用': '应用', '分析': '分析', '评估': '评估', '创造': '创造' }
  return map[level] || level || '—'
}

function displayTopic(item) {
  return stepKnowledgeTitle(item, item?.topic || item?.title || item?.name || '未命名知识点')
}

// ═══ 数据加载 ═══
async function fetchData() {
  loading.value = true
  try {
    const res = await evaluationApi.getDashboard(daysRange.value)

    // ① AI综合评估
    if (res.ai_summary) {
      summary.value = res.ai_summary
    }

    // ② 四个评分卡
    if (res.score_cards) {
      scoreCards.value = Object.entries(res.score_cards).map(([key, card]) => ({
        key,
        label: card.label,
        score: card.score || 0,
        barWidth: card.bar_width || card.score || 0,
        barColor: cardBarColorMap[key] || '#c84c5a',
        description: card.description || '',
        gradient: cardGradientMap[key] || '',
        icon: cardIconMap[key] || TrendCharts,
        delta: card.delta,
        deltaLabel: card.delta_label || '',
      }))
    }

    // ③ 学习行为分析
    if (res.behavior_analysis) {
      behavior.value = res.behavior_analysis
    }

    // ④ AI智能诊断
    if (res.ai_diagnosis) {
      diagnosis.value = res.ai_diagnosis
    }

    // ⑤ 资源优化
    if (res.resource_optimization) {
      optimization.value = res.resource_optimization
    }

    // ⑥ 学习计划
    if (res.plan_optimization) {
      plan.value = res.plan_optimization
    }

  } catch (e) {
    console.error('[Evaluation] 数据加载失败:', e)
    setDemoData()
  } finally {
    loading.value = false
  }
}

function setDemoData() {
  // 降级：演示数据
  summary.value = {
    composite_score: 86, stars: 4, status_label: '良好', trend_label: '持续进步中',
    summary_text: '本周学习状态稳定。学习积极性较高（92%），但练习正确率仅提升4%，AI判断存在"刷资源快、消化慢"的问题。建议今天优先完成「树的遍历」，预计学习35分钟。',
    highlight: '连续5天保持学习，活跃度优秀', concern: '练习正确率提升较慢，建议增加动手练习比例',
    today_recommendation: { topic: '树的遍历', description: '当前掌握度较低', difficulty: 'medium', estimated_minutes: 35, bloom_level: '理解' }
  }
  scoreCards.value = [
    { key: 'knowledge_mastery', label: '知识掌握', score: 82, barWidth: 82, barColor: '#c84c5a', description: '基于所有已学知识点的掌握程度综合评估', gradient: cardGradientMap.knowledge_mastery, icon: TrendCharts },
    { key: 'practice_effect', label: '练习效果', score: 65, barWidth: 65, barColor: '#14b8a6', description: '最近练习正确率', gradient: cardGradientMap.practice_effect, icon: DataAnalysis, delta: 6, deltaLabel: '+6%' },
    { key: 'knowledge_retention', label: '知识保持率', score: 72, barWidth: 72, barColor: '#f59e0b', description: '同一知识点7天内重复测试的保持程度', gradient: cardGradientMap.knowledge_retention, icon: MagicStick },
    { key: 'learning_efficiency', label: '学习效率', score: 91, barWidth: 91, barColor: '#22c55e', description: '近7天完成12个学习节点，共8.5小时', gradient: cardGradientMap.learning_efficiency, icon: Coin, delta: -2, deltaLabel: '-2%' },
  ]
  diagnosis.value = {
    cards: [
      { id: 'discovery', title: 'AI发现', icon: '🔍', content: '最近7天观看视频类资源增加52%，但练习正确率未同步提高。AI认为存在被动学习倾向。', type: 'info' },
      { id: 'prediction', title: 'AI预测', icon: '🔮', content: '如果保持当前学习方式，预计「树」仍需约3小时的学习才能达到掌握水平。', type: 'prediction' },
      { id: 'risk', title: '学习风险', icon: '⚠️', content: '检测到「图论」连续5次错误。建议先完成DFS动画再挑战图论题目。', risk_level: 'medium', risk_factors: ['图论连续错误'], type: 'warning' },
      { id: 'explanation', title: 'AI解释', icon: '💡', content: '推荐优先学习DFS，因为图论遍历依赖DFS基础，你的DFS掌握度仅38%。', type: 'info' },
    ]
  }
  optimization.value = {
    total: 3, has_more: false,
    items: [
      { id: 1, date: '7月18日', from_desc: '视频课', to_desc: '动画+代码案例', reason: '因为代码练习正确率更高，调整为实践型学习', improvement: 15, metric_before: null, metric_after: null },
      { id: 2, date: '7月14日', from_desc: '20题练习', to_desc: '10题精练', reason: '检测到连续疲劳，减少题目数量提升质量', improvement: 8, metric_before: null, metric_after: null },
      { id: 3, date: '7月12日', from_desc: '排序章节', to_desc: '树章节', reason: '排序掌握度达92%，提前进入树的学期', improvement: 22, metric_before: null, metric_after: null },
    ]
  }
  plan.value = {
    total_minutes: 95, difficulty_stars: 4, mastery_improvement: 15,
    rationale: '基于AI分析，当前学习路径聚焦树和图的基础知识，按依赖关系排序，确保先掌握DFS再挑战图论。',
    steps: [
      { step_no: 1, topic: '链表复习', description: '巩固线性结构基础', difficulty: 'easy', bloom_level: '记忆', estimated_minutes: 20, status: 'pending', score: null },
      { step_no: 2, topic: '树', description: '二叉树基本概念与遍历', difficulty: 'medium', bloom_level: '理解', estimated_minutes: 30, status: 'pending', score: null },
      { step_no: 3, topic: 'DFS动画', description: '通过动画理解递归与回溯', difficulty: 'medium', bloom_level: '应用', estimated_minutes: 15, status: 'pending', score: null },
      { step_no: 4, topic: '练习', description: '完成10道配套练习题', difficulty: 'hard', bloom_level: '应用', estimated_minutes: 25, status: 'pending', score: null },
      { step_no: 5, topic: 'AI检测', description: '检测学习效果', difficulty: 'medium', bloom_level: '评估', estimated_minutes: 5, status: 'pending', score: null },
    ]
  }
}

function exportReport() {
  // TODO: 导出PDF报告
  console.log('[Evaluation] 导出报告')
}

onMounted(() => {
  fetchData()
})
</script>

<style lang="scss" scoped>
.evaluation-page {
  padding: 32px 40px;
  max-width: 1400px;
  margin: 0 auto;
}

/* ═══ 页面头部 ═══ */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
  .breadcrumb-row { margin-bottom: 8px; }
  .page-title {
    font-size: 28px; font-weight: var(--font-extrabold);
    margin: 0 0 6px 0; color: var(--text-main);
    letter-spacing: -0.5px;
  }
  .page-subtitle { color: var(--text-secondary); margin: 0; font-size: 14px; }
  .header-right {
    display: flex; align-items: center; gap: 12px; flex-shrink: 0;
    .export-btn { margin-left: 8px; }
  }
}

/* ═══ Loading ═══ */
.loading-overlay {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 80px 0; gap: 16px; color: var(--text-secondary);
  .loading-icon { font-size: 36px; animation: spin 1.2s linear infinite; color: var(--color-primary); }
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ═══ Section titles ═══ */
.section-title {
  font-size: 18px; font-weight: var(--font-semibold);
  margin: 0 0 20px 0; color: var(--text-main);
}

/* ════════════════════════════
   ① AI综合评估总评
   ════════════════════════════ */
.section-ai-summary {
  margin-bottom: 32px;
}
.summary-hero {
  display: flex; gap: 32px; align-items: stretch;
  background: white; border-radius: var(--radius-xl); padding: 32px;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
  position: relative; overflow: hidden;
  &::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 4px;
    background: linear-gradient(90deg, #c84c5a, #d97982, #14b8a6);
  }
}

.score-ring-area {
  flex-shrink: 0; display: flex; flex-direction: column; align-items: center; gap: 12px;
}
.score-ring {
  position: relative; width: 140px; height: 140px;
  .ring-svg { width: 100%; height: 100%; transform: rotate(-90deg); }
  .ring-progress { transition: stroke-dashoffset 1.2s cubic-bezier(0.16,1,0.3,1); }
  .score-inner {
    position: absolute; inset: 0; display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    .score-number { font-size: 42px; font-weight: var(--font-extrabold); color: var(--text-main); line-height: 1; }
    .score-total { font-size: 14px; color: var(--text-tertiary); margin-top: 2px; }
  }
}
.score-stars {
  display: flex; gap: 4px;
  .star { color: #e2e6f0; font-size: 18px; &.active { color: #f59e0b; } }
}

.summary-content {
  flex: 1; display: flex; flex-direction: column; gap: 12px; min-width: 0;
}
.summary-status-row {
  display: flex; gap: 10px; align-items: center;
  .status-badge {
    padding: 4px 14px; border-radius: var(--radius-round); font-size: 13px; font-weight: var(--font-semibold);
    &.status-excellent { background: #dcfce7; color: #16a34a; }
    &.status-good { background: #f9e7e9; color: #c84c5a; }
    &.status-normal { background: #fef3c7; color: #d97706; }
    &.status-warning { background: #fee2e2; color: #dc2626; }
  }
  .trend-badge {
    padding: 4px 14px; border-radius: var(--radius-round);
    background: rgba(200,76,90,0.06); color: var(--color-primary);
    font-size: 13px; font-weight: var(--font-medium);
  }
}
.summary-text {
  font-size: 15px; line-height: 1.7; color: var(--text-secondary); margin: 0;
}
.summary-highlights {
  display: flex; gap: 12px; flex-wrap: wrap;
  .highlight-green {
    padding: 6px 14px; background: rgba(22,163,74,0.08); color: #16a34a;
    border-radius: var(--radius-sm); font-size: 13px; font-weight: var(--font-medium);
    border-left: 3px solid #16a34a;
  }
  .highlight-amber {
    padding: 6px 14px; background: rgba(245,158,11,0.08); color: #d97706;
    border-radius: var(--radius-sm); font-size: 13px; font-weight: var(--font-medium);
    border-left: 3px solid #f59e0b;
  }
}

.today-recommend {
  flex-shrink: 0; display: flex; flex-direction: column; align-items: center; gap: 10px;
  padding: 24px; background: var(--bg-soft-blue); border-radius: var(--radius-lg);
  min-width: 180px;
  .recommend-label { font-size: 12px; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: 1px; }
  .recommend-topic { font-size: 18px; font-weight: var(--font-bold); color: var(--text-main); }
  .recommend-meta { font-size: 13px; color: var(--text-secondary); }
}

/* ════════════════════════════
   ② 四个评分卡
   ════════════════════════════ */
.section-score-cards {
  margin-bottom: 32px;
}
.score-cards-grid {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px;
}
.score-card {
  background: white; border-radius: var(--radius-lg); padding: 24px;
  border: 1px solid var(--border-color); box-shadow: var(--shadow-xs);
  display: flex; flex-direction: column; gap: 14px;
  transition: box-shadow var(--transition-normal), transform var(--transition-normal);
  &:hover { box-shadow: var(--shadow-md); transform: translateY(-2px); }
  .card-icon {
    width: 40px; height: 40px; border-radius: var(--radius-sm);
    display: flex; align-items: center; justify-content: center; color: white;
  }
  .card-info {
    display: flex; flex-direction: column; gap: 6px;
    .card-label { font-size: 13px; color: var(--text-tertiary); font-weight: var(--font-medium); }
    .card-bar-wrap {
      height: 8px; background: var(--border-light); border-radius: 4px; overflow: hidden;
      .card-bar { height: 100%; border-radius: 4px; transition: width 1s cubic-bezier(0.16,1,0.3,1); }
    }
    .card-value-row {
      display: flex; align-items: baseline; gap: 8px;
      .card-score { font-size: 28px; font-weight: var(--font-extrabold); line-height: 1; }
      .card-delta { font-size: 13px; font-weight: var(--font-semibold);
        &.up { color: #16a34a; } &.down { color: #dc2626; }
      }
    }
  }
  .card-desc { font-size: 12px; color: var(--text-tertiary); margin: 0; line-height: 1.5; }
}

/* ════════════════════════════
   ③ 学习行为分析
   ════════════════════════════ */
.section-behavior { margin-bottom: 32px; }
.behavior-grid { display: grid; grid-template-columns: 1.2fr 1fr 1fr; gap: 20px; }
.behavior-card {
  background: white; border-radius: var(--radius-lg); padding: 24px;
  border: 1px solid var(--border-color); box-shadow: var(--shadow-xs);
  h3 { font-size: 15px; font-weight: var(--font-semibold); margin: 0 0 16px 0; color: var(--text-main); }
}

/* 周活跃度 */
.mini-heatmap {
  display: flex; flex-direction: column; gap: 8px; margin-bottom: 16px;
}
.week-row {
  display: flex; align-items: center; gap: 10px;
  .day-label { width: 36px; font-size: 12px; color: var(--text-tertiary); text-align: right; }
  .day-bar-wrap {
    flex: 1; height: 10px; background: var(--border-light); border-radius: 5px; overflow: hidden;
    .day-bar {
      height: 100%; border-radius: 5px; background: linear-gradient(90deg, #c84c5a, #d97982);
      transition: width 0.8s cubic-bezier(0.16,1,0.3,1);
      &.today { background: linear-gradient(90deg, #d97982, #e4a5aa); }
    }
  }
  .day-value { width: 36px; font-size: 12px; color: var(--text-secondary); text-align: right; }
}
.behavior-total { font-size: 13px; color: var(--text-tertiary); text-align: center; strong { color: var(--text-main); } }

/* 时段分布 */
.time-slots { display: flex; flex-direction: column; gap: 10px; }
.time-slot {
  display: flex; align-items: center; gap: 10px;
  .slot-label { width: 88px; font-size: 12px; color: var(--text-secondary); }
  .slot-bar-wrap {
    flex: 1; height: 8px; background: var(--border-light); border-radius: 4px; overflow: hidden;
    .slot-bar { height: 100%; border-radius: 4px; background: #14b8a6; transition: width 0.8s ease; }
  }
  .slot-value { width: 32px; font-size: 12px; color: var(--text-tertiary); text-align: right; }
}
.slot-peak { margin-top: 12px; font-size: 13px; color: var(--text-tertiary); strong { color: var(--text-main); } }

/* 资源使用 */
.resource-tags { display: flex; flex-direction: column; gap: 10px; }
.resource-tag {
  display: flex; align-items: center; gap: 10px;
  .rt-label { width: 64px; font-size: 12px; color: var(--text-secondary); }
  .rt-bar-wrap {
    flex: 1; height: 8px; background: var(--border-light); border-radius: 4px; overflow: hidden;
    .rt-bar { height: 100%; border-radius: 4px; background: #f59e0b; transition: width 0.8s ease; }
  }
  .rt-percent { width: 36px; font-size: 12px; color: var(--text-tertiary); text-align: right; }
}
.empty-hint { color: var(--text-tertiary); font-size: 13px; text-align: center; padding: 20px 0; }

/* ════════════════════════════
   ④ AI智能诊断
   ════════════════════════════ */
.section-diagnosis { margin-bottom: 32px; }
.diagnosis-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
.diagnosis-card {
  background: white; border-radius: var(--radius-lg); padding: 22px;
  border: 1px solid var(--border-color); box-shadow: var(--shadow-xs);
  transition: box-shadow var(--transition-normal);
  &:hover { box-shadow: var(--shadow-md); }
  .diag-header {
    display: flex; align-items: center; gap: 10px; margin-bottom: 12px;
    .diag-icon { font-size: 20px; }
    .diag-title { font-size: 15px; font-weight: var(--font-semibold); color: var(--text-main); }
    .el-tag { margin-left: auto; }
  }
  .diag-content { font-size: 14px; line-height: 1.65; color: var(--text-secondary); margin: 0; }
  /* 不同卡片的左边框色彩 */
  &.diag-discovery { border-left: 3px solid #c84c5a; }
  &.diag-prediction { border-left: 3px solid #d97982; }
  &.diag-risk { border-left: 3px solid #f59e0b; }
  &.diag-explanation { border-left: 3px solid #14b8a6; }
}

/* ════════════════════════════
   ⑤⑥ 底部双栏
   ════════════════════════════ */
.section-bottom { margin-bottom: 32px; }
.bottom-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
.bottom-card {
  background: white; border-radius: var(--radius-lg); padding: 24px;
  border: 1px solid var(--border-color); box-shadow: var(--shadow-xs);
  .bottom-card-header {
    display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 20px;
    h2 { font-size: 18px; font-weight: var(--font-semibold); margin: 0; color: var(--text-main); }
    .plan-stats { font-size: 13px; color: var(--text-tertiary); .stat-sep { margin: 0 6px; } }
  }
}

/* 时间线 */
.optimization-timeline { display: flex; flex-direction: column; gap: 0; }
.timeline-item {
  display: flex; gap: 14px; padding-bottom: 18px; position: relative;
  &:not(:last-child)::after {
    content: ''; position: absolute; left: 5px; top: 14px; bottom: 0;
    width: 2px; background: var(--border-color);
  }
  .tl-dot {
    width: 12px; height: 12px; border-radius: 50%; background: var(--color-primary);
    flex-shrink: 0; margin-top: 4px; z-index: 1;
  }
  .tl-content {
    flex: 1; display: flex; flex-direction: column; gap: 4px;
    .tl-date { font-size: 12px; color: var(--text-tertiary); font-weight: var(--font-medium); }
    .tl-change {
      display: flex; align-items: center; gap: 6px; font-size: 14px;
      .tl-from { color: var(--text-secondary); }
      .tl-arrow { color: var(--color-primary); font-size: 13px; }
      .tl-to { color: var(--color-primary); font-weight: var(--font-semibold); }
    }
    .tl-reason { font-size: 13px; color: var(--text-tertiary); line-height: 1.5; }
    .tl-effect { font-size: 12px; color: var(--text-tertiary); .effect-up { color: #16a34a; font-weight: var(--font-semibold); } }
  }
}

/* 空状态 */
.empty-state {
  display: flex; flex-direction: column; align-items: center; padding: 32px 0; gap: 8px; color: var(--text-tertiary);
  p { margin: 0; font-size: 14px; }
  .empty-sub { font-size: 12px; }
}
.view-all-btn { margin-top: 12px; width: 100%; }

/* 学习计划流程 */
.plan-flow {
  display: flex; flex-direction: column; gap: 0;
}
.plan-step {
  display: flex; align-items: flex-start; gap: 14px; position: relative; padding-bottom: 16px;
  .step-index {
    width: 32px; height: 32px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; font-weight: var(--font-extrabold); flex-shrink: 0;
    background: var(--bg-soft-blue); color: var(--color-primary);
    &.completed { background: #dcfce7; color: #16a34a; }
    &.in_progress { background: #f9e7e9; color: #c84c5a; }
  }
  .step-body {
    flex: 1;
    .step-topic { font-size: 14px; font-weight: var(--font-semibold); color: var(--text-main); margin-bottom: 4px; }
    .step-meta { display: flex; align-items: center; gap: 8px; .step-time { font-size: 12px; color: var(--text-tertiary); } }
  }
  .step-connector {
    position: absolute; left: 13px; bottom: -2px; color: var(--border-color); font-size: 12px;
  }
}

.plan-rationale {
  display: flex; align-items: flex-start; gap: 8px;
  margin-top: 16px; padding: 14px; background: var(--bg-soft-blue); border-radius: var(--radius-sm);
  font-size: 13px; color: var(--text-secondary); line-height: 1.6;
  .el-icon { flex-shrink: 0; margin-top: 1px; color: var(--color-primary); }
}
.plan-footer {
  display: flex; justify-content: space-between; align-items: center; margin-top: 16px; padding-top: 16px;
  border-top: 1px solid var(--border-light);
  .plan-diff {
    font-size: 13px; color: var(--text-tertiary);
    .diff-star { color: #e2e6f0; &.active { color: #f59e0b; } }
  }
}

/* ═══ 响应式 ═══ */
@media (max-width: 1200px) {
  .evaluation-page { padding: 24px 20px; }
  .summary-hero { flex-direction: column; align-items: center; text-align: center; }
  .score-cards-grid { grid-template-columns: repeat(2, 1fr); }
  .diagnosis-grid { grid-template-columns: repeat(2, 1fr); }
  .behavior-grid { grid-template-columns: 1fr 1fr; .heatmap-area { grid-column: span 2; } }
  .bottom-grid { grid-template-columns: 1fr; }
}
@media (max-width: 768px) {
  .page-header { flex-direction: column; gap: 16px; .header-right { flex-wrap: wrap; } }
  .score-cards-grid { grid-template-columns: 1fr; }
  .diagnosis-grid { grid-template-columns: 1fr; }
  .behavior-grid { grid-template-columns: 1fr; .heatmap-area { grid-column: span 1; } }
}
</style>

