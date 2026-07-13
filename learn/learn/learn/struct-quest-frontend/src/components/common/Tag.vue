<template>
  <span :class="['tag', `tag--${type}`, `tag--${size}`, { 'tag--closable': closable }]">
    <span class="tag__content">
      <slot />
    </span>
    <button v-if="closable" class="tag__close" @click.stop="$emit('close')">
      <el-icon><Close /></el-icon>
    </button>
  </span>
</template>

<script setup>
import { Close } from '@element-plus/icons-vue'

defineProps({
  type: {
    type: String,
    default: 'default',
    validator: (value) => ['default', 'primary', 'success', 'warning', 'danger', 'info'].includes(value)
  },
  size: {
    type: String,
    default: 'medium',
    validator: (value) => ['small', 'medium', 'large'].includes(value)
  },
  closable: {
    type: Boolean,
    default: false
  }
})

defineEmits(['close'])
</script>

<style scoped>
.tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-weight: 500;
  border-radius: 6px;
  transition: all var(--transition-fast);
}

/* Sizes */
.tag--small {
  padding: 2px 8px;
  font-size: 12px;
}

.tag--medium {
  padding: 4px 12px;
  font-size: 13px;
}

.tag--large {
  padding: 6px 16px;
  font-size: 14px;
}

/* Type variants */
.tag--default {
  background-color: var(--bg-secondary);
  color: var(--text-secondary);
}

.tag--primary {
  background-color: rgba(16, 163, 127, 0.1);
  color: var(--color-primary);
}

.tag--success {
  background-color: rgba(16, 163, 127, 0.1);
  color: var(--color-success);
}

.tag--warning {
  background-color: rgba(245, 158, 11, 0.1);
  color: var(--color-warning);
}

.tag--danger {
  background-color: rgba(239, 68, 68, 0.1);
  color: var(--color-danger);
}

.tag--info {
  background-color: rgba(59, 130, 246, 0.1);
  color: var(--color-info);
}

.tag__close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  padding: 0;
  border: none;
  background: transparent;
  border-radius: 50%;
  cursor: pointer;
  opacity: 0.7;
  transition: opacity var(--transition-fast);
}

.tag__close:hover {
  opacity: 1;
}
</style>
