/**
 * 考试/错题相关 API
 */
import { http } from '../utils/request'

const examApi = {
  /**
   * 获取章节测试题目
   */
  getQuestions(nodeId) {
    return http.get(`/exam/${nodeId}/questions`)
  },

  /**
   * 提交考试答案
   */
  submitExam(nodeId, answers) {
    return http.post(`/exam/${nodeId}/submit`, { answers })
  },

  /**
   * 获取错题本（温故知新）
   */
  getMistakes() {
    return http.get('/exam/mistakes')
  },

  /**
   * ★ 保存练习题中的错题（今日学习 → 温故知新）
   */
  saveQuizResult(data) {
    return http.post('/exam/quiz-result', data)
  },

  /**
   * ★ 移除错题本中的一道错题
   */
  removeMistake(mistakeId) {
    return http.post('/exam/mistakes/remove', { mistake_id: mistakeId })
  },
}

export default examApi
