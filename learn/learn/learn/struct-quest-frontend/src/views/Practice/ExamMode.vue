<template>
  <div class="exam-mode-page animate-in">
    <header class="em-header">
      <router-link to="/app/practice" class="em-back">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="15 18 9 12 15 6"/></svg>
        返回练习中心
      </router-link>
      <h1 class="em-title">📖 考研模式</h1>
      <p class="em-subtitle">408 数据结构 — 选择要练习的章节</p>
    </header>

    <!-- Chapter Grid -->
    <div class="em-chapters">
      <router-link
        v-for="ch in chapters"
        :key="ch.id"
        :to="{ path: `/app/exam/${ch.nodeId}`, query: { practice: 'exam', mode: 'exam', count: 10 } }"
        class="em-chapter-card"
      >
        <span class="ch-icon">{{ ch.icon }}</span>
        <span class="ch-name">{{ ch.name }}</span>
        <svg class="ch-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="9 18 15 12 9 6"/></svg>
      </router-link>
    </div>

    <!-- Quick actions -->
    <div class="em-actions">
      <h3 class="em-action-title">快捷入口</h3>
      <div class="em-action-grid">
        <div class="em-action-card purple" @click="goAllChapters">
          <span class="ac-icon">📋</span>
          <span class="ac-label">全部章节</span>
          <span class="ac-sub">随机抽取所有章节题目</span>
        </div>
        <div class="em-action-card orange" @click="goWrongOnly">
          <span class="ac-icon">❌</span>
          <span class="ac-label">错题模式</span>
          <span class="ac-sub">只做你做错过的题目</span>
        </div>
        <div class="em-action-card gold" @click="goBookmarked">
          <span class="ac-icon">⭐</span>
          <span class="ac-label">收藏题目</span>
          <span class="ac-sub">复习你收藏的题目</span>
        </div>
        <div class="em-action-card teal" @click="goMockExam">
          <span class="ac-icon">📝</span>
          <span class="ac-label">开始考试</span>
          <span class="ac-sub">模拟真实考试环境</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { CHAPTERS } from './practiceData'
import knowledgeApi from '@/api/knowledge'

const router = useRouter()
const chapters = ref(CHAPTERS)

onMounted(async () => {
  // try to load chapters from API
  try {
    const res = await knowledgeApi.getMap()
    const data = res?.data || res || {}
    const nodes = data.nodes || data.knowledge_nodes || []
    if (nodes.length > 0) {
      chapters.value = nodes.slice(0, 8).map((n, i) => ({
        id: n.id || `ch${i + 1}`,
        name: n.name || n.title || CHAPTERS[i]?.name || `章节${i + 1}`,
        nodeId: n.node_id || n.id || CHAPTERS[i]?.nodeId || `ch-${i + 1}`,
        icon: CHAPTERS[i]?.icon || '📖',
      }))
    }
  } catch { /* use default chapters */ }
})

function goAllChapters() { router.push('/app/practice/random') }
function goWrongOnly() { router.push('/app/practice/wrong') }
function goBookmarked() { router.push('/app/practice/wrong') }
function goMockExam() { router.push('/app/practice/mock') }
</script>

<style scoped>
.exam-mode-page {
  max-width: 1100px;
  margin: 0 auto;
  padding: var(--space-6) var(--space-8) var(--space-12);
}

.em-header {
  margin-bottom: var(--space-8);
}

.em-back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--text-tertiary);
  text-decoration: none;
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  margin-bottom: var(--space-3);
  transition: color var(--transition-fast);
}
.em-back:hover { color: var(--color-primary); }

.em-title {
  font-size: var(--text-3xl);
  font-weight: var(--font-extrabold);
  color: var(--text-main);
  margin: 0 0 4px;
}
.em-subtitle {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin: 0;
}

/* Chapters */
.em-chapters {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-3);
  margin-bottom: var(--space-10);
}

.em-chapter-card {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  background: var(--bg-elevated);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  text-decoration: none;
  color: var(--text-main);
  transition: all var(--transition-fast);
  cursor: pointer;
}
.em-chapter-card:hover {
  border-color: rgba(200,76,90, 0.3);
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.ch-icon { font-size: 24px; flex-shrink: 0; }
.ch-name {
  flex: 1;
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
}
.ch-arrow { color: var(--text-tertiary); flex-shrink: 0; }

/* Actions */
.em-actions { margin-top: var(--space-6); }

.em-action-title {
  font-size: var(--text-base);
  font-weight: var(--font-bold);
  color: var(--text-main);
  margin: 0 0 var(--space-4);
}

.em-action-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-3);
}

.em-action-card {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: var(--space-4) var(--space-5);
  background: var(--bg-elevated);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}
.em-action-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-sm); }
.em-action-card.purple:hover { border-color: rgba(217,121,130, 0.3); }
.em-action-card.orange:hover { border-color: rgba(249, 115, 22, 0.3); }
.em-action-card.gold:hover { border-color: rgba(245, 158, 11, 0.3); }
.em-action-card.teal:hover { border-color: rgba(20, 184, 166, 0.3); }

.ac-icon { font-size: 22px; }
.ac-label { font-size: var(--text-sm); font-weight: var(--font-semibold); color: var(--text-main); }
.ac-sub { font-size: 11px; color: var(--text-tertiary); }

@media (max-width: 900px) {
  .em-chapters { grid-template-columns: repeat(2, 1fr); }
  .em-action-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 600px) {
  .em-chapters, .em-action-grid { grid-template-columns: 1fr; }
  .em-title { font-size: var(--text-2xl); }
}
</style>


