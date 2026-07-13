import { createRouter, createWebHistory } from 'vue-router'
import { useSessionStore } from '../store/session'
import { getStorage, STORAGE_KEYS } from '../utils/storage'

const routes = [
  // ═══════ Backward-compatible redirects ═══════
  { path: '/dashboard', redirect: '/app' },
  { path: '/map', redirect: '/app/map' },
  { path: '/learn/:nodeId', redirect: (to) => `/app/learn/${to.params.nodeId}` },
  { path: '/exam/:nodeId', redirect: (to) => `/app/exam/${to.params.nodeId}` },
  { path: '/quest', redirect: '/app/quest' },
  { path: '/review', redirect: '/app/review' },
  { path: '/analysis', redirect: '/app/analysis' },
  { path: '/profile', redirect: '/app/profile' },
  { path: '/admin', redirect: '/app/admin' },
  { path: '/chat', redirect: '/app/chat' },
  { path: '/daily-practice', redirect: '/app' },
  { path: '/hot/:topicId', redirect: (to) => `/app/hot/${to.params.topicId}` },
  // ═══════ Public Landing Page (no auth required, no sidebar) ═══════
  {
    path: '/',
    name: 'Landing',
    component: () => import('../views/Landing/index.vue'),
    meta: { requiresAuth: false, layout: 'blank' }
  },
  // ═══════ Standalone Login (fallback) ═══════
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login/index.vue'),
    meta: { requiresAuth: false }
  },
  // ═══════ Onboarding ═══════
  {
    path: '/onboarding',
    name: 'Onboarding',
    component: () => import('../views/Onboarding/index.vue'),
    meta: { requiresAuth: true }
  },
  // ═══════ Mode Choice ═══════
  {
    path: '/mode-choice',
    name: 'ModeChoice',
    component: () => import('../views/ModeChoice/index.vue'),
    meta: { requiresAuth: true }
  },
  // ═══════ App Shell (authenticated, with sidebar) ═══════
  {
    path: '/app',
    component: () => import('../layout/index.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        alias: '/app/dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard/index.vue')
      },
      {
        path: 'map',
        name: 'Map',
        component: () => import('../views/Map/index.vue')
      },
      {
        path: 'quest',
        name: 'Quest',
        component: () => import('../views/Quest/index.vue')
      },
      {
        path: 'chat',
        name: 'Chat',
        component: () => import('../views/Chat/index.vue')
      },
      {
        path: 'analysis',
        name: 'Analysis',
        component: () => import('../views/Analysis/index.vue')
      },
      {
        path: 'learn/:nodeId',
        name: 'NodeLearning',
        component: () => import('../views/NodeLearning/index.vue')
      },
      {
        path: 'review',
        name: 'Review',
        component: () => import('../views/Review/index.vue')
      },
      {
        path: 'resources',
        name: 'Resources',
        component: () => import('../views/Resources/index.vue')
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('../views/Profile/index.vue')
      },
      {
        path: 'admin',
        name: 'Admin',
        component: () => import('../views/Admin/index.vue'),
        meta: { requiresAuth: true, requiresAdmin: true }
      },
      {
        path: 'exam/:nodeId',
        name: 'ChapterExam',
        component: () => import('../views/ChapterExam/index.vue')
      },
      {
        path: 'daily-practice',
        redirect: '/app',
      },
      {
        path: 'hot/:topicId',
        name: 'HotTopicDetail',
        component: () => import('../views/Dashboard/HotTopicDetail.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to) {
    // Landing page: scroll to section anchor
    if (to.hash) {
      return { el: to.hash, behavior: 'smooth' }
    }
    return { top: 0 }
  }
})

/** 从 localStorage 判断用户是否已完成引导（兜底逻辑） */
function hasLocalOnboardingDone() {
  if (getStorage(STORAGE_KEYS.ONBOARDING_DONE, false)) return true
  const profile = getStorage(STORAGE_KEYS.PROFILE)
  return !!(profile && (profile.persona_type || profile.ability_level))
}

// 路由守卫
router.beforeEach(async (to) => {
  const sessionStore = useSessionStore()

  // ★ 如果路由不需要认证，直接放行（Landing page 等公开页面）
  if (to.meta.requiresAuth === false) {
    return
  }

  // ★ 如果有 token 但还没恢复用户信息，先同步
  if (!sessionStore.isAuthenticated) {
    console.log('[Router Guard] 未认证，尝试同步登录状态...')
    let synced = false
    try {
      const syncPromise = sessionStore.syncFromServer()
      const timeoutPromise = new Promise((_, reject) =>
        setTimeout(() => reject(new Error('syncFromServer 超时 (8s)')), 8000)
      )
      synced = await Promise.race([syncPromise, timeoutPromise])
      console.log('[Router Guard] syncFromServer 结果:', synced)
    } catch (e) {
      console.warn('[Router Guard] syncFromServer 失败/超时:', e?.message || e)
    }
    if (!synced && hasLocalOnboardingDone()) {
      sessionStore.hasCompletedOnboarding = true
      const localMode = getStorage(STORAGE_KEYS.LEARNING_MODE)
      if (localMode) {
        sessionStore.learningMode = localMode
      }
    }
  }

  // ★ 需要认证但未登录 → 跳转 Landing page
  if (to.meta.requiresAuth && !sessionStore.isAuthenticated) {
    console.log('[Router Guard] 需登录 → 跳转 /')
    return '/'
  }

  // ★ 管理员路由保护
  if (to.meta.requiresAdmin && !sessionStore.isAdmin) {
    console.log('[Router Guard] 非管理员 → 跳转 /app')
    return '/app'
  }

  // ★ 已登录用户访问登录页 → 跳转 App
  if (to.name === 'Login' && sessionStore.isAuthenticated) {
    console.log('[Router Guard] 已登录用户访问登录页 → 跳转 /app')
    return '/app'
  }

  // ★ 已登录但未完成引导 → 跳转引导页
  if (
    sessionStore.isAuthenticated &&
    !sessionStore.hasCompletedOnboarding &&
    !hasLocalOnboardingDone() &&
    to.name !== 'Onboarding' &&
    to.meta.requiresAuth
  ) {
    console.log('[Router Guard] 未完成引导 → 跳转 /onboarding')
    return '/onboarding'
  }

  // ★ 已完成引导但未选择模式 → 跳转模式选择页
  if (
    sessionStore.isAuthenticated &&
    (sessionStore.hasCompletedOnboarding || hasLocalOnboardingDone()) &&
    !sessionStore.learningMode &&
    to.name !== 'ModeChoice' &&
    to.meta.requiresAuth
  ) {
    console.log('[Router Guard] 未选择模式 → 跳转 /mode-choice')
    return '/mode-choice'
  }

  // ★ 已选模式访问模式选择页 → 跳转 App
  if (
    sessionStore.isAuthenticated &&
    sessionStore.learningMode &&
    to.name === 'ModeChoice'
  ) {
    console.log('[Router Guard] 已选模式 → 跳转 /app')
    return '/app'
  }

  console.log('[Router Guard] ✅ 放行:', to.path)
})

export default router
