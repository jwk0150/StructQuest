<template>
  <div class="resources-page">
    <div class="page-header">
      <button class="back-btn" @click="$router.push('/app')">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M10 4l-4 4 4 4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
        返回首页
      </button>
      <h2 class="page-title">精选学习资源</h2>
      <p class="page-sub">AI 为你从全网筛选的优质数据结构与算法学习资源</p>
    </div>
    <ExternalResources />
  </div>
</template>

<script setup>
import ExternalResources from '../Dashboard/ExternalResources.vue'
</script>

<style lang="scss" scoped>
.resources-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px 40px 80px;
}

.page-header {
  margin-bottom: 32px;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: 1px solid var(--border-color);
  border-radius: 10px;
  background: var(--bg-color);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  font-family: var(--font-body);
  cursor: pointer;
  margin-bottom: 20px;
  transition: all var(--transition-fast);

  &:hover {
    border-color: var(--color-primary);
    color: var(--color-primary);
  }
}

.page-title {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 800;
  color: var(--text-main);
  margin: 0 0 8px;
  letter-spacing: -0.02em;
}

.page-sub {
  font-size: 15px;
  color: var(--text-tertiary);
  margin: 0;
}
</style>
