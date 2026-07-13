import { defineStore } from 'pinia'
import { learningApi } from '../api/learning'

export const useLearningStore = defineStore('learning', {
  state: () => ({
    // ─── 原有字段 ───
    nodes: [],
    currentNode: null,
    progress: {
      totalNodes: 0,
      completedNodes: 0,
      masteryPercentage: 0
    },
    recentActivities: [],
    weeklyStats: [],
    weakPoints: [],

    // ─── AI 多智能体会话状态（新增）───
    sessionId: null,           // 当前会话 ID
    isLoading: false,          // 是否正在执行 AI 任务
    error: null,               // 错误信息

    // ProfileAgent 输出
    profile: {
      ability_level: '',
      learning_style: '',
      weakness_summary: '',
      cognitive: {
        mbti_style: '',
        feynman_adaptation: 0,
        abstract_reasoning: 0,
        error_tolerance: 0,
      },
      confidence_score: 0,
    },

    // PathPlanningAgent 输出
    learningPath: [],          // List[PathStep]
    currentStepIndex: 0,

    // ResourceAgent 输出
    resources: [],             // List[ResourceItem]
    resourceBundle: {},        // ResourceBundle (v4 新格式)

    // AssessmentAgent 输出
    assessment: {
      overall_score: 0,
      passed: false,
      bloom_scores: {},
      gaps_found: [],
      recommendation: '',
      error_analysis: {
        primary_error_type: '',
        patterns: [],
        fixes: [],
      },
    },

    // 会话快照（用于断点续学）
    sessionSnapshot: null,
    fullState: null,           // 完整后端 state（用于 continue_session）
  }),

  getters: {
    masteredNodes: (state) => state.nodes.filter(n => n.status === 'mastered'),
    learningNodes: (state) => state.nodes.filter(n => n.status === 'learning'),
    recommendedNodes: (state) => state.nodes.filter(n => n.status === 'recommended'),

    overallProgress: (state) => {
      if (state.progress.totalNodes === 0) return 0
      return Math.round((state.progress.completedNodes / state.progress.totalNodes) * 100)
    },

    /** 当前正在学习的步骤 */
    currentStep(state) {
      if (!state.learningPath.length || state.currentStepIndex >= state.learningPath.length) return null
      return state.learningPath[state.currentStepIndex]
    },

    /** 总步骤数 */
    totalSteps: (state) => state.learningPath.length,

    /** 进度百分比（基于 AI 路径） */
    pathProgress: (state) => {
      if (!state.learningPath.length) return 0
      return Math.round(((state.currentStepIndex + 1) / state.learningPath.length) * 100)
    },

    /** 按类型分组的资源 */
    resourcesByType: (state) => {
      const grouped = {}
      state.resources.forEach(r => {
        const t = r.resource_type || r.type || 'other'
        if (!grouped[t]) grouped[t] = []
        grouped[t].push(r)
      })
      return grouped
    },

    /** 学习讲义 */
    lectureNotes: (state) => state.resources.filter(r =>
      (r.resource_type || r.type) === 'notes' ||
      (r.resource_type || r.type) === 'lecture' ||
      (r.resource_type || r.type) === 'lecture_notes' ||
      (r.title && r.title.includes('讲义'))
    ),

    /** 练习题 */
    exercises: (state) => state.resources.filter(r =>
      (r.resource_type || r.type) === 'quiz' ||
      (r.resource_type || r.type) === 'exercise' ||
      (r.title && (r.title.includes('题') || r.title.includes('练习')))
    ),

    /** 代码案例 */
    codeExamples: (state) => state.resources.filter(r =>
      (r.resource_type || r.type) === 'code_example' ||
      (r.format || '') === 'code' || (r.format || '') === 'python'
    ),

    /** 思维导图 */
    mindMaps: (state) => state.resources.filter(r =>
      (r.resource_type || r.type) === 'mindmap' ||
      (r.resource_type || r.type) === 'mind_map' ||
      (r.title && r.title.includes('思维导图'))
    ),

    /** PPT 大纲 */
    pptOutlines: (state) => state.resources.filter(r =>
      (r.resource_type || r.type) === 'ppt_outline' ||
      (r.title && r.title.includes('PPT'))
    ),

    /** 资源包（新格式） */
    currentResourceBundle: (state) => state.resourceBundle || {},
  },

  actions: {
    /* ─── 原有方法保持兼容 ─── */

    setNodes(nodes) {
      this.nodes = nodes
      this.updateProgress()
    },

    updateNodeStatus(nodeId, status) {
      const node = this.nodes.find(n => n.id === nodeId)
      if (node) {
        node.status = status
        this.updateProgress()
      }
    },

    updateProgress() {
      this.progress.totalNodes = this.nodes.length
      this.progress.completedNodes = this.nodes.filter(n => n.status === 'mastered').length
      this.progress.masteryPercentage = this.overallProgress
    },

    setCurrentNode(node) {
      this.currentNode = node
    },

    addActivity(activity) {
      this.recentActivities.unshift({
        ...activity,
        timestamp: new Date().toISOString()
      })
      if (this.recentActivities.length > 20) {
        this.recentActivities = this.recentActivities.slice(0, 20)
      }
    },

    setWeeklyStats(stats) {
      this.weeklyStats = stats
    },

    setWeakPoints(weakPoints) {
      this.weakPoints = weakPoints
    },

    reset() {
      this.nodes = []
      this.currentNode = null
      this.progress = { totalNodes: 0, completedNodes: 0, masteryPercentage: 0 }
      this.recentActivities = []
      this.weeklyStats = []
      this.weakPoints = []
      // AI 状态也清空
      this.sessionId = null
      this.profile = { ability_level: '', learning_style: '', weakness_summary: '', cognitive: {}, confidence_score: 0 }
      this.learningPath = []
      this.currentStepIndex = 0
      this.resources = []
      this.assessment = { overall_score: 0, passed: false, bloom_scores: {}, gaps_found: [], recommendation: '', error_analysis: {} }
      this.sessionSnapshot = null
      this.fullState = null
      this.error = null
    },

    /* ─── 新增：AI 会话操作 ─── */

    /**
     * 启动学习会话（REST 方式）
     * 完整流程：Profile → Path → Resource → Assessment（可能循环多次）
     */
    async startSession({ subject, goal, userId = 'default', userMessages = [], maxIterations = 5 }) {
      this.isLoading = true
      this.error = null

      try {
        const res = await learningApi.startSession({
          subject,
          goal,
          user_id: String(userId || 'default'),
          user_messages: userMessages,
          max_iterations: maxIterations,
        })

        // 写入所有状态
        this.sessionId = res.session_id
        this._applyResult(res)

        this.addActivity({ event: `开始「${subject}」AI 学习会话`, type: 'session_start' })

        return res
      } catch (err) {
        console.error('[LearningStore] startSession 失败:', err)
        this.error = err.detail || err.message || '启动学习会话失败'
        throw err
      } finally {
        this.isLoading = false
      }
    },

    /**
     * 继续会话（提交答案后触发测评+路径调整）
     */
    async submitAnswer(answer) {
      if (!this.fullState) {
        console.warn('[LearningStore] 无会话状态，无法提交答案')
        return null
      }

      this.isLoading = true
      this.error = null

      try {
        const res = await learningApi.continueSession(this.fullState, answer)
        this._applyResult(res)

        this.addActivity({ event: `提交答案并完成测评 (得分: ${res.assessment?.overall_score || '?'})`, type: 'assessment' })

        return res
      } catch (err) {
        this.error = err.detail || err.message || '测评失败'
        throw err
      } finally {
        this.isLoading = false
      }
    },

    /**
     * 将后端返回结果写入 Store 各字段
     */
    _applyResult(result) {
      // Profile
      if (result.student_profile) {
        this.profile = { ...this.profile, ...result.student_profile }
        if (!result.student_profile.cognitive) {
          this.profile.cognitive = this.profile.cognitive || {}
        }
      }

      // Path
      if (result.learning_path) {
        this.learningPath = result.learning_path
      }

      // Resources
      if (result.resources) {
        this.resources = result.resources
      }

      // Assessment
      if (result.assessment) {
        this.assessment = { ...this.assessment, ...result.assessment }
      }

      // Snapshot
      if (result.session_snapshot) {
        this.sessionSnapshot = result.session_snapshot
      }

      // 保存完整状态用于续传
      this.fullState = result
    },

    /**
     * 推进到下一步骤
     */
    advanceStep() {
      if (this.currentStepIndex < this.learningPath.length - 1) {
        this.currentStepIndex++
        this.addActivity({ event: `进入第 ${this.currentStepIndex + 1} 步：${this.currentStep?.topic || ''}`, type: 'step_advance' })
      }
    },

    /**
     * 设置当前步骤索引
     */
    setStepIndex(index) {
      if (index >= 0 && index < this.learningPath.length) {
        this.currentStepIndex = index
      }
    },
  }
})
