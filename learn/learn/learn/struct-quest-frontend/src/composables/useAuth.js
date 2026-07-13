import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '../store/session'
import { http } from '../utils/request'
import { setStorage, getStorage, removeStorage, STORAGE_KEYS } from '../utils/storage'

export function useAuth() {
  const router = useRouter()
  const sessionStore = useSessionStore()

  const loading = ref(false)
  const error = ref(null)

  const isAuthenticated = computed(() => sessionStore.isAuthenticated)
  const user = computed(() => sessionStore.user)
  const hasCompletedOnboarding = computed(() => sessionStore.hasCompletedOnboarding)

  /**
   * Login with credentials
   */
  const login = async (credentials) => {
    loading.value = true
    error.value = null

    try {
      // For development, simulate login
      // In production, replace with actual API call
      const response = await http.post('/auth/login', credentials)
      
      const { token, user: userData } = response
      
      // Store token
      setStorage(STORAGE_KEYS.TOKEN, token)
      
      // Update session store
      sessionStore.login(userData)
      
      // Navigate based on onboarding status
      if (userData.hasCompletedOnboarding) {
        router.push('/dashboard')
      } else {
        router.push('/onboarding')
      }
      
      return { success: true }
    } catch (err) {
      error.value = err.message || '登录失败，请重试'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  /**
   * Guest login
   */
  const guestLogin = async () => {
    loading.value = true
    error.value = null

    try {
      const response = await http.post('/auth/guest')
      const { token, user: userData } = response
      
      setStorage(STORAGE_KEYS.TOKEN, token)
      sessionStore.login({ ...userData, hasCompletedOnboarding: false })
      
      router.push('/onboarding')
      return { success: true }
    } catch (err) {
      error.value = err.message || '游客登录失败'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  /**
   * Logout
   */
  const logout = async () => {
    try {
      await http.post('/auth/logout')
    } catch (err) {
      // Continue with logout even if API fails
      console.error('Logout API error:', err)
    }
    
    removeStorage(STORAGE_KEYS.TOKEN)
    sessionStore.logout()
    router.push('/')
  }

  /**
   * Check if user is logged in (on app init)
   */
  const checkAuth = async () => {
    const token = getStorage(STORAGE_KEYS.TOKEN)
    if (!token) {
      return false
    }

    try {
      const response = await http.get('/auth/me')
      sessionStore.login(response)
      return true
    } catch (err) {
      removeStorage(STORAGE_KEYS.TOKEN)
      return false
    }
  }

  /**
   * Remember me functionality
   */
  const setRememberMe = (value) => {
    setStorage(STORAGE_KEYS.REMEMBER_ME, value)
  }

  const getRememberMe = () => {
    return getStorage(STORAGE_KEYS.REMEMBER_ME, false)
  }

  return {
    loading,
    error,
    isAuthenticated,
    user,
    hasCompletedOnboarding,
    login,
    guestLogin,
    logout,
    checkAuth,
    setRememberMe,
    getRememberMe
  }
}
