<template>
  <div class="home-page">
    
    <section class="hero-section">
      <div class="hero-content">
        <div class="hero-welcome">
          <div class="hero-badge"><span class="badge-dot"></span>AI 智能学伴</div>
          <p class="hero-greeting">你好 {{ userName }} <span class="greeting-wave">👋</span></p>
          <h1 class="hero-title">数据结构探险<br/><span class="hero-title-gradient">智取未来</span></h1>
          <p class="hero-desc">AI 智能规划专属学习路径，带你从基础到高阶轻松掌握</p>
          <div class="hero-actions">
            <button class="cta-btn cta-primary" @click="continueLearning"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"/></svg>继续学习</button>
            <button class="cta-btn cta-glass" @click="goToMap"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polygon points="12 2 2 12 12 22 22 12"/></svg>探索地图</button>
          </div>
          <div class="ai-tip-bubble">
            <div class="tip-avatar"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a4 4 0 014 4c0 2-2 3-2 5h-4c0-2-2-3-2-5a4 4 0 014-4z"/><path d="M8 14h8v4a4 4 0 01-4 4 4 4 0 01-4-4v-4z"/></svg></div>
            <span class="tip-text">{{ aiDynamicTip }}</span>
          </div>
        </div>
        <div class="hero-visual">
          <div class="knowledge-universe">
            <svg viewBox="0 0 400 380" class="network-svg">
              <defs><radialGradient id="heroGlow"><stop offset="0%" stop-color="#8b5cf6" stop-opacity="0.15"/><stop offset="100%" stop-color="#8b5cf6" stop-opacity="0"/></radialGradient></defs>
              <circle cx="200" cy="180" r="160" fill="url(#heroGlow)"/>
              <g v-for="(node, i) in networkNodes" :key="'c'+i"><line :x1="200" :y1="180" :x2="node.x" :y2="node.y" stroke="rgba(139,92,246,0.15)" stroke-width="1" stroke-dasharray="4,5"/></g>
              <g v-for="(node, i) in networkNodes" :key="'n'+i"><circle :cx="node.x" :cy="node.y" r="20" fill="rgba(255,255,255,0.85)" :stroke="node.color" stroke-width="1.5"/><text :x="node.x" :y="node.y" text-anchor="middle" fill="node.color" font-size="10" font-weight="700">{{ node.label }}</text></g>
              <g transform="translate(200,180)"><circle cx="0" cy="0" r="26" fill="rgba(255,255,255,0.9)" stroke="#7c3aed" stroke-width="2"/><text x="0" y="0" text-anchor="middle" dominant-baseline="central" fill="#7c3aed" font-size="15" font-weight="900">DS</text></g>
            </svg>
            <div class="float-particle p1"></div><div class="float-particle p2"></div><div class="float-particle p3"></div><div class="float-particle p4"></div>
          </div>
        </div>
      </div>
    </section>
    <div class="stats-row">
      <div class="glass-stat"><div class="gs-icon" style="--icon-bg:rgba(124,58,237,0.10);--icon-color:#7c3aed;"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg></div><div class="gs-body"><span class="gs-value">{{ displayKnowledge }}</span><span class="gs-label">已掌握知识</span></div></div>
      <div class="glass-stat"><div class="gs-icon" style="--icon-bg:rgba(59,130,246,0.10);--icon-color:#3b82f6;"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div><div class="gs-body"><span class="gs-value">{{ displayStudyHours }}<small>h</small></span><span class="gs-label">学习时长</span></div></div>
      <div class="glass-stat"><div class="gs-icon" style="--icon-bg:rgba(16,185,129,0.10);--icon-color:#10b981;"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg></div><div class="gs-body"><span class="gs-value">{{ displaySkills }}</span><span class="gs-label">技能掌握</span></div></div>
      <div class="glass-stat"><div class="gs-icon" style="--icon-bg:rgba(245,158,11,0.10);--icon-color:#f59e0b;"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9H4.5a2.5 2.5 0 010-5C7 4 8 6 8 9"/><path d="M18 9h1.5a2.5 2.5 0 000-5C17 4 16 6 16 9"/><path d="M4 22h16"/><path d="M10 22V8c0-1.1.9-2 2-2s2 .9 2 2v14"/></svg></div><div class="gs-body"><span class="gs-value">{{ displayAccuracy }}<small>%</small></span><span class="gs-label">正确率</span></div></div>
    </div>
    <div class="main-grid">
      <div class="main-left">
        <section class="glass-panel tasks-panel">
          <div class="panel-header">
            <h3 class="panel-title"><span class="title-icon" style="--t-color:#7c3aed;--t-bg:rgba(124,58,237,0.10);"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg></span>今日学习任务 <span class="badge-ai">AI 推荐</span></h3>
          </div>
          <div class="tasks-list">
            <div v-for="t in todayTasks" :key="t.id" :class="['task-row', 'task-'+t.status]" @click="goToNode(t.nodeId)">
              <div class="task-icon-area">
                <span v-if="t.status==='done'" class="task-check"><svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" fill="#10B981"/><path d="M5 8L7 10L11 6" stroke="#fff" stroke-width="1.8" stroke-linecap="round"/></svg></span>
                <span v-else :class="['task-dot', t.status==='active'?'dot-active':'dot-pending']"></span>
              </div>
              <div class="task-body"><span class="task-name">{{ t.name }}</span>
                <div v-if="t.status!=='done'" class="task-progress-bar"><div class="task-fill" :style="{width:(t.progress||0)+'%'}"></div></div>
              </div>
              <span :class="['task-tag', 'tag-'+t.status]">{{ {done:'已完成',active:'进行中',pending:'待开始'}[t.status]||'' }}</span>
            </div>
          </div>
        </section>
      </div>
      <div class="main-mid">
        <section class="glass-panel">
          <div class="panel-header">
            <h3 class="panel-title"><span class="title-icon" style="--t-color:#6366f1;--t-bg:rgba(99,102,241,0.10);"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/></svg></span>章节进度</h3>
          </div>
          <div class="progress-list">
            <div v-for="ch in chapterProgress" :key="ch.name" class="progress-item">
              <div class="pi-top"><span class="pi-name">{{ ch.name }}</span><span class="pi-pct">{{ ch.progress }}%</span></div>
              <div class="pi-bar"><div :class="['pi-fill', ch.progress>=100?'pi-done':'']" :style="{width:ch.progress+'%'}"></div></div>
            </div>
          </div>
        </section>
        <section class="glass-panel">
          <div class="panel-header">
            <h3 class="panel-title"><span class="title-icon" style="--t-color:#f59e0b;--t-bg:rgba(245,158,11,0.10);"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg></span>热门知识点</h3>
          </div>
          <div class="hot-grid">
            <div v-for="topic in hotTopics" :key="topic.name" class="hot-chip" @click="goToNode(topic.nodeId)">
              <span :class="['hot-rank', 'rank-'+(topic.rank||1)]">{{ topic.rank||1 }}</span>
              <span class="hot-name">{{ topic.name }}</span>
            </div>
          </div>
        </section>
      </div>
      <div class="main-right">
        <div class="glass-card"><div class="gc-header"><h4 class="gc-title">学习打卡</h4><span class="gc-badge">{{ displayStreak }} ?</span></div>
          <div class="week-strip"><div v-for="(d,i) in weekDays" :key="i" :class="['ws-day',{active:d.active,today:d.today}]">{{ d.label }}</div></div>
        </div>
        <div class="glass-card"><div class="gc-header"><h4 class="gc-title">AI 学习建议</h4></div>
          <div class="advice-bubble">
            <div class="advice-avatar"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2"><path d="M12 2a4 4 0 014 4c0 2-2 3-2 5h-4c0-2-2-3-2-5a4 4 0 014-4z"/><path d="M8 14h8v4a4 4 0 01-4 4 4 4 0 01-4-4v-4z"/></svg></div>
            <div class="advice-content"><p>{{ aiAdvice }}</p></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '../../store/session'
