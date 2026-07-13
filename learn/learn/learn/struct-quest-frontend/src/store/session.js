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
      learningMode: getStorage(STORAGE_KEYS.LEARNING_MODE) || '', // 学习模式（空=未选择）
      learningModeInfo: null,
    }
  },
  actions: {
    /** 登录（保存 token 到 localStorage + 同步学习模式） */
    login(userData, token) {
      this.isAuthenticated = true
      this.user = userData
      this.token = token
      // ★ 优先使用后端返回的 has_completed_onboarding
      this.hasCompletedOnboarding = userData.has_completed_onboarding ?? false
      if (token) {
        setStorage(STORAGE_KEYS.TOKEN, token)
      }
      // ★ 同步后端学习模式（老用户已有模式，新用户为空）
      const serverMode = userData.learning_mode || ''
      if (serverMode) {
        this.learningMode = serverMode
        setStorage(STORAGE_KEYS.LEARNING_MODE, serverMode)
      } else {
        // ★ 后端返回空 = 新用户尚未选择模式
        // 必须清除 store 和 localStorage，防止残留旧用户的模式
        this.learningMode = ''
        removeStorage(STORAGE_KEYS.LEARNING_MODE)
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
      this.learningMode = ''
      this.learningModeInfo = null
      removeStorage(STORAGE_KEYS.TOKEN)
      removeStorage(STORAGE_KEYS.LEARNING_MODE)
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

    /** 设置学习模式（本地 + 后端持久化） */
    setLearningMode(mode, modeInfo) {
      this.learningMode = mode
      this.learningModeInfo = modeInfo || null
      setStorage(STORAGE_KEYS.LEARNING_MODE, mode)
    },

    /** 从后端同步学习模式 */
    async syncLearningMode() {
      try {
        const token = getStorage(STORAGE_KEYS.TOKEN)
        if (!token) return
        const base = import.meta.env.VITE_API_BASE || '/api'
        const r = await fetch(`${base}/profile/my-learning-mode`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (r.ok) {
          const data = await r.json()
          const mode = data.learning_mode || ''
          if (mode) {
            this.learningMode = mode
            this.learningModeInfo = data.learning_mode_info || null
            setStorage(STORAGE_KEYS.LEARNING_MODE, mode)
          }
        }
      } catch (e) {
        console.warn('[session] syncLearningMode failed', e)
      }
    },
  },
  getters: {
    isAdmin: (state) => state.user?.is_admin ?? false,
  },
})
