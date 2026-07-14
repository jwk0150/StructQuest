import { defineStore } from 'pinia'
import { setStorage, getStorage, removeStorage, STORAGE_KEYS } from '../utils/storage'
import authApi from '../api/auth'

export const useSessionStore = defineStore('session', {
  state: () => {
    // ★ 从 localStorage 恢复关键状态，避免老用户被重复引导
    const savedProfile = getStorage(STORAGE_KEYS.PROFILE)
    const hasSavedProfile = !!(savedProfile && (savedProfile.persona_type || savedProfile.ability_level))
    return {
      isAuthenticated: false,
      hasCompletedOnboarding: hasSavedProfile, // 有本地画像即视为已完成引导
      fatigueLevel: 0,
      currentTask: null,
      isAIThinking: false,
      user: null,
      token: null,
    }
  },
  actions: {
    /** 登录（保存 token + 同步用户信息） */
    login(userData, token) {
      this.isAuthenticated = true
      this.user = userData
      this.token = token
      // ★ 优先使用后端返回的 has_completed_onboarding
      this.hasCompletedOnboarding = userData.has_completed_onboarding ?? false
      // 新用户（未完成引导）清除可能残留的旧 localStorage 数据，防止路由守卫跳过
      if (!this.hasCompletedOnboarding) {
        removeStorage(STORAGE_KEYS.ONBOARDING_DONE)
        removeStorage(STORAGE_KEYS.PROFILE)
      }
      if (token) {
        setStorage(STORAGE_KEYS.TOKEN, token)
      }
      // ★ 如果后端没返回 profile_data，但后端标记了已完成引导，尝试从 localStorage 恢复
      // （防止后端 DB 丢失但本地有备份的情况）
      if (!userData.profile_data && userData.has_completed_onboarding) {
        try {
          const localProfile = getStorage(STORAGE_KEYS.PROFILE)
          if (localProfile && (localProfile.persona_type || localProfile.ability_level)) {
            userData.profile_data = localProfile
            this.user = { ...this.user, profile_data: localProfile }
          }
        } catch (e) { /* ignore */ }
      }
      // ★ 如果后端返回了 profile_data，同步到 localStorage 作为备份
      if (userData.profile_data && (userData.profile_data.persona_type || userData.profile_data.ability_level)) {
        setStorage(STORAGE_KEYS.PROFILE, userData.profile_data)
      }
    },

    /** 退出登录（清除所有本地状态和数据） */
    logout() {
      this.isAuthenticated = false
      this.user = null
      this.token = null
      this.hasCompletedOnboarding = false
      removeStorage(STORAGE_KEYS.TOKEN)
      removeStorage(STORAGE_KEYS.PROFILE)
      removeStorage(STORAGE_KEYS.ONBOARDING_DONE)
    },

    /** 标记完成新手引导 */
    completeOnboarding() {
      this.hasCompletedOnboarding = true
      if (this.user) {
        this.user.has_completed_onboarding = true
      }
      // ★ 持久化到 localStorage，防止页面刷新后丢失
      setStorage(STORAGE_KEYS.ONBOARDING_DONE, true)
    },

    /** 更新用户画像（完成引导 + 保存画像数据） */
    updateProfile(profileData) {
      this.hasCompletedOnboarding = true
      if (this.user) {
        this.user.has_completed_onboarding = true
        this.user.profile_data = profileData
      }
      // ★ 持久化到 localStorage，防止后端同步失败导致引导状态丢失
      setStorage(STORAGE_KEYS.ONBOARDING_DONE, true)
      if (profileData && (profileData.persona_type || profileData.ability_level)) {
        setStorage(STORAGE_KEYS.PROFILE, profileData)
      }
    },

    /** 从后端同步用户状态 */
    async syncFromServer() {
      const token = getStorage(STORAGE_KEYS.TOKEN)
      if (!token) return false
      try {
        const user = await authApi.me()
        this.login(user, token)
        return true
      } catch {
        this.logout()
        return false
      }
    },

    addFatigue(amount) {
      this.fatigueLevel = Math.min(100, this.fatigueLevel + amount)
    },
    resetFatigue() {
      this.fatigueLevel = 0
    },
    setAIThinking(status) {
      this.isAIThinking = status
    },
  },
  getters: {
    isAdmin: (state) => state.user?.is_admin ?? false,
  },
})
