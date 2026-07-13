/** 认证 API */
import { http } from '../utils/request'

export const authApi = {
  /** 注册 */
  register(data) {
    return http.post('/auth/register', data)
  },

  /** 登录 */
  login(data, config = {}) {
    return http.post('/auth/login', data, config)
  },

  /** 游客登录 */
  guest() {
    return http.post('/auth/guest')
  },

  /** 获取当前用户 */
  me() {
    return http.get('/auth/me')
  },

  /** 检查用户名是否可用 */
  checkUsername(username) {
    return http.get('/auth/check-username', { username })
  },

  /** 忘记密码 */
  forgotPassword(email) {
    return http.post('/auth/forgot-password', { email })
  },

  /** 获取密码强度评估 */
  passwordStrength(password) {
    return http.get('/auth/password-strength', { password })
  },
}

export default authApi
