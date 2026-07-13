<template>
  <section id="flow" class="flow-section">
    <div class="section-inner">
      <!-- Section Header -->
      <div class="section-header" ref="headerRef">
        <span class="section-tag">学习流程</span>
        <h2 class="section-title">AI 驱动的<br><span class="title-accent">智能学习闭环</span></h2>
        <p class="section-subtitle">
          从初次画像分析到最终学习报告，每一步都由专精 AI Agent 驱动，形成持续优化的学习闭环。
        </p>
      </div>

      <!-- Timeline Flow -->
      <div class="timeline" ref="timelineRef">
        <!-- Progress line -->
        <div class="timeline-line">
          <div class="timeline-progress" ref="progressRef"></div>
        </div>

        <!-- Steps -->
        <div class="timeline-steps">
          <div
            v-for="(step, i) in steps"
            :key="i"
            class="timeline-step"
            ref="stepRefs"
          >
            <!-- Step Node -->
            <div class="step-node" :class="`node-${i}`">
              <span class="step-number">{{ i + 1 }}</span>
              <div class="node-ring"></div>
            </div>

            <!-- Step Content -->
            <div class="step-content" :class="{ 'content-left': i % 2 === 0, 'content-right': i % 2 === 1 }">
              <div class="step-card">
                <div class="step-icon">{{ step.icon }}</div>
                <h4 class="step-title">{{ step.title }}</h4>
                <p class="step-desc">{{ step.desc }}</p>
                <div class="step-tags">
                  <span v-for="tag in step.tags" :key="tag" class="step-tag">{{ tag }}</span>
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

const steps = [
  {
    icon: '🧑‍🎓',
    title: '学习画像',
    desc: '通过多维度问卷与 MBTI 风格测试，AI 全面分析你的学习风格、认知特征与基础水平，构建个性化学习画像。',
    tags: ['MBTI 分析', '能力测评', '风格识别'],
  },
  {
    icon: '👁️',
    title: 'AI 行为分析',
    desc: '持续追踪学习行为数据：专注度、答题模式、资源偏好，AI 实时调整教学策略与内容难度。',
    tags: ['行为追踪', '专注度分析', '偏好学习'],
  },
  {
    icon: '🗺️',
    title: '路径规划',
    desc: '基于知识依赖图谱与布鲁姆认知层级，动态规划最优学习路径。自动识别薄弱环节，精准推荐下一步。',
    tags: ['依赖图谱', '布鲁姆模型', '难度螺旋'],
  },
  {
    icon: '📝',
    title: '资源生成',
    desc: 'AI 自动生成六大学习资源：讲义、思维导图、练习题、代码案例、PPT 大纲、Manim 动画。',
    tags: ['AI 生成', '六种资源', '个性化定制'],
  },
  {
    icon: '🎯',
    title: '智能练习',
    desc: '自适应难度题目 + 布鲁姆六维评估，精准定位知识盲区。错题自动收集，针对性强化训练。',
    tags: ['自适应难度', '六维评估', '错题分析'],
  },
  {
    icon: '📊',
    title: '学习报告',
    desc: '生成详细的学习分析报告：能力雷达图、进度趋势、知识掌握热力图。数据驱动，持续优化学习效果。',
    tags: ['雷达图', '热力图', '趋势分析'],
  },
]

const headerRef = ref(null)
const timelineRef = ref(null)
const progressRef = ref(null)
const stepRefs = ref([])

onMounted(() => {
  // Header
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
  }

  // Timeline progress animation
  if (progressRef.value) {
    gsap.from(progressRef.value, {
      scrollTrigger: {
        trigger: timelineRef.value,
        start: 'top 70%',
        end: 'bottom 30%',
        scrub: 0.5,
      },
      scaleY: 0,
      transformOrigin: 'top center',
      ease: 'none',
    })
  }

  // Steps staggered
  if (timelineRef.value) {
    const stepCards = timelineRef.value.querySelectorAll('.step-card')
    gsap.from(stepCards, {
      scrollTrigger: { trigger: timelineRef.value, start: 'top 72%' },
      opacity: 0,
      y: 30,
      duration: 0.6,
      stagger: 0.15,
      ease: 'power3.out',
    })

    const stepNodes = timelineRef.value.querySelectorAll('.step-node')
    gsap.from(stepNodes, {
      scrollTrigger: { trigger: timelineRef.value, start: 'top 72%' },
      scale: 0,
      duration: 0.5,
      stagger: 0.15,
      ease: 'back.out(2)',
    })
  }
})
</script>

