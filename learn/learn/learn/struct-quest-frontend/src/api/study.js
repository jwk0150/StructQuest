/**
 * 学习相关 API（今日任务、计时统计等）
 */
import { http } from '../utils/request'

const studyApi = {
  /**
   * 获取今日推荐任务（根据学习情况动态生成）
   */
  getDailyTasks() {
    return http.get('/study/daily-tasks')
  },

  /**
   * 获取今日任务接取/完成状态映射
   */
  getTaskStatus() {
    return http.get('/study/tasks/status')
  },

  /**
   * 获取侧边栏徽章数字（未接取任务数量）
   */
  getTaskBadge() {
    return http.get('/study/tasks/badge')
  },

  /**
   * 接取一个今日任务
   */
  claimTask(data) {
    return http.post('/study/tasks/claim', data)
  },

  /**
   * 根据学习行为自动完成匹配的任务
   */
  autoCompleteTasks(data) {
    return http.post('/study/tasks/auto-complete', data)
  },
}

export default studyApi
