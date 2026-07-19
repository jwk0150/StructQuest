<template>
  <div class="random-page animate-in">
    <header class="rp-header">
      <router-link to="/app/practice" class="rp-back">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="15 18 9 12 15 6"/></svg>
        返回练习中心
      </router-link>
      <h1 class="rp-title">AI 随机练习</h1>
      <p class="rp-subtitle">AI 个性化出题 + 本地精选题库兜底，稳定提供选择、填空和编程题</p>
    </header>

    <div class="rp-preview-card">
      <div class="preview-glow"></div>
      <div class="preview-icon">AI</div>
      <h3 class="preview-label">今天的 AI 练习套餐</h3>
      <div class="preview-items">
        <div class="preview-item">
          <span class="pi-icon">✓</span>
          <span class="pi-text">{{ preview.choices }} 道选择题</span>
        </div>
        <div class="preview-item">
          <span class="pi-icon">✓</span>
          <span class="pi-text">{{ preview.blanks }} 道填空题</span>
        </div>
        <div class="preview-item">
          <span class="pi-icon">✓</span>
          <span class="pi-text">{{ preview.coding }} 道编程题</span>
        </div>
      </div>
      <div class="preview-meta">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
        预计 {{ preview.duration }} 分钟
      </div>
      <button class="preview-cta" @click="startPractice">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>
        开始练习
      </button>
    </div>

    <div class="rp-custom-section">
      <h3 class="rp-section-title">AI 自定义生成</h3>
      <div class="rp-custom-form">
        <div class="form-row">
          <label class="form-label">我想练习</label>
          <select v-model="customTopic" class="form-input">
            <option v-for="topic in topicOptions" :key="topic.nodeId" :value="topic.nodeId">
              {{ topic.label }}
            </option>
          </select>
        </div>
        <div class="form-row">
          <label class="form-label">难度</label>
          <div class="form-stars">
            <button v-for="s in 4" :key="s" class="fs-star" :class="{ active: customDifficulty >= s }" @click="customDifficulty = s">
              ★
            </button>
          </div>
        </div>
        <div class="form-row">
          <label class="form-label">题量</label>
          <div class="form-qty">
            <button v-for="q in [8, 10, 12]" :key="q" class="fq-btn" :class="{ active: customQty === q }" @click="customQty = q">{{ q }} 题</button>
          </div>
        </div>
        <button class="form-submit" @click="generateCustom">生成题目</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { RANDOM_PREVIEW } from './practiceData'

const router = useRouter()
const preview = RANDOM_PREVIEW

const topicOptions = [
  { nodeId: 'ch01_algorithm', label: '算法与复杂度分析' },
  { nodeId: 'ch02_seq_list', label: '顺序表' },
  { nodeId: 'ch02_linked_list', label: '链表' },
  { nodeId: 'ch03_stack_basic', label: '栈' },
  { nodeId: 'ch03_queue_basic', label: '队列' },
  { nodeId: 'ch05_tree_basic', label: '树与二叉树' },
  { nodeId: 'ch06_graph_concept', label: '图与深度优先搜索' },
  { nodeId: 'ch06_shortest_path', label: '最短路径' },
  { nodeId: 'ch08_quick_sort', label: '快速排序' },
  { nodeId: 'ch07_binary_search', label: '二分查找' },
]

const customTopic = ref('ch05_tree_basic')
const customDifficulty = ref(2)
const customQty = ref(8)

function openMixedPractice(nodeId, count, difficulty) {
  router.push({
    path: `/app/exam/${nodeId}`,
    query: { practice: 'mixed', mode: 'mixed', count, difficulty },
  })
}

function startPractice() {
  openMixedPractice('ch05_tree_basic', 8, 'balanced')
}

function generateCustom() {
  const difficultyMap = { 1: 'easy', 2: 'balanced', 3: 'hard', 4: 'hard' }
  openMixedPractice(customTopic.value, customQty.value, difficultyMap[customDifficulty.value])
}
</script>

