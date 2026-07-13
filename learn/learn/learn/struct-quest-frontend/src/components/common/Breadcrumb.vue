<template>
  <el-breadcrumb class="app-breadcrumb" separator="/">
    <el-breadcrumb-item v-for="(item, index) in items" :key="index">
      <router-link v-if="item.path && index < items.length - 1" :to="item.path" class="breadcrumb-link">
        {{ item.label }}
      </router-link>
      <span v-else class="breadcrumb-text">{{ item.label }}</span>
    </el-breadcrumb-item>
  </el-breadcrumb>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps({
  items: {
    type: Array,
    default: () => []
  },
  auto: {
    type: Boolean,
    default: false
  }
})

const route = useRoute()

const autoItems = computed(() => {
  if (!props.auto) return props.items

  const matched = route.matched.filter(item => item.meta && item.meta.title)
  const items = matched.map(item => ({
    label: item.meta.title,
    path: item.path
  }))

  // Add home as first item if not already present
  if (items.length === 0 || items[0].path !== '/dashboard') {
    items.unshift({ label: '首页', path: '/dashboard' })
  }

  return items
})

const displayItems = computed(() => props.auto ? autoItems.value : props.items)
</script>

<style scoped>
.app-breadcrumb {
  font-size: 14px;
}

.breadcrumb-link {
  color: var(--text-secondary);
  text-decoration: none;
  transition: color var(--transition-fast);
}

.breadcrumb-link:hover {
  color: var(--color-primary);
}

.breadcrumb-text {
  color: var(--text-main);
}
</style>
