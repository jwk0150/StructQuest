/**
 * 能力值全局状态管理（Pinia）
 *
 * 统一管理用户六维学习能力值的获取、缓存、刷新。
 * 任何页面完成学习行为后，调用 refreshAbility() 即可让所有引用能力数据的组件自动更新。
 *
 * 使用方式：
 *   import { useAbilityStore } from '../../store/ability'
 *   const abilityStore = useAbilityStore()
 *
 *   // 获取能力值（响应式）
 *   abilityStore.scores  => { visual, comprehensive, stability, exploration, theory, practice }
 *
 *   // 学习行为完成后刷新
 *   await abilityStore.refreshAbility()
 */
import { defineStore } from 'pinia'
import profileApi from '../api/profile'

export const useAbilityStore = defineStore('ability', {
  state: () => ({
    /** 六维能力值，格式：{ visual, comprehensive, stability, exploration, theory, practice } */
    scores: null,
    /** 上次成功获取的时间戳 */
    lastFetchAt: null,
    /** 加载中标记 */
    loading: false,
    /** 错误信息 */
    error: null,
  }),

  getters: {
    /** 是否已有能力数据 */
    hasData: (state) => state.scores !== null,
    /** 能力值数组（便于 ECharts 使用），按雷达图维度顺序排列 */
    radarValues: (state) => {
      if (!state.scores) return [0, 0, 0, 0, 0, 0]
      return [
        state.scores.visual || 0,
        state.scores.practice || 0,
        state.scores.theory || 0,
        state.scores.exploration || 0,
        state.scores.stability || 0,
        state.scores.comprehensive || 0,
      ]
    },
  },

  actions: {
    /**
     * 获取最新能力值（GET /api/user/ability）
     * 每次调用都会发送真实请求，确保数据为最新
     */
    async refreshAbility() {
      this.loading = true
      this.error = null
      try {
        const res = await profileApi.getAbility()
        if (res) {
          this.scores = {
            visual: Number(res.visual) || 0,
            comprehensive: Number(res.comprehensive) || 0,
            stability: Number(res.stability) || 0,
            exploration: Number(res.exploration) || 0,
            theory: Number(res.theory) || 0,
            practice: Number(res.practice) || 0,
          }
          this.lastFetchAt = Date.now()
        }
        return this.scores
      } catch (e) {
        this.error = e?.detail || e?.message || '获取能力值失败'
        console.warn('[AbilityStore] refreshAbility failed:', e)
        // 失败不清空已有数据，保留上次有效值
        return this.scores
      } finally {
        this.loading = false
      }
    },

    /**
     * 在页面初始化时获取能力值（不会覆盖已有数据，除非 scores 为空）
     */
    async initAbility() {
      if (this.scores !== null) {
        // 已有数据，跳过初始化（最多允许 30 秒内不重新请求）
        if (this.lastFetchAt && Date.now() - this.lastFetchAt < 30000) {
          return this.scores
        }
      }
      return await this.refreshAbility()
    },
  },
})
