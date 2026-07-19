/**
 * AI学习效果评估中心 API
 */
import { http } from '../utils/request'

const BASE = '/evaluation'

export const evaluationApi = {
  /**
   * 获取评估 Dashboard 全部数据（六大模块）
   * @param {number} days - 统计天数，默认7天
   */
  getDashboard(days = 7) {
    return http.get(`${BASE}/dashboard`, { days })
  },

  /**
   * 记录一次资源/计划调整
   */
  logAdjustment(data) {
    return http.post(`${BASE}/log-adjustment`, data)
  },
}

export default evaluationApi
