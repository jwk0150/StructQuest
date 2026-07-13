/**
 * 多智能体学习系统 — RESTful API 封装
 *
 * 对接后端 /api/learning/* 接口，提供完整的学习会话生命周期管理
 */
import { http } from '../utils/request'

const BASE = '/learning'

export const learningApi = {
  /**
   * 启动一次完整的 AI 多智能体学习会话
   * 触发: ProfileAgent → PathPlanningAgent → ResourceAgent → AssessmentAgent
   */
  startSession(data) {
    return http.post(`${BASE}/session/start`, data)
  },

  /**
   * 继续已有学习会话（提交答案后触发测评+路径调整）
   */
  continueSession(sessionState, answer) {
    return http.post(`${BASE}/session/continue`, {
      session_state: sessionState,
      ...(answer ? { user_answer: answer, user_answer: answer } : {}),
    })
  },

  /**
   * 获取多智能体系统架构信息
   */
  getGraphInfo() {
    return http.get(`${BASE}/graph/info`)
  },

  /**
   * 获取 Mermaid 流程图定义
   */
  getMermaidGraph() {
    return http.get(`${BASE}/graph/mermaid`)
  },

  /**
   * 按需生成单个类型的学习资源
   * 支持类型: notes / mindmap / quiz / code_example / animation
   * 注：ppt_outline 已迁移至独立 PPT 智能生成器（/api/ppt/ 接口）
   */
  generateResource(data) {
    return http.post(`${BASE}/resource/generate`, data)
  },

  /**
   * 生成完整的资源包（一次返回）
   * 返回: { notes, mindmap, quiz, code_example, animation }
   * 注：ppt_outline 已迁移至独立 PPT 智能生成器（/api/ppt/ 接口）
   */
  generateBundle(data) {
    return http.post(`${BASE}/resource/bundle`, data)
  },
}

export default learningApi
