<template>
  <div class="wrong-page animate-in">
    <header class="wp-header">
      <router-link to="/app/practice" class="wp-back">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="15 18 9 12 15 6"/></svg>
        返回练习中心
      </router-link>
      <h1 class="wp-title">❌ AI 错题本</h1>
      <p class="wp-subtitle">基于间隔重复算法，精准攻克你的薄弱知识点</p>
    </header>

    <!-- Loading -->
    <div v-if="loading" class="wp-loading">
      <div class="wp-skeleton" v-for="i in 3" :key="i">
        <span class="sk-icon"></span>
        <span class="sk-line w-60"></span>
        <span class="sk-line w-40"></span>
      </div>
    </div>

    <!-- Empty -->
    <div v-else-if="!loading && items.length === 0" class="wp-empty">
      <span class="empty-icon">🎉</span>
      <h3>暂无错题</h3>
      <p>继续保持！你做得很好。</p>
      <router-link to="/app/practice" class="empty-cta">去练习</router-link>
    </div>

    <!-- List -->
    <div v-else class="wp-list">
      <div
        v-for="item in sortedItems"
        :key="item.id || item.nodeId"
        class="wp-item"
        @click="goPractice(item)"
      >
        <div class="wpi-rank">
          <span class="wpi-stars">
            <span v-for="i in 5" :key="i" class="star" :class="{ filled: i <= itemStars(item) }">★</span>
          </span>
          <span class="wpi-count" v-if="item.mistakeCount || item.count">
            连续错 {{ item.mistakeCount || item.count }} 次
          </span>
        </div>
        <div class="wpi-info">
          <span class="wpi-node" :class="{ priority: itemStars(item) >= 4 }">{{ item.nodeName || item.name || '未知知识点' }}</span>
          <span class="wpi-suggestion">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
            建议立即练习
          </span>
        </div>
        <span class="wpi-cta">开始练习</span>
      </div>
    </div>

    <!-- Stats -->
    <div class="wp-stats" v-if="!loading && items.length > 0">
      <div class="wps-card">
        <em>{{ items.length }}</em>
        <span>错题节点</span>
      </div>
      <div class="wps-card">
        <em>{{ totalMistakes }}</em>
        <span>累计错误</span>
      </div>
      <div class="wps-card">
        <em>{{ masteredCount }}</em>
        <span>已掌握</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getMistakes } from '@/api/practice'

const router = useRouter()
const items = ref([])
const loading = ref(true)

const sortedItems = computed(() => {
  return [...items.value].sort((a, b) => {
    const ac = a.mistakeCount || a.count || 0
    const bc = b.mistakeCount || b.count || 0
    return bc - ac
  })
})

const totalMistakes = computed(() =>
  items.value.reduce((sum, item) => sum + (item.mistakeCount || item.count || 1), 0)
)

const masteredCount = computed(() =>
  items.value.filter((item) => (item.mistakeCount || item.count || 0) <= 1).length
)

onMounted(async () => {
  loading.value = true
  items.value = await getMistakes()
  loading.value = false
})

function itemStars(item) {
  const c = item.mistakeCount || item.count || 1
  return Math.min(c, 5)
}

function goPractice(item) {
  const nodeId = item.nodeId || item.node_id || 'ch05_tree_basic'
  router.push(`/app/exam/${nodeId}`)
}
</script>

<style scoped>
.wrong-page {
  max-width: 900px;
  margin: 0 auto;
  padding: var(--space-6) var(--space-8) var(--space-12);
}
.wp-header { margin-bottom: var(--space-8); }
.wp-back {
  display: inline-flex; align-items: center; gap: 6px; color: var(--text-tertiary);
  text-decoration: none; font-size: var(--text-xs); font-weight: var(--font-semibold);
  margin-bottom: var(--space-3); transition: color var(--transition-fast);
}
.wp-back:hover { color: var(--color-primary); }
.wp-title { font-size: var(--text-3xl); font-weight: var(--font-extrabold); color: var(--text-main); margin: 0 0 4px; }
.wp-subtitle { font-size: var(--text-sm); color: var(--text-secondary); margin: 0; }

/* Skeleton */
.wp-loading { display: flex; flex-direction: column; gap: var(--space-3); }
.wp-skeleton {
  display: flex; align-items: center; gap: var(--space-4);
  padding: var(--space-5); background: var(--bg-elevated);
  border-radius: var(--radius-md); border: 1px solid var(--border-light);
}
.wp-skeleton .sk-icon { width: 40px; height: 40px; border-radius: var(--radius-sm); background: var(--bg-tertiary); }
.wp-skeleton .sk-line { height: 12px; border-radius: 6px; background: var(--bg-tertiary); }
.w-60 { width: 60%; } .w-40 { width: 40%; }

/* Empty */
.wp-empty {
  text-align: center;
  padding: var(--space-16) var(--space-6);
}
.empty-icon { font-size: 56px; display: block; margin-bottom: var(--space-3); }
.wp-empty h3 { font-size: var(--text-xl); font-weight: var(--font-bold); color: var(--text-main); margin: 0 0 4px; }
.wp-empty p { font-size: var(--text-sm); color: var(--text-tertiary); margin: 0 0 var(--space-5); }
.empty-cta {
  display: inline-flex; padding: 8px 24px; background: var(--color-primary);
  color: #fff; border-radius: var(--radius-sm); text-decoration: none;
  font-size: var(--text-sm); font-weight: var(--font-bold);
}

/* List */
.wp-list { display: flex; flex-direction: column; gap: var(--space-3); margin-bottom: var(--space-8); }

.wp-item {
  display: flex; align-items: center; gap: var(--space-5);
  padding: var(--space-5); background: var(--bg-elevated);
  border: 1px solid var(--border-light); border-radius: var(--radius-md);
  cursor: pointer; transition: all var(--transition-fast);
}
.wp-item:hover {
  border-color: rgba(249, 115, 22, 0.25);
  transform: translateX(4px);
  box-shadow: var(--shadow-sm);
}

.wpi-rank { display: flex; flex-direction: column; gap: 2px; min-width: 100px; }
.wpi-stars .star { color: #e2e6f0; font-size: 13px; }
.wpi-stars .star.filled { color: #f97316; }
.wpi-count { font-size: 10px; color: var(--text-tertiary); font-weight: var(--font-semibold); }

.wpi-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.wpi-node { font-size: var(--text-base); font-weight: var(--font-bold); color: var(--text-main); }
.wpi-node.priority { color: #dc2626; }

.wpi-suggestion {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 11px; color: var(--color-accent-teal); font-weight: var(--font-semibold);
}

.wpi-cta {
  padding: 7px 18px; background: linear-gradient(135deg, #f97316, #ef4444);
  color: #fff; border-radius: var(--radius-sm); font-size: var(--text-xs);
  font-weight: var(--font-bold); white-space: nowrap; transition: opacity var(--transition-fast);
}
.wp-item:hover .wpi-cta { opacity: 0.9; }

/* Stats */
.wp-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--space-4); }
.wps-card {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  padding: var(--space-5); background: var(--bg-elevated);
  border: 1px solid var(--border-light); border-radius: var(--radius-md);
}
.wps-card em { font-size: var(--text-2xl); font-weight: var(--font-extrabold); color: var(--color-primary); font-style: normal; }
.wps-card span { font-size: var(--text-xs); color: var(--text-tertiary); }

@media (max-width: 600px) {
  .wp-item { flex-wrap: wrap; }
  .wp-stats { grid-template-columns: repeat(3, 1fr); }
  .wp-title { font-size: var(--text-2xl); }
}
</style>
