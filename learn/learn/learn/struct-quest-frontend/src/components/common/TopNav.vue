<template>
  <nav class="topnav">
    <div class="topnav-inner">
      <!-- Logo -->
      <router-link to="/app" class="topnav-brand">
        <span class="brand-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
          </svg>
        </span>
        <span class="brand-name">StructQuest</span>
      </router-link>

      <!-- Nav Links -->
      <div class="topnav-links">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-link"
          :class="{ active: isActive(item) }"
        >
          <component :is="item.icon" class="nav-link-icon" />
          <span>{{ item.label }}</span>
        </router-link>
      </div>

      <!-- Right -->
      <div class="topnav-right">
        <!-- Notification -->
        <button class="topnav-icon-btn" title="通知">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/>
          </svg>
        </button>

        <!-- User -->
        <div class="topnav-user" @click="goToProfile">
          <div class="user-avatar">{{ userName.charAt(0) }}</div>
          <span class="user-level-badge">Lv.{{ userLevel }}</span>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSessionStore } from '@/store/session'

const route = useRoute()
const router = useRouter()
const sessionStore = useSessionStore()

const userName = computed(() => sessionStore.user?.username || '学生')
const userLevel = computed(() => sessionStore.user?.level || 5)

// SVG icons as render functions
const IconHome = { render() { return h('svg', { width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', innerHTML: '<path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>' }) } }
const IconMap = { render() { return h('svg', { width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', innerHTML: '<circle cx="12" cy="12" r="10"/><polygon points="12 2 2 12 12 22 22 12"/>' }) } }
const IconResources = { render() { return h('svg', { width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', innerHTML: '<path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/><path d="M12 11v6"/><path d="M9 14h6"/>' }) } }
const IconViz = { render() { return h('svg', { width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', innerHTML: '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>' }) } }
const IconChat = { render() { return h('svg', { width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', innerHTML: '<path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>' }) } }
const IconReport = { render() { return h('svg', { width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', innerHTML: '<path d="M18 20V10"/><path d="M12 20V4"/><path d="M6 20v-6"/>' }) } }

const navItems = [
  { path: '/app',           label: '首页',       icon: IconHome,    match: 'home' },
  { path: '/app/map',       label: '学习地图',   icon: IconMap,     match: 'map' },
  { path: '/app/resources', label: '学习资源',   icon: IconResources, match: 'resources' },
  { path: '/app/viz',       label: '算法可视化', icon: IconViz,     match: 'viz' },
  { path: '/app/chat',      label: 'AI 导师',    icon: IconChat,    match: 'chat' },
  { path: '/app/analysis',  label: '学习报告',   icon: IconReport,  match: 'analysis' },
]

function isActive(item) {
  const p = route.path
  if (item.match === 'home') return p === '/app' || p.startsWith('/app/dashboard')
  if (item.match === 'map') return p.startsWith('/app/map')
  if (item.match === 'chat') return p.startsWith('/app/chat')
  if (item.match === 'analysis') return p.startsWith('/app/analysis')
  if (item.match === 'resources') return p.startsWith('/app/resources')
  if (item.match === 'viz') return p.startsWith('/app/viz')
  return false
}

function goToProfile() {
  router.push('/app/profile')
}
</script>

<style scoped>
.topnav {
  position: sticky;
  top: 0;
  z-index: 200;
  height: var(--topnav-height);
  background: var(--topnav-bg);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border-bottom: 1px solid var(--topnav-border);
}

.topnav-inner {
  max-width: 1440px;
  margin: 0 auto;
  height: 100%;
  display: flex;
  align-items: center;
  padding: 0 28px;
  gap: 32px;
}

/* Brand */
.topnav-brand {
  display: flex;
  align-items: center;
  gap: 9px;
  text-decoration: none;
  flex-shrink: 0;
}
.brand-icon {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--hero-gradient);
  border-radius: 10px;
  color: #fff;
}
.brand-name {
  font-size: 17px;
  font-weight: 800;
  color: var(--text-main);
  letter-spacing: -0.3px;
}

/* Nav Links */
.topnav-links {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;
}
.nav-link {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 7px 14px;
  border-radius: 10px;
  text-decoration: none;
  font-size: 13.5px;
  font-weight: 600;
  color: var(--text-tertiary);
  transition: all var(--transition-fast);
  white-space: nowrap;
}
.nav-link:hover {
  color: var(--text-main);
  background: rgba(0, 0, 0, 0.03);
}
.nav-link.active {
  color: var(--color-primary);
  background: rgba(99, 102, 241, 0.08);
}
.nav-link-icon {
  flex-shrink: 0;
  opacity: 0.85;
}
.nav-link.active .nav-link-icon {
  opacity: 1;
}

/* Right */
.topnav-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
  margin-left: auto;
}

.topnav-icon-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  border-radius: 10px;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all var(--transition-fast);
}
.topnav-icon-btn:hover {
  background: rgba(0, 0, 0, 0.04);
  color: var(--text-main);
}

.topnav-user {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px 4px 4px;
  border-radius: 12px;
  transition: background var(--transition-fast);
}
.topnav-user:hover {
  background: rgba(0, 0, 0, 0.03);
}
.user-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: var(--hero-gradient);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}
.user-level-badge {
  font-size: 11px;
  font-weight: 700;
  color: var(--color-primary);
  background: rgba(99, 102, 241, 0.08);
  padding: 2px 8px;
  border-radius: 999px;
  white-space: nowrap;
}

/* Responsive */
@media (max-width: 900px) {
  .topnav-inner {
    padding: 0 16px;
    gap: 16px;
  }
  .brand-name { display: none; }
  .nav-link { padding: 7px 10px; font-size: 12.5px; }
  .nav-link-icon { width: 16px; height: 16px; }
  .user-level-badge { display: none; }
}
@media (max-width: 680px) {
  .topnav-links { overflow-x: auto; gap: 1px; }
  .nav-link span { display: none; }
}
</style>
