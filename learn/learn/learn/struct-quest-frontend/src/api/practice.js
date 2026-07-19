/**
 * AI 练习中心 API — 综合推荐 & 错题 & 统计
 * 从画像、错题、学习记录计算个性化推荐
 */
import { http } from '../utils/request'
import { DEFAULT_RECOMMEND, generateReason } from '../views/Practice/practiceData'

/**
 * AI 推荐练习
 * 综合计算优先级：
 *   1. 错题最多的节点（weight 最高）
 *   2. 画像弱项节点
 *   3. 最近学习但未完成节点
 *   4. 默认推荐（树结构）
 */
export async function getAIRecommend() {
  try {
    const results = await Promise.allSettled([
      http.get('/exam/mistakes').catch(() => null),
      http.get('/profile').catch(() => null),
      http.get('/knowledge/progress').catch(() => null),
    ])

    const mistakesResult = results[0].status === 'fulfilled' ? results[0].value : null
    const profileResult = results[1].status === 'fulfilled' ? results[1].value : null
    const progressResult = results[2].status === 'fulfilled' ? results[2].value : null

    // Parse mistake data
    const mistakes = Array.isArray(mistakesResult)
      ? mistakesResult
      : (mistakesResult?.data || mistakesResult?.mistakes || [])
    const profile = profileResult?.data || profileResult || {}
    const progress = progressResult?.data || progressResult || {}

    // ── Strategy 1: most frequent mistake node ──
    if (mistakes.length > 0) {
      const freqMap = {}
      mistakes.forEach((m) => {
        const key = m.node_id || m.nodeId || m.name
        if (!key) return
        freqMap[key] = (freqMap[key] || 0) + 1
      })
      const sorted = Object.entries(freqMap).sort((a, b) => b[1] - a[1])
      if (sorted.length > 0) {
        const [nodeName, count] = sorted[0]
        // find nodeId from mistake record
        const match = mistakes.find((m) => (m.node_id || m.nodeId || m.name) === nodeName)
        const nodeId = match?.node_id || match?.nodeId || nodeName
        return {
          nodeName,
          nodeId,
          stars: Math.min(count, 5),
          duration: Math.max(count * 5, 10),
          reason: generateReason(nodeName, count, 0),
        }
      }
    }

    // ── Strategy 2: profile weak node ──
    const weakPoints = profile.weak_points || profile.weakPoints || []
    if (weakPoints.length > 0) {
      const w = weakPoints[0]
      const nodeName = w.name || w.node_name || w
      const nodeId = w.node_id || w.nodeId || nodeName
      return {
        nodeName,
        nodeId,
        stars: 4,
        duration: 15,
        reason: generateReason(nodeName, w.error_count || 1, w.days_ago || 1),
      }
    }

    // ── Strategy 3: in-progress node ──
    const inProgress = progress.in_progress || progress.inProgress || progress.current
    if (inProgress) {
      const nodeName = inProgress.name || inProgress.node_name || '当前节点'
      const nodeId = inProgress.node_id || inProgress.nodeId || 'ch05_tree_basic'
      return {
        nodeName,
        nodeId,
        stars: 4,
        duration: 15,
        reason: generateReason(nodeName, 0, 0, '上一节点'),
      }
    }

    // ── Strategy 4: default fallback ──
    return DEFAULT_RECOMMEND
  } catch {
    return DEFAULT_RECOMMEND
  }
}

/** 获取错题列表 */
export async function getMistakes() {
  try {
    const res = await http.get('/exam/mistakes')
    return Array.isArray(res) ? res : (res?.data || res?.mistakes || [])
  } catch {
    return []
  }
}

/** 获取最近练习记录 */
export async function getRecentPractice() {
  try {
    // /study/stats 是现有稳定接口，recent_chapters 即最近完成/练习的知识点。
    const res = await http.get('/study/stats')
    const data = res?.data || res || {}
    const recent = data.recent_chapters || []
    return recent.slice(0, 5).map((item, index) => ({
      id: `recent-${item.node_id || index}`,
      nodeName: item.title || item.node_name || '最近学习',
      nodeId: item.node_id || item.nodeId,
      progress: 1,
      time: item.completed_at || item.time || null,
      correctRate: item.correct_rate ?? item.correctRate,
    }))
  } catch {
    return []
  }
}

export default {
  getAIRecommend,
  getMistakes,
  getRecentPractice,
}
