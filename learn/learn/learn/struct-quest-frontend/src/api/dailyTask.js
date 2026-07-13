/** 每日任务 API */
import { http } from '../utils/request'

export const dailyTaskApi = {
  getTodayTasks() {
    return http.get('/daily-tasks/today')
  },
  refreshTasks() {
    return http.post('/daily-tasks/refresh')
  },
  updateTaskStatus(taskId, data) {
    return http.post(`/daily-tasks/${taskId}/status`, data)
  },
  getPracticeQuestions() {
    return http.get('/daily-tasks/practice-questions')
  },
  submitPractice(data) {
    return http.post('/daily-tasks/practice-submit', data)
  },
  getReviewQuestions() {
    return http.get('/daily-tasks/review-questions')
  },
  submitReview(data) {
    return http.post('/daily-tasks/review-submit', data)
  },
}

export default dailyTaskApi