import http from '../../utils/request'

const router = useRouter()
const session = useSessionStore()
const userName = computed(() => session.user?.username || '同学')

const displayKnowledge = ref(0)
const displayStudyHours = ref(0)
const displaySkills = ref(0)
const displayAccuracy = ref(0)
const displayStreak = ref(0)
const aiDynamicTip = ref('今天也要继续加油学习...')
const aiAdvice = ref('近期建议重点复习 AVL 树的旋转操作与平衡调整方法，本节为重点务必掌握')
const chapterProgress = ref([])
const todayTasks = ref([])
const continueNode = ref(null)
const resources = ref([])
const hotTopics = ref([])
const learningPath = ref([])
const dailyTasks = ref([])
const weekDays = ref([])

const networkNodes = ref([
  { label: '线性', x: 200, y: 45, color: '#7c3aed' },
  { label: '栈队', x: 310, y: 105, color: '#6366f1' },
  { label: '树', x: 325, y: 220, color: '#8b5cf6' },
  { label: '查找', x: 270, y: 310, color: '#a78bfa' },
  { label: '图', x: 125, y: 310, color: '#6366f1' },
  { label: '串', x: 70, y: 220, color: '#7c3aed' },
  { label: '排序', x: 90, y: 105, color: '#8b5cf6' },
])

