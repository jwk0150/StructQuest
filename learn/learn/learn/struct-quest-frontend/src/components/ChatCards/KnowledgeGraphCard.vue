<template>
  <div class="kg-card">
    <!-- 当前节点高亮 -->
    <div class="kg-current">
      <el-tag type="primary" effect="dark" size="default">{{ data.current || '当前' }}</el-tag>
    </div>

    <!-- 父节点 -->
    <div v-if="data.parent" class="kg-line">
      <span class="kg-rel">📁 父级</span>
      <el-tag size="small" effect="plain">{{ data.parent }}</el-tag>
    </div>

    <!-- 邻居节点 -->
    <div v-if="data.neighbors?.length" class="kg-line">
      <span class="kg-rel">🔗 关联</span>
      <div class="kg-nodes">
        <el-tag
          v-for="(n, i) in data.neighbors"
          :key="i"
          size="small"
          :effect="n.relation === '前置' ? 'plain' : 'plain'"
          :type="n.relation === '前置' ? 'warning' : 'info'"
          class="kg-node-tag"
          @click="$emit('click-node', n)"
        >
          {{ n.title }}
          <span class="kg-node-rel">({{ n.relation }})</span>
        </el-tag>
      </div>
    </div>

    <!-- 子节点 -->
    <div v-if="data.children?.length" class="kg-line">
      <span class="kg-rel">📌 子级</span>
      <div class="kg-nodes">
        <el-tag
          v-for="(ch, i) in data.children"
          :key="i"
          size="small"
          effect="plain"
          type="success"
          class="kg-node-tag"
          @click="$emit('click-node', ch)"
        >
          {{ ch.title }}
        </el-tag>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  data: { type: Object, default: () => ({}) },
})
defineEmits(['click-node'])
</script>

<style scoped>
.kg-card {
  font-size: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.kg-current {
  text-align: center;
  padding: 6px;
}

.kg-line {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.kg-rel {
  flex-shrink: 0;
  font-size: 12px;
  color: #94a3b8;
  font-weight: 600;
  min-width: 50px;
  padding-top: 2px;
}

.kg-nodes {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.kg-node-tag {
  cursor: pointer;
  transition: all 0.15s;
}
.kg-node-tag:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(0,0,0,0.1);
}

.kg-node-rel {
  font-size: 11px;
  opacity: 0.7;
}
</style>
