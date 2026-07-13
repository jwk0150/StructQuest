<template>
  <div :class="['skeleton', `skeleton--${variant}`]">
    <template v-if="variant === 'text'">
      <div v-for="i in rows" :key="i" class="skeleton__text" />
    </template>

    <template v-else-if="variant === 'card'">
      <div class="skeleton__card">
        <div class="skeleton__card-header">
          <div class="skeleton__avatar" />
          <div class="skeleton__card-title">
            <div class="skeleton__text skeleton__text--short" />
          </div>
        </div>
        <div v-for="i in 3" :key="i" class="skeleton__text" />
      </div>
    </template>

    <template v-else-if="variant === 'list'">
      <div v-for="i in rows" :key="i" class="skeleton__list-item">
        <div class="skeleton__avatar" />
        <div class="skeleton__list-content">
          <div class="skeleton__text skeleton__text--short" />
          <div class="skeleton__text skeleton__text--medium" />
        </div>
      </div>
    </template>

    <template v-else-if="variant === 'image'">
      <div class="skeleton__image" />
    </template>
  </div>
</template>

<script setup>
defineProps({
  variant: {
    type: String,
    default: 'text',
    validator: (value) => ['text', 'card', 'list', 'image'].includes(value)
  },
  rows: {
    type: Number,
    default: 3
  }
})
</script>

<style scoped>
.skeleton {
  width: 100%;
}

.skeleton__text {
  height: 16px;
  background: linear-gradient(90deg, var(--bg-secondary) 25%, var(--bg-tertiary) 50%, var(--bg-secondary) 75%);
  background-size: 200% 100%;
  border-radius: 4px;
  margin-bottom: 12px;
  animation: skeleton-loading 1.5s ease-in-out infinite;
}

.skeleton__text--short {
  width: 40%;
}

.skeleton__text--medium {
  width: 70%;
}

.skeleton__avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(90deg, var(--bg-secondary) 25%, var(--bg-tertiary) 50%, var(--bg-secondary) 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s ease-in-out infinite;
  flex-shrink: 0;
}

.skeleton__card {
  padding: 16px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
}

.skeleton__card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.skeleton__card-title {
  flex: 1;
}

.skeleton__list-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid var(--border-light);
}

.skeleton__list-item:last-child {
  border-bottom: none;
}

.skeleton__list-content {
  flex: 1;
}

.skeleton__image {
  width: 100%;
  height: 200px;
  background: linear-gradient(90deg, var(--bg-secondary) 25%, var(--bg-tertiary) 50%, var(--bg-secondary) 75%);
  background-size: 200% 100%;
  border-radius: var(--radius-md);
  animation: skeleton-loading 1.5s ease-in-out infinite;
}

@keyframes skeleton-loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>
