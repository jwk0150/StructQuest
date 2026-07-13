/** 用户画像 API */
import { http } from '../utils/request'

export const profileApi = {
  /** 获取当前用户画像 */
  get() {
    return http.get('/profile/')
  },

  /** 保存画像（新用户完成问卷） */
  save(profileData) {
    return http.post('/profile/save', { profile_data: profileData })
  },

  /** 同步画像更新 */
  sync(profileData) {
    return http.post('/profile/sync', { profile_data: profileData })
  },

  /**
   * 获取用户六维学习能力值（真实动态计算，非随机值）
   * 返回：{ visual, comprehensive, stability, exploration, theory, practice }
   */
  getAbility() {
    return http.get('/user/ability')
  },
}

export default profileApi

