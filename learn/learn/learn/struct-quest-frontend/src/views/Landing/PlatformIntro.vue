<template>
  <section id="platform" class="platform-section">
    <div class="section-inner">
      <!-- Section Header -->
      <div class="section-header" ref="headerRef">
        <span class="section-tag">平台理念</span>
        <h2 class="section-title">Learn Data Structures <span class="title-accent">Visually</span></h2>
        <p class="section-subtitle">
          我们相信，理解数据结构的最佳方式是「看见」它。StructQuest 将抽象概念转化为交互式可视化，
          让每个算法都在你眼前「活」起来。
        </p>
      </div>

      <!-- Alternating rows -->
      <div class="intro-rows">
        <!-- Row 1: Image Left, Text Right -->
        <div class="intro-row" ref="row1">
          <div class="intro-visual">
            <div class="viz-card">
              <!-- Knowledge Graph Visualization -->
              <div class="kg-viz">
                <div class="kg-node kg-root">
                  <span>数据结构</span>
                </div>
                <div class="kg-branch kg-branch-left">
                  <div class="kg-node kg-child">
                    <span>线性结构</span>
                  </div>
                  <div class="kg-leaf-group">
                    <div class="kg-node kg-leaf"><span>数组</span></div>
                    <div class="kg-node kg-leaf"><span>链表</span></div>
                    <div class="kg-node kg-leaf"><span>栈</span></div>
                    <div class="kg-node kg-leaf"><span>队列</span></div>
                  </div>
                </div>
                <div class="kg-branch kg-branch-right">
                  <div class="kg-node kg-child">
                    <span>非线性结构</span>
                  </div>
                  <div class="kg-leaf-group">
                    <div class="kg-node kg-leaf"><span>树</span></div>
                    <div class="kg-node kg-leaf"><span>图</span></div>
                    <div class="kg-node kg-leaf"><span>堆</span></div>
                    <div class="kg-node kg-leaf"><span>哈希表</span></div>
                  </div>
                </div>
                <!-- Connection lines (SVG overlay) -->
                <svg class="kg-lines" viewBox="0 0 500 200" preserveAspectRatio="none">
                  <path d="M250 30 L130 70" stroke="#E5E7EB" stroke-width="1.5" fill="none"/>
                  <path d="M250 30 L370 70" stroke="#E5E7EB" stroke-width="1.5" fill="none"/>
                  <path d="M130 70 L50 110" stroke="#F3F4F6" stroke-width="1" fill="none"/>
                  <path d="M130 70 L90 110" stroke="#F3F4F6" stroke-width="1" fill="none"/>
                  <path d="M130 70 L130 110" stroke="#F3F4F6" stroke-width="1" fill="none"/>
                  <path d="M130 70 L170 110" stroke="#F3F4F6" stroke-width="1" fill="none"/>
                  <path d="M370 70 L330 110" stroke="#F3F4F6" stroke-width="1" fill="none"/>
                  <path d="M370 70 L370 110" stroke="#F3F4F6" stroke-width="1" fill="none"/>
                  <path d="M370 70 L410 110" stroke="#F3F4F6" stroke-width="1" fill="none"/>
                  <path d="M370 70 L450 110" stroke="#F3F4F6" stroke-width="1" fill="none"/>
                </svg>
              </div>
            </div>
          </div>
          <div class="intro-text">
            <h3>知识图谱驱动的学习路径</h3>
            <p>
              8 大章节、50+ 知识点，通过依赖图谱精准关联。系统自动识别你的薄弱环节，
              动态规划最优学习顺序，让每一步都踩在关键点上。
            </p>
            <ul class="intro-features">
              <li>
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="#4F7CFF" stroke-width="1.5"/><path d="M5 8l2 2 4-4" stroke="#4F7CFF" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
                布鲁姆六层认知模型
              </li>
              <li>
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="#4F7CFF" stroke-width="1.5"/><path d="M5 8l2 2 4-4" stroke="#4F7CFF" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
                自适应难度螺旋
              </li>
              <li>
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="#4F7CFF" stroke-width="1.5"/><path d="M5 8l2 2 4-4" stroke="#4F7CFF" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
                前后置依赖自动解析
              </li>
            </ul>
          </div>
        </div>

        <!-- Row 2: Text Left, Image Right -->
        <div class="intro-row intro-row--reverse" ref="row2">
          <div class="intro-text">
            <h3>AI 多智能体协同教学</h3>
            <p>
              7 个专业 AI Agent 协同工作：从学习画像分析、行为特征提取，到个性化路径规划、
              六种资源生成、布鲁姆六维测评——每个环节都有专精 AI 为你服务。
            </p>
            <ul class="intro-features">
              <li>
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="#4F7CFF" stroke-width="1.5"/><path d="M5 8l2 2 4-4" stroke="#4F7CFF" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
                费曼学习法深度交互
              </li>
              <li>
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="#4F7CFF" stroke-width="1.5"/><path d="M5 8l2 2 4-4" stroke="#4F7CFF" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
                MBTI 风格学习画像
              </li>
              <li>
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="#4F7CFF" stroke-width="1.5"/><path d="M5 8l2 2 4-4" stroke="#4F7CFF" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
                实时学习诊断与干预
              </li>
            </ul>
          </div>
          <div class="intro-visual">
            <div class="viz-card">
              <!-- Agent Collaboration Visualization -->
              <div class="agent-viz">
                <div class="agent-center">
                  <span>🧠</span>
                </div>
                <div class="agent-ring">
                  <div class="agent-item" v-for="(agent, i) in agents" :key="i" :style="{ '--angle': (i * 51.4) + 'deg' }">
                    <div class="agent-icon">{{ agent.icon }}</div>
                    <span class="agent-label">{{ agent.label }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

const agents = [
  { icon: '📊', label: '画像分析' },
  { icon: '👁️', label: '行为追踪' },
  { icon: '🗺️', label: '路径规划' },
  { icon: '📝', label: '资源生成' },
  { icon: '✅', label: '质量审核' },
  { icon: '🎯', label: '智能测评' },
  { icon: '🔄', label: '动态更新' },
]

const headerRef = ref(null)
const row1 = ref(null)
const row2 = ref(null)

onMounted(() => {
  // Header animation
  gsap.from(headerRef.value?.querySelector('.section-tag'), {
    scrollTrigger: { trigger: headerRef.value, start: 'top 80%' },
    opacity: 0, y: 16, duration: 0.5,
  })
  gsap.from(headerRef.value?.querySelector('.section-title'), {
    scrollTrigger: { trigger: headerRef.value, start: 'top 80%' },
    opacity: 0, y: 24, duration: 0.6, delay: 0.1,
  })
  gsap.from(headerRef.value?.querySelector('.section-subtitle'), {
    scrollTrigger: { trigger: headerRef.value, start: 'top 80%' },
    opacity: 0, y: 16, duration: 0.5, delay: 0.2,
  })

  // Row animations
  ;[row1, row2].forEach((rowRef, i) => {
    if (!rowRef.value) return
    gsap.from(rowRef.value.querySelector('.intro-visual'), {
      scrollTrigger: { trigger: rowRef.value, start: 'top 75%' },
      opacity: 0, x: i === 0 ? -30 : 30, duration: 0.8, ease: 'power3.out',
    })
    gsap.from(rowRef.value.querySelector('.intro-text'), {
      scrollTrigger: { trigger: rowRef.value, start: 'top 75%' },
      opacity: 0, x: i === 0 ? 30 : -30, duration: 0.8, ease: 'power3.out', delay: 0.15,
    })
  })
})
</script>

<style lang="scss" scoped>
.platform-section {
  padding: var(--lp-section-gap, 140px) 40px;
  background: var(--lp-bg-secondary);
}

.section-inner {
  max-width: var(--lp-max-width);
  margin: 0 auto;
}

/* ── Section Header ── */
.section-header {
  text-align: center;
  max-width: 640px;
  margin: 0 auto 100px;
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

/* ── Intro Rows ── */
.intro-rows {
  display: flex;
  flex-direction: column;
  gap: 120px;
}

.intro-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 80px;
  align-items: center;

  &--reverse {
    .intro-visual { order: 2; }
    .intro-text { order: 1; }
  }
}

.intro-visual {
  display: flex;
  justify-content: center;
}

.intro-text {
  h3 {
    font-family: var(--lp-font-display);
    font-size: 28px;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--lp-text);
    margin: 0 0 16px;
    line-height: 1.2;
  }

  p {
    font-size: 16px;
    line-height: 1.7;
    color: var(--lp-text-secondary);
    margin: 0 0 24px;
  }
}

