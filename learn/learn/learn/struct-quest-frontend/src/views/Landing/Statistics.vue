<template>
  <section id="stats" class="stats-section">
    <div class="section-inner">
      <!-- Large Numbers -->
      <div class="stats-grid" ref="statsGrid">
        <div
          v-for="(stat, i) in stats"
          :key="i"
          class="stat-card"
        >
          <div class="stat-number" ref="numberRefs">
            <span class="stat-value" :data-target="stat.value">{{ stat.prefix }}</span>
            <span class="stat-suffix">{{ stat.suffix }}</span>
          </div>
          <div class="stat-label">{{ stat.label }}</div>
          <p class="stat-desc">{{ stat.desc }}</p>
        </div>
      </div>

      <!-- Trust Bar -->
      <div class="trust-bar" ref="trustBar">
        <span class="trust-text">来自全球顶尖高校的认可</span>
        <div class="trust-logos">
          <span v-for="logo in trustLogos" :key="logo" class="trust-logo">{{ logo }}</span>
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

const stats = [
  { prefix: '', value: 12800, suffix: '+', label: '学习人数', desc: '来自全球的学习者正在使用 StructQuest' },
  { prefix: '', value: 500000, suffix: '+', label: '完成题目', desc: 'AI 生成的海量练习题已被完成' },
  { prefix: '', value: 52, suffix: '', label: '知识点', desc: '覆盖数据结构全部核心领域' },
  { prefix: '', value: 94.8, suffix: '%', label: '平均提升率', desc: '学习者考试成绩平均提升幅度' },
]

const trustLogos = ['清华大学出版社', '北大计算机系', '浙大 ACM 队', '中科院计算所', '上海交大 CS']

const statsGrid = ref(null)
const numberRefs = ref([])
const trustBar = ref(null)

function animateNumber(el, target) {
  const duration = 2000
  const startTime = performance.now()

  function update(now) {
    const elapsed = now - startTime
    const progress = Math.min(elapsed / duration, 1)
    // Ease out cubic
    const eased = 1 - Math.pow(1 - progress, 3)
    const current = target * eased

    if (target % 1 !== 0) {
      el.textContent = current.toFixed(1)
    } else if (target >= 10000) {
      el.textContent = Math.floor(current).toLocaleString()
    } else {
      el.textContent = Math.floor(current).toString()
    }

    if (progress < 1) {
      requestAnimationFrame(update)
    } else {
      el.textContent = target % 1 !== 0 ? target.toFixed(1) : target.toLocaleString()
    }
  }

  requestAnimationFrame(update)
}

onMounted(() => {
  // Animate numbers when in view
  if (statsGrid.value) {
    const numberEls = statsGrid.value.querySelectorAll('.stat-value')
    numberEls.forEach((el) => {
      const target = parseFloat(el.getAttribute('data-target'))
      if (!isNaN(target)) {
        ScrollTrigger.create({
          trigger: el,
          start: 'top 85%',
          onEnter: () => animateNumber(el, target),
          once: true,
        })
      }
    })
  }

  // Cards entrance
  if (statsGrid.value) {
    gsap.from(statsGrid.value.querySelectorAll('.stat-card'), {
      scrollTrigger: { trigger: statsGrid.value, start: 'top 80%' },
      opacity: 0,
      y: 30,
      duration: 0.7,
      stagger: 0.1,
      ease: 'power3.out',
    })
  }

  // Trust bar
  if (trustBar.value) {
    gsap.from(trustBar.value, {
      scrollTrigger: { trigger: trustBar.value, start: 'top 85%' },
      opacity: 0,
      y: 20,
      duration: 0.6,
    })
  }
})
</script>

<style lang="scss" scoped>
.stats-section {
  padding: var(--lp-section-gap, 140px) 40px;
  background: var(--lp-bg-secondary);
}

.section-inner {
  max-width: var(--lp-max-width);
  margin: 0 auto;
}

/* ── Stats Grid ── */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  margin-bottom: 80px;
}

.stat-card {
  text-align: center;
  padding: 48px 24px;
  background: var(--lp-bg);
  border-radius: var(--lp-radius-2xl);
  border: 1px solid var(--lp-border-light);
  box-shadow: var(--lp-shadow-sm);
  transition: all var(--lp-transition-base);

  &:hover {
    transform: translateY(-4px);
    box-shadow: var(--lp-shadow-lg);
    border-color: var(--lp-border);
  }
}

.stat-number {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 2px;
  margin-bottom: 12px;
}

.stat-value {
  font-family: var(--lp-font-display);
  font-size: clamp(40px, 5vw, 56px);
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--lp-primary);
  line-height: 1;
}

.stat-suffix {
  font-family: var(--lp-font-display);
  font-size: 24px;
  font-weight: 700;
  color: var(--lp-primary);
  opacity: 0.6;
}

.stat-label {
  font-family: var(--lp-font-display);
  font-size: 17px;
  font-weight: 700;
  color: var(--lp-text);
  margin-bottom: 8px;
  letter-spacing: -0.01em;
}

.stat-desc {
  font-size: 13.5px;
  color: var(--lp-text-secondary);
  margin: 0;
  line-height: 1.5;
}

/* ── Trust Bar ── */
.trust-bar {
  text-align: center;
  padding: 40px 0 0;
  border-top: 1px solid var(--lp-border-light);
}

.trust-text {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--lp-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 24px;
}

.trust-logos {
  display: flex;
  justify-content: center;
  gap: 48px;
  flex-wrap: wrap;
}

.trust-logo {
  font-size: 15px;
  font-weight: 600;
  color: var(--lp-text-secondary);
  opacity: 0.5;
  transition: opacity var(--lp-transition-fast);

  &:hover {
    opacity: 0.8;
  }
}

/* ── Responsive ── */
@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .stats-section {
    padding: 80px 24px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .trust-logos {
    gap: 24px;
  }
}
</style>
