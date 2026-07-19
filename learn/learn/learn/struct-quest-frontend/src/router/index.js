import { createRouter, createWebHistory } from 'vue-router'
import { useSessionStore } from '../store/session'
import { getStorage, STORAGE_KEYS } from '../utils/storage'

const routes = [
  // ═══════ Admin Shell (independent layout) ═══════
  {
    path: '/admin',
    component: () => import('../layout/AdminLayout.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      { path: '', redirect: '/admin/users' },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('../views/Admin/Users.vue'),
      },
      {
        path: 'users/:userId',
        name: 'AdminUserDetail',
        component: () => import('../views/Admin/StudentDetail.vue'),
        props: true,
      },
      {
        path: 'database',
        name: 'AdminDatabase',
        component: () => import('../views/Admin/DbBrowser.vue'),
      },
      {
        path: 'knowledge',
        name: 'AdminKnowledge',
        component: () => import('../views/Admin/KnowledgeHub.vue'),
      },
    ]
  },
  // ═══════ Public Landing Page (no auth required, no sidebar) ═══════
  {
    path: '/',
    redirect: '/login',
    meta: { requiresAuth: false, layout: 'blank' }
  },
  // ═══════ Official long-form login ═══════
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginPreviewLong/index.vue'),
    meta: { requiresAuth: false }
  },
  // Original account form retained for registration and password recovery.
  {
    path: '/login-account',
    name: 'LoginAccount',
    redirect: '/login',
    meta: { requiresAuth: false, layout: 'blank' }
  },
  // ═══════ Onboarding ═══════
  // Legacy URLs now resolve to the current page structure without loading old views.
  { path: '/login-preview', redirect: '/login', meta: { requiresAuth: false } },
  { path: '/dashboard', redirect: '/app' },
  { path: '/map', redirect: '/app/map' },
  { path: '/quest', redirect: '/app/quest' },
  { path: '/chat', redirect: '/app/chat' },
  { path: '/analysis', redirect: '/app/analysis' },
  { path: '/review', redirect: '/app/review' },
  { path: '/profile', redirect: '/app/profile' },
  { path: '/daily-practice', redirect: '/app/practice/daily' },
  { path: '/learn/:nodeId', redirect: to => ({ path: '/app/learn/' + to.params.nodeId, query: to.query }) },
  { path: '/exam/:nodeId', redirect: to => ({ path: '/app/exam/' + to.params.nodeId, query: to.query }) },
  { path: '/hot/:topicId', redirect: to => ({ path: '/app/hot/' + to.params.topicId, query: to.query }) },
  {
    path: '/onboarding',
    name: 'Onboarding',
    component: () => import('../views/Onboarding/index.vue'),
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
        path: 'viz',
        name: 'Viz',
        component: () => import('../views/Viz/index.vue')
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('../views/Profile/index.vue')
      },
      // Admin moved to /admin independent layout
      {
        path: 'exam/:nodeId',
        name: 'ChapterExam',
        component: () => import('../views/ChapterExam/index.vue')
      },
      {
        path: 'daily-practice',
        redirect: '/app/practice/daily',
      },
      {
        path: 'hot/:topicId',
        name: 'HotTopicDetail',
        component: () => import('../views/Dashboard/HotTopicDetail.vue')
      },
      // ═══════ AI 智能练习中心 ═══════
      {
        path: 'practice',
        name: 'Practice',
        component: () => import('../views/Practice/index.vue')
      },
      {
        path: 'practice/exam',
        name: 'PracticeExam',
        component: () => import('../views/Practice/ExamMode.vue')
      },
      {
        path: 'practice/coding',
        name: 'PracticeCoding',
        component: () => import('../views/Practice/CodingMode.vue')
      },
      {
        path: 'practice/random',
        name: 'PracticeRandom',
        component: () => import('../views/Practice/AIRandom.vue')
      },
      {
        path: 'practice/wrong',
        name: 'PracticeWrong',
        component: () => import('../views/Practice/WrongQuestion.vue')
      },
      {
        path: 'practice/daily',
        name: 'PracticeDaily',
        component: () => import('../views/Practice/DailyChallenge.vue')
      },
      {
        path: 'practice/mock',
        name: 'PracticeMock',
        component: () => import('../views/Practice/MockExam.vue')
      }
    ]
  },
  { path: '/:pathMatch(.*)*', redirect: '/login', meta: { requiresAuth: false } }
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
    const isAuthEntry = to.name === 'Login' || to.name === 'LoginAccount' || to.path === '/'
    const hasStoredToken = !!getStorage(STORAGE_KEYS.TOKEN)

    if (isAuthEntry && !sessionStore.isAuthenticated && hasStoredToken) {
      try {
        await Promise.race([
          sessionStore.syncFromServer(),
          new Promise(resolve => setTimeout(() => resolve(false), 3000))
        ])
      } catch (error) {
        console.warn('[Router Guard] Public entry session restore failed:', error)
      }
    }

    if (isAuthEntry && sessionStore.isAuthenticated) {
      return sessionStore.isAdmin ? '/admin/users' : '/app'
    }
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
    }
  }

  // ★ 需要认证但未登录 → 跳转 Landing page
  if (to.meta.requiresAuth && !sessionStore.isAuthenticated) {
    console.log('[Router Guard] 需登录 → 跳转 /')
    return '/login'
  }

  // ★ 管理员路由保护
  if (to.meta.requiresAdmin && !sessionStore.isAdmin) {
    console.log('[Router Guard] 非管理员 → 跳转 /app')
    return '/app'
  }

  // ★ 已登录用户访问登录页 or Landing → 管理员进 /admin，普通用户进 /app
  if ((to.name === 'Login' || to.name === 'LoginAccount' || to.path === '/') && sessionStore.isAuthenticated) {
    if (sessionStore.isAdmin) {
      console.log('[Router Guard] 管理员 → 跳转管理端')
      return '/admin/users'
    }
    console.log('[Router Guard] 已登录用户 → 跳转 /app')
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

  console.log('[Router Guard] ✅ 放行:', to.path)
})

export default router
