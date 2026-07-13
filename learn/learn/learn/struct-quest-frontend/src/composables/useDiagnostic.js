/**
 * 诊断测试组合式函数
 *
 * 管理诊断测试的完整状态：
 * - 题目加载与分模块展示
 * - 每题计时（answer_time_ms）
 * - 跳过/修改计数追踪
 * - 模块得分计算
 * - 行为数据收集
 */
import { ref, reactive, computed } from 'vue'

export function useDiagnostic() {
  // ── 状态 ──
  const modules = ref([])           // [{key, name}]
  const questions = ref({})         // {module: [{id, question, options, ...}]}
  const loading = ref(false)
  const started = ref(false)
  const finished = ref(false)

  // 当前进度
  const currentModuleIndex = ref(0)
  const currentQuestionIndex = ref(0)   // 在当前模块中的索引

  // 全局题目列表（扁平化，方便导航）
  const allQuestionsFlat = ref([])  // [{moduleKey, questionIndex, question}]

  // 答题记录
  const answers = ref({})           // {questionId: {userAnswer, answerTimeMs, skipCount, modifyCount, startTime}}
  const questionStartTime = ref(null)

  // 总计时
  const sessionStartTime = ref(null)
  const totalTimeMs = ref(0)

  // ── 计算属性 ──
  const currentModule = computed(() => modules.value[currentModuleIndex.value] || {})
  const currentQuestion = computed(() => {
    const mod = currentModule.value
    if (!mod.key) return null
    const qs = questions.value[mod.key] || []
    return qs[currentQuestionIndex.value] || null
  })

  const totalQuestions = computed(() => allQuestionsFlat.value.length)
  const answeredCount = computed(() => Object.keys(answers.value).length)

  const currentGlobalIndex = computed(() => {
    let idx = 0
    for (let mi = 0; mi < currentModuleIndex.value; mi++) {
      const mod = modules.value[mi]
      if (mod) idx += (questions.value[mod.key] || []).length
    }
    return idx + currentQuestionIndex.value
  })

  const progressPercent = computed(() => {
    if (totalQuestions.value === 0) return 0
    return Math.round((currentGlobalIndex.value / totalQuestions.value) * 100)
  })

  /** 当前模块的名称 */
  const currentModuleName = computed(() => currentModule.value.name || '')

  /** 是否可以跳过当前题 */
  const canSkip = computed(() => !!currentQuestion.value)

  /** 是否是最后一题 */
  const isLastQuestion = computed(() => {
    return currentGlobalIndex.value >= totalQuestions.value - 1
  })

  /** 是否是当前模块的最后一题 */
  const isLastInModule = computed(() => {
    const mod = currentModule.value
    if (!mod.key) return false
    const qs = questions.value[mod.key] || []
    return currentQuestionIndex.value >= qs.length - 1
  })

  // ── 方法 ──

  /** 加载题目 */
  async function loadQuestions(api) {
    loading.value = true
    try {
      const res = await api.getDiagnosticQuestions()
      modules.value = res.modules || []
      questions.value = res.questions || {}

      // 构建扁平题目列表
      const flat = []
      for (const mod of modules.value) {
        const qs = questions.value[mod.key] || []
        qs.forEach((q, qi) => {
          flat.push({ moduleKey: mod.key, moduleName: mod.name, questionIndex: qi, question: q })
        })
      }
      allQuestionsFlat.value = flat
    } finally {
      loading.value = false
    }
  }

  /** 开始测试 */
  function startTest() {
    started.value = true
    sessionStartTime.value = Date.now()
    _startQuestionTimer()
  }

  /** 开始当前题计时 */
  function _startQuestionTimer() {
    questionStartTime.value = Date.now()
  }

  /** 选择答案 */
  function selectAnswer(optionIndex) {
    if (!currentQuestion.value || finished.value) return

    const q = currentQuestion.value
    const elapsed = questionStartTime.value ? Date.now() - questionStartTime.value : 0
    const existing = answers.value[q.id]

    const modifyCount = existing ? existing.modifyCount + 1 : 0

    answers.value[q.id] = {
      questionId: q.id,
      module: currentModule.value.key,
      difficulty: q.difficulty || 1,
      userAnswer: optionIndex,
      answerTimeMs: (existing ? existing.answerTimeMs : 0) + elapsed,
      skipCount: existing ? existing.skipCount : 0,
      modifyCount,
    }

    // 自动前进到下一题
    setTimeout(() => goNext(), 300)
  }

  /** 跳过当前题 */
  function skipQuestion() {
    if (!currentQuestion.value || finished.value) return

    const q = currentQuestion.value
    const existing = answers.value[q.id]

    answers.value[q.id] = {
      questionId: q.id,
      module: currentModule.value.key,
      difficulty: q.difficulty || 1,
      userAnswer: -1,  // -1 表示跳过
      answerTimeMs: existing ? existing.answerTimeMs : 0,
      skipCount: (existing ? existing.skipCount : 0) + 1,
      modifyCount: existing ? existing.modifyCount : 0,
    }

    goNext()
  }

  /** 前进到下一题 */
  function goNext() {
    if (finished.value) return

    const mod = currentModule.value
    if (!mod.key) return
    const qs = questions.value[mod.key] || []

    if (currentQuestionIndex.value < qs.length - 1) {
      // 同一模块内下一题
      currentQuestionIndex.value++
    } else if (currentModuleIndex.value < modules.value.length - 1) {
      // 下一个模块
      currentModuleIndex.value++
      currentQuestionIndex.value = 0
    } else {
      // 全部完成
      finishTest()
      return
    }

    _startQuestionTimer()
  }

  /** 回退到上一题 */
  function goPrev() {
    if (currentQuestionIndex.value > 0) {
      currentQuestionIndex.value--
    } else if (currentModuleIndex.value > 0) {
      currentModuleIndex.value--
      const prevMod = modules.value[currentModuleIndex.value]
      const prevQs = questions.value[prevMod.key] || []
      currentQuestionIndex.value = Math.max(0, prevQs.length - 1)
    }
    _startQuestionTimer()
  }

  /** 完成测试 */
  function finishTest() {
    finished.value = true
    totalTimeMs.value = Date.now() - (sessionStartTime.value || Date.now())
  }

  /** 构建提交数据 */
  function buildSubmitData() {
    const answerList = []
    for (const qid in answers.value) {
      const a = answers.value[qid]
      // 跳过那些未回答的
      if (a.userAnswer === -1) continue
      answerList.push({
        question_id: a.questionId,
        module: a.module,
        difficulty: a.difficulty,
        user_answer: a.userAnswer,
        correct_answer: 0,  // 后端会用正确答案覆盖
        is_correct: true,     // 后端会重新判定
        answer_time_ms: a.answerTimeMs || 0,
        skip_count: a.skipCount || 0,
        modify_count: a.modifyCount || 0,
      })
    }
    return {
      answers: answerList,
      total_time_ms: totalTimeMs.value,
    }
  }

  /** 提交诊断结果 */
  async function submitDiagnostic(api) {
    const data = buildSubmitData()
    return await api.submitDiagnostic(data)
  }

  return {
    // 状态
    modules, questions, loading, started, finished,
    currentModuleIndex, currentQuestionIndex,
    answers, totalTimeMs,

    // 计算属性
    currentModule, currentQuestion, currentModuleName,
    totalQuestions, answeredCount, currentGlobalIndex,
    progressPercent, canSkip, isLastQuestion, isLastInModule,

    // 方法
    loadQuestions, startTest, selectAnswer, skipQuestion,
    goNext, goPrev, finishTest, buildSubmitData, submitDiagnostic,
  }
}
