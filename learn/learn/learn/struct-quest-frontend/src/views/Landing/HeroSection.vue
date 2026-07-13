<template>
  <section id="hero" class="hero-section">
    <!-- Particle background -->
    <div class="particle-bg-wrapper">
      <ParticleBackground />
    </div>
    <div class="hero-inner">
      <!-- Left Content -->
      <div class="hero-content" ref="heroContent">
        <!-- Badge -->
        <div class="hero-badge">
          <span class="badge-dot"></span>
          全新 AI 驱动学习体验
        </div>

        <!-- Main Heading -->
        <h1 class="hero-title">
          用<span class="title-highlight">可视化</span>的方式<br>掌握数据结构
        </h1>

        <!-- Description -->
        <p class="hero-desc">
          StructQuest 通过 AI 多智能体协同、动态学习画像与交互式可视化，<br>
          为你量身定制最适合的数据结构学习路径。告别死记硬背，真正理解算法之美。
        </p>

        <!-- CTA Buttons -->
        <div class="hero-actions">
          <button class="btn-primary" @click="$emit('scroll-to', 'login')">
            开始学习
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
          <button class="btn-secondary">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="6.5" stroke="currentColor" stroke-width="1.5"/>
              <path d="M6.5 5.5v5l4-2.5-4-2.5z" fill="currentColor"/>
            </svg>
            观看演示
          </button>
        </div>

        <!-- Social Proof -->
        <div class="hero-social-proof">
          <div class="avatar-stack">
            <span v-for="i in 4" :key="i" class="avatar-dot" :style="{ background: ['#4F7CFF','#818CF8','#6366F1','#A78BFA'][i-1] }"></span>
          </div>
          <span class="proof-text">已有 <strong>12,800+</strong> 名学习者加入</span>
        </div>
      </div>

      <!-- Right Visualization -->
      <div class="hero-visual" ref="heroVisual">
        <div class="visual-container">
          <!-- Central Hub -->
          <div class="viz-hub">
            <div class="viz-hub-inner">
              <svg width="28" height="28" viewBox="0 0 32 32" fill="none">
                <path d="M16 4L4 10v12l12 6 12-6V10L16 4z" stroke="#fff" stroke-width="1.8" stroke-linejoin="round"/>
                <path d="M16 16L4 10M16 16l12-6M16 16v12" stroke="#fff" stroke-width="1.2" stroke-linejoin="round" opacity="0.6"/>
              </svg>
            </div>
          </div>

          <!-- Orbiting Nodes -->
          <div class="viz-orbit orbit-1">
            <div class="viz-node node-tree">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="5" r="2.5" stroke="#4F7CFF" stroke-width="1.8"/><circle cx="6" cy="15" r="2.5" stroke="#818CF8" stroke-width="1.8"/><circle cx="18" cy="15" r="2.5" stroke="#6366F1" stroke-width="1.8"/>
                <path d="M11 7.5L7 13M13 7.5l5 5.5" stroke="#94A3B8" stroke-width="1.2"/>
              </svg>
            </div>
            <div class="viz-node node-array">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <rect x="2" y="4" width="5" height="5" rx="1.5" stroke="#4F7CFF" stroke-width="1.5"/><rect x="9" y="4" width="5" height="5" rx="1.5" stroke="#818CF8" stroke-width="1.5"/><rect x="16" y="4" width="5" height="5" rx="1.5" stroke="#6366F1" stroke-width="1.5"/>
              </svg>
            </div>
            <div class="viz-node node-graph">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <circle cx="6" cy="6" r="2.5" stroke="#4F7CFF" stroke-width="1.8"/><circle cx="18" cy="4" r="2.5" stroke="#818CF8" stroke-width="1.8"/><circle cx="12" cy="16" r="2.5" stroke="#6366F1" stroke-width="1.8"/>
                <path d="M8 7.5l8 7M17 6.5l-6 8" stroke="#CBD5E1" stroke-width="1.2"/>
              </svg>
            </div>
          </div>

          <div class="viz-orbit orbit-2">
            <div class="viz-node node-stack">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <rect x="6" y="3" width="12" height="4" rx="1" stroke="#4F7CFF" stroke-width="1.5"/><rect x="6" y="8.5" width="12" height="4" rx="1" stroke="#818CF8" stroke-width="1.5"/><rect x="6" y="14" width="12" height="4" rx="1" stroke="#6366F1" stroke-width="1.5"/>
              </svg>
            </div>
            <div class="viz-node node-list">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <circle cx="5" cy="12" r="2.5" stroke="#4F7CFF" stroke-width="1.8"/><circle cx="12" cy="12" r="2.5" stroke="#818CF8" stroke-width="1.8"/><circle cx="19" cy="12" r="2.5" stroke="#6366F1" stroke-width="1.8"/>
                <path d="M7.5 12h2M14.5 12h2" stroke="#94A3B8" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
            </div>
            <div class="viz-node node-heap">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M12 3L4 9v6l8 6 8-6V9L12 3z" stroke="#4F7CFF" stroke-width="1.5" stroke-linejoin="round"/>
              </svg>
            </div>
          </div>

          <!-- Floating particles -->
          <div class="viz-particle p1"></div>
          <div class="viz-particle p2"></div>
          <div class="viz-particle p3"></div>
          <div class="viz-particle p4"></div>
          <div class="viz-particle p5"></div>
          <div class="viz-particle p6"></div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { gsap } from 'gsap'
