<template>
  <router-link :to="mode.route" class="mode-card" :class="mode.gradient">
    <div class="mode-bg"></div>
    <div class="mode-top">
      <span class="mode-icon">{{ mode.icon }}</span>
      <span class="mode-badge" v-if="mode.stats.dynamic">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
        实时
      </span>
    </div>
    <div class="mode-body">
      <h3 class="mode-title">{{ mode.title }}</h3>
      <p class="mode-desc">{{ mode.desc }}</p>
    </div>
    <div class="mode-footer">
      <span class="mode-stat">
        <em>{{ mode.stats.count }}</em>
        <i>{{ mode.stats.unit }}</i>
      </span>
      <span class="mode-arrow">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
        </svg>
      </span>
    </div>
  </router-link>
</template>

<script setup>
defineProps({
  mode: { type: Object, required: true },
})
</script>

<style scoped>
.mode-card {
  position: relative;
  display: flex;
  flex-direction: column;
  padding: var(--space-5) var(--space-5) var(--space-4);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-light);
  background: var(--bg-elevated);
  text-decoration: none;
  color: inherit;
  cursor: pointer;
  overflow: hidden;
  transition: all var(--transition-spring);
}

.mode-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-card-hover);
  border-color: rgba(200,76,90, 0.1);
}

.mode-card:hover .mode-arrow {
  transform: translateX(4px);
  opacity: 1;
}

.mode-bg {
  position: absolute;
  top: -30%;
  right: -15%;
  width: 180px;
  height: 180px;
  border-radius: 50%;
  opacity: 0.05;
  pointer-events: none;
  transition: opacity var(--transition-normal);
}

.mode-card:hover .mode-bg { opacity: 0.1; }

/* gradient colors per mode */
.purple .mode-bg { background: #d97982; }
.blue   .mode-bg { background: #b94b5a; }
.pink   .mode-bg { background: #ec4899; }
.orange .mode-bg { background: #f97316; }
.gold   .mode-bg { background: #f59e0b; }
.teal   .mode-bg { background: #14b8a6; }

.mode-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-3);
  position: relative;
}

.mode-icon {
  font-size: 28px;
  line-height: 1;
}

.mode-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: var(--radius-round);
  background: rgba(249, 115, 22, 0.1);
  color: #f97316;
  font-size: 11px;
  font-weight: var(--font-semibold);
}

.mode-body {
  flex: 1;
  position: relative;
  margin-bottom: var(--space-4);
}

.mode-title {
  font-size: var(--text-base);
  font-weight: var(--font-bold);
  color: var(--text-main);
  margin: 0 0 6px;
  letter-spacing: -0.2px;
}

.mode-desc {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin: 0;
  line-height: var(--leading-relaxed);
}

.mode-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
}

.mode-stat {
  display: flex;
  align-items: baseline;
  gap: 3px;
}

.mode-stat em {
  font-size: var(--text-lg);
  font-weight: var(--font-extrabold);
  font-style: normal;
  line-height: 1;
}

/* colored stat per gradient */
.purple .mode-stat em { color: #d97982; }
.blue   .mode-stat em { color: #b94b5a; }
.pink   .mode-stat em { color: #ec4899; }
.orange .mode-stat em { color: #f97316; }
.gold   .mode-stat em { color: #f59e0b; }
.teal   .mode-stat em { color: #14b8a6; }

.mode-stat i {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  font-style: normal;
  font-weight: var(--font-medium);
}

.mode-arrow {
  color: var(--text-tertiary);
  opacity: 0.5;
  transition: all var(--transition-fast);
}

/* Responsive */
@media (max-width: 600px) {
  .mode-card { padding: var(--space-4); }
  .mode-icon { font-size: 24px; }
  .mode-title { font-size: var(--text-sm); }
}
</style>

