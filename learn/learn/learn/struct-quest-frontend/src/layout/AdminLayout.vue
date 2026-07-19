<template>
  <div class="admin-layout">
    <!-- 顶部栏 -->
    <header class="admin-topbar">
      <div class="topbar-left">
        <h1 class="topbar-logo">StructQuest 管理后台</h1>
      </div>
      <div class="topbar-right">
        <span class="topbar-user">{{ sessionStore.user?.username || '管理员' }}</span>
        <el-button text size="small" @click="goStudent">学生端</el-button>
        <el-button text type="danger" size="small" @click="logout">退出</el-button>
      </div>
    </header>

    <div class="admin-body">
      <!-- 侧边栏 -->
      <aside class="admin-sidebar">
        <el-menu
          :default-active="activeMenu"
          router
          class="admin-menu"
          background-color="#1e293b"
          text-color="#94a3b8"
          active-text-color="#38bdf8"
        >
          <el-menu-item index="/admin/users">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/knowledge">
            <el-icon><Document /></el-icon>
            <span>知识库管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/database">
            <el-icon><Coin /></el-icon>
            <span>数据库管理</span>
          </el-menu-item>
        </el-menu>
      </aside>

      <!-- 主内容区 -->
      <main class="admin-main">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSessionStore } from '../store/session'
import { User, Coin, Document } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const sessionStore = useSessionStore()

const activeMenu = computed(() => route.path)

function goStudent() {
  router.push('/app')
}

async function logout() {
  await sessionStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.admin-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f1f5f9;
}
.admin-topbar {
  height: 56px;
  background: #0f172a;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
  z-index: 10;
}
.topbar-logo {
  color: #e2e8f0;
  font-size: 18px;
  margin: 0;
  font-weight: 700;
}
.topbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.topbar-user {
  color: #94a3b8;
  font-size: 13px;
}
.admin-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}
.admin-sidebar {
  width: 220px;
  background: #1e293b;
  flex-shrink: 0;
  overflow-y: auto;
}
.admin-menu {
  border-right: none;
  padding-top: 8px;
}
.admin-menu .el-menu-item {
  margin: 2px 8px;
  border-radius: 8px;
  font-size: 14px;
}
.admin-menu .el-menu-item.is-active {
  background: #334155 !important;
}
.admin-main {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
}
</style>