import ParticleBackground from './ParticleBackground.vue'

defineEmits(['scroll-to'])

const heroContent = ref(null)
const heroVisual = ref(null)

onMounted(() => {
  const tl = gsap.timeline({ defaults: { ease: 'power3.out' } })

  tl.from(heroContent.value?.querySelector('.hero-badge'), {
    opacity: 0, y: 20, duration: 0.6,
  })
  tl.from(heroContent.value?.querySelector('.hero-title'), {
    opacity: 0, y: 30, duration: 0.7,
  }, '-=0.3')
  tl.from(heroContent.value?.querySelector('.hero-desc'), {
    opacity: 0, y: 20, duration: 0.6,
  }, '-=0.4')
  tl.from(heroContent.value?.querySelector('.hero-actions'), {
    opacity: 0, y: 20, duration: 0.6,
  }, '-=0.3')
  tl.from(heroContent.value?.querySelector('.hero-social-proof'), {
    opacity: 0, y: 10, duration: 0.5,
  }, '-=0.3')

  tl.from(heroVisual.value, {
    opacity: 0, scale: 0.9, duration: 0.8,
  }, '-=1.0')
})
</script>

<style lang="scss" scoped>
/* ═══════════════════════════════════
   HERO SECTION
   ═══════════════════════════════════ */
.hero-section {
  min-height: 100vh;
  display: flex;
  align-items: center;
  padding: 120px 40px 80px;
  background: var(--lp-bg);
  position: relative;
  overflow: hidden;

  /* Subtle bg pattern */
  &::before {
    content: '';
    position: absolute;
    inset: 0;
    background-image: radial-gradient(circle, var(--lp-border-light) 1px, transparent 1px);
    background-size: 48px 48px;
    opacity: 0.5;
    pointer-events: none;
  }
}

/* Particle canvas wrapper — behind content but above dot grid */
.particle-bg-wrapper {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}

.hero-inner {
  max-width: var(--lp-max-width);
  margin: 0 auto;
  width: 100%;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 80px;
  align-items: center;
  position: relative;
  z-index: 2;
}

/* ── Left Content ── */
.hero-content {
  max-width: 580px;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  background: var(--lp-primary-light);
  border-radius: var(--lp-radius-full);
  font-size: 13px;
  font-weight: 600;
  color: var(--lp-primary);
  margin-bottom: 32px;
  letter-spacing: -0.01em;
}

.badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--lp-primary);
  animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.5); }
}

.hero-title {
  font-family: var(--lp-font-display);
  font-size: clamp(40px, 5.5vw, 64px);
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: -0.03em;
  color: var(--lp-text);
  margin: 0 0 28px;
}

.title-highlight {
  background: linear-gradient(135deg, var(--lp-primary), #818CF8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-desc {
  font-size: 17px;
  line-height: 1.7;
  color: var(--lp-text-secondary);
  margin: 0 0 40px;
  max-width: 500px;
}

/* ── CTA Buttons ── */
.hero-actions {
  display: flex;
  gap: 14px;
  margin-bottom: 40px;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 48px;
  padding: 0 28px;
  border-radius: var(--lp-radius-lg);
  border: none;
  background: var(--lp-primary);
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  font-family: var(--lp-font-body);
  cursor: pointer;
  transition: all var(--lp-transition-base);
  letter-spacing: -0.01em;

  svg {
    transition: transform var(--lp-transition-fast);
  }

  &:hover {
    background: var(--lp-primary-hover);
    transform: translateY(-2px);
    box-shadow: 0 8px 24px var(--lp-primary-glow);

    svg {
      transform: translateX(3px);
    }
  }

  &:active {
    transform: translateY(0) scale(0.98);
  }
}

.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 48px;
  padding: 0 28px;
  border-radius: var(--lp-radius-lg);
  border: 1.5px solid var(--lp-border);
  background: var(--lp-bg);
  color: var(--lp-text);
  font-size: 15px;
  font-weight: 600;
  font-family: var(--lp-font-body);
  cursor: pointer;
  transition: all var(--lp-transition-base);
  letter-spacing: -0.01em;

  &:hover {
    border-color: var(--lp-text);
    transform: translateY(-2px);
    box-shadow: var(--lp-shadow-md);
  }

  &:active {
    transform: translateY(0) scale(0.98);
  }
}

