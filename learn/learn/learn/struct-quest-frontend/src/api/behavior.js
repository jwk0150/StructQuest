/** 行为上报 + 动态画像 + 推荐 Feed API */
import { http } from '../utils/request'

export const behaviorApi = {
  /** 记录学习行为（前端自动上报） */
  log(data) {
    return http.post('/behaviors/log', data)
  },

  /** 获取六维动态画像 */
  getDynamicProfile() {
    return http.get('/profile/dynamic')
  },

  /** 获取个性化推荐 Feed */
  getRecommendationFeed(limit = 8) {
    return http.get('/recommendations/feed', { limit })
  },

  /** 记录推荐点击 */
  clickRecommendation(id) {
    return http.post(`/recommendations/${id}/click`)
  },

  /** Orchestrator 统一入口 */
  orchestratedLearning(data) {
    return http.post('/learning/orchestrated', data)
  },
}

export default behaviorApi
