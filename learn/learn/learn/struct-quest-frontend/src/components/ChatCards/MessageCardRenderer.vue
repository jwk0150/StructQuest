<template>
  <div class="message-cards">
    <template v-for="(card, idx) in cards" :key="idx">
      <div class="card-container" :class="{ collapsed: card.collapsed }">
        <!-- 卡片头部 -->
        <div class="card-header" @click="toggleCard(idx)">
          <span class="card-icon">{{ card.icon }}</span>
          <span class="card-title">{{ card.title }}</span>
          <span v-if="card.difficulty" class="difficulty-badge">{{ card.difficulty }}</span>
          <el-icon class="collapse-icon" :class="{ rotated: !collapsedMap[idx] }">
            <ArrowDown />
          </el-icon>
        </div>

        <!-- 卡片内容 -->
        <div class="card-body" v-show="!collapsedMap[idx]">
          <!-- 📘 知识讲解卡 -->
          <KnowledgeCard v-if="card.type === 'knowledge'" :data="card.data" />

          <!-- 💻 代码卡 -->
          <CodeCard v-else-if="card.type === 'code'" :data="card.data" :actions="card.actions" />

          <!-- 📊 复杂度卡 -->
          <ComplexityCard v-else-if="card.type === 'complexity'" :data="card.data" />

          <!-- 📝 练习卡 -->
          <InteractiveQuizCard v-else-if="card.type === 'quiz'" :data="card.data" @submit="(r) => $emit('quiz-submit', r)" />

          <!-- 🎯 建议卡 -->
          <SuggestionCard v-else-if="card.type === 'suggestion'" :data="card.data" @navigate="(t) => $emit('navigate', t)" />

          <!-- 🗺 知识图谱卡 -->
          <KnowledgeGraphCard v-else-if="card.type === 'knowledge_graph'" :data="card.data" @click-node="(n) => $emit('navigate', n)" />

          <!-- ⚖️ 对比卡 -->
          <ComparisonCard v-else-if="card.type === 'comparison'" :data="card.data" />

          <!-- 🔧 调试卡 -->
          <DebugCard v-else-if="card.type === 'debug'" :data="card.data" />

          <!-- 📐 Mermaid -->
          <MermaidRenderer v-else-if="card.type === 'mermaid'" :code="card.data.code" />
        </div>

        <!-- 卡片操作按钮 -->
        <div class="card-footer" v-if="card.actions?.length && !collapsedMap[idx]">
          <el-button
            v-for="(action, ai) in card.actions"
            :key="ai"
            link
            size="small"
            @click.stop="handleAction(action, card)"
          >
            {{ action.label }}
          </el-button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ArrowDown } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import KnowledgeCard from './KnowledgeCard.vue'
import CodeCard from './CodeCard.vue'
import ComplexityCard from './ComplexityCard.vue'
import InteractiveQuizCard from './InteractiveQuizCard.vue'
import SuggestionCard from './SuggestionCard.vue'
import KnowledgeGraphCard from './KnowledgeGraphCard.vue'
import ComparisonCard from './ComparisonCard.vue'
import DebugCard from './DebugCard.vue'
import MermaidRenderer from './MermaidRenderer.vue'

const props = defineProps({
  cards: { type: Array, default: () => [] },
})

const emit = defineEmits(['quiz-submit', 'navigate', 'action'])

// 折叠状态管理
const collapsedMap = ref({})

watch(() => props.cards, (newCards) => {
  newCards.forEach((card, idx) => {
    if (!(idx in collapsedMap.value)) {
      collapsedMap.value[idx] = !!card.collapsed
    }
  })
}, { immediate: true, deep: true })

function toggleCard(idx) {
  collapsedMap.value[idx] = !collapsedMap.value[idx]
}

function handleAction(action, card) {
  if (action.action === 'copy' && action.target) {
    navigator.clipboard.writeText(action.target).then(() => {
      ElMessage.success('已复制到剪贴板')
    })
  } else if (action.action === 'toggle_explain') {
    // 由 CodeCard 内部处理
  }
  emit('action', { action, card })
}
</script>

<style scoped>
.message-cards {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
}

.card-container {
  border: 1px solid #e8e8e8;
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
  transition: box-shadow 0.2s;
}
.card-container:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  cursor: pointer;
  user-select: none;
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.15s;
}
.card-header:hover {
  background: #f5f5f5;
}

.card-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  flex: 1;
}

.difficulty-badge {
  font-size: 12px;
  color: #f59e0b;
  background: #fef3c7;
  padding: 2px 8px;
  border-radius: 10px;
  flex-shrink: 0;
}

.collapse-icon {
  font-size: 14px;
  color: #999;
  transition: transform 0.25s;
  flex-shrink: 0;
}
.collapse-icon.rotated {
  transform: rotate(-180deg);
}

.card-body {
  padding: 14px;
}

.card-footer {
  display: flex;
  gap: 8px;
  padding: 8px 14px 12px;
  border-top: 1px solid #f5f5f5;
}
</style>
