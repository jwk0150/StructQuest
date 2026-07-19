<template>
  <div class="home-page">
    <!-- ═══ HERO SECTION ═══ -->
    <HeroSection
      :ai-dynamic-tip="aiDynamicTip"
      @continue="continueLearning"
      @explore="goToMap"
    />

    <!-- ═══ STATS ROW ═══ -->
    <div class="stats-row">
      <div class="stat-item" v-for="s in statsData" :key="s.label">
        <div class="stat-icon" :style="{ background: s.bg, color: s.color }">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" v-html="s.icon"></svg>
        </div>
        <div class="stat-body">
          <span class="stat-value">{{ s.value }}<small v-if="s.unit">{{ s.unit }}</small></span>
          <span class="stat-label">{{ s.label }}</span>
        </div>
      </div>
    </div>

    <!-- ═══ MAIN CONTENT: Left + Right ═══ -->
    <div class="main-grid">
      <!-- Left Column -->
      <div class="main-left">
        <TaskList :tasks="todayTasks" @go-node="goToNode" />
        <ContinueLearning
          :chapter-label="continueData.chapterLabel"
          :node-name="continueData.nodeName"
          :progress="continueData.progress"
          @continue="continueLearning"
        />
        <ResourceRecommend :resources="resources" @go-node="goToNode" />
      </div>

      <!-- Right Column -->
      <div class="main-right">
        <StatsOverview
          :study-minutes="displayStudyHours"
          :knowledge-count="displayKnowledge"
          :task-count="displaySkills"
          :accuracy="displayAccuracy"
          :streak="displayStreak"
          :advice="aiAdvice"
          :motivation="aiMotivation"
          :path-steps="pathSteps"
          :active-step="activeStep"
        />
      </div>
    </div>

    <!-- ═══ External Resources ═══ -->
    <ExternalResources />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '@/store/session'
import http from '@/utils/request'
import HeroSection from './HeroSection.vue'
import StatsOverview from './StatsOverview.vue'
import TaskList from './TaskList.vue'
import ContinueLearning from './ContinueLearning.vue'
import ResourceRecommend from './ResourceRecommend.vue'
import ExternalResources from './ExternalResources.vue'

const router = useRouter()
const session = useSessionStore()

const userName = computed(() => session.user?.username || '同学')

// ── State ──
const displayKnowledge = ref(0)
const displayStudyHours = ref(0)
const displaySkills = ref(0)
const displayAccuracy = ref(0)
const displayStreak = ref(0)
const aiDynamicTip = ref('AI 正在为你规划今日最佳学习路径...')
const aiAdvice = ref('正在分析你的学习数据...')
const aiMotivation = ref('种一棵树最好的时间是十年前，其次是现在')
const todayTasks = ref([])
const resources = ref([
  { id: 1, type: 'animation', name: '栈操作动画', desc: '入栈、出栈过程可视化', nodeId: 'stack_anim', color: '#d97982' },
  { id: 2, type: 'mindmap', name: '排序算法导图', desc: '七大排序对比总览', nodeId: 'sort_map', color: '#c84c5a' },
  { id: 3, type: 'code', name: 'AVL树实现', desc: 'Python 旋转操作实战', nodeId: 'avl_code', color: '#10b981' },
  { id: 4, type: 'video', name: '图论入门精讲', desc: 'BFS/DFS 算法解析', nodeId: 'graph_video', color: '#f59e0b' },
])

const continueData = ref({
  chapterLabel: '第三章',
  nodeName: '栈与队列',
  progress: 62,
})

const pathSteps = ref([
  { name: '线性表基础', done: true },
  { name: '栈与队列', done: true },
  { name: '树与二叉树', done: false },
  { name: '图的遍历', done: false },
  { name: '排序算法', done: false },
])
const activeStep = ref(2)

const statsData = computed(() => [
  {
    label: '已掌握知识',
    value: displayKnowledge.value,
    unit: '',
    icon: '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
    color: '#d97982',
    bg: 'rgba(217,121,130,0.08)',
  },
  {
    label: '学习时长',
    value: displayStudyHours.value,
    unit: 'h',
    icon: '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    color: '#c84c5a',
    bg: 'rgba(200,76,90,0.08)',
  },
  {
    label: '技能掌握',
    value: displaySkills.value,
    unit: '',
    icon: '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
    color: '#10b981',
    bg: 'rgba(16,185,129,0.08)',
  },
  {
    label: '正确率',
    value: displayAccuracy.value,
    unit: '%',
    icon: '<path d="M6 9H4.5a2.5 2.5 0 010-5C7 4 8 6 8 9"/><path d="M18 9h1.5a2.5 2.5 0 000-5C17 4 16 6 16 9"/><path d="M4 22h16"/><path d="M10 22V8c0-1.1.9-2 2-2s2 .9 2 2v14"/>',
    color: '#f59e0b',
    bg: 'rgba(245,158,11,0.08)',
  },
])

