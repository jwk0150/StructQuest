<template>
  <section class="continue-panel">
    <div class="continue-header">
      <h3 class="panel-title">
        <span class="title-icon">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
        </span>
        继续学习
      </h3>
    </div>

    <div class="continue-body">
      <!-- Left: big card content -->
      <div class="continue-content">
        <div class="continue-chapter-label">{{ chapterLabel }}</div>
        <h4 class="continue-node-name">{{ nodeName }}</h4>
        <p class="continue-progress-text">已完成 {{ progress }}%</p>
        <div class="continue-progress-bar">
          <div class="progress-fill" :style="{ width: progress + '%' }"></div>
        </div>
        <button class="continue-btn" @click="$emit('continue')">
          继续
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M6 4l4 4-4 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
      </div>

      <!-- Right: tree visual -->
      <div class="continue-visual">
        <svg viewBox="0 0 140 160" class="tree-svg">
          <!-- Tree structure -->
          <line x1="70" y1="20" x2="70" y2="50" stroke="#c7d2e2" stroke-width="2"/>
          <line x1="70" y1="50" x2="40" y2="80" stroke="#c7d2e2" stroke-width="1.5"/>
          <line x1="70" y1="50" x2="100" y2="80" stroke="#c7d2e2" stroke-width="1.5"/>
          <line x1="40" y1="80" x2="25" y2="110" stroke="#c7d2e2" stroke-width="1.5"/>
          <line x1="40" y1="80" x2="55" y2="110" stroke="#c7d2e2" stroke-width="1.5"/>
          <line x1="100" y1="80" x2="85" y2="110" stroke="#c7d2e2" stroke-width="1.5"/>
          <line x1="100" y1="80" x2="115" y2="110" stroke="#c7d2e2" stroke-width="1.5"/>

          <!-- Nodes -->
          <circle cx="70" cy="20" r="8" fill="#10b981" opacity="0.9"/>
          <circle cx="70" cy="50" r="8" fill="#6366f1" opacity="0.9"/>
          <circle cx="40" cy="80" r="8" fill="#8b5cf6" opacity="0.9"/>
          <circle cx="100" cy="80" r="8" fill="#c7d2e2" opacity="0.7"/>
          <circle cx="25" cy="110" r="6" fill="#c7d2e2" opacity="0.5"/>
          <circle cx="55" cy="110" r="6" fill="#c7d2e2" opacity="0.5"/>
          <circle cx="85" cy="110" r="6" fill="#c7d2e2" opacity="0.5"/>
          <circle cx="115" cy="110" r="6" fill="#c7d2e2" opacity="0.5"/>

          <!-- Highlight active -->
          <circle cx="40" cy="80" r="13" fill="none" stroke="#8b5cf6" stroke-width="2" stroke-dasharray="4 3" opacity="0.6">
            <animateTransform attributeName="transform" type="rotate" from="0 40 80" to="360 40 80" dur="20s" repeatCount="indefinite"/>
          </circle>
          <circle cx="40" cy="80" r="4" fill="#fff"/>
        </svg>
      </div>
    </div>
  </section>
</template>

<script setup>
defineEmits(['continue'])
defineProps({
  chapterLabel: { type: String, default: '第三章' },
  nodeName: { type: String, default: '栈与队列' },
  progress: { type: Number, default: 62 },
})
</script>

<style scoped>
.continue-panel {
  background: var(--bg-color);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);
  padding: 22px 24px;
  transition: all var(--transition-normal);
  position: relative;
  overflow: hidden;
}
.continue-panel::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 200px;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(99,102,241,0.02));
  pointer-events: none;
}
.continue-panel:hover {
  box-shadow: var(--shadow-card-hover);
}

.continue-header {
  margin-bottom: 18px;
}
.panel-title {
  display: flex;
  align-items: center;
  gap: 9px;
  font-size: 15px;
  font-weight: 700;
  color: var(--text-main);
  margin: 0;
}
.title-icon {
  width: 28px; height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: rgba(16,185,129,0.1);
  color: var(--color-success);
}

.continue-body {
  display: flex;
  gap: 24px;
}

.continue-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.continue-chapter-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 6px;
}
.continue-node-name {
  font-size: 20px;
  font-weight: 800;
  color: var(--text-main);
  margin: 0 0 8px;
  letter-spacing: -0.02em;
}
.continue-progress-text {
  font-size: 12px;
  color: var(--text-secondary);
  margin: 0 0 8px;
}
.continue-progress-bar {
  height: 6px;
  border-radius: 3px;
  background: var(--bg-tertiary);
  overflow: hidden;
  max-width: 200px;
  margin-bottom: 16px;
}
.progress-fill {
  height: 100%;
  border-radius: 3px;
  background: var(--hero-gradient);
  transition: width 1s cubic-bezier(0.16,1,0.3,1);
}
.continue-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 38px;
  padding: 0 18px;
  border-radius: 10px;
  background: var(--hero-gradient);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  font-family: inherit;
  border: none;
  cursor: pointer;
  width: fit-content;
  transition: all var(--transition-fast);
  box-shadow: 0 3px 12px rgba(99,102,241,0.2);
}
.continue-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(99,102,241,0.28);
}

.continue-visual {
  flex-shrink: 0;
  width: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.tree-svg {
  width: 100%;
  height: auto;
}
</style>
