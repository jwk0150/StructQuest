<template>
  <section class="practice-hero">
    <div class="hero-bg-glow"></div>
    <div class="hero-content">
      <div class="hero-icon">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z"/>
        </svg>
      </div>
      <div class="hero-text">
        <h1 class="hero-title">AI 智能练习中心</h1>
        <p class="hero-subtitle">
          AI 根据你的<span class="highlight">学习画像</span>智能推荐今日练习内容，精准攻克薄弱点
        </p>
      </div>
      <div class="hero-badges">
        <span class="badge badge-purple">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
          数据结构
        </span>
        <span class="badge badge-blue">408 考研</span>
        <span class="badge badge-teal">AI 驱动</span>
      </div>
    </div>
  </section>
</template>

<script setup>
</script>

<style scoped>
.practice-hero {
  position: relative;
  margin-bottom: var(--space-6);
  border-radius: var(--radius-xl);
  background: var(--bg-elevated);
  border: 1px solid var(--border-light);
  overflow: hidden;
}

.hero-bg-glow {
  position: absolute;
  inset: 0;
  background: var(--hero-gradient-soft);
  pointer-events: none;
}

.hero-content {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--space-5);
  padding: var(--space-8) var(--space-8);
  flex-wrap: wrap;
}

.hero-icon {
  width: 72px;
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--hero-gradient);
  border-radius: 20px;
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 8px 28px rgba(200,76,90, 0.28);
}

.hero-text {
  flex: 1;
  min-width: 260px;
}

.hero-title {
  font-size: var(--text-3xl);
  font-weight: var(--font-extrabold);
  color: var(--text-main);
  margin: 0 0 8px;
  letter-spacing: -0.5px;
  line-height: 1.2;
}

.hero-subtitle {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin: 0;
  line-height: var(--leading-relaxed);
  max-width: 520px;
}

.hero-subtitle .highlight {
  color: var(--color-primary);
  font-weight: var(--font-semibold);
  background: linear-gradient(135deg, var(--color-accent-purple), var(--color-primary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-badges {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 14px;
  border-radius: var(--radius-round);
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  white-space: nowrap;
}

.badge-purple {
  background: rgba(217,121,130, 0.1);
  color: var(--color-accent-purple);
}

.badge-blue {
  background: rgba(59, 130, 246, 0.1);
  color: #b94b5a;
}

.badge-teal {
  background: rgba(20, 184, 166, 0.1);
  color: var(--color-accent-teal);
}

@media (max-width: 900px) {
  .hero-content {
    padding: var(--space-6) var(--space-5);
    gap: var(--space-4);
  }
  .hero-icon {
    width: 56px;
    height: 56px;
    border-radius: 16px;
  }
  .hero-icon svg { width: 28px; height: 28px; }
  .hero-title { font-size: var(--text-2xl); }
  .hero-badges { width: 100%; margin-top: 4px; }
}

@media (max-width: 600px) {
  .hero-content { justify-content: center; text-align: center; }
  .hero-subtitle { max-width: 100%; }
}
</style>