// ── Navigation ──
function goToMap() { router.push('/app/map') }
function continueLearning() { router.push('/app/learn/stack_queue') }
function goToNode(id) { if (id) router.push('/app/learn/' + id) }

// ── Data Loading ──
function anim(refObj, target, duration = 1400) {
  const start = performance.now()
  function update(now) {
    const p = Math.min((now - start) / duration, 1)
    refObj.value = Math.round(target * (1 - Math.pow(1 - p, 3)))
    if (p < 1) requestAnimationFrame(update)
    else refObj.value = target
  }
  requestAnimationFrame(update)
}

async function loadData() {
  try {
    const [profileRes, statsRes, tasksRes, adviceRes] = await Promise.all([
      http.get('/profile').catch(() => null),
      http.get('/study/stats').catch(() => null),
      http.get('/study/ai-tasks').catch(() => null),
      http.get('/study/ai-advice').catch(() => null),
    ])

    if (profileRes?.data) {
      const d = profileRes.data
      displayKnowledge.value = d.knowledge_count || 28
      displayStudyHours.value = d.study_hours || 42
      displaySkills.value = d.skills_count || 31
      displayAccuracy.value = d.accuracy || 91
      displayStreak.value = d.streak || 18
      if (d.ai_tip) aiDynamicTip.value = d.ai_tip
    }

    if (statsRes) {
      if (statsRes.activity) displayAccuracy.value = statsRes.activity
      if (statsRes.streak_days) displayStreak.value = statsRes.streak_days
      if (statsRes.today_tasks?.length) todayTasks.value = statsRes.today_tasks
    }

    if (tasksRes?.tasks?.length) {
      todayTasks.value = tasksRes.tasks.map(t => ({ ...t, id: t.id || t.nodeId }))
    }

    if (adviceRes) {
      aiAdvice.value = adviceRes.advice || aiAdvice.value
      aiMotivation.value = adviceRes.motivation || aiMotivation.value
      aiDynamicTip.value = adviceRes.motivation || aiDynamicTip.value
    }
  } catch (e) {
    console.warn('[Dashboard] Data load:', e)
  }
}

onMounted(async () => {
  await loadData()
  // Animate numbers
  setTimeout(() => {
    anim(displayKnowledge, displayKnowledge.value)
    anim(displayStudyHours, displayStudyHours.value)
    anim(displaySkills, displaySkills.value)
    anim(displayAccuracy, displayAccuracy.value)
    anim(displayStreak, displayStreak.value)
  }, 200)
})
</script>

<style lang="scss" scoped>
.home-page {
  max-width: 1440px;
  margin: 0 auto;
  padding: 32px 28px 40px;
}

/* ── Stats Row ── */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 28px;
}
.stat-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
  border-radius: var(--radius-lg);
  background: var(--bg-color);
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-xs);
  transition: all var(--transition-normal);
}
.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-card-hover);
}
.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.stat-body {
  display: flex;
  flex-direction: column;
}
.stat-value {
  font-size: 24px;
  font-weight: 800;
  color: var(--text-main);
  line-height: 1.2;
  letter-spacing: -0.02em;
}
.stat-value small {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-tertiary);
}
.stat-label {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 2px;
}

/* ── Main Grid ── */
.main-grid {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 24px;
  margin-bottom: 32px;
  align-items: start;
}

.main-left {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.main-right {
  position: sticky;
  top: calc(var(--topnav-height) + 20px);
  display: flex;
  flex-direction: column;
}

/* ── Responsive ── */
@media (max-width: 1200px) {
  .main-grid {
    grid-template-columns: 1fr;
  }
  .main-right {
    position: static;
  }
}
@media (max-width: 900px) {
  .home-page {
    padding: 20px 16px 32px;
  }
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (max-width: 560px) {
  .stats-row {
    grid-template-columns: 1fr;
  }
}
</style>