function goToMap() { router.push('/app/map') }
function continueLearning() { router.push('/app/learn/avl_tree') }
function goToNode(id) { if (id) router.push('/app/learn/' + id) }

async function loadStats() {
  try {
    const res = await http.get('/study/stats')
    if (res) {
      displayAccuracy.value = res.activity || 85
      displayStreak.value = res.streak_days || 12
      if (res.week_days) {
        const labels = ['一','二','三','四','五','六','日']
        const today = new Date().getDay() || 7
        weekDays.value = labels.map((l, i) => ({
          label: l, active: res.week_days.includes(i+1) || [true,true,true,false,false,false,false][i],
          today: (i+1) === today
        }))
      }
      if (res.hot_topics) hotTopics.value = res.hot_topics
      if (res.today_tasks?.length) todayTasks.value = res.today_tasks
    }
  } catch(e) { console.warn('[Dashboard] Stats:', e) }
}

async function loadChapterProgress() {
  try {
    const res = await http.get('/knowledge/chapters')
    if (res?.chapters) { chapterProgress.value = res.chapters }
  } catch(e) {
    chapterProgress.value = [
      {name:'第一章 绪论',progress:100},{name:'第二章 线性表',progress:85},
      {name:'第三章 栈和队列',progress:62},{name:'第四章 串',progress:40},
      {name:'第五章 树和二叉树',progress:72},{name:'第六章 图',progress:35},
    ]
  }
}

async function loadProfileData() {
  try {
    const res = await http.get('/profile')
    if (res?.data) {
      const d = res.data
      displayKnowledge.value = d.knowledge_count || 28
      displayStudyHours.value = d.study_hours || 12
      displaySkills.value = d.skills_count || 4
      displayAccuracy.value = d.accuracy || 85
      displayStreak.value = d.streak || 12
      if (d.ai_tip) aiDynamicTip.value = d.ai_tip
      if (d.ai_advice) aiAdvice.value = d.ai_advice
    }
  } catch(e) { console.warn('[Dashboard] Profile:', e) }
}

function anim(refObj, target, duration) {
  const start = performance.now()
  function update(now) {
    const p = Math.min((now - start) / duration, 1)
    refObj.value = Math.round(target * (1 - Math.pow(1 - p, 3)))
    if (p < 1) requestAnimationFrame(update)
    else refObj.value = target
  }
  requestAnimationFrame(update)
}

onMounted(async () => {
  await Promise.all([loadProfileData(), loadChapterProgress(), loadStats()])
  await nextTick()
  anim(displayKnowledge, displayKnowledge.value, 1400)
  anim(displayStudyHours, displayStudyHours.value, 1400)
  anim(displaySkills, displaySkills.value, 1300)
  anim(displayAccuracy, displayAccuracy.value, 1600)
  anim(displayStreak, displayStreak.value, 1200)
})
</script>
<style lang="scss" scoped>
.home-page { position: relative; width: 100%; min-height: 100vh; padding: 28px; box-sizing: border-box; overflow-x: hidden; }

