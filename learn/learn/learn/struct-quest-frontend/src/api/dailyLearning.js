/**
 * 每日学习任务 API（三阶段：知识点→练习题→温故知新）
 */
import { http } from '../utils/request'

const dailyLearningApi = {
  /** 获取今日任务状态 */
  getTodayTask() {
    return http.get('/daily-learning/today')
  },

  /** 获取完整进度（含题目预览、错题数） */
  getFullStatus() {
    return http.get('/daily-learning/full-status')
  },

  /** 获取练习题列表 */
  getQuestions() {
    return http.get('/daily-learning/questions')
  },

  /** 提交练习题答案 */
  submitAnswer(data) {
    return http.post('/daily-learning/answer', data)
  },

  /** 获取错题复习列表 */
  getReviewQuestions() {
    return http.get('/daily-learning/review')
  },

  /** 提交错题复习答案 */
  submitReviewAnswer(data) {
    return http.post('/daily-learning/answer-review', data)
  },

  /** AI 主动更新任务状态 */
  updateTaskStatus(data) {
    return http.post('/daily-learning/update-task', data)
  },

  /** 获取每日学习系统提示（用于 LLM system_prompt） */
  getPrompt() {
    return http.get('/daily-learning/prompt')
  },
}

export default dailyLearningApi
