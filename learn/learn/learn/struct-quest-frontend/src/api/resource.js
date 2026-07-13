

/**
 * 学习资源持久化 API
 *
 * 对接后端 /api/learning/resource/saved 接口
 * 用于保存、查询、删除 AI 生成的学习资源（温故知新）
 */
import { http } from '../utils/request'

const BASE = '/learning/resource'

export const resourceApi = {
  /**
   * 保存一个 AI 生成的学习资源
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
    return http.post(`${BASE}/saved`, data)
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
