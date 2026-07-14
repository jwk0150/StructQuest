<template>
  <section class="hero">
    <div class="hero-inner">
      <!-- Left: Text + CTAs -->
      <div class="hero-text">
        <div class="hero-badge">
          <span class="badge-dot"></span>AI 智能学伴
        </div>
        <p class="hero-greeting">你好 {{ userName }} <span class="greeting-wave">👋</span></p>
        <h1 class="hero-title">
          今天继续学习<br/>
          <span class="hero-title-gradient">数据结构</span>
        </h1>
        <p class="hero-desc">{{ aiDynamicTip }}</p>
        <div class="hero-actions">
          <button class="cta-btn cta-primary" @click="$emit('continue')">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>
            继续学习
          </button>
          <button class="cta-btn cta-ghost" @click="$emit('explore')">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polygon points="12 2 2 12 12 22 22 12"/></svg>
            查看地图
          </button>
        </div>
      </div>

      <!-- Right: Hex Network Visual -->
      <div class="hero-visual">
        <div class="hex-network">
          <svg viewBox="0 0 400 380" class="network-svg">
            <defs>
              <radialGradient id="heroGlow">
                <stop offset="0%" stop-color="var(--color-accent-purple)" stop-opacity="0.12"/>
                <stop offset="100%" stop-color="var(--color-accent-purple)" stop-opacity="0"/>
              </radialGradient>
            </defs>
            <circle cx="200" cy="180" r="160" fill="url(#heroGlow)"/>
            <!-- Connection lines -->
            <g v-for="(node, i) in hexNodes" :key="'line'+i">
              <line :x1="200" :y1="180" :x2="node.x" :y2="node.y" stroke="rgba(139,92,246,0.12)" stroke-width="1" stroke-dasharray="4,6"/>
            </g>
            <!-- Outer nodes -->
            <g v-for="(node, i) in hexNodes" :key="'node'+i">
              <circle :cx="node.x" :cy="node.y" r="18" fill="rgba(255,255,255,0.9)" :stroke="node.color" stroke-width="1.5"/>
              <text :x="node.x" :y="node.y" text-anchor="middle" dominant-baseline="central" :fill="node.color" font-size="9" font-weight="700" font-family="var(--font-body)">{{ node.label }}</text>
            </g>
            <!-- Center hex -->
            <g transform="translate(200,180)">
              <polygon points="0,-28 24,-14 24,14 0,28 -24,14 -24,-14" fill="rgba(255,255,255,0.95)" stroke="var(--color-primary)" stroke-width="2.5" stroke-linejoin="round"/>
              <text x="0" y="0" text-anchor="middle" dominant-baseline="central" fill="var(--color-primary)" font-size="14" font-weight="900" font-family="var(--font-body)">DS</text>
            </g>
          </svg>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { useSessionStore } from '@/store/session'

defineEmits(['continue', 'explore'])

const session = useSessionStore()
const userName = computed(() => session.user?.username || '同学')

defineProps({
  aiDynamicTip: { type: String, default: 'AI 正在为你规划今日最佳学习路径...' }
})

const hexNodes = [
  { label: '线性', x: 200, y: 42, color: 'var(--color-accent-purple)' },
  { label: '栈队', x: 308, y: 98, color: '#6366f1' },
  { label: '树', x: 328, y: 220, color: 'var(--color-accent-purple)' },
  { label: '查找', x: 275, y: 316, color: '#a78bfa' },
  { label: '图', x: 122, y: 316, color: '#6366f1' },
  { label: '串', x: 68, y: 220, color: 'var(--color-accent-purple)' },
  { label: '排序', x: 88, y: 98, color: '#8b5cf6' },
]
</script>

<style scoped>
.hero {
  margin-bottom: 28px;
}

.hero-inner {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 32px;
  align-items: center;
  padding: 52px 48px 44px;
  background: var(--bg-color);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-xs);
}

/* Left */
.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 5px 14px;
  border-radius: 999px;
  background: rgba(139,92,246,0.06);
  border: 1px solid rgba(139,92,246,0.1);
  font-size: 12px;
  font-weight: 600;
  color: var(--color-accent-purple);
  margin-bottom: 18px;
}
.badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-accent-purple);
  animation: pulseDot 2s ease-in-out infinite;
}
@keyframes pulseDot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.7); }
}

.hero-greeting {
  font-size: 15px;
  color: var(--text-secondary);
  margin: 0 0 6px;
  font-weight: 500;
}
.greeting-wave {
  display: inline-block;
  animation: wave 2s ease-in-out infinite;
  transform-origin: 70% 70%;
}
@keyframes wave {
  0%,100%{transform:rotate(0)} 10%{transform:rotate(14deg)} 20%{transform:rotate(-8deg)}
  30%{transform:rotate(14deg)} 40%{transform:rotate(-4deg)} 50%{transform:rotate(10deg)}
}

.hero-title {
  font-size: 42px;
  font-weight: 800;
  color: var(--text-main);
  margin: 0 0 12px;
  line-height: 1.12;
  letter-spacing: -0.03em;
}
.hero-title-gradient {
  background: var(--hero-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-desc {
  font-size: 14px;
  color: var(--text-tertiary);
  line-height: 1.6;
  margin: 0 0 26px;
  max-width: 380px;
}

.hero-actions {
  display: flex;
  gap: 12px;
}
.cta-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 46px;
  padding: 0 22px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.16,1,0.3,1);
  border: none;
  white-space: nowrap;
}
.cta-btn:active { transform: scale(0.97); }
.cta-primary {
  background: var(--hero-gradient);
  color: #fff;
  box-shadow: 0 4px 18px rgba(99,102,241,0.25);
}
.cta-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 28px rgba(99,102,241,0.32);
}
.cta-ghost {
  background: var(--bg-secondary);
  color: var(--text-secondary);
  border: 1px solid var(--border-light);
}
.cta-ghost:hover {
  background: var(--bg-color);
  color: var(--color-primary);
  border-color: rgba(99,102,241,0.2);
  transform: translateY(-2px);
}

/* Right visual */
.hero-visual {
  display: flex;
  align-items: center;
  justify-content: center;
}
.hex-network {
  width: 100%;
  max-width: 400px;
  position: relative;
}
.network-svg {
  width: 100%;
  height: auto;
}

@media (max-width: 1100px) {
  .hero-inner {
    grid-template-columns: 1fr;
    padding: 36px 28px;
  }
  .hero-visual { display: none; }
  .hero-title { font-size: 32px; }
}
</style>
