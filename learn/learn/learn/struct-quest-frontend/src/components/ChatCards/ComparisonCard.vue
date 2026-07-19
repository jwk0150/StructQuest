<template>
  <div class="comparison-card">
    <div v-if="data.items?.length" class="comp-items">
      <div v-for="(item, i) in data.items" :key="i" class="comp-item">
        <div class="comp-item-name">{{ item.name }}</div>
        <div class="comp-item-desc">{{ item.description }}</div>
      </div>
    </div>
    <div v-else class="comp-raw" v-html="renderMarkdown(data.raw_answer || '')"></div>
  </div>
</template>

<script setup>
defineProps({
  data: { type: Object, default: () => ({}) },
})

function renderMarkdown(text) {
  if (!text) return ''
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
}
</script>

<style scoped>
.comparison-card {
  font-size: 14px;
}

.comp-items {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.comp-item {
  padding: 10px 14px;
  border-left: 3px solid #c84c5a;
  background: #f8fafc;
  border-radius: 0 8px 8px 0;
}
.comp-item-name {
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 4px;
}
.comp-item-desc {
  color: #475569;
  font-size: 13px;
}

.comp-raw {
  color: #555;
}
</style>

