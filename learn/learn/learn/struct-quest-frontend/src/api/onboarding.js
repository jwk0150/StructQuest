/** 冷启动引导 API */
import { http } from '../utils/request'

export const onboardingApi = {
  /** 提交学习目标问卷（第二阶段） */
  submitQuestionnaire(data) {
    return http.post('/onboarding/questionnaire', data)
  },

  /** 获取诊断测试题目（第三阶段） */
  getDiagnosticQuestions() {
    return http.get('/onboarding/diagnostic/questions')
  },

  /** 提交诊断测试结果（含行为数据） */
  submitDiagnostic(data) {
    return http.post('/onboarding/diagnostic/submit', data)
  },

  /** 调用 AI 生成初始画像（第四阶段） */
  generateProfile() {
    return http.post('/onboarding/generate-profile')
  },
}

export default onboardingApi
