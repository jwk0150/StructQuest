<template>
  <div class="suggestion-card">
    <!-- 已掌握 -->
    <div v-if="data.mastered?.length" class="sug-section">
      <div class="sug-label">✅ 已掌握</div>
      <div class="sug-tags">
        <el-tag v-for="(t, i) in data.mastered" :key="i" size="small" type="success" effect="plain">
          {{ t }}
        </el-tag>
      </div>
    </div>

    <!-- 薄弱点 -->
    <div v-if="data.weak_points?.length" class="sug-section">
      <div class="sug-label">❗ 待加强</div>
      <div class="sug-tags">
        <el-tag v-for="(t, i) in data.weak_points" :key="i" size="small" type="warning" effect="plain">
          {{ t }}
        </el-tag>
      </div>
    </div>

    <!-- 下一步建议 -->
    <div v-if="data.next_steps?.length" class="sug-section">
      <div class="sug-label">🎓 建议下一步</div>
      <div class="next-steps">
        <div
          v-for="(step, i) in data.next_steps"
          :key="i"
          class="next-step-item"
          @click="$emit('navigate', step)"
        >
          <div class="step-topic">
            <span class="step-arrow">→</span>
            <span class="step-name">{{ step.topic }}</span>
          </div>
          <div class="step-reason">{{ step.reason }}</div>
        </div>
      </div>
    </div>

    <!-- 知识图谱快照 -->
    <div v-if="data.knowledge_graph_snippet?.neighbors?.length" class="sug-section">
      <div class="sug-label">🔗 知识关联</div>
      <div class="kg-snippet">
        <el-tag size="small" type="primary" effect="dark">{{ data.knowledge_graph_snippet.current }}</el-tag>
        <span class="kg-arrow">→</span>
        <el-tag
          v-for="(nb, i) in data.knowledge_graph_snippet.neighbors.slice(0, 4)"
          :key="i"
          size="small"
          effect="plain"
        >
          {{ nb.title }}
        </el-tag>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  data: { type: Object, default: () => ({}) },
})
defineEmits(['navigate'])
</script>

<style scoped>
.suggestion-card {
  font-size: 14px;
}

.sug-section {
  margin-bottom: 12px;
}

.sug-label {
  font-weight: 600;
  color: #475569;
  font-size: 13px;
  margin-bottom: 6px;
}

.sug-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.next-steps {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.next-step-item {
  padding: 10px 14px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}
.next-step-item:hover {
  background: #fbf0f1;
  border-color: #c7d2fe;
}

.step-topic {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: #1e293b;
}
.step-arrow {
  color: #c84c5a;
  font-weight: 700;
}
.step-name {
  color: #c84c5a;
}
.step-reason {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 4px;
  padding-left: 22px;
}

.kg-snippet {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.kg-arrow {
  color: #94a3b8;
}
</style>