<style lang="scss" scoped>
.flow-section {
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
  max-width: 500px;
  margin: 0 auto;
}

/* ── Timeline ── */
.timeline {
  position: relative;
  max-width: 1000px;
  margin: 0 auto;
}

/* Vertical progress line */
.timeline-line {
  position: absolute;
  left: 50%;
  top: 0;
  bottom: 0;
  width: 2px;
  background: var(--lp-border);
  transform: translateX(-50%);
}

.timeline-progress {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(180deg, var(--lp-primary), #A78BFA);
  transform-origin: top center;
}

/* Steps */
.timeline-steps {
  display: flex;
  flex-direction: column;
}

.timeline-step {
  position: relative;
  display: flex;
  align-items: flex-start;
  padding: 28px 0;

  &:first-child { padding-top: 0; }
  &:last-child { padding-bottom: 0; }
}

/* Step Node (central dot) */
.step-node {
  position: absolute;
  left: 50%;
  top: 32px;
  transform: translate(-50%, -50%);
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: #fff;
  border: 2px solid var(--lp-border);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 5;
  transition: all var(--lp-transition-base);

  .node-ring {
    position: absolute;
    inset: -4px;
    border-radius: 50%;
    border: 2px solid transparent;
    transition: all var(--lp-transition-base);
  }

  &:hover {
    border-color: var(--lp-primary);
    box-shadow: 0 0 20px var(--lp-primary-glow);

    .node-ring {
      border-color: var(--lp-primary);
      animation: node-ring-pulse 1.5s ease-out infinite;
    }
  }
}

@keyframes node-ring-pulse {
  0% { transform: scale(1); opacity: 0.5; }
  100% { transform: scale(1.8); opacity: 0; }
}

.step-number {
  font-size: 14px;
  font-weight: 700;
  color: var(--lp-text);
  font-family: var(--lp-font-display);
}

/* Step Content Card */
.step-content {
  width: calc(50% - 50px);
}

.content-left {
  margin-right: auto;
  padding-right: 28px;
}

.content-right {
  margin-left: auto;
  padding-left: 28px;
}

.step-card {
  background: var(--lp-bg);
  border: 1px solid var(--lp-border-light);
  border-radius: var(--lp-radius-xl);
  padding: 28px;
  box-shadow: var(--lp-shadow-sm);
  transition: all var(--lp-transition-base);

  &:hover {
    border-color: var(--lp-border);
    box-shadow: var(--lp-shadow-md);
    transform: translateY(-2px);
  }
}

.step-icon {
  font-size: 28px;
  margin-bottom: 14px;
}

.step-title {
  font-family: var(--lp-font-display);
  font-size: 18px;
  font-weight: 700;
  color: var(--lp-text);
  margin: 0 0 8px;
  letter-spacing: -0.01em;
}

.step-desc {
  font-size: 14px;
  line-height: 1.6;
  color: var(--lp-text-secondary);
  margin: 0 0 16px;
}

.step-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.step-tag {
  font-size: 12px;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: var(--lp-radius-full);
  background: var(--lp-bg-secondary);
  color: var(--lp-text-secondary);
  border: 1px solid var(--lp-border-light);
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .flow-section {
    padding: 80px 24px;
  }

  .timeline-line {
    left: 22px;
  }

  .timeline-progress {
    left: 0;
  }

  .step-node {
    left: 22px;
    width: 36px;
    height: 36px;
  }

  .step-content {
    width: calc(100% - 56px);
    margin-left: 56px !important;
    padding-left: 20px !important;
    padding-right: 0 !important;
  }

  .section-header {
    margin-bottom: 60px;
  }
}
</style>
