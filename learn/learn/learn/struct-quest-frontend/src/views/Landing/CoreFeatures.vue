<template>
  <section id="features" class="features-section">
    <div class="section-inner">
      <!-- Section Header -->
      <div class="section-header" ref="headerRef">
        <span class="section-tag">核心功能</span>
        <h2 class="section-title">为深度学习而设计的<br><span class="title-accent">四大核心能力</span></h2>
        <p class="section-subtitle">
          从智能规划到可视化理解，从刻意练习到知识体系构建，一站式覆盖数据结构学习的每个环节。
        </p>
      </div>

      <!-- Feature Cards Grid -->
      <div class="features-grid" ref="gridRef">
        <div
          v-for="(feature, i) in features"
          :key="i"
          class="feature-card"
          ref="cardRefs"
          @mouseenter="hoveredCard = i"
          @mouseleave="hoveredCard = null"
        >
          <!-- Card Icon -->
          <div class="feature-icon" :class="`icon-${i}`">
            <component :is="feature.icon" />
          </div>

          <!-- Card Content -->
          <h3 class="feature-title">{{ feature.title }}</h3>
          <p class="feature-desc">{{ feature.desc }}</p>

          <!-- Feature Highlights -->
          <ul class="feature-points">
            <li v-for="(point, j) in feature.points" :key="j">
              <svg width="12" height="12" viewBox="0 0 16 16" fill="none">
                <path d="M3 8l3 3 7-7" stroke="#4F7CFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              {{ point }}
            </li>
          </ul>

          <!-- Hover glow effect -->
          <div class="card-glow" :class="{ active: hoveredCard === i }"></div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, h, onMounted } from 'vue'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

const hoveredCard = ref(null)

// SVG icon components as render functions
const IconAIPlan = {
  render() {
    return h('svg', { width: 28, height: 28, viewBox: '0 0 28 28', fill: 'none' }, [
      h('circle', { cx: 14, cy: 14, r: 12, stroke: 'currentColor', 'stroke-width': 1.8 }),
      h('path', { d: 'M14 6v5M14 14v3M8 14h5M16 14h4', stroke: 'currentColor', 'stroke-width': 1.5, 'stroke-linecap': 'round' }),
      h('circle', { cx: 14, cy: 14, r: 2.5, fill: 'currentColor' }),
    ])
  }
}

const IconAlgoViz = {
  render() {
    return h('svg', { width: 28, height: 28, viewBox: '0 0 28 28', fill: 'none' }, [
      h('rect', { x: 2, y: 2, width: 10, height: 10, rx: 2, stroke: 'currentColor', 'stroke-width': 1.8 }),
      h('rect', { x: 16, y: 2, width: 10, height: 10, rx: 2, stroke: 'currentColor', 'stroke-width': 1.8 }),
      h('rect', { x: 2, y: 16, width: 10, height: 10, rx: 2, stroke: 'currentColor', 'stroke-width': 1.8 }),
      h('rect', { x: 16, y: 16, width: 10, height: 10, rx: 2, stroke: 'currentColor', 'stroke-width': 1.8 }),
    ])
  }
}

const IconPractice = {
  render() {
    return h('svg', { width: 28, height: 28, viewBox: '0 0 28 28', fill: 'none' }, [
      h('path', { d: 'M10 5H6a2 2 0 00-2 2v16a2 2 0 002 2h16a2 2 0 002-2V7a2 2 0 00-2-2h-4', stroke: 'currentColor', 'stroke-width': 1.8 }),
      h('path', { d: 'M18 3H10v4h8V3z', stroke: 'currentColor', 'stroke-width': 1.8 }),
      h('path', { d: 'M9 14l2 2 4-4', stroke: 'currentColor', 'stroke-width': 1.8, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }),
    ])
  }
}

const IconGraph = {
  render() {
    return h('svg', { width: 28, height: 28, viewBox: '0 0 28 28', fill: 'none' }, [
      h('circle', { cx: 14, cy: 5, r: 3, stroke: 'currentColor', 'stroke-width': 1.8 }),
      h('circle', { cx: 6, cy: 21, r: 3, stroke: 'currentColor', 'stroke-width': 1.8 }),
      h('circle', { cx: 22, cy: 21, r: 3, stroke: 'currentColor', 'stroke-width': 1.8 }),
      h('path', { d: 'M13 8L8 18M15 8l5 10M9 19.5h10', stroke: 'currentColor', 'stroke-width': 1.3 }),
    ])
  }
}

