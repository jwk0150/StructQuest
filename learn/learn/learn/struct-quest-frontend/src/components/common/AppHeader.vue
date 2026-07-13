<template>
  <header class="app-header">
    <div class="header-left">
      <button v-if="showSidebarToggle" class="sidebar-toggle" @click="$emit('toggle-sidebar')">
        <el-icon><Menu /></el-icon>
      </button>
      <div class="logo">
        <span class="logo-text">Learn</span>
      </div>
    </div>

    <div class="header-center">
      <div class="search-wrapper">
        <el-input
          v-model="searchQuery"
          placeholder="搜索课程、知识点..."
          prefix-icon="Search"
          clearable
        />
      </div>
    </div>

    <div class="header-right">
      <button class="theme-toggle" @click="toggleTheme" :title="isDark ? '切换到浅色模式' : '切换到深色模式'">
        <el-icon v-if="isDark"><Sunny /></el-icon>
        <el-icon v-else><Moon /></el-icon>
      </button>

      <el-badge :value="notificationCount" :hidden="!notificationCount" class="notification-badge">
        <button class="icon-button">
          <el-icon><Bell /></el-icon>
        </button>
      </el-badge>

      <el-dropdown trigger="click" @command="handleUserMenuCommand">
        <div class="user-menu">
          <el-avatar :size="32" :src="userAvatar">
            <el-icon><User /></el-icon>
          </el-avatar>
          <span class="user-name">{{ userName }}</span>
          <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">
              <el-icon><User /></el-icon>
              个人中心
            </el-dropdown-item>
            <el-dropdown-item command="settings">
              <el-icon><Setting /></el-icon>
              设置
            </el-dropdown-item>
            <el-dropdown-item divided command="logout">
              <el-icon><SwitchButton /></el-icon>
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </header>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme } from '../../composables/useTheme'
import {
  Menu,
  Sunny,
  Moon,
  Bell,
  User,
  ArrowDown,
  Setting,
  SwitchButton
} from '@element-plus/icons-vue'

defineProps({
  showSidebarToggle: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['toggle-sidebar'])

const router = useRouter()
const { isDark, toggleTheme } = useTheme()

const searchQuery = ref('')
const notificationCount = ref(0)
const userName = computed(() => '用户')
const userAvatar = computed(() => '')

const handleUserMenuCommand = (command) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'settings':
      router.push('/settings')
      break
    case 'logout':
      // Handle logout
      router.push('/')
      break
  }
}
</script>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
  padding: 0 20px;
  background-color: var(--bg-color);
  border-bottom: 1px solid var(--border-color);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.sidebar-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  color: var(--text-main);
  transition: background-color var(--transition-fast);
}

.sidebar-toggle:hover {
  background-color: var(--bg-secondary);
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-main);
}

.header-center {
  flex: 1;
  max-width: 600px;
  margin: 0 20px;
}

.search-wrapper {
  width: 100%;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.theme-toggle,
.icon-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  color: var(--text-main);
  transition: background-color var(--transition-fast);
}

.theme-toggle:hover,
.icon-button:hover {
  background-color: var(--bg-secondary);
}

.notification-badge {
  cursor: pointer;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color var(--transition-fast);
}

.user-menu:hover {
  background-color: var(--bg-secondary);
}

.user-name {
  font-size: 14px;
  color: var(--text-main);
}

.dropdown-icon {
  font-size: 12px;
  color: var(--text-secondary);
  transition: transform var(--transition-fast);
}

.user-menu:hover .dropdown-icon {
  transform: rotate(180deg);
}
</style>
