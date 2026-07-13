import { http } from '../utils/request'

export const adminApi = {
  getOverview() {
    return http.get('/admin/overview')
  },
  getResources(params = {}) {
    return http.get('/admin/resources', params)
  },
  getStudents(params = {}) {
    return http.get('/admin/students', params)
  },
  reviewResource(assetId, payload) {
    return http.post(`/admin/resources/${assetId}/review`, payload)
  },
  getAgentReviews() {
    return http.get('/admin/agent-reviews')
  },
  getAgentSessions() {
    return http.get('/admin/agent-sessions')
  },
  getAgentStats() {
    return http.get('/admin/agent-stats')
  },
}

export default adminApi
