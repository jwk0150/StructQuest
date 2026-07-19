

/**
 * 学习资源持久化 API
 *
 * 对接后端 /api/learning/resource/saved 接口
 * 用于保存、查询、删除 AI 生成的学习资源（温故知新）
 */
import { http } from '../utils/request'

const BASE = '/learning/resource'

// ★ 正在进行的保存请求（防抖：相同去重键短时间内不重复触发）
const inflightSaves = new Map()   // key -> Promise

function _makeKey(data) {
  // 与后端去重键保持一致：(resource_type, topic_tag, title)
  return `${data.resource_type || ''}::${data.topic_tag || ''}::${data.title || ''}`
}

export const resourceApi = {
  /**
   * 保存一个 AI 生成的学习资源（前端去重：相同键短时间内只触发一次请求）
   * @param {Object} data
   * @param {string} data.resource_type - mindmap/notes/quiz/code_example/example/common_mistakes/ppt/animation
   * @param {string} data.title - 资源标题
   * @param {string} [data.content_text] - 文本内容
   * @param {Object} [data.content_json] - 结构化数据
   * @param {string} [data.file_url] - 视频/文件URL
   * @param {string} [data.topic_tag] - 知识点ID
   * @param {string} [data.topic_name] - 知识点名称
   * @param {string} [data.chapter_name] - 章节名称
   * @param {string} [data.format] - 内容格式
   */
  save(data) {
    const key = _makeKey(data)
    const existing = inflightSaves.get(key)
    if (existing) {
      // 已有相同键的请求在飞，复用同一个 Promise
      console.log(`[resourceApi] 跳过重复保存（去重键命中）: ${key}`)
      return existing
    }
    const p = http.post(`${BASE}/saved`, data)
      .finally(() => {
        // 无论成功失败，1.5s 后清理（避免过快误判）
        setTimeout(() => inflightSaves.delete(key), 1500)
      })
    inflightSaves.set(key, p)
    return p
  },

  /**
   * 一次性清理当前用户的重复资源记录（管理员/用户均可调用）
   */
  dedup() {
    return http.post(`${BASE}/saved/dedup`)
  },

  /**
   * 获取所有已保存的学习资源
   * @param {Object} [params]
   * @param {string} [params.resource_type] - 按类型过滤
   * @param {string} [params.topic_tag] - 按知识点过滤
   */
  list(params) {
    return http.get(`${BASE}/saved`, { params })
  },

  /**
   * 删除一个已保存的学习资源
   * @param {number} resourceId
   */
  remove(resourceId) {
    return http.delete(`${BASE}/saved/${resourceId}`)
  },
}

export default resourceApi
