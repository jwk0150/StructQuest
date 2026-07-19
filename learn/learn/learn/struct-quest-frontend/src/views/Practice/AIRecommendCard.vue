<template>
  <div class="ai-recommend-card" :class="{ loading }">
    <div class="card-glow"></div>

    <!-- loading skeleton -->
    <template v-if="loading">
      <div class="rec-left skeleton">
        <div class="sk-icon"></div>
        <div class="sk-lines">
          <span class="sk-line" style="width:60%"></span>
          <span class="sk-line" style="width:80%"></span>
        </div>
      </div>
      <div class="rec-right skeleton-badge"></div>
    </template>

    <!-- content -->
    <template v-else>
      <div class="rec-left" @click="$emit('start', recommend)">
        <div class="rec-badge">🎯 AI 推荐练习</div>
        <div class="rec-info">
          <span class="rec-node">{{ recommend.nodeName }}</span>
          <div class="rec-stars">
            <span v-for="i in 5" :key="i" class="star" :class="{ filled: i <= recommend.stars }">★</span>
            <span class="rec-duration">· 预计 {{ recommend.duration }} 分钟</span>
          </div>
          <p class="rec-reason">{{ recommend.reason }}</p>
        </div>
      </div>
      <div class="rec-right">
        <button class="rec-cta" @click="$emit('start', recommend)">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="5 3 19 12 5 21 5 3"/>
          </svg>
          开始练习
        </button>
        <span class="rec-hint">基于你的学习画像动态推荐</span>
      </div>
    </template>
  </div>
</template>

<script setup>
defineProps({
  recommend: {
    type: Object,
    default: () => ({ nodeName: '--', nodeId: '', stars: 0, duration: 0, reason: '' }),
  },
  loading: { type: Boolean, default: false },
})
defineEmits(['start'])
</script>

<style scoped>
.ai-recommend-card {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-6) var(--space-8);
  background: var(--bg-elevated);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-8);
  gap: var(--space-6);
  overflow: hidden;
  transition: all var(--transition-normal);
  cursor: pointer;
}

.ai-recommend-card:hover {
  border-color: rgba(200,76,90, 0.2);
  box-shadow: var(--shadow-md), 0 0 48px rgba(217,121,130, 0.06);
}

.card-glow {
  position: absolute;
  top: -40%;
  right: -10%;
  width: 360px;
  height: 360px;
  background: radial-gradient(circle, rgba(217,121,130, 0.04) 0%, transparent 70%);
  pointer-events: none;
}

.rec-left {
  display: flex;
  align-items: flex-start;
  gap: var(--space-5);
  flex: 1;
  min-width: 0;
}

.rec-badge {
  flex-shrink: 0;
  padding: 5px 14px;
  background: linear-gradient(135deg, rgba(217,121,130, 0.12), rgba(200,76,90, 0.08));
  border: 1px solid rgba(200,76,90, 0.12);
  border-radius: var(--radius-round);
  font-size: var(--text-xs);
  font-weight: var(--font-bold);
  color: var(--color-primary);
  letter-spacing: 0.3px;
  white-space: nowrap;
}

.rec-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.rec-node {
  font-size: var(--text-xl);
  font-weight: var(--font-bold);
  color: var(--text-main);
  letter-spacing: -0.3px;
}

.rec-stars {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 13px;
}

.star {
  color: #e2e6f0;
  transition: color var(--transition-fast);
}
.star.filled {
  color: #f59e0b;
}

.rec-duration {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin-left: 6px;
}

.rec-reason {
  margin: 4px 0 0;
  font-size: var(--text-xs);
  color: var(--text-secondary);
  line-height: var(--leading-relaxed);
  max-width: 400px;
}

.rec-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  flex-shrink: 0;
}

.rec-cta {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 11px 22px;
  background: var(--hero-gradient);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  font-weight: var(--font-bold);
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
  box-shadow: 0 4px 16px rgba(200,76,90, 0.25);
}

.rec-cta:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 24px rgba(200,76,90, 0.35);
}

.rec-hint {
  font-size: 11px;
  color: var(--text-tertiary);
}

/* skeleton */
.skeleton .sk-icon {
  width: 48px; height: 48px;
  border-radius: var(--radius-sm);
  background: var(--bg-tertiary);
  flex-shrink: 0;
}
.skeleton .sk-lines {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}
.skeleton .sk-line {
  display: block;
  height: 12px;
  border-radius: 6px;
  background: var(--bg-tertiary);
  animation: shimmer 1.6s infinite;
}
.skeleton .skeleton-badge {
  width: 100px;
  height: 44px;
  border-radius: var(--radius-sm);
  background: var(--bg-tertiary);
  animation: shimmer 1.6s infinite;
}

@keyframes shimmer {
  0% { opacity: 1; }
  50% { opacity: 0.4; }
  100% { opacity: 1; }
}

/* Responsive */
@media (max-width: 900px) {
  .ai-recommend-card {
    flex-direction: column;
    align-items: stretch;
    padding: var(--space-5);
    gap: var(--space-4);
  }
  .rec-right {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
  .rec-node { font-size: var(--text-lg); }
}
</style>

