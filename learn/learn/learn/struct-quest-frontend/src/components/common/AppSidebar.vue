<template>
  <aside :class="['app-sidebar', { collapsed }]">
    <div class="sidebar-header">
      <div v-if="!collapsed" class="sidebar-title">Learn</div>
      <button class="collapse-btn" @click="$emit('update:collapsed', !collapsed)">
        <el-icon>
          <ArrowLeft v-if="!collapsed" />
          <ArrowRight v-else />
        </el-icon>
      </button>
    </div>

    <el-menu
      :default-active="activeMenu"
      :collapse="collapsed"
      :collapse-transition="false"
      class="sidebar-menu"
    >
      <template v-for="item in menuItems" :key="item.id">
        <el-sub-menu v-if="item.children && item.children.length" :index="item.id">
          <template #title>
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.label }}</span>
          </template>
          <el-menu-item
            v-for="child in item.children"
            :key="child.id"
            :index="child.id"
            @click="handleMenuClick(child)"
          >
            <el-icon v-if="child.icon"><component :is="child.icon" /></el-icon>
            <span>{{ child.label }}</span>
            <el-badge v-if="child.badge" :value="child.badge" class="menu-badge" />
          </el-menu-item>
        </el-sub-menu>

        <el-menu-item v-else :index="item.id" @click="handleMenuClick(item)">
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>
            <span>{{ item.label }}</span>
            <el-badge v-if="item.badge" :value="item.badge" class="menu-badge" />
          </template>
        </el-menu-item>
      </template>
    </el-menu>

    <div class="sidebar-footer">
      <div v-if="!collapsed" class="user-info">
        <el-avatar :size="32">
          <el-icon><User /></el-icon>
        </el-avatar>
        <div class="user-details">
          <span class="user-name">{{ userName }}</span>
          <span class="user-role">{{ userRole }}</span>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  ArrowLeft,
  ArrowRight,
  HomeFilled,
  Document,
  Reading,
  Calendar,
  ChatDotRound,
  TrendCharts,
  User,
  Grid,
  FolderOpened,
  SwitchButton
} from '@element-plus/icons-vue'

const props = defineProps({
  collapsed: {
    type: Boolean,
    default: false
  },
  menuItems: {
    type: Array,
    default: () => []
  }
})

defineEmits(['update:collapsed'])

const route = useRoute()

const activeMenu = computed(() => {
  return route.path
})

const userName = computed(() => '学生用户')
const userRole = computed(() => '学习者')

const defaultMenuItems = [
  { id: '/app', icon: HomeFilled, label: '概览首页', path: '/app' },
  { id: '/map', icon: Grid, label: '知识图谱', path: '/map' },
  { id: '/quest', icon: Calendar, label: '探索任务', path: '/quest' },
  { id: '/chat', icon: ChatDotRound, label: 'AI 聊天', path: '/chat' },
  { id: '/knowledge', icon: FolderOpened, label: '专属知识库', path: '/knowledge' },
  { id: '/analysis', icon: TrendCharts, label: '学习分析', path: '/analysis' },
  { id: '/profile', icon: User, label: '个人中心', path: '/profile' },
  { id: '/admin', icon: SwitchButton, label: '管理员平台', path: '/admin' }
]

const items = computed(() => props.menuItems.length ? props.menuItems : defaultMenuItems)

const handleMenuClick = (item) => {
  if (item.path) {
    window.location.href = item.path
  }
}
</script>

<style scoped>
.app-sidebar {
  display: flex;
  flex-direction: column;
  width: 260px;
  height: 100vh;
  background-color: var(--sidebar-bg);
  color: var(--text-sidebar);
  transition: width var(--transition-normal);
  position: fixed;
  left: 0;
  top: 0;
  z-index: 200;
}

.app-sidebar.collapsed {
  width: 64px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
  padding: 0 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-sidebar);
}

.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  color: var(--text-sidebar);
  transition: background-color var(--transition-fast);
}

.collapse-btn:hover {
  background-color: var(--sidebar-hover);
}

.sidebar-menu {
  flex: 1;
  border: none;
  background-color: transparent;
  overflow-y: auto;
  overflow-x: hidden;
}

.sidebar-menu:not(.el-menu--collapse) {
  width: 260px;
}

.sidebar-menu.el-menu--collapse {
  width: 64px;
}

:deep(.el-menu-item),
:deep(.el-sub-menu__title) {
  color: var(--text-sidebar);
  background-color: transparent;
  height: 48px;
  line-height: 48px;
}

:deep(.el-menu-item:hover),
:deep(.el-sub-menu__title:hover) {
  background-color: var(--sidebar-hover);
}

:deep(.el-menu-item.is-active) {
  color: var(--color-primary);
  background-color: rgba(16, 163, 127, 0.1);
}

:deep(.el-sub-menu .el-menu-item) {
  padding-left: 48px !important;
}

.menu-badge {
  margin-left: 8px;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-details {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-sidebar);
}

.user-role {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}
</style>
