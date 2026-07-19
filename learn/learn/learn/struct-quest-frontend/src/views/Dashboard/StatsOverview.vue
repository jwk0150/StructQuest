<template>
  <div class="stats-stack">
    <!-- ① Today Overview -->
    <div class="stat-card today-overview">
      <h3 class="card-label">今日学习概览</h3>
      <div class="overview-main">
        <div class="ring-chart">
          <svg width="72" height="72" viewBox="0 0 72 72">
            <circle cx="36" cy="36" r="30" fill="none" stroke="var(--border-light)" stroke-width="6"/>
            <circle cx="36" cy="36" r="30" fill="none" stroke="url(#ringGrad)" stroke-width="6"
              stroke-linecap="round" stroke-dasharray="188.5" :stroke-dashoffset="ringOffset"
              transform="rotate(-90 36 36)" style="transition: stroke-dashoffset 1.2s cubic-bezier(0.16,1,0.3,1)"/>
            <defs>
              <linearGradient id="ringGrad" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stop-color="var(--color-accent-purple)"/>
                <stop offset="100%" stop-color="var(--color-primary)"/>
              </linearGradient>
            </defs>
          </svg>
          <span class="ring-center">{{ studyMinutes }}<small>min</small></span>
        </div>
        <div class="overview-meta">
          <div class="meta-row">
            <span class="meta-dot" style="--dot: #d97982"></span>
            <span class="meta-label">知识点</span>
            <span class="meta-val">{{ knowledgeCount }}</span>
          </div>
          <div class="meta-row">
            <span class="meta-dot" style="--dot: #c84c5a"></span>
            <span class="meta-label">任务</span>
            <span class="meta-val">{{ taskCount }}</span>
          </div>
          <div class="meta-row">
            <span class="meta-dot" style="--dot: #10b981"></span>
            <span class="meta-label">正确率</span>
            <span class="meta-val">{{ accuracy }}%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ② Streak -->
    <div class="stat-card streak-card">
      <div class="streak-content">
        <div class="streak-flame">
          <svg width="28" height="34" viewBox="0 0 24 30" fill="none">
            <path d="M12 30c-5-4-10-10-10-16C2 8 6 4 10 0c2 4 4 6 4 10 0 4-2 8-2 12 0 3 2 6 4 8-1 0-3 0-4 0z" fill="url(#flameGrad)"/>
            <defs><linearGradient id="flameGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#f59e0b"/><stop offset="100%" stop-color="#dc2626"/></linearGradient></defs>
          </svg>
        </div>
        <div class="streak-info">
          <span class="streak-num">{{ streak }}</span>
          <span class="streak-label">连续学习天数</span>
        </div>
      </div>
      <div class="streak-bar">
        <div v-for="(d, i) in weekDays" :key="i" :class="['streak-dot', { active: d.active, today: d.today }]"></div>
      </div>
    </div>

    <!-- ③ AI Advice -->
    <div class="stat-card advice-card">
      <h3 class="card-label">AI 今日建议</h3>
      <p class="advice-text">{{ advice }}</p>
      <p class="advice-motivation">{{ motivation }}</p>
    </div>

    <!-- ④ Learning Path Preview -->
    <div class="stat-card path-card">
      <h3 class="card-label">学习路径预览</h3>
      <div class="path-list">
        <div v-for="(step, i) in pathSteps" :key="i" class="path-step">
          <div class="path-step-dot" :class="{ done: step.done, current: i === activeStep }">
            <svg v-if="step.done" width="10" height="10" viewBox="0 0 12 12" fill="none"><path d="M2 6l3 3 5-7" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </div>
          <div class="path-step-info">
            <span class="path-step-name">{{ step.name }}</span>
            <span class="path-step-status">{{ step.done ? '已完成' : (i === activeStep ? '进行中' : '待学习') }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'

const props = defineProps({
  studyMinutes: { type: Number, default: 42 },
  knowledgeCount: { type: Number, default: 8 },
  taskCount: { type: Number, default: 31 },
  accuracy: { type: Number, default: 91 },
  streak: { type: Number, default: 18 },
  advice: { type: String, default: '今天建议复习"树和二叉树"章节' },
  motivation: { type: String, default: '坚持就是胜利，你已经很棒了！' },
  pathSteps: { type: Array, default: () => [
    { name: '线性表基础', done: true },
    { name: '栈与队列', done: true },
    { name: '树与二叉树', done: false },
    { name: '图的遍历', done: false },
    { name: '排序算法', done: false },
  ]},
  activeStep: { type: Number, default: 2 },
})

const weekDays = [
  { label: '一', active: true }, { label: '二', active: true },
  { label: '三', active: true }, { label: '四', active: true },
  { label: '五', active: true }, { label: '六', active: false },
  { label: '日', active: false, today: true },
]

const ringOffset = ref(188.5)
const circumference = 188.5 // 2 * PI * 30

onMounted(() => {
  // Animate ring
  const target = props.studyMinutes / 60
  setTimeout(() => {
    ringOffset.value = circumference * (1 - Math.min(target, 1))
  }, 300)
})
</script>

<style scoped>
.stats-stack {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stat-card {
  background: var(--bg-color);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-xs);
  transition: all var(--transition-normal);
}
.stat-card:hover {
  box-shadow: var(--shadow-card-hover);
  border-color: rgba(200,76,90,0.08);
}

.card-label {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin: 0 0 14px;
}

/* ── Today Overview ── */
.overview-main {
  display: flex;
  align-items: center;
  gap: 20px;
}
.ring-chart {
  position: relative;
  flex-shrink: 0;
}
.ring-center {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 800;
  color: var(--text-main);
}
.ring-center small {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-tertiary);
  margin-left: 1px;
}
.overview-meta {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.meta-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.meta-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--dot);
  flex-shrink: 0;
}
.meta-label {
  font-size: 12px;
  color: var(--text-secondary);
  flex: 1;
}
.meta-val {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-main);
}

/* ── Streak ── */
.streak-content {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 14px;
}
.streak-flame {
  flex-shrink: 0;
}
.streak-info {
  display: flex;
  flex-direction: column;
}
.streak-num {
  font-size: 28px;
  font-weight: 800;
  color: var(--text-main);
  line-height: 1;
  letter-spacing: -0.02em;
}
.streak-label {
  font-size: 11px;
  color: var(--text-tertiary);
  margin-top: 3px;
}
.streak-bar {
  display: flex;
  justify-content: center;
  gap: 8px;
}
.streak-dot {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--bg-tertiary);
  transition: all var(--transition-fast);
}
.streak-dot.active {
  background: rgba(200,76,90,0.12);
}
.streak-dot.today {
  background: var(--color-primary);
  box-shadow: 0 2px 8px rgba(200,76,90,0.3);
}

/* ── AI Advice ── */
.advice-text {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0 0 8px;
  background: var(--bg-soft-purple);
  padding: 10px 12px;
  border-radius: 10px;
}
.advice-motivation {
  font-size: 11px;
  color: var(--color-accent-purple);
  font-weight: 600;
  margin: 0;
}

/* ── Learning Path ── */
.path-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.path-step {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
}
.path-step-dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 2px solid var(--border-color);
  background: var(--bg-color);
}
.path-step-dot.done {
  background: var(--color-success);
  border-color: var(--color-success);
}
.path-step-dot.current {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(200,76,90,0.12);
}
.path-step-dot.current::after {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-primary);
}
.path-step-info {
  display: flex;
  flex-direction: column;
  flex: 1;
}
.path-step-name {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--text-main);
}
.path-step-status {
  font-size: 11px;
  color: var(--text-tertiary);
}
</style>

