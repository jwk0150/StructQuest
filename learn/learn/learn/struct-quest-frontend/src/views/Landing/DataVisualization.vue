<template>
  <section id="dataviz" class="dataviz-section">
    <!-- Particle background -->
    <div class="particle-bg-wrapper">
      <ParticleBackground />
    </div>
    <div class="section-inner">
      <!-- Section Header -->
      <div class="section-header" ref="headerRef">
        <span class="section-tag">可视化展示</span>
        <h2 class="section-title">看见数据结构的<span class="title-accent">美</span></h2>
        <p class="section-subtitle">
          不再面对枯燥的代码。用可视化拆解每个数据结构的核心逻辑，让理解变得直观而深刻。
        </p>
      </div>

      <!-- Dashboard Grid -->
      <div class="viz-dashboard" ref="dashboardRef">
        <!-- Row 1: Tree + Graph -->
        <div class="viz-row">
          <!-- Tree Visualization -->
          <div class="viz-panel" ref="vizPanels">
            <div class="viz-panel-header">
              <div class="panel-dot" style="background: #4F7CFF;"></div>
              <h4>二叉树</h4>
              <span class="panel-badge">Tree</span>
            </div>
            <div class="viz-panel-body">
              <svg viewBox="0 0 300 180" class="tree-svg">
                <!-- Edges -->
                <g stroke="#CBD5E1" stroke-width="1.5" fill="none">
                  <path d="M150 20 L75 70"/>
                  <path d="M150 20 L225 70"/>
                  <path d="M75 70 L40 120"/>
                  <path d="M75 70 L110 120"/>
                  <path d="M225 70 L190 120"/>
                  <path d="M225 70 L260 120"/>
                </g>
                <!-- Nodes -->
                <g v-for="(node, i) in treeNodes" :key="i">
                  <circle :cx="node.x" :cy="node.y" r="14" :fill="node.fill" stroke="#fff" stroke-width="2"/>
                  <text :x="node.x" :y="node.y + 5" text-anchor="middle" fill="#fff" font-size="11" font-weight="600">{{ node.val }}</text>
                </g>
              </svg>
            </div>
          </div>

          <!-- Graph Visualization -->
          <div class="viz-panel" ref="vizPanels">
            <div class="viz-panel-header">
              <div class="panel-dot" style="background: #818CF8;"></div>
              <h4>图</h4>
              <span class="panel-badge">Graph</span>
            </div>
            <div class="viz-panel-body">
              <svg viewBox="0 0 300 180" class="graph-svg">
                <!-- Edges -->
                <g stroke="#CBD5E1" stroke-width="1.2" fill="none">
                  <path d="M150 20 L100 90"/>
                  <path d="M150 20 L200 90"/>
                  <path d="M100 90 L60 150"/>
                  <path d="M100 90 L150 140"/>
                  <path d="M200 90 L150 140"/>
                  <path d="M200 90 L240 150"/>
                </g>
                <!-- Nodes -->
                <g v-for="(node, i) in graphNodes" :key="i">
                  <circle :cx="node.x" :cy="node.y" r="12" :fill="node.fill" stroke="#fff" stroke-width="2"/>
                </g>
              </svg>
            </div>
          </div>
        </div>

        <!-- Row 2: Array + Linked List + Stack + Heap -->
        <div class="viz-row viz-row--quad">
          <!-- Array -->
          <div class="viz-panel viz-panel--sm" ref="vizPanels">
            <div class="viz-panel-header">
              <div class="panel-dot" style="background: #6366F1;"></div>
              <h4>数组</h4>
              <span class="panel-badge">Array</span>
            </div>
            <div class="viz-panel-body">
              <div class="array-viz">
                <div class="array-cell" v-for="i in 8" :key="i" :style="{ background: i <= 4 ? 'rgba(99,102,241,0.1)' : '#fff', borderColor: i <= 4 ? '#6366F1' : '#E5E7EB' }">
                  <span :style="{ color: i <= 4 ? '#6366F1' : '#9CA3AF' }">{{ [5, 2, 8, 1, null, null, null, null][i-1] ?? '—' }}</span>
                  <small>{{ i - 1 }}</small>
                </div>
              </div>
            </div>
          </div>

          <!-- Linked List -->
          <div class="viz-panel viz-panel--sm" ref="vizPanels">
            <div class="viz-panel-header">
              <div class="panel-dot" style="background: #A78BFA;"></div>
              <h4>链表</h4>
              <span class="panel-badge">Linked List</span>
            </div>
            <div class="viz-panel-body">
              <div class="list-viz">
                <div class="list-node" v-for="i in 4" :key="i">
                  <div class="list-node-val">{{ ['A','B','C','D'][i-1] }}</div>
                  <svg v-if="i < 4" width="20" height="12" viewBox="0 0 20 12" fill="none">
                    <path d="M2 6h14M14 2l4 4-4 4" stroke="#CBD5E1" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </div>
              </div>
            </div>
          </div>

          <!-- Stack -->
          <div class="viz-panel viz-panel--sm" ref="vizPanels">
            <div class="viz-panel-header">
              <div class="panel-dot" style="background: #F59E0B;"></div>
              <h4>栈</h4>
              <span class="panel-badge">Stack</span>
            </div>
            <div class="viz-panel-body">
              <div class="stack-viz">
                <div class="stack-item" v-for="i in 4" :key="i" :style="{ opacity: 1 - (4 - i) * 0.15 }">
                  {{ ['Push D','Push C','Push B','Push A'][i-1] }}
                </div>
                <div class="stack-arrow">← Top</div>
              </div>
            </div>
          </div>

          <!-- Heap -->
          <div class="viz-panel viz-panel--sm" ref="vizPanels">
            <div class="viz-panel-header">
              <div class="panel-dot" style="background: #10B981;"></div>
              <h4>堆</h4>
              <span class="panel-badge">Heap</span>
            </div>
            <div class="viz-panel-body">
              <svg viewBox="0 0 200 120" class="heap-svg">
                <g stroke="#CBD5E1" stroke-width="1.2" fill="none">
                  <path d="M100 10 L50 50"/>
                  <path d="M100 10 L150 50"/>
                  <path d="M50 50 L25 90"/>
                  <path d="M50 50 L75 90"/>
                  <path d="M150 50 L125 90"/>
                  <path d="M150 50 L175 90"/>
                </g>
                <g v-for="(n, i) in heapNodes" :key="i">
                  <circle :cx="n.x" :cy="n.y" r="11" fill="#ECFDF5" stroke="#10B981" stroke-width="1.5"/>
                  <text :x="n.x" :y="n.y + 4" text-anchor="middle" fill="#059669" font-size="10" font-weight="600">{{ n.val }}</text>
                </g>
              </svg>
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
import ParticleBackground from './ParticleBackground.vue'