<style scoped>
.random-page {
  max-width: 800px;
  margin: 0 auto;
  padding: var(--space-6) var(--space-8) var(--space-12);
}
.rp-header { margin-bottom: var(--space-8); }
.rp-back {
  display: inline-flex; align-items: center; gap: 6px;
  color: var(--text-tertiary); text-decoration: none;
  font-size: var(--text-xs); font-weight: var(--font-semibold);
  margin-bottom: var(--space-3); transition: color var(--transition-fast);
}
.rp-back:hover { color: var(--color-primary); }
.rp-title { font-size: var(--text-3xl); font-weight: var(--font-extrabold); color: var(--text-main); margin: 0 0 4px; }
.rp-subtitle { font-size: var(--text-sm); color: var(--text-secondary); margin: 0; }

.rp-preview-card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--space-10) var(--space-6);
  background: var(--bg-elevated);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-xl);
  text-align: center;
  overflow: hidden;
  margin-bottom: var(--space-8);
}

.preview-glow {
  position: absolute;
  top: -30%;
  left: 50%;
  transform: translateX(-50%);
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(217,121,130, 0.06) 0%, transparent 70%);
  pointer-events: none;
}

.preview-icon {
  display: grid;
  place-items: center;
  width: 52px;
  height: 52px;
  border-radius: var(--radius-md);
  background: var(--bg-tertiary);
  color: var(--color-primary);
  font-size: var(--text-lg);
  font-weight: var(--font-extrabold);
  margin-bottom: var(--space-3);
  position: relative;
}
.preview-label { font-size: var(--text-xl); font-weight: var(--font-bold); color: var(--text-main); margin: 0 0 var(--space-5); position: relative; }

.preview-items {
  display: flex;
  gap: var(--space-5);
  margin-bottom: var(--space-4);
  position: relative;
  flex-wrap: wrap;
  justify-content: center;
}

.preview-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-round);
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  color: var(--text-secondary);
}

.pi-icon { color: #16a34a; font-weight: var(--font-bold); }

.preview-meta {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin-bottom: var(--space-6);
  position: relative;
}

.preview-cta {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 32px;
  background: var(--hero-gradient);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  font-weight: var(--font-bold);
  cursor: pointer;
  position: relative;
  transition: all var(--transition-fast);
  box-shadow: 0 4px 20px rgba(200,76,90, 0.3);
}
.preview-cta:hover { transform: translateY(-2px); box-shadow: 0 8px 28px rgba(200,76,90, 0.4); }

.rp-custom-section { margin-top: var(--space-8); }
.rp-section-title { font-size: var(--text-lg); font-weight: var(--font-bold); color: var(--text-main); margin: 0 0 var(--space-5); }

.rp-custom-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-6);
  background: var(--bg-elevated);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
}

.form-row { display: flex; align-items: center; gap: var(--space-3); flex-wrap: wrap; }
.form-label { font-size: var(--text-sm); font-weight: var(--font-semibold); color: var(--text-secondary); min-width: 72px; }
.form-input {
  flex: 1; min-width: 200px;
  padding: 8px 14px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  background: var(--bg-color);
  color: var(--text-main);
  outline: none;
  transition: border-color var(--transition-fast);
}
.form-input:focus { border-color: var(--color-primary); }

.form-stars { display: flex; gap: 4px; }
.fs-star {
  background: none; border: none; font-size: 22px; cursor: pointer;
  color: #e2e6f0; padding: 0 2px; transition: color var(--transition-fast);
}
.fs-star.active { color: #f59e0b; }

.form-qty { display: flex; gap: 6px; }
.fq-btn {
  padding: 6px 16px; border: 1px solid var(--border-color);
  border-radius: var(--radius-sm); background: var(--bg-color);
  font-size: var(--text-xs); font-weight: var(--font-semibold);
  color: var(--text-secondary); cursor: pointer;
  transition: all var(--transition-fast);
}
.fq-btn.active { background: var(--color-primary); color: #fff; border-color: var(--color-primary); }
.fq-btn:hover:not(.active) { border-color: var(--color-primary); }

.form-submit {
  padding: 10px 24px; background: var(--hero-gradient);
  color: #fff; border: none; border-radius: var(--radius-sm);
  font-size: var(--text-sm); font-weight: var(--font-bold); cursor: pointer;
  align-self: flex-start; transition: all var(--transition-fast);
  box-shadow: 0 4px 16px rgba(200,76,90, 0.25);
}
.form-submit:hover { transform: translateY(-1px); box-shadow: 0 6px 22px rgba(200,76,90, 0.35); }

@media (max-width: 600px) {
  .preview-items { flex-direction: column; align-items: center; }
  .rp-title { font-size: var(--text-2xl); }
}
</style>