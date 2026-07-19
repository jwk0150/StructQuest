<template>
  <div class="daily-page animate-in">
    <header class="dp-header">
      <router-link to="/app/practice" class="dp-back">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="15 18 9 12 15 6"/></svg>
        返回练习中心
      </router-link>
      <h1 class="dp-title">🏆 每日挑战</h1>
      <p class="dp-subtitle">每日限时挑战 + 排行榜 + 连续签到奖励</p>
    </header>

    <!-- Today Challenge -->
    <div class="dp-challenge-card">
      <div class="dpc-glow"></div>
      <div class="dpc-header">
        <span class="dpc-badge">今日挑战</span>
        <span class="dpc-date">{{ todayStr }}</span>
      </div>
      <div class="dpc-body">
        <span class="dpc-topic">{{ challenge.topic }}</span>
        <div class="dpc-stars">
          <span v-for="i in 5" :key="i" class="star" :class="{ filled: i <= challenge.stars }">★</span>
        </div>
        <div class="dpc-info">
          <span class="dpc-rank">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 9H4.5a2.5 2.5 0 010-5C7 4 6 9 6 9z"/><path d="M18 9h1.5a2.5 2.5 0 000-5C17 4 18 9 18 9z"/><path d="M4 22h16"/><path d="M10 22V8h4v14"/><path d="M6 12h12v-3H6z"/></svg>
            排名 {{ challenge.rank }}
          </span>
          <span class="dpc-exp">+{{ challenge.reward.exp }} 经验</span>
          <span class="dpc-badge-reward">{{ challenge.reward.badge }}</span>
        </div>
      </div>
      <button class="dpc-cta" @click="startChallenge">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>
        开始挑战
      </button>
    </div>

    <!-- Streak -->
    <div class="dp-streak-section">
      <h3 class="dp-section-title">🔥 连续签到</h3>
      <div class="dp-streak-bar">
        <div class="streak-counter">
          <span class="streak-num">{{ challenge.streak }}</span>
          <span class="streak-unit">天</span>
        </div>
        <div class="streak-days">
          <div v-for="i in 7" :key="i" class="streak-day" :class="{ done: i <= (challenge.streak % 7 || 7), today: i === (new Date().getDay() || 7) }">
            <span class="sd-dot"></span>
            <span class="sd-label">{{ weekShort[i - 1] }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Leaderboard -->
    <div class="dp-leaderboard">
      <h3 class="dp-section-title">🏅 排行榜</h3>
      <div class="dp-lb-list">
        <div v-for="(user, idx) in leaderboard" :key="idx" class="dp-lb-item" :class="{ me: user.me }">
          <span class="lb-rank" :class="'r' + (idx + 1)">{{ idx + 1 }}</span>
          <span class="lb-avatar">{{ user.name.charAt(0) }}</span>
          <span class="lb-name">{{ user.name }}</span>
          <span class="lb-score">{{ user.score }} 分</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { DAILY_CHALLENGE } from './practiceData'

const router = useRouter()
const challenge = DAILY_CHALLENGE
const weekShort = ['一', '二', '三', '四', '五', '六', '日']

const todayStr = computed(() => {
  return new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
})

const leaderboard = ref([
  { name: '代码达人', score: 2840 },
  { name: '算法新手', score: 2560 },
  { name: '你', score: 2430, me: true },
  { name: '编程高手', score: 2180 },
  { name: '数据结构迷', score: 1920 },
])

function startChallenge() {
  router.push({
    path: '/app/exam/ch06_dfs',
    query: { practice: 'challenge', mode: 'challenge', count: 5, difficulty: 'hard' },
  })
}
</script>

<style scoped>
.daily-page { max-width: 900px; margin: 0 auto; padding: var(--space-6) var(--space-8) var(--space-12); }
.dp-header { margin-bottom: var(--space-8); }
.dp-back {
  display: inline-flex; align-items: center; gap: 6px; color: var(--text-tertiary);
  text-decoration: none; font-size: var(--text-xs); font-weight: var(--font-semibold);
  margin-bottom: var(--space-3); transition: color var(--transition-fast);
}
.dp-back:hover { color: var(--color-primary); }
.dp-title { font-size: var(--text-3xl); font-weight: var(--font-extrabold); color: var(--text-main); margin: 0 0 4px; }
.dp-subtitle { font-size: var(--text-sm); color: var(--text-secondary); margin: 0; }

/* Challenge card */
.dp-challenge-card {
  position: relative; display: flex; flex-direction: column; align-items: center;
  padding: var(--space-8) var(--space-6); background: var(--bg-elevated);
  border: 1px solid rgba(245, 158, 11, 0.15); border-radius: var(--radius-xl);
  text-align: center; overflow: hidden; margin-bottom: var(--space-8);
}
.dpc-glow {
  position: absolute; top: -20%; left: 50%; transform: translateX(-50%);
  width: 360px; height: 360px;
  background: radial-gradient(circle, rgba(245, 158, 11, 0.06) 0%, transparent 70%);
  pointer-events: none;
}
.dpc-header { display: flex; align-items: center; gap: var(--space-4); margin-bottom: var(--space-4); position: relative; }
.dpc-badge {
  padding: 4px 14px; background: rgba(245, 158, 11, 0.12);
  border-radius: var(--radius-round); font-size: var(--text-xs);
  font-weight: var(--font-bold); color: #f59e0b;
}
.dpc-date { font-size: var(--text-xs); color: var(--text-tertiary); }
.dpc-body { position: relative; margin-bottom: var(--space-6); }
.dpc-topic { display: block; font-size: var(--text-2xl); font-weight: var(--font-extrabold); color: var(--text-main); margin-bottom: var(--space-2); }
.dpc-stars { margin-bottom: var(--space-4); }
.dpc-stars .star { color: #e2e6f0; font-size: 16px; }
.dpc-stars .star.filled { color: #f59e0b; }
.dpc-info { display: flex; align-items: center; gap: var(--space-3); flex-wrap: wrap; justify-content: center; }
.dpc-rank, .dpc-exp, .dpc-badge-reward {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 4px 12px; border-radius: var(--radius-round);
  font-size: 11px; font-weight: var(--font-semibold);
}
.dpc-rank { background: rgba(200,76,90, 0.08); color: var(--color-primary); }
.dpc-exp { background: rgba(16, 163, 74, 0.08); color: var(--color-success); }
.dpc-badge-reward { background: rgba(245, 158, 11, 0.08); color: #f59e0b; }

.dpc-cta {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 12px 36px; background: linear-gradient(135deg, #f59e0b, #d97706);
  color: #fff; border: none; border-radius: var(--radius-sm);
  font-size: var(--text-sm); font-weight: var(--font-bold); cursor: pointer;
  position: relative; transition: all var(--transition-fast);
  box-shadow: 0 4px 20px rgba(245, 158, 11, 0.3);
}
.dpc-cta:hover { transform: translateY(-2px); box-shadow: 0 8px 28px rgba(245, 158, 11, 0.4); }

/* Streak */
.dp-streak-section { margin-bottom: var(--space-8); }
.dp-section-title { font-size: var(--text-lg); font-weight: var(--font-bold); color: var(--text-main); margin: 0 0 var(--space-4); }

.dp-streak-bar {
  display: flex; align-items: center; gap: var(--space-6);
  padding: var(--space-5) var(--space-6); background: var(--bg-elevated);
  border: 1px solid var(--border-light); border-radius: var(--radius-lg);
}
.streak-counter { display: flex; align-items: baseline; gap: 3px; flex-shrink: 0; }
.streak-num { font-size: 42px; font-weight: var(--font-extrabold); color: #f97316; line-height: 1; }
.streak-unit { font-size: var(--text-sm); color: var(--text-tertiary); font-weight: var(--font-semibold); }

.streak-days { display: flex; gap: var(--space-3); flex: 1; justify-content: space-around; }
.streak-day { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.sd-dot { width: 12px; height: 12px; border-radius: 50%; background: var(--bg-tertiary); transition: all var(--transition-fast); }
.streak-day.done .sd-dot { background: var(--color-success); }
.streak-day.today .sd-dot { background: var(--color-primary); box-shadow: 0 0 0 3px rgba(200,76,90, 0.2); }
.sd-label { font-size: 11px; color: var(--text-tertiary); font-weight: var(--font-semibold); }
.streak-day.today .sd-label { color: var(--color-primary); font-weight: var(--font-bold); }

/* Leaderboard */
.dp-leaderboard { margin-top: var(--space-6); }
.dp-lb-list { display: flex; flex-direction: column; gap: var(--space-2); }
.dp-lb-item {
  display: flex; align-items: center; gap: var(--space-3);
  padding: var(--space-3) var(--space-5); background: var(--bg-elevated);
  border: 1px solid var(--border-light); border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}
.dp-lb-item.me { border-color: rgba(200,76,90, 0.2); background: rgba(200,76,90, 0.03); }

.lb-rank { width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; border-radius: 50%; font-size: var(--text-xs); font-weight: var(--font-bold); color: var(--text-tertiary); background: var(--bg-tertiary); }
.lb-rank.r1 { background: #f59e0b; color: #fff; }
.lb-rank.r2 { background: #94a3b8; color: #fff; }
.lb-rank.r3 { background: #d97706; color: #fff; }

.lb-avatar { width: 32px; height: 32px; border-radius: 50%; background: var(--hero-gradient); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: var(--font-bold); }
.lb-name { flex: 1; font-size: var(--text-sm); font-weight: var(--font-semibold); color: var(--text-main); }
.lb-score { font-size: var(--text-sm); font-weight: var(--font-bold); color: var(--color-primary); }

@media (max-width: 600px) {
  .dp-streak-bar { flex-direction: column; align-items: stretch; }
  .dp-title { font-size: var(--text-2xl); }
}
</style>

