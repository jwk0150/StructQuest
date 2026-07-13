<template>
  <div
    :class="[
      'card',
      `card--${shadow}`,
      `card--radius-${borderRadius}`,
      { 'card--hoverable': hoverable, 'card--loading': loading }
    ]"
  >
    <div v-if="$slots.header || title" class="card__header">
      <slot name="header">
        <h3 v-if="title" class="card__title">{{ title }}</h3>
        <span v-if="subtitle" class="card__subtitle">{{ subtitle }}</span>
      </slot>
    </div>

    <div class="card__body">
      <slot v-if="!loading" />
      <div v-else class="card__skeleton">
        <el-skeleton :rows="3" animated />
      </div>
    </div>

    <div v-if="$slots.footer" class="card__footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: ''
  },
  subtitle: {
    type: String,
    default: ''
  },
  shadow: {
    type: String,
    default: 'always',
    validator: (value) => ['always', 'hover', 'never'].includes(value)
  },
  borderRadius: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg'].includes(value)
  },
  loading: {
    type: Boolean,
    default: false
  },
  hoverable: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
.card {
  background-color: var(--bg-color);
  border: 1px solid var(--border-color);
  padding: 20px;
  transition: box-shadow var(--transition-normal), transform var(--transition-normal);
}

/* Border Radius */
.card--radius-sm {
  border-radius: var(--radius-sm);
}

.card--radius-md {
  border-radius: var(--radius-md);
}

.card--radius-lg {
  border-radius: var(--radius-lg);
}

/* Shadow variants */
.card--shadow-always {
  box-shadow: var(--shadow-sm);
}

.card--shadow-hover {
  box-shadow: none;
}

.card--shadow-hover:hover {
  box-shadow: var(--shadow-md);
}

.card--shadow-never {
  box-shadow: none;
}

/* Hoverable */
.card--hoverable:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.card--loading {
  pointer-events: none;
}

.card__header {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-light);
}

.card__title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-main);
}

.card__subtitle {
  font-size: 14px;
  color: var(--text-secondary);
}

.card__body {
  flex: 1;
}

.card__skeleton {
  padding: 8px 0;
}

.card__footer {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border-light);
}
</style>
