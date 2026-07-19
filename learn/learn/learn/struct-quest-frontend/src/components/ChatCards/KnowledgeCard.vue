<template>
  <div class="knowledge-card">
    <!-- 摘要 -->
    <div v-if="data.summary" class="summary">
      <span class="summary-label">一句话解释：</span>
      <span>{{ data.summary }}</span>
    </div>

    <!-- 分段内容 -->
    <div v-if="data.sections?.length" class="sections">
      <div v-for="(sec, i) in data.sections" :key="i" class="section-item">
        <h4 class="section-heading">{{ sec.heading }}</h4>
        <p class="section-content">{{ sec.content }}</p>
      </div>
    </div>

    <!-- 关键要点 -->
    <div v-if="data.key_points?.length" class="key-points">
      <div class="kp-title">📌 关键要点</div>
      <ul>
        <li v-for="(pt, i) in data.key_points" :key="i">{{ pt }}</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
defineProps({
  data: { type: Object, default: () => ({}) },
})
</script>

<style scoped>
.knowledge-card {
  font-size: 14px;
  line-height: 1.8;
  color: #333;
}

.summary {
  background: #f0f9ff;
  border-left: 3px solid #b94b5a;
  padding: 10px 14px;
  border-radius: 6px;
  margin-bottom: 14px;
}
.summary-label {
  font-weight: 600;
  color: #b94b5a;
}

.sections {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 14px;
}

.section-item {
  padding: 8px 0;
}
.section-heading {
  font-size: 15px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0 0 4px 0;
}
.section-content {
  margin: 0;
  color: #555;
  line-height: 1.7;
}

.key-points {
  background: #fafafa;
  border-radius: 8px;
  padding: 12px 16px;
}
.kp-title {
  font-weight: 600;
  font-size: 13px;
  color: #666;
  margin-bottom: 6px;
}
.key-points ul {
  margin: 0;
  padding-left: 18px;
}
.key-points li {
  margin-bottom: 4px;
  color: #444;
}
</style>

