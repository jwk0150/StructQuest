import { http } from '../utils/request'

export const adminApi = {
  // ── 总览 ──
  getOverview() { return http.get('/admin/overview') },
  getResources(params = {}) { return http.get('/admin/resources', params) },
  reviewResource(assetId, payload) { return http.post(`/admin/resources/${assetId}/review`, payload) },
  getAgentReviews() { return http.get('/admin/agent-reviews') },
  getAgentSessions() { return http.get('/admin/agent-sessions') },
  getAgentStats() { return http.get('/admin/agent-stats') },

  // ── 学生管理 ──
  getStudents(params = {}) { return http.get('/admin/students', params) },
  getStudentDetail(userId) { return http.get(`/admin/students/${userId}/detail`) },
  getStudentRadar(userId) { return http.get(`/admin/students/${userId}/profile-radar`) },
  getStudentHeatmap(userId) { return http.get(`/admin/students/${userId}/mastery-heatmap`) },
  getStudentTimeline(userId, limit = 50) { return http.get(`/admin/students/${userId}/event-timeline`, { limit }) },

  // ── 级联删除 ──
  cascadeDeleteUser(userId) { return http.delete(`/admin/students/${userId}/cascade`) },

  // ── 手动注入数据（自动触发画像重算）──
  getKnowledgeNodes() { return http.get('/admin/knowledge-nodes') },
  addExam(userId, data) { return http.post(`/admin/students/${userId}/exams`, data) },
  recalculateProfile(userId) { return http.post(`/admin/students/${userId}/recalculate-profile`) },

  // ── 数据库浏览 ──
  getDbTables() { return http.get('/admin/db/tables') },
  getDbStats() { return http.get('/admin/db/stats') },
  getDbBrowse(tableName, limit = 50, offset = 0) {
    return http.get('/admin/db/browse', { table_name: tableName, limit, offset })
  },
  getTableColumns(tableName) { return http.get(`/admin/db/${tableName}/columns`) },

  // ── 数据库 CRUD ──
  deleteDbRow(table, rowId) { return http.delete(`/admin/db/${table}/${rowId}`) },
  updateDbRow(table, rowId, data) { return http.put(`/admin/db/${table}/${rowId}`, { data }) },
  insertDbRow(table, data) { return http.post(`/admin/db/${table}`, { data }) },
}

export default adminApi
