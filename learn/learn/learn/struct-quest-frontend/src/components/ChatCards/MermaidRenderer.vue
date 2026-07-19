<template>
  <div class="mermaid-renderer">
    <div v-if="error" class="mermaid-error">
      <span>⚠️ 图表渲染失败: {{ error }}</span>
      <pre class="mermaid-raw">{{ code }}</pre>
    </div>
    <div v-else ref="mermaidEl" class="mermaid-svg"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import mermaid from 'mermaid'

const props = defineProps({
  code: { type: String, default: '' },
})

const mermaidEl = ref(null)
const error = ref('')

// 初始化 mermaid
mermaid.initialize({
  startOnLoad: false,
  theme: 'default',
  securityLevel: 'loose',
  flowchart: { useMaxWidth: true, htmlLabels: true },
  themeCSS: `
    .node rect, .node circle, .node polygon { fill: #f8fafc; stroke: #c84c5a; stroke-width: 1.5px; }
    .edgePath .path { stroke: #94a3b8; stroke-width: 1.5px; }
    .label { color: #1e293b; font-family: 'SF Pro', sans-serif; font-size: 12px; }
    .cluster rect { fill: #f8fafc; stroke: #e2e8f0; stroke-width: 1px; }
  `,
})

onMounted(async () => {
  await nextTick()
  if (mermaidEl.value && props.code) {
    try {
      const id = 'mermaid-' + Math.random().toString(36).slice(2, 8)
      const { svg } = await mermaid.render(id, props.code)
      mermaidEl.value.innerHTML = svg
    } catch (e) {
      error.value = e.message || '渲染失败'
    }
  }
})
</script>

<style scoped>
.mermaid-renderer {
  display: flex;
  justify-content: center;
  min-height: 60px;
}

.mermaid-svg {
  max-width: 100%;
  overflow-x: auto;
}

.mermaid-error {
  color: #991b1b;
  font-size: 13px;
}

.mermaid-raw {
  background: #fef2f2;
  padding: 10px;
  border-radius: 6px;
  margin-top: 8px;
  font-size: 12px;
  white-space: pre-wrap;
  color: #991b1b;
}
</style>

