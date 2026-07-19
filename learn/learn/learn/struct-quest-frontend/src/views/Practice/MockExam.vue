<template>
  <div class="mock-page animate-in">
    <header class="mp-header">
      <router-link to="/app/practice" class="mp-back">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="15 18 9 12 15 6"/></svg>
        返回练习中心
      </router-link>
      <h1 class="mp-title">📊 AI 模拟考试</h1>
      <p class="mp-subtitle">真实考试环境模拟 + AI 智能评分 + 详细学习报告</p>
    </header>

    <div class="mp-exam-card">
      <div class="mpec-glow"></div>

      <div class="mpec-badge">408 模拟</div>
      <h3 class="mpec-title">{{ preset.title }}</h3>

      <div class="mpec-meta">
        <div class="mpec-meta-item">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          <span>{{ preset.duration }} 分钟</span>
        </div>
        <div class="mpec-meta-item">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          <span>{{ preset.questions }} 题</span>
        </div>
      </div>

      <div class="mpec-features">
        <div v-for="(feat, idx) in preset.features" :key="idx" class="mpec-feat">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="20 6 9 17 4 12"/></svg>
          {{ feat }}
        </div>
      </div>

      <button class="mpec-cta" @click="startExam">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>
        开始考试
      </button>

      <p class="mpec-hint">考试结束后自动生成 AI 学习报告</p>
    </div>

    <!-- Exam rules -->
    <div class="mp-rules">
      <h3 class="mp-rules-title">考试规则</h3>
      <ul>
        <li>全程计时，不可暂停</li>
        <li>提交后由 AI 自动评分</li>
        <li>每道题提供详细 AI 解析</li>
        <li>自动关联薄弱知识点到资源中心</li>
        <li>分数纳入学习画像，影响后续推荐</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { MOCK_EXAM_PRESET } from './practiceData'

const router = useRouter()
const preset = MOCK_EXAM_PRESET

function startExam() {
  router.push({
    path: '/app/exam/ch05_tree_basic',
    query: { practice: 'mock', mode: 'mock', count: preset.questions, difficulty: 'hard' },
  })
}
</script>

<style scoped>
.mock-page { max-width: 800px; margin: 0 auto; padding: var(--space-6) var(--space-8) var(--space-12); }
.mp-header { margin-bottom: var(--space-8); }
.mp-back {
  display: inline-flex; align-items: center; gap: 6px; color: var(--text-tertiary);
  text-decoration: none; font-size: var(--text-xs); font-weight: var(--font-semibold);
  margin-bottom: var(--space-3); transition: color var(--transition-fast);
}
.mp-back:hover { color: var(--color-primary); }
.mp-title { font-size: var(--text-3xl); font-weight: var(--font-extrabold); color: var(--text-main); margin: 0 0 4px; }
.mp-subtitle { font-size: var(--text-sm); color: var(--text-secondary); margin: 0; }

/* Exam card */
.mp-exam-card {
  position: relative; display: flex; flex-direction: column; align-items: center;
  padding: var(--space-10) var(--space-6); background: var(--bg-elevated);
  border: 1px solid rgba(20, 184, 166, 0.15); border-radius: var(--radius-xl);
  text-align: center; overflow: hidden; margin-bottom: var(--space-8);
}
.mpec-glow {
  position: absolute; top: -20%; left: 50%; transform: translateX(-50%);
  width: 380px; height: 380px;
  background: radial-gradient(circle, rgba(20, 184, 166, 0.05) 0%, transparent 70%);
  pointer-events: none;
}

.mpec-badge {
  padding: 4px 16px; background: rgba(20, 184, 166, 0.1);
  border-radius: var(--radius-round); font-size: var(--text-xs);
  font-weight: var(--font-bold); color: var(--color-accent-teal);
  margin-bottom: var(--space-3); position: relative;
}

.mpec-title { font-size: var(--text-2xl); font-weight: var(--font-extrabold); color: var(--text-main); margin: 0 0 var(--space-5); position: relative; }

.mpec-meta {
  display: flex; gap: var(--space-6); margin-bottom: var(--space-5); position: relative;
}

.mpec-meta-item {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 18px; background: var(--bg-tertiary);
  border-radius: var(--radius-sm); font-size: var(--text-sm);
  font-weight: var(--font-semibold); color: var(--text-secondary);
}

.mpec-features {
  display: flex; flex-wrap: wrap; gap: var(--space-3);
  justify-content: center; margin-bottom: var(--space-6); position: relative;
}

.mpec-feat {
  display: flex; align-items: center; gap: 5px;
  padding: 5px 12px; background: rgba(20, 184, 166, 0.06);
  border-radius: var(--radius-round); font-size: var(--text-xs);
  font-weight: var(--font-semibold); color: var(--color-accent-teal);
}

.mpec-cta {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 14px 40px; background: linear-gradient(135deg, #14b8a6, #0d9488);
  color: #fff; border: none; border-radius: var(--radius-sm);
  font-size: var(--text-base); font-weight: var(--font-bold); cursor: pointer;
  position: relative; transition: all var(--transition-fast);
  box-shadow: 0 4px 24px rgba(20, 184, 166, 0.3);
}
.mpec-cta:hover { transform: translateY(-2px); box-shadow: 0 8px 32px rgba(20, 184, 166, 0.4); }

.mpec-hint {
  margin: var(--space-4) 0 0;
  font-size: 11px; color: var(--text-tertiary); position: relative;
}

/* Rules */
.mp-rules {
  padding: var(--space-6); background: var(--bg-elevated);
  border: 1px solid var(--border-light); border-radius: var(--radius-lg);
}

.mp-rules-title { font-size: var(--text-base); font-weight: var(--font-bold); color: var(--text-main); margin: 0 0 var(--space-3); }

.mp-rules ul { margin: 0; padding: 0 0 0 var(--space-5); }
.mp-rules li { font-size: var(--text-xs); color: var(--text-secondary); line-height: var(--leading-relaxed); margin-bottom: 6px; }

@media (max-width: 600px) {
  .mpec-meta { flex-direction: column; }
  .mp-title { font-size: var(--text-2xl); }
}
</style>

