import axios from 'axios'
import { getStorage, STORAGE_KEYS } from './storage'

// ★ 延迟绑定 router，避免循环依赖
let _router = null
export function initRequestRouter(router) {
  _router = router
}

// Create axios instance with default config
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
request.interceptors.request.use(
  (config) => {
    // 使用与 session.js 一致的 getStorage 读取 token，避免键名不一致问题
    const token = getStorage(STORAGE_KEYS.TOKEN)
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
request.interceptors.response.use(
  (response) => {
    console.log(`[Http] ${response.config?.method?.toUpperCase()} ${response.config?.url} → ${response.status}`)
    return response.data
  },
  (error) => {
    const { response, message } = error
    
    // Network error (no response received)
    if (!response) {
      console.error(`[Http] ❌ 网络错误:`, message || '请求未发送或连接被拒绝')
      console.error(`[Http] 请求地址:`, error.config?.url || '未知')
      return Promise.reject({
        detail: '网络连接失败，请检查后端服务是否启动 (端口 8008)'
      })
    }

    const url = error.config?.url || ''
    console.error(`[Http] ❌ ${error.config?.method?.toUpperCase()} ${url} → ${response.status}`, response.data)

    switch (response.status) {
      case 401:
        // 豁免列表：这些接口支持可选认证，不跳转登录，让调用方自己处理
        if (
          url.includes('/profile/') ||
          url.includes('/knowledge/') ||
          url.includes('/recommendations/')
        ) {
          return Promise.reject(response.data || { detail: '未登录' })
        }
        // 其他接口的 401：清除 token 并跳转登录（但不在登录页时跳转）
        localStorage.removeItem('learn-' + STORAGE_KEYS.TOKEN)
        // ★ 使用 router.push 代替 window.location.href
        // ★ 重要：如果已经在 /login 页面，不重复跳转，避免循环
        if (_router) {
          const currentPath = _router.currentRoute?.value?.path || ''
          if (currentPath !== '/login') {
            console.log('[Http] 401 → 跳转登录页')
            _router.push('/login')
          }
        } else {
          if (!window.location.pathname.includes('/login')) {
            window.location.href = '/login'
          }
        }
        return Promise.reject(response.data || { detail: '登录已过期，请重新登录' })

      case 403:
        console.error('[Http] ❌ 权限不足 (403)')
        return Promise.reject(response.data || { detail: '权限不足' })

      case 404:
        console.error('[Http] ❌ 接口不存在 (404):', url)
        return Promise.reject(response.data || { detail: `接口 ${url} 不存在` })

      case 500:
        console.error('[Http] ❌ 服务器错误 (500)')
        return Promise.reject(response.data || { detail: '服务器内部错误' })

      default:
        console.error('[Http] ❌ 请求失败:', response.status, response.data)
        return Promise.reject(response.data || { detail: `请求失败 (${response.status})` })
    }
  }
)

// HTTP methods
export const http = {
  get: (url, params, config = {}) => request.get(url, { params, ...config }),
  post: (url, data, config = {}) => request.post(url, data, config),
  put: (url, data, config = {}) => request.put(url, data, config),
  patch: (url, data, config = {}) => request.patch(url, data, config),
  delete: (url, config = {}) => request.delete(url, config)
}

export default request