.hero-section { position: relative; z-index: 1; margin-bottom: 24px; border-radius: 20px; overflow: hidden; }
.hero-content { display: grid; grid-template-columns: 1fr 380px; gap: 24px; align-items: center; padding: 48px 48px 40px; position: relative; z-index: 1; }
.hero-badge { display: inline-flex; align-items: center; gap: 8px; padding: 6px 14px; border-radius: 999px; background: rgba(139,92,246,0.08); backdrop-filter: blur(8px); border: 1px solid rgba(139,92,246,0.12); font-size: 12px; font-weight: 600; color: #7c3aed; margin-bottom: 20px; }
.badge-dot { width: 6px; height: 6px; border-radius: 50%; background: #7c3aed; animation: pulseDot 2s ease-in-out infinite; }
@keyframes pulseDot { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.5;transform:scale(0.7)} }
.hero-greeting { font-size: 16px; color: #6b7280; margin: 0 0 6px; font-weight: 500; }
.greeting-wave { display: inline-block; animation: wave 2s ease-in-out infinite; transform-origin: 70% 70%; }
@keyframes wave { 0%,100%{transform:rotate(0)} 10%{transform:rotate(14deg)} 20%{transform:rotate(-8deg)} 30%{transform:rotate(14deg)} 40%{transform:rotate(-4deg)} 50%{transform:rotate(10deg)} }
.hero-title { font-size: 44px; font-weight: 800; color: #111827; margin: 0 0 14px; line-height: 1.12; letter-spacing: -0.03em; }
.hero-title-gradient { background: linear-gradient(135deg,#7c3aed,#6366f1,#3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.hero-desc { font-size: 15px; color: #9ca3af; line-height: 1.6; margin: 0 0 28px; max-width: 380px; }
.hero-actions { display: flex; gap: 12px; margin-bottom: 24px; }
.cta-btn { display: inline-flex; align-items: center; gap: 8px; height: 48px; padding: 0 24px; border-radius: 12px; font-size: 14px; font-weight: 600; font-family: inherit; cursor: pointer; transition: all 0.25s cubic-bezier(0.16,1,0.3,1); border: none; white-space: nowrap; }
.cta-btn:active { transform: scale(0.97); }
.cta-primary { background: linear-gradient(135deg,#7c3aed,#6366f1); color: #fff; box-shadow: 0 4px 20px rgba(124,58,237,0.25); }
.cta-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 30px rgba(124,58,237,0.3); }
.cta-glass { background: rgba(255,255,255,0.7); backdrop-filter: blur(12px); color: #374151; border: 1px solid rgba(255,255,255,0.8); }
.cta-glass:hover { background: rgba(255,255,255,0.9); transform: translateY(-2px); border-color: rgba(139,92,246,0.2); color: #7c3aed; }
.ai-tip-bubble { display: inline-flex; align-items: center; gap: 10px; padding: 10px 18px; border-radius: 14px; background: rgba(139,92,246,0.04); border: 1px solid rgba(139,92,246,0.10); max-width: 420px; }
.tip-avatar { width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg,#7c3aed,#6366f1); display: flex; align-items: center; justify-content: center; color: #fff; flex-shrink: 0; }
.tip-text { font-size: 13px; color: #6b7280; line-height: 1.5; flex: 1; }
.hero-visual { display: flex; align-items: center; justify-content: center; position: relative; }
.knowledge-universe { position: relative; width: 100%; max-width: 400px; }
.network-svg { width: 100%; height: auto; }
.float-particle { position: absolute; border-radius: 50%; pointer-events: none; }
.p1 { width: 8px; height: 8px; background: rgba(139,92,246,0.2); top: 15%; left: 10%; animation: particleDrift 8s ease-in-out infinite; }
.p2 { width: 5px; height: 5px; background: rgba(99,102,241,0.2); top: 60%; right: 8%; animation: particleDrift 10s ease-in-out infinite 2s; }
.p3 { width: 6px; height: 6px; background: rgba(6,182,212,0.15); bottom: 20%; left: 20%; animation: particleDrift 7s ease-in-out infinite 4s; }
.p4 { width: 4px; height: 4px; background: rgba(236,72,153,0.15); top: 25%; right: 15%; animation: particleDrift 9s ease-in-out infinite 1s; }
@keyframes particleDrift { 0%,100%{transform:translate(0,0)scale(1);opacity:0.4} 25%{transform:translate(15px,-20px)scale(1.3);opacity:0.7} 50%{transform:translate(-10px,10px)scale(0.8);opacity:0.3} 75%{transform:translate(8px,-8px)scale(1.1);opacity:0.6} }
.stats-row { position: relative; z-index: 1; display: grid; grid-template-columns: repeat(4,1fr); gap: 16px; margin-bottom: 28px; }
.glass-stat { display: flex; align-items: center; gap: 14px; padding: 20px 22px; border-radius: 16px; background: rgba(255,255,255,0.55); backdrop-filter: blur(16px); border: 1px solid rgba(255,255,255,0.8); box-shadow: 0 1px 3px rgba(0,0,0,0.04); transition: all 0.3s cubic-bezier(0.16,1,0.3,1); }
.glass-stat:hover { transform: translateY(-3px); box-shadow: 0 8px 30px rgba(0,0,0,0.06); background: rgba(255,255,255,0.7); }
.gs-icon { width: 44px; height: 44px; border-radius: 12px; background: var(--icon-bg); color: var(--icon-color); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.gs-body { display: flex; flex-direction: column; }
.gs-value { font-size: 26px; font-weight: 800; color: #111827; line-height: 1.2; letter-spacing: -0.02em; }
.gs-value small { font-size: 14px; font-weight: 600; color: #9ca3af; }
.gs-label { font-size: 12px; color: #9ca3af; margin-top: 2px; }
.main-grid { position: relative; z-index: 1; display: grid; grid-template-columns: 1.1fr 0.9fr 300px; gap: 20px; }
.main-left, .main-mid, .main-right { display: flex; flex-direction: column; gap: 20px; }
.main-mid > :last-child, .main-right > .glass-card { flex: 1; }
.main-mid > :last-child, .main-right > :last-child { flex: 1; }
.glass-panel { padding: 22px 24px; border-radius: 16px; background: rgba(255,255,255,0.6); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.8); box-shadow: 0 1px 3px rgba(0,0,0,0.04); transition: box-shadow 0.3s, background 0.3s; }
.glass-panel:hover { box-shadow: 0 8px 32px rgba(0,0,0,0.06); background: rgba(255,255,255,0.7); }
.glass-card { padding: 20px; border-radius: 16px; background: rgba(255,255,255,0.6); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.8); box-shadow: 0 1px 3px rgba(0,0,0,0.04); transition: box-shadow 0.3s, background 0.3s; }
.glass-card:hover { box-shadow: 0 8px 32px rgba(0,0,0,0.06); background: rgba(255,255,255,0.7); }
.panel-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.panel-title { display: flex; align-items: center; gap: 10px; font-size: 16px; font-weight: 700; color: #111827; margin: 0; }
.title-icon { display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; border-radius: 8px; background: var(--t-bg); color: var(--t-color); flex-shrink: 0; }
.badge-ai { font-size: 10px; font-weight: 700; padding: 3px 9px; border-radius: 999px; background: rgba(124,58,237,0.08); color: #7c3aed; margin-left: 6px; letter-spacing: 0.05em; }
.gc-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.gc-title { font-size: 13px; font-weight: 700; color: #374151; margin: 0; }
.gc-badge { font-size: 12px; font-weight: 700; color: #6b7280; padding: 2px 10px; border-radius: 999px; background: rgba(255,255,255,0.5); }
.tasks-list { display: flex; flex-direction: column; gap: 2px; flex: 1; min-height: 200px; }
.task-row { display: flex; align-items: center; gap: 12px; padding: 12px 14px; border-radius: 12px; cursor: pointer; transition: background 0.2s; }
.task-row:hover { background: rgba(255,255,255,0.5); }
.task-done { opacity: 0.6; }
.task-done .task-name { text-decoration: line-through; color: #9ca3af; }
.task-check { flex-shrink: 0; width: 22px; display: flex; justify-content: center; }
.task-dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; margin-top: 2px; }
.dot-active { background: #7c3aed; animation: pulseRing 2s ease-in-out infinite; }
@keyframes pulseRing { 0%,100%{box-shadow:0 0 0 0 rgba(124,58,237,0.4)} 50%{box-shadow:0 0 0 7px rgba(124,58,237,0)} }
.dot-pending { border: 2px solid #d1d5db; background: transparent; }
.task-body { flex: 1; min-width: 0; }
.task-name { display: block; font-size: 13.5px; font-weight: 600; color: #111827; margin-bottom: 2px; }
.task-progress-bar { height: 5px; border-radius: 3px; background: rgba(0,0,0,0.04); overflow: hidden; max-width: 140px; }
.task-fill { height: 100%; border-radius: 3px; background: linear-gradient(90deg,#7c3aed,#6366f1); transition: width 0.8s cubic-bezier(0.16,1,0.3,1); }
.task-tag { font-size: 10px; font-weight: 600; padding: 3px 8px; border-radius: 999px; flex-shrink: 0; }
.tag-done { background: rgba(16,185,129,0.10); color: #059669; }
.tag-active { background: rgba(124,58,237,0.08); color: #7c3aed; }
.tag-pending { background: rgba(0,0,0,0.03); color: #9ca3af; }
.progress-list { display: flex; flex-direction: column; gap: 14px; }
.pi-top { display: flex; justify-content: space-between; margin-bottom: 6px; }
.pi-name { font-size: 13px; font-weight: 600; color: #374151; }
.pi-pct { font-size: 12px; font-weight: 700; color: #6b7280; }
.pi-bar { width: 100%; height: 6px; border-radius: 3px; background: rgba(0,0,0,0.04); overflow: hidden; }
.pi-fill { height: 100%; border-radius: 3px; background: linear-gradient(90deg,#6366f1,#818cf8); transition: width 1s cubic-bezier(0.16,1,0.3,1); }
.pi-done { background: linear-gradient(90deg,#10b981,#34d399); }
.hot-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.hot-chip { display: flex; align-items: center; gap: 8px; padding: 10px 12px; border-radius: 10px; background: rgba(255,255,255,0.4); cursor: pointer; transition: all 0.2s; border: 1px solid rgba(255,255,255,0.5); }
.hot-chip:hover { background: rgba(255,255,255,0.7); border-color: rgba(139,92,246,0.15); transform: translateY(-2px); }
.hot-rank { width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; color: #fff; background: #9ca3af; flex-shrink: 0; }
.rank-1 { background: linear-gradient(135deg,#f59e0b,#f97316); }
.rank-2 { background: linear-gradient(135deg,#94a3b8,#64748b); }
.rank-3 { background: linear-gradient(135deg,#d97706,#b45309); }
.hot-name { font-size: 13px; font-weight: 600; color: #374151; flex: 1; }
.week-strip { display: flex; justify-content: center; gap: 6px; }
.ws-day { width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 600; color: #9ca3af; background: rgba(255,255,255,0.3); }
.ws-day.active { background: rgba(245,158,11,0.10); color: #d97706; }
.ws-day.today { background: linear-gradient(135deg,#f59e0b,#f97316); color: #fff; box-shadow: 0 2px 8px rgba(245,158,11,0.25); }
.advice-bubble { display: flex; gap: 10px; align-items: flex-start; }
.advice-avatar { width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg,#7c3aed,#6366f1); display: flex; align-items: center; justify-content: center; flex-shrink: 0; box-shadow: 0 2px 8px rgba(124,58,237,0.2); }
.advice-content p { margin: 0; font-size: 12.5px; line-height: 1.6; color: #6b7280; background: rgba(255,255,255,0.4); padding: 10px 12px; border-radius: 12px 12px 12px 3px; }
.hero-section::before { content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 33.33vh; background-image: url('/bg-top-right.png'); background-size: cover; background-repeat: no-repeat; background-position: center; z-index: 0; pointer-events: none; opacity: 0.5; }
@media (max-width:1280px) {
  .hero-content { grid-template-columns: 1fr; }
  .hero-visual { display: none; }
  .main-grid { grid-template-columns: 1fr; }
  .main-right { grid-column: 1/-1; display: grid; grid-template-columns: repeat(3,1fr); }
}
@media (max-width:900px) {
  .hero-title { font-size: 32px; }
  .stats-row { grid-template-columns: repeat(2,1fr); }
  .main-right { grid-template-columns: 1fr; }
  .home-page { padding: 16px; }
  .hero-content { padding: 32px 24px; }
}
</style>

