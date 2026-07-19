<template>
  <section class="practice-modes">
    <div class="section-header">
      <h2 class="section-title">📚 练习分类</h2>
      <span class="section-hint">选择适合你的练习模式</span>
    </div>
    <div class="mode-grid">
      <PracticeModeCard
        v-for="mode in modes"
        :key="mode.key"
        :mode="mode"
      />
    </div>
  </section>
</template>

<script setup>
import PracticeModeCard from './PracticeModeCard.vue'

defineProps({
  modes: { type: Array, required: true },
})
</script>

<style scoped>
.practice-modes {
  margin-bottom: var(--space-8);
}

.section-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: var(--space-5);
}

.section-title {
  font-size: var(--text-lg);
  font-weight: var(--font-bold);
  color: var(--text-main);
  margin: 0;
  letter-spacing: -0.2px;
}

.section-hint {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.mode-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-4);
}

@media (max-width: 1100px) {
  .mode-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .mode-grid {
    grid-template-columns: 1fr;
  }
}
</style>