gsap.registerPlugin(ScrollTrigger)

const treeNodes = [
  { x: 150, y: 20, val: '8', fill: '#4F7CFF' },
  { x: 75, y: 70, val: '3', fill: '#818CF8' },
  { x: 225, y: 70, val: '10', fill: '#6366F1' },
  { x: 40, y: 120, val: '1', fill: '#A78BFA' },
  { x: 110, y: 120, val: '6', fill: '#A78BFA' },
  { x: 190, y: 120, val: '—', fill: '#E5E7EB' },
  { x: 260, y: 120, val: '14', fill: '#A78BFA' },
]

const graphNodes = [
  { x: 150, y: 20, fill: '#4F7CFF' },
  { x: 100, y: 90, fill: '#818CF8' },
  { x: 200, y: 90, fill: '#6366F1' },
  { x: 60, y: 150, fill: '#A78BFA' },
  { x: 150, y: 140, fill: '#C4B5FD' },
  { x: 240, y: 150, fill: '#A78BFA' },
]

const heapNodes = [
  { x: 100, y: 10, val: '2', fill: '#ECFDF5' },
  { x: 50, y: 50, val: '5', fill: '#ECFDF5' },
  { x: 150, y: 50, val: '8', fill: '#ECFDF5' },
  { x: 25, y: 90, val: '10', fill: '#ECFDF5' },
  { x: 75, y: 90, val: '12', fill: '#ECFDF5' },
  { x: 125, y: 90, val: '15', fill: '#ECFDF5' },
  { x: 175, y: 90, val: '20', fill: '#ECFDF5' },
]

const headerRef = ref(null)
const dashboardRef = ref(null)
const vizPanels = ref([])

