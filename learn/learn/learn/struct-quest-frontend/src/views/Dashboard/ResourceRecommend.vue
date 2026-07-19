<template>
  <section class="resource-panel">
    <div class="panel-header">
      <h3 class="panel-title">
        <span class="title-icon">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>
          </svg>
        </span>
        为你推荐
      </h3>
    </div>

    <div class="resource-scroll">
      <div
        v-for="item in resources"
        :key="item.id"
        class="resource-card"
        @click="$emit('goNode', item.nodeId)"
      >
        <div class="rc-icon" :style="{ background: item.color + '15', color: item.color }">
          <svg v-if="item.type === 'animation'" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="5 3 19 12 5 21 5 3"/>
          </svg>
          <svg v-else-if="item.type === 'mindmap'" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="8"/><line x1="12" y1="4" x2="12" y2="20"/><line x1="4" y1="12" x2="20" y2="12"/>
          </svg>
          <svg v-else-if="item.type === 'code'" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>
          </svg>
          <svg v-else width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="9 9 15 15"/><polyline points="15 9 9 15"/>
          </svg>
        </div>
        <div class="rc-info">
          <span class="rc-tag" :style="{ background: item.color + '12', color: item.color }">{{ typeLabels[item.type] }}</span>
          <h4 class="rc-name">{{ item.name }}</h4>
          <p class="rc-desc">{{ item.desc }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
defineEmits(['goNode'])

defineProps({
  resources: {
    type: Array,
    default: () => [
      { id: 1, type: 'animation', name: '栈操作动画', desc: '入栈、出栈过程可视化', nodeId: 'stack_anim', color: '#d97982' },
      { id: 2, type: 'mindmap', name: '排序算法导图', desc: '七大排序对比总览', nodeId: 'sort_map', color: '#c84c5a' },
      { id: 3, type: 'code', name: 'AVL树实现', desc: 'Python 旋转操作实战', nodeId: 'avl_code', color: '#10b981' },
      { id: 4, type: 'video', name: '图论入门精讲', desc: 'BFS/DFS 算法解析', nodeId: 'graph_video', color: '#f59e0b' },
    ]
  }
})

const typeLabels = {
  animation: '动画',
  mindmap: '导图',
  code: '代码',
  video: '视频',
  article: '文章',
}
</script>

<style scoped>
.resource-panel {
  background: var(--bg-color);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);
  padding: 22px 24px;
  transition: box-shadow var(--transition-normal);
}
.resource-panel:hover {
  box-shadow: var(--shadow-card-hover);
}

.panel-header {
  margin-bottom: 16px;
}
.panel-title {
  display: flex;
  align-items: center;
  gap: 9px;
  font-size: 15px;
  font-weight: 700;
  color: var(--text-main);
  margin: 0;
}
.title-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: rgba(245,158,11,0.1);
  color: var(--color-accent-gold);
}

.resource-scroll {
  display: flex;
  gap: 14px;
  overflow-x: auto;
  padding-bottom: 6px;
  scroll-snap-type: x mandatory;
}
.resource-scroll::-webkit-scrollbar { height: 5px; }
.resource-scroll::-webkit-scrollbar-thumb { background: var(--border-color); border-radius: 3px; }

.resource-card {
  flex: 0 0 200px;
  padding: 16px;
  border-radius: 12px;
  border: 1px solid var(--border-light);
  background: var(--bg-secondary);
  cursor: pointer;
  transition: all var(--transition-normal);
  scroll-snap-align: start;
}
.resource-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
  border-color: rgba(200,76,90,0.12);
  background: var(--bg-color);
}

.rc-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
}
.rc-tag {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 6px;
  display: inline-block;
  margin-bottom: 6px;
}
.rc-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-main);
  margin: 0 0 4px;
}
.rc-desc {
  font-size: 11px;
  color: var(--text-tertiary);
  margin: 0;
  line-height: 1.4;
}
</style>

