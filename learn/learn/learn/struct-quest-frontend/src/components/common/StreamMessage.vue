<template>
  <div class="stream-message">
    <div ref="contentRef" class="message-content" v-html="renderedContent" />
    <span v-if="isStreaming && showCursor" class="cursor" />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  content: {
    type: String,
    default: ''
  },
  isStreaming: {
    type: Boolean,
    default: false
  },
  showCursor: {
    type: Boolean,
    default: true
  }
})

const contentRef = ref(null)

const renderedContent = computed(() => {
  if (!props.content) return ''
  
  let html = props.content
  
  // Escape HTML
  html = html
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  
  // Code blocks with language
  html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
    return `<pre class="code-block"><code class="language-${lang || 'text'}">${code.trim()}</code></pre>`
  })
  
  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
  
  // Headers
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>')
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>')
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>')
  
  // Bold
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  
  // Italic
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>')
  
  // Links
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
  
  // Unordered lists
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>')
  html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
  
  // Ordered lists
  html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
  
  // Line breaks
  html = html.replace(/\n\n/g, '</p><p>')
  html = html.replace(/\n/g, '<br>')
  
  return `<p>${html}</p>`
})
</script>

<style scoped>
.stream-message {
  line-height: 1.6;
}

.message-content {
  color: var(--text-main);
  word-wrap: break-word;
}

.message-content :deep(h1),
.message-content :deep(h2),
.message-content :deep(h3) {
  margin: 16px 0 8px;
  font-weight: 600;
  color: var(--text-main);
}

.message-content :deep(h1) {
  font-size: 24px;
}

.message-content :deep(h2) {
  font-size: 20px;
}

.message-content :deep(h3) {
  font-size: 16px;
}

.message-content :deep(p) {
  margin: 8px 0;
}

.message-content :deep(code) {
  font-family: 'Söhne Mono', Monaco, Andale Mono, Ubuntu Mono, monospace;
}

.message-content :deep(.inline-code) {
  padding: 2px 6px;
  background-color: var(--bg-tertiary);
  border-radius: 4px;
  font-size: 0.9em;
}

.message-content :deep(.code-block) {
  margin: 12px 0;
  padding: 16px;
  background-color: var(--bg-secondary);
  border-radius: 8px;
  overflow-x: auto;
}

.message-content :deep(.code-block code) {
  font-size: 14px;
  line-height: 1.5;
}

.message-content :deep(ul),
.message-content :deep(ol) {
  margin: 8px 0;
  padding-left: 24px;
}

.message-content :deep(li) {
  margin: 4px 0;
}

.message-content :deep(a) {
  color: var(--color-primary);
  text-decoration: none;
}

.message-content :deep(a:hover) {
  text-decoration: underline;
}

.message-content :deep(strong) {
  font-weight: 600;
}

.cursor {
  display: inline-block;
  width: 2px;
  height: 1.2em;
  background-color: var(--color-primary);
  margin-left: 2px;
  animation: blink 1s infinite;
  vertical-align: text-bottom;
}

@keyframes blink {
  0%, 50% {
    opacity: 1;
  }
  51%, 100% {
    opacity: 0;
  }
}
</style>