.intro-features {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;

  li {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 14.5px;
    color: var(--lp-text-secondary);

    svg {
      flex-shrink: 0;
    }
  }
}

/* ── Viz Card ── */
.viz-card {
  width: 100%;
  max-width: 500px;
  aspect-ratio: 4/3;
  background: #fff;
  border-radius: var(--lp-radius-2xl);
  border: 1px solid var(--lp-border-light);
  box-shadow: var(--lp-shadow-lg);
  padding: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

/* Knowledge Graph Viz */
.kg-viz {
  position: relative;
  width: 100%;
  height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.kg-lines {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.kg-node {
  padding: 6px 14px;
  border-radius: var(--lp-radius-full);
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}

.kg-root {
  background: var(--lp-primary);
  color: #fff;
  font-size: 14px;
  padding: 8px 20px;
  z-index: 2;
  margin-bottom: 4px;
}

.kg-branch {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  position: absolute;
  top: 48px;

  &-left { left: 0; }
  &-right { right: 0; }
}

.kg-child {
  background: var(--lp-primary-light);
  color: var(--lp-primary);
  z-index: 2;
}

.kg-leaf-group {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: center;
}

.kg-leaf {
  background: #fff;
  border: 1px solid var(--lp-border);
  color: var(--lp-text-secondary);
  font-size: 12px;
  padding: 4px 10px;
}

/* Agent Viz */
.agent-viz {
  position: relative;
  width: 280px;
  height: 280px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.agent-center {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--lp-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  z-index: 2;
  box-shadow: 0 8px 32px var(--lp-primary-glow);
}

.agent-ring {
  position: absolute;
  inset: 0;
}

.agent-item {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: rotate(var(--angle)) translateY(-110px) rotate(calc(-1 * var(--angle)));
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.agent-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--lp-radius-lg);
  background: #fff;
  border: 1px solid var(--lp-border-light);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  box-shadow: var(--lp-shadow-sm);
}

.agent-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--lp-text-secondary);
  white-space: nowrap;
}

/* ── Responsive ── */
@media (max-width: 1024px) {
  .platform-section {
    padding: 80px 24px;
  }

  .intro-row,
  .intro-row--reverse {
    grid-template-columns: 1fr;
    gap: 40px;

    .intro-visual,
    .intro-text {
      order: unset;
    }
  }

  .intro-text {
    text-align: center;

    .intro-features li {
      justify-content: center;
    }
  }

  .intro-rows {
    gap: 80px;
  }

  .section-header {
    margin-bottom: 60px;
  }
}
</style>