const features = [
  {
    icon: IconAIPlan,
    title: 'AI 学习规划',
    desc: '多智能体协同分析你的学习画像，动态规划最优路径。基于布鲁姆认知模型，让每个知识点都在最佳时机呈现。',
    points: ['MBTI 风格学习画像', '自适应难度螺旋', '实时进度追踪'],
  },
  {
    icon: IconAlgoViz,
    title: '算法可视化',
    desc: '将抽象的数据结构转化为交互动画。Manim 数学动画引擎驱动，支持树、图、排序算法等全部经典结构的动态演示。',
    points: ['Manim 数学动画', '交互式调试', '逐步执行演示'],
  },
  {
    icon: IconPractice,
    title: '智能练习',
    desc: 'AI 自动生成适应你当前水平的练习题。布鲁姆六维评估体系，精准定位知识盲区，错题自动收集分析。',
    points: ['自适应难度', '错题智能分析', '六维能力雷达图'],
  },
  {
    icon: IconGraph,
    title: '知识图谱',
    desc: '8 章 50+ 知识点构建完整依赖图谱。ECharts 可视化展示学习进度，一目了然的掌握度热力图与能力雷达。',
    points: ['依赖关系可视化', '掌握度热力图', '学习路径推荐'],
  },
]

const headerRef = ref(null)
const gridRef = ref(null)
const cardRefs = ref([])

onMounted(() => {
  // Header animation
  const headerEl = headerRef.value
  if (headerEl) {
    gsap.from(headerEl.querySelector('.section-tag'), {
      scrollTrigger: { trigger: headerEl, start: 'top 80%' },
      opacity: 0, y: 16, duration: 0.5,
    })
    gsap.from(headerEl.querySelector('.section-title'), {
      scrollTrigger: { trigger: headerEl, start: 'top 80%' },
      opacity: 0, y: 24, duration: 0.6, delay: 0.1,
    })
    gsap.from(headerEl.querySelector('.section-subtitle'), {
      scrollTrigger: { trigger: headerEl, start: 'top 80%' },
      opacity: 0, y: 16, duration: 0.5, delay: 0.2,
    })
  }

  // Cards staggered animation
  if (gridRef.value) {
    const cards = gridRef.value.querySelectorAll('.feature-card')
    gsap.from(cards, {
      scrollTrigger: { trigger: gridRef.value, start: 'top 78%' },
      opacity: 0,
      y: 40,
      duration: 0.7,
      stagger: 0.12,
      ease: 'power3.out',
    })
  }
})
</script>

<style lang="scss" scoped>
.features-section {
  padding: var(--lp-section-gap, 140px) 40px;
  background: var(--lp-bg);
}

.section-inner {
  max-width: var(--lp-max-width);
  margin: 0 auto;
}

/* ── Section Header ── */
.section-header {
  text-align: center;
  max-width: 640px;
  margin: 0 auto 80px;
}

.section-tag {
  display: inline-block;
  font-size: 13px;
  font-weight: 600;
  color: var(--lp-primary);
  background: var(--lp-primary-light);
  padding: 5px 14px;
  border-radius: var(--lp-radius-full);
  margin-bottom: 20px;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}

.section-title {
  font-family: var(--lp-font-display);
  font-size: clamp(32px, 4vw, 48px);
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--lp-text);
  margin: 0 0 20px;
  line-height: 1.15;
}

.title-accent {
  color: var(--lp-primary);
}

.section-subtitle {
  font-size: 17px;
  line-height: 1.7;
  color: var(--lp-text-secondary);
  margin: 0;
}

/* ── Features Grid ── */
.features-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

/* ── Feature Card ── */
.feature-card {
  position: relative;
  padding: 40px;
  background: var(--lp-bg);
  border-radius: var(--lp-radius-2xl);
  border: 1px solid var(--lp-border-light);
  box-shadow: var(--lp-shadow-sm);
  transition: all var(--lp-transition-base);
  overflow: hidden;
  cursor: default;

  &:hover {
    transform: translateY(-4px);
    box-shadow: var(--lp-shadow-lg);
    border-color: var(--lp-border);
  }
}

/* Hover glow */
.card-glow {
  position: absolute;
  inset: 0;
  background: radial-gradient(600px circle at var(--mouse-x, 50%) var(--mouse-y, 50%), var(--lp-primary-light), transparent 40%);
  opacity: 0;
  transition: opacity 0.4s ease;
  pointer-events: none;

  &.active {
    opacity: 1;
  }
}

/* Icon */
.feature-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--lp-radius-xl);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
  color: var(--lp-primary);
  transition: all var(--lp-transition-base);

  .feature-card:hover & {
    transform: scale(1.05);
  }
}

.icon-0 { background: rgba(79, 124, 255, 0.08); }
.icon-1 { background: rgba(129, 140, 248, 0.08); color: #818CF8; }
.icon-2 { background: rgba(99, 102, 241, 0.08); color: #6366F1; }
.icon-3 { background: rgba(167, 139, 250, 0.08); color: #A78BFA; }

.feature-title {
  font-family: var(--lp-font-display);
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--lp-text);
  margin: 0 0 12px;
}

.feature-desc {
  font-size: 15px;
  line-height: 1.65;
  color: var(--lp-text-secondary);
  margin: 0 0 20px;
}

.feature-points {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;

  li {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13.5px;
    color: var(--lp-text-secondary);

    svg {
      flex-shrink: 0;
    }
  }
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .features-section {
    padding: 80px 24px;
  }

  .features-grid {
    grid-template-columns: 1fr;
  }

  .feature-card {
    padding: 28px;
  }
}
</style>