onMounted(() => {
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

  // Dashboard panels animation
  if (dashboardRef.value) {
    const panels = dashboardRef.value.querySelectorAll('.viz-panel')
    gsap.from(panels, {
      scrollTrigger: { trigger: dashboardRef.value, start: 'top 75%' },
      opacity: 0,
      y: 30,
      scale: 0.97,
      duration: 0.7,
      stagger: 0.1,
      ease: 'power3.out',
    })
  }
})
</script>

<style lang="scss" scoped>
.dataviz-section {
  padding: var(--lp-section-gap, 140px) 40px;
  background: var(--lp-bg-secondary);
  position: relative;
  overflow: hidden;
}

/* Particle canvas wrapper */
.particle-bg-wrapper {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}

/* Ensure section content is above particles */
.dataviz-section .section-inner {
  position: relative;
  z-index: 2;
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

.title-accent { color: var(--lp-primary); }

.section-subtitle {
  font-size: 17px;
  line-height: 1.7;
  color: var(--lp-text-secondary);
  margin: 0 auto;
  max-width: 500px;
}

/* ── Dashboard Grid ── */
.viz-dashboard {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.viz-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;

  &--quad {
    grid-template-columns: repeat(4, 1fr);
  }
}

/* ── Viz Panel ── */
.viz-panel {
  background: var(--lp-bg);
  border: 1px solid var(--lp-border-light);
  border-radius: var(--lp-radius-xl);
  box-shadow: var(--lp-shadow-sm);
  overflow: hidden;
  transition: all var(--lp-transition-base);

  &:hover {
    box-shadow: var(--lp-shadow-md);
    border-color: var(--lp-border);
  }

  &--sm {
    /* smaller panels */
  }
}

.viz-panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--lp-border-light);

  h4 {
    font-family: var(--lp-font-display);
    font-size: 14px;
    font-weight: 600;
    color: var(--lp-text);
    margin: 0;
    flex: 1;
  }
}

.panel-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.panel-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: var(--lp-radius-full);
  background: var(--lp-bg-secondary);
  color: var(--lp-text-tertiary);
  font-family: var(--lp-font-mono);
  letter-spacing: 0.03em;
}

.viz-panel-body {
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 180px;
}

/* SVG styles */
.tree-svg, .graph-svg, .heap-svg {
  width: 100%;
  height: auto;
  max-height: 180px;
}

/* Array visual */
.array-viz {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  justify-content: center;
}

.array-cell {
  width: 48px;
  height: 56px;
  border-radius: var(--lp-radius-md);
  border: 1.5px solid #E5E7EB;
  background: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  transition: all var(--lp-transition-fast);

  &:hover {
    transform: translateY(-2px);
    box-shadow: var(--lp-shadow-sm);
  }

  span {
    font-size: 15px;
    font-weight: 700;
    font-family: var(--lp-font-mono);
  }

  small {
    font-size: 10px;
    color: var(--lp-text-tertiary);
    font-family: var(--lp-font-mono);
  }
}

/* Linked List visual */
.list-viz {
  display: flex;
  align-items: center;
  gap: 0;
  overflow-x: auto;
  padding: 8px 0;
}

.list-node {
  display: flex;
  align-items: center;
  gap: 0;
}

.list-node-val {
  width: 36px;
  height: 36px;
  border-radius: var(--lp-radius-md);
  background: rgba(167, 139, 250, 0.1);
  border: 1.5px solid #A78BFA;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  color: #7C3AED;
  font-family: var(--lp-font-mono);
}

/* Stack visual */
.stack-viz {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 8px;
  position: relative;
}

.stack-item {
  padding: 6px 16px;
  border-radius: var(--lp-radius-sm);
  background: rgba(245, 158, 11, 0.1);
  border: 1px solid rgba(245, 158, 11, 0.3);
  font-size: 12px;
  font-weight: 600;
  color: #D97706;
  font-family: var(--lp-font-mono);
}

.stack-arrow {
  font-size: 11px;
  color: var(--lp-text-tertiary);
  margin-top: 4px;
  font-weight: 500;
}

/* ── Responsive ── */
@media (max-width: 1024px) {
  .viz-row--quad {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .dataviz-section {
    padding: 80px 24px;
  }

  .viz-row {
    grid-template-columns: 1fr;
  }

  .viz-row--quad {
    grid-template-columns: 1fr;
  }

  .section-header {
    margin-bottom: 48px;
  }
}
</style>