/* ── Social Proof ── */
.hero-social-proof {
  display: flex;
  align-items: center;
  gap: 14px;
}

.avatar-stack {
  display: flex;

  .avatar-dot {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    border: 2px solid #fff;
    margin-left: -8px;

    &:first-child {
      margin-left: 0;
    }
  }
}

.proof-text {
  font-size: 14px;
  color: var(--lp-text-secondary);

  strong {
    color: var(--lp-text);
    font-weight: 600;
  }
}

/* ── Right Visualization ── */
.hero-visual {
  display: flex;
  align-items: center;
  justify-content: center;
}

.visual-container {
  position: relative;
  width: 480px;
  height: 480px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Central Hub */
.viz-hub {
  position: absolute;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: var(--lp-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  box-shadow: 0 8px 32px var(--lp-primary-glow);
  animation: hub-pulse 3s ease-in-out infinite;
}

.viz-hub-inner {
  display: flex;
  align-items: center;
  justify-content: center;
}

@keyframes hub-pulse {
  0%, 100% { box-shadow: 0 8px 32px var(--lp-primary-glow); }
  50% { box-shadow: 0 8px 48px rgba(79, 124, 255, 0.25), 0 0 80px rgba(79, 124, 255, 0.1); }
}

/* Orbits */
.viz-orbit {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  animation: orbit-spin 20s linear infinite;

  &.orbit-2 {
    animation-duration: 28s;
    animation-direction: reverse;
  }
}

@keyframes orbit-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Nodes on orbits */
.viz-node {
  position: absolute;
  width: 64px;
  height: 64px;
  border-radius: var(--lp-radius-xl);
  background: #fff;
  border: 1px solid var(--lp-border);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--lp-shadow-sm);
  animation: orbit-spin 20s linear infinite reverse;

  .orbit-2 & {
    animation-duration: 28s;
    animation-direction: reverse;
  }
}

.node-tree   { top: 0; left: 50%; transform: translate(-50%, -50%); }
.node-array  { top: 14%; right: 4%; }
.node-graph  { bottom: 14%; right: 4%; }
.node-stack  { bottom: 0; left: 50%; transform: translate(-50%, 50%); }
.node-list   { bottom: 14%; left: 4%; }
.node-heap   { top: 14%; left: 4%; }

/* Floating Particles */
.viz-particle {
  position: absolute;
  border-radius: 50%;
  background: var(--lp-primary);
  opacity: 0.15;
  pointer-events: none;

  &.p1 { width: 6px; height: 6px; top: 20%; left: 20%; animation: float-particle 4s ease-in-out infinite; }
  &.p2 { width: 4px; height: 4px; top: 30%; right: 25%; animation: float-particle 3.5s ease-in-out 0.5s infinite; }
  &.p3 { width: 5px; height: 5px; bottom: 25%; left: 30%; animation: float-particle 5s ease-in-out 1s infinite; }
  &.p4 { width: 3px; height: 3px; bottom: 35%; right: 30%; animation: float-particle 4.5s ease-in-out 1.5s infinite; }
  &.p5 { width: 7px; height: 7px; top: 45%; left: 15%; animation: float-particle 3.8s ease-in-out 0.8s infinite; }
  &.p6 { width: 4px; height: 4px; top: 55%; right: 18%; animation: float-particle 4.2s ease-in-out 2s infinite; }
}

@keyframes float-particle {
  0%, 100% { transform: translateY(0) scale(1); opacity: 0.15; }
  50% { transform: translateY(-20px) scale(1.5); opacity: 0.3; }
}

/* ── Responsive ── */
@media (max-width: 1024px) {
  .hero-section {
    padding: 100px 24px 60px;
    min-height: auto;
  }

  .hero-inner {
    grid-template-columns: 1fr;
    gap: 48px;
    text-align: center;
  }

  .hero-content {
    max-width: 100%;
    order: 1;
  }

  .hero-desc {
    max-width: 100%;
    margin-left: auto;
    margin-right: auto;
  }

  .hero-actions {
    justify-content: center;
  }

  .hero-social-proof {
    justify-content: center;
  }

  .hero-visual {
    order: 0;
  }

  .visual-container {
    width: 320px;
    height: 320px;
  }
}
</style>
