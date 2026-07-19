<template>
  <section class="tasks-panel">
    <div class="panel-header">
      <h3 class="panel-title">
        <span class="title-icon">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
          </svg>
        </span>
        今日任务
        <span class="ai-badge">AI 推荐</span>
      </h3>
    </div>

    <div class="tasks-list">
      <div
        v-for="t in tasks"
        :key="t.id"
        :class="['task-row', 'task-' + t.status]"
        @click="$emit('goNode', t.nodeId)"
      >
        <div class="task-left">
          <span v-if="t.status === 'done'" class="task-check">
            <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="7" fill="#10B981"/>
              <path d="M5 8l2 2 4-5" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </span>
          <span v-else :class="['task-dot', t.status === 'active' ? 'dot-active' : 'dot-pending']"></span>
        </div>
        <div class="task-body">
          <span class="task-name">{{ t.name }}</span>
          <span v-if="t.reason" class="task-reason">{{ t.reason }}</span>
          <div v-if="t.status !== 'done'" class="task-progress-bar">
            <div class="task-fill" :style="{ width: (t.progress || 0) + '%' }"></div>
          </div>
        </div>
        <div class="task-right">
          <span :class="['task-tag', 'tag-' + t.status]">
            {{ { done: '已完成', active: '进行中', pending: '待开始' }[t.status] }}
          </span>
          <svg class="task-go" width="14" height="14" viewBox="0 0 16 16" fill="none">
            <path d="M6 4l4 4-4 4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
      </div>

      <div v-if="tasks.length === 0" class="tasks-empty">
        <p>暂无任务，去知识地图看看吧</p>
      </div>
    </div>
  </section>
</template>

<script setup>
defineProps({
  tasks: { type: Array, default: () => [] }
})
defineEmits(['goNode'])
</script>

<style scoped>
.tasks-panel {
  background: var(--bg-color);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);
  padding: 22px 24px;
  transition: box-shadow var(--transition-normal);
}
.tasks-panel:hover {
  box-shadow: var(--shadow-card-hover);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
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
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: rgba(200,76,90,0.08);
  color: var(--color-primary);
}
.ai-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(217,121,130,0.08);
  color: var(--color-accent-purple);
  letter-spacing: 0.03em;
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.task-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: background var(--transition-fast);
}
.task-row:hover { background: var(--bg-secondary); }

.task-left { flex-shrink: 0; }
.task-check { flex-shrink: 0; display: flex; }
.task-dot {
  width: 9px; height: 9px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dot-active {
  background: var(--color-accent-purple);
  animation: pulseRing 2s ease-in-out infinite;
}
@keyframes pulseRing {
  0%,100%{box-shadow:0 0 0 0 rgba(217,121,130,0.4)}
  50%{box-shadow:0 0 0 7px rgba(217,121,130,0)}
}
.dot-pending {
  border: 2px solid var(--border-color);
  background: transparent;
}

.task-body { flex: 1; min-width: 0; }
.task-name {
  display: block;
  font-size: 13.5px;
  font-weight: 600;
  color: var(--text-main);
  margin-bottom: 2px;
}
.task-reason {
  display: block;
  font-size: 11px;
  color: var(--text-tertiary);
  margin-bottom: 4px;
}
.task-progress-bar {
  height: 4px;
  border-radius: 2px;
  background: var(--bg-tertiary);
  overflow: hidden;
  max-width: 120px;
}
.task-fill {
  height: 100%;
  border-radius: 2px;
  background: var(--hero-gradient);
  transition: width 0.8s cubic-bezier(0.16,1,0.3,1);
}

.task-right {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
.task-tag {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 999px;
}
.tag-done { background: rgba(16,185,129,0.1); color: #059669; }
.tag-active { background: rgba(217,121,130,0.08); color: var(--color-accent-purple); }
.tag-pending { background: var(--bg-tertiary); color: var(--text-tertiary); }
.task-go { color: var(--text-tertiary); opacity: 0; transition: all var(--transition-fast); }
.task-row:hover .task-go { opacity: 1; transform: translateX(2px); }

.task-done { opacity: 0.5; }
.task-done .task-name { text-decoration: line-through; }

.tasks-empty {
  text-align: center;
  padding: 32px 0;
  color: var(--text-tertiary);
  font-size: 13px;
}
</style>

