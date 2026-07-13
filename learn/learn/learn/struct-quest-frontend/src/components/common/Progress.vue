<template>
  <div class="learning-progress">
    <div v-if="showLabel" class="progress-header">
      <span class="progress-label">{{ label }}</span>
      <span class="progress-value">{{ percentage }}%</span>
    </div>
    
    <div class="progress-bar">
      <div
        :class="['progress-fill', `progress-fill--${status}`]"
        :style="{ width: `${percentage}%` }"
      />
    </div>
    
    <div v-if="showInfo" class="progress-info">
      <span class="info-text">{{ infoText }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  percentage: {
    type: Number,
    default: 0,
    validator: (value) => value >= 0 && value <= 100
  },
  label: {
    type: String,
    default: ''
  },
  status: {
    type: String,
    default: 'default',
    validator: (value) => ['default', 'success', 'warning', 'danger'].includes(value)
  },
  showLabel: {
    type: Boolean,
    default: true
  },
  showInfo: {
    type: Boolean,
    default: false
  },
  infoText: {
    type: String,
    default: ''
  }
})

const status = computed(() => {
  if (props.status !== 'default') return props.status
  if (props.percentage >= 100) return 'success'
  if (props.percentage >= 70) return 'default'
  if (props.percentage >= 40) return 'warning'
  return 'danger'
})
</script>

<style scoped>
.learning-progress {
  width: 100%;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.progress-label {
  font-size: 14px;
  color: var(--text-main);
  font-weight: 500;
}

.progress-value {
  font-size: 14px;
  color: var(--text-secondary);
}

.progress-bar {
  width: 100%;
  height: 8px;
  background-color: var(--bg-tertiary);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width var(--transition-normal), background-color var(--transition-normal);
}

.progress-fill--default {
  background-color: var(--color-primary);
}

.progress-fill--success {
  background-color: var(--color-success);
}

.progress-fill--warning {
  background-color: var(--color-warning);
}

.progress-fill--danger {
  background-color: var(--color-danger);
}

.progress-info {
  margin-top: 4px;
}

.info-text {
  font-size: 12px;
  color: var(--text-tertiary);
}
</style>
