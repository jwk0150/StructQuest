<template>
  <div :class="['ai-status', `ai-status--${status}`]">
    <div class="status-icon">
      <div class="status-dot" />
      <div class="status-pulse" />
    </div>
    <span v-if="showLabel" class="status-label">{{ statusLabel }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    default: 'idle',
    validator: (value) => ['thinking', 'analyzing', 'recommending', 'idle'].includes(value)
  },
  showLabel: {
    type: Boolean,
    default: true
  }
})

const statusLabel = computed(() => {
  const labels = {
    thinking: '思考中',
    analyzing: '分析中',
    recommending: '推荐中',
    idle: '就绪'
  }
  return labels[props.status] || '就绪'
})
</script>

<style scoped>
.ai-status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
}

.ai-status--thinking {
  background-color: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.ai-status--analyzing {
  background-color: rgba(139, 92, 246, 0.1);
  color: #8b5cf6;
}

.ai-status--recommending {
  background-color: rgba(16, 163, 127, 0.1);
  color: var(--color-primary);
}

.ai-status--idle {
  background-color: var(--bg-secondary);
  color: var(--text-secondary);
}

.status-icon {
  position: relative;
  width: 8px;
  height: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: currentColor;
}

.ai-status--thinking .status-dot,
.ai-status--analyzing .status-dot,
.ai-status--recommending .status-dot {
  animation: pulse 1.5s ease-in-out infinite;
}

.status-pulse {
  position: absolute;
  top: 0;
  left: 0;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: currentColor;
  opacity: 0.3;
  animation: pulse-ring 1.5s ease-out infinite;
}

.ai-status--idle .status-pulse {
  display: none;
}

.status-label {
  line-height: 1;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

@keyframes pulse-ring {
  0% {
    transform: scale(1);
    opacity: 0.3;
  }
  100% {
    transform: scale(2.5);
    opacity: 0;
  }
}
</style>
