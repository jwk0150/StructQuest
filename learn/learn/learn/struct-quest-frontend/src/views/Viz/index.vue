<template>
  <div class="viz-page">
    <div class="viz-header">
      <h1 class="viz-title">算法可视化</h1>
      <p class="viz-desc">通过动画直观理解数据结构与算法的运行过程</p>
    </div>

    <div class="viz-grid">
      <div v-for="item in vizItems" :key="item.id" class="viz-card" @click="router.push(item.path)">
        <div class="viz-card-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
          </svg>
        </div>
        <h3 class="viz-card-title">{{ item.name }}</h3>
        <p class="viz-card-desc">{{ item.desc }}</p>
        <span class="viz-card-tag">即将上线</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()

const vizItems = [
  { id: 1, name: '排序算法', desc: '冒泡、快排、归并等排序过程动画', path: '/app/viz' },
  { id: 2, name: '链表操作', desc: '插入、删除、反转等链表操作演示', path: '/app/viz' },
  { id: 3, name: '树遍历', desc: '前序、中序、后序、层序遍历动画', path: '/app/viz' },
  { id: 4, name: '图算法', desc: 'DFS、BFS、最短路径可视化', path: '/app/viz' },
  { id: 5, name: '栈与队列', desc: '入栈出栈、入队出队过程演示', path: '/app/viz' },
  { id: 6, name: '搜索算法', desc: '二分查找、哈希查找过程', path: '/app/viz' },
]
</script>

<style lang="scss" scoped>
.viz-page {
  max-width: 1280px;
  margin: 0 auto;
  padding: 40px 28px;
}

.viz-header {
  margin-bottom: 40px;
  text-align: center;
}
.viz-title {
  font-size: 32px;
  font-weight: 800;
  color: var(--text-main);
  margin-bottom: 8px;
  letter-spacing: -0.02em;
}
.viz-desc {
  font-size: 15px;
  color: var(--text-secondary);
  margin: 0;
}

.viz-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.viz-card {
  padding: 28px 24px;
  border-radius: var(--radius-lg);
  background: var(--bg-color);
  border: 1px solid var(--border-light);
  cursor: pointer;
  transition: all var(--transition-normal);
  position: relative;
  overflow: hidden;

  &:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-card-hover);
    border-color: rgba(99, 102, 241, 0.15);
  }
}
.viz-card-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: var(--hero-gradient-soft);
  color: var(--color-primary);
  margin-bottom: 16px;
}
.viz-card-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--text-main);
  margin: 0 0 6px;
}
.viz-card-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.5;
}
.viz-card-tag {
  position: absolute;
  top: 16px;
  right: 16px;
  font-size: 10px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 999px;
  background: rgba(245, 158, 11, 0.1);
  color: var(--color-accent-gold);
}
</style>
