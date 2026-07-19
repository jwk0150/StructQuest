<template>
  <div class="quiz-display">
    <!-- 头部统计 -->
    <div class="quiz-header">
      <div class="quiz-title-row">
        <span class="quiz-icon">✏️</span>
        <h3>{{ title || '练习题' }}</h3>
        <span class="quiz-count">{{ quizItems.length }} 题</span>
        <span v-if="!allSubmitted && answeredCount > 0" class="quiz-progress">
          已答 {{ answeredCount }}/{{ quizItems.length }}
        </span>
      </div>
    </div>

    <!-- 操作栏：提交 / 结果筛选 / 重新作答 -->
    <div class="quiz-toolbar">
      <!-- 提交前：只显示提交按钮 -->
      <template v-if="!allSubmitted">
        <div class="toolbar-hint">
          💡 完成所有题目后点击提交查看成绩
        </div>
        <button
          class="action-btn submit-btn"
          @click="submitAll"
          :disabled="isSubmitting"
        >
          {{ isSubmitting ? '提交中...' : '📝 提交答案' }}
        </button>
      </template>

      <!-- 提交后：结果显示 + 筛选 + 重新作答 -->
      <template v-else>
        <div class="result-summary" :class="{ pass: scorePercent >= 60, fail: scorePercent < 60 }">
          <span class="result-emoji">{{ scorePercent >= 60 ? '🎉' : '💪' }}</span>
          <span class="result-text">
            {{ scorePercent >= 60 ? '恭喜通过！' : '继续加油！' }}
          </span>
          <span class="result-score">
            <strong>{{ correctCount }}</strong>/{{ quizItems.length }}
          </span>
          <span class="result-percent">（{{ scorePercent }}%）</span>
          <span class="result-breakdown">
            <span class="breakdown-correct">✓ {{ correctCount }}</span>
            <span v-if="wrongCount > 0" class="breakdown-wrong">✗ {{ wrongCount }}</span>
            <span v-if="unreachedCount > 0" class="breakdown-unreached">— {{ unreachedCount }}</span>
          </span>
          <div class="result-bar-wrap">
            <div class="result-bar" :style="{ width: scorePercent + '%' }"></div>
          </div>
        </div>
        <div class="toolbar-actions">
          <label class="toggle-wrong">
            <input type="checkbox" v-model="showWrongOnly" />
            <span>只看错题</span>
            <span v-if="wrongCount + unreachedCount > 0" class="wrong-badge">{{ wrongCount + unreachedCount }}</span>
          </label>
          <button class="action-btn retry-btn" @click="resetAll">
            🔄 重新作答
          </button>
        </div>
      </template>
    </div>

    <!-- 题目列表 -->
    <div class="quiz-list">
      <div
        v-for="quizItem in filteredItems"
        :key="quizItem._origIdx"
        class="quiz-card"
        :class="{
          correct: allSubmitted && isCorrect(quizItem._origIdx),
          wrong: allSubmitted && !isCorrect(quizItem._origIdx) && userAnswers[quizItem._origIdx] !== undefined,
          unreached: allSubmitted && userAnswers[quizItem._origIdx] === undefined,
        }"
      >
        <!-- 题号与标签行 -->
        <div class="qc-header">
          <span class="qc-num" :class="{
            'num-correct': allSubmitted && isCorrect(quizItem._origIdx),
            'num-wrong': allSubmitted && !isCorrect(quizItem._origIdx) && userAnswers[quizItem._origIdx] !== undefined,
            'num-unreached': allSubmitted && (userAnswers[quizItem._origIdx] === undefined || userAnswers[quizItem._origIdx] === null || userAnswers[quizItem._origIdx] === ''),
          }">{{ quizItem._origIdx + 1 }}</span>
          <div class="qc-tags">
            <span v-if="quizItem.difficulty" class="qc-tag" :class="'diff-' + quizItem.difficulty">
              {{ difficultyLabel(quizItem.difficulty) }}
            </span>
            <span v-if="quizItem.bloom_level" class="qc-tag bloom">
              {{ bloomLabel(quizItem.bloom_level) }}
            </span>
            <span class="qc-tag type-tag">{{ typeLabel(quizItem.type) }}</span>
            <span v-if="quizItem.weakness_related" class="qc-tag weak">薄弱点</span>
          </div>
        </div>

        <!-- 知识点 -->
        <div v-if="quizItem.knowledge_point" class="qc-knowledge">
          📍 {{ quizItem.knowledge_point }}
        </div>

        <!-- 题干 -->
        <div class="qc-question">{{ quizItem.question }}</div>

        <!-- 选择题选项 -->
        <div v-if="quizItem.type === 'choice' && quizItem.options" class="qc-options">
          <label
            v-for="(opt, j) in quizItem.options"
            :key="j"
            class="qc-option"
            :class="optionClass(quizItem._origIdx, j, opt)"
          >
            <input
              type="radio"
              :name="'q' + quizItem._origIdx"
              :value="j"
              v-model="userAnswers[quizItem._origIdx]"
              :disabled="allSubmitted"
            />
            <span class="opt-label">{{ String.fromCharCode(65 + j) }}</span>
            <span class="opt-text">{{ opt }}</span>
            <span v-if="allSubmitted && answersMatch(j, quizItem.answer, quizItem.options)" class="opt-icon">✓</span>
          </label>
        </div>

        <!-- 填空题 / 简答题 -->
        <div v-if="quizItem.type === 'fill_blank' || quizItem.type === 'short_answer'" class="qc-input-area">
          <textarea
            v-model="userAnswers[quizItem._origIdx]"
            placeholder="在此输入你的答案..."
            rows="3"
            :disabled="allSubmitted"
          ></textarea>
        </div>

        <!-- 答案与解析（仅提交后显示） -->
        <transition name="expand">
          <div v-if="allSubmitted" class="qc-explanation">
            <div class="explain-header" :class="{
              'explain-correct': isCorrect(quizItem._origIdx),
              'explain-wrong': !isCorrect(quizItem._origIdx) && userAnswers[quizItem._origIdx] !== undefined && userAnswers[quizItem._origIdx] !== '',
              'explain-unreached': userAnswers[quizItem._origIdx] === undefined || userAnswers[quizItem._origIdx] === null || userAnswers[quizItem._origIdx] === '',
            }">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>
              </svg>
              <span class="explain-label">
                <template v-if="isCorrect(quizItem._origIdx)">✓ 回答正确</template>
                <template v-else-if="userAnswers[quizItem._origIdx] === undefined || userAnswers[quizItem._origIdx] === null || userAnswers[quizItem._origIdx] === ''">⚠ 未作答</template>
                <template v-else>✗ 回答错误</template>
              </span>
            </div>
            <div class="explain-content">
              <div class="answer-row">
                <span class="answer-label">正确答案：</span>
                <span class="answer-value">{{ quizItem.answer }}</span>
              </div>
              <div v-if="quizItem.explanation" class="explain-text">{{ quizItem.explanation }}</div>
            </div>
          </div>
        </transition>
      </div>

      <!-- 空状态 -->
      <div v-if="allSubmitted && showWrongOnly && filteredItems.length === 0" class="empty-wrong">
        🎉 全部正确，没有错题！
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import examApi from '../../api/exam'

const props = defineProps({
  quizItems: { type: Array, default: () => [] },
  title: { type: String, default: '' },
  nodeId: { type: String, default: '' },  // ★ 用于保存错题
})

// 用户答案 { [index]: value }
const userAnswers = ref({})
const allSubmitted = ref(false)
const isSubmitting = ref(false)
const showWrongOnly = ref(false)

/** 已回答的题目数 */
const answeredCount = computed(() => {
  return props.quizItems.filter((_, idx) => {
    const ans = userAnswers.value[idx]
    return ans !== undefined && ans !== null && ans !== ''
  }).length
})

/**
 * 灵活匹配用户选择与正确答案
 * 兼容多种 answer 格式：纯字母 "B"、字母+文本 "B. 0"、纯文本 "0"、索引 "1"
 */
function answersMatch(selectedIndex, correctAnswer, options) {
  if (selectedIndex === undefined || selectedIndex === null) return false
  const selectedText = options?.[selectedIndex]
  if (!selectedText && selectedText !== '') return false
  const answer = String(correctAnswer ?? '').trim()
  if (!answer) return false

  // 1. 索引直接匹配（answer 是数字字符串如 "1"）
  if (/^\d+$/.test(answer) && parseInt(answer) === selectedIndex) return true

  // 2. 提取字母前缀匹配（"A" vs "B. 0" → 匹配选项的字母前缀和答案的字母）
  const selectedLetter = String(selectedText).match(/^[A-Za-z]+(?=[\.\s、\)])/)?.[0]
  const answerLetter = answer.match(/^[A-Za-z]+(?=[\.\s、\)])/)?.[0]
  if (selectedLetter && answerLetter) {
    return selectedLetter.toUpperCase() === answerLetter.toUpperCase()
  }

  // 3. 答案纯字母 A/B/C/D 映射到索引
  const letterMap = { A: 0, B: 1, C: 2, D: 3, E: 4, F: 5 }
  if (answer.length === 1 && letterMap[answer.toUpperCase()] !== undefined) {
    return letterMap[answer.toUpperCase()] === selectedIndex
  }

  // 4. 精确文本匹配
  if (String(selectedText) === answer) return true

  // 5. 所选文本包含答案或答案包含所选文本
  if (answer.length > 1 && String(selectedText).includes(answer)) return true

  return false
}

/** 判断某一题是否正确 */
function isCorrect(idx) {
  const item = props.quizItems[idx]
  if (!item) return false
  const userAns = userAnswers.value[idx]
  if (userAns === undefined || userAns === null || userAns === '') return false

  if (item.type === 'choice') {
    return answersMatch(userAns, item.answer, item.options)
  }
  // 填空题/简答题：模糊匹配（忽略大小写、前后空格）
  const ua = String(userAns).trim().toLowerCase()
  const ca = String(item.answer).trim().toLowerCase()
  if (ua === ca) return true
  // 如果答案较长（>30字），有较高重叠度也算对
  if (ca.length > 30) {
    let overlap = 0
    for (const ch of ua) {
      if (ca.includes(ch)) overlap++
    }
    if (overlap / Math.max(ca.length, 1) > 0.6) return true
  }
  return false
}

const correctCount = computed(() => {
  if (!allSubmitted.value) return 0
  let count = 0
  props.quizItems.forEach((_, idx) => {
    if (isCorrect(idx)) count++
  })
  return count
})

const wrongCount = computed(() => {
  if (!allSubmitted.value) return 0
  return props.quizItems.filter((_, idx) => {
    const ans = userAnswers.value[idx]
    return ans !== undefined && ans !== null && ans !== '' && !isCorrect(idx)
  }).length
})

const unreachedCount = computed(() => {
  if (!allSubmitted.value) return 0
  return props.quizItems.filter((_, idx) => {
    const ans = userAnswers.value[idx]
    return ans === undefined || ans === null || ans === ''
  }).length
})

const scorePercent = computed(() => {
  if (!props.quizItems.length) return 0
  return Math.round((correctCount.value / props.quizItems.length) * 100)
})

/** 筛选后的题目列表 */
const filteredItems = computed(() => {
  if (!allSubmitted.value || !showWrongOnly.value) {
    return props.quizItems.map((item, i) => ({ ...item, _origIdx: i }))
  }
  return props.quizItems
    .map((item, i) => ({ ...item, _origIdx: i }))
    .filter((_, i) => {
      // 未作答也算错题，统一用 isCorrect 判断
      return !isCorrect(i)
    })
})

/** 选项样式 */
function optionClass(itemIdx, j, _opt) {
  const selected = userAnswers.value[itemIdx]
  const item = props.quizItems[itemIdx]
  const classes = []
  if (selected === j) classes.push('selected')
  if (allSubmitted.value && item) {
    // 使用 answersMatch 判断当前选项是否为正确答案
    if (answersMatch(j, item.answer, item.options)) {
      classes.push('correct')
    } else if (selected === j) {
      // 用户选了此选项但非正确答案
      classes.push('wrong')
    }
  }
  return classes
}

function submitAll() {
  isSubmitting.value = true
  showWrongOnly.value = false
  setTimeout(async () => {
    allSubmitted.value = true
    isSubmitting.value = false

    // ★ 保存错题到后端（温故知新）：只保存已作答但答错的题
    const nid = Array.isArray(props.nodeId) ? props.nodeId[0] : props.nodeId
    if (nid) {
      // ★ 直接用索引，避免 indexOf 在 Proxy 对象上返回 -1
      const wrongItems = []
      props.quizItems.forEach((item, idx) => {
        const ans = userAnswers.value[idx]
        const answered = ans !== undefined && ans !== null && ans !== ''
        if (!answered || isCorrect(idx)) return  // 跳过未答或答对的

        let userAnswerText = ''
        if (item.type === 'choice' && item.options) {
          if (ans !== undefined && ans !== null) {
            const letter = String.fromCharCode(65 + Number(ans))
            userAnswerText = `${letter}. ${item.options[ans] || ''}`
          }
        } else {
          userAnswerText = ans !== undefined ? String(ans) : ''
        }

        wrongItems.push({
          question: item.question,
          answer: item.answer,
          user_answer: userAnswerText || '未作答',
          explanation: item.explanation || '',
          type: item.type,
          options: item.options || [],
          knowledge_point: item.knowledge_point || '',
        })
      })

      console.log(`[Quiz] nodeId=${nid}, 错题数=${wrongItems.length}, 正确数=${correctCount.value}, 总数=${props.quizItems.length}`)

      if (wrongItems.length > 0) {
        try {
          const res = await examApi.saveQuizResult({
            node_id: nid,
            wrong_items: wrongItems,
            correct_count: correctCount.value,
            total_count: props.quizItems.length,
          })
          console.log(`[Quiz] ✅ 已保存 ${wrongItems.length} 道错题到温故知新`, res)
        } catch (e) {
          console.error('[Quiz] 保存错题失败:', e)
        }
      } else {
        console.log('[Quiz] 没有错题需要保存')
      }
      // ★ 练习完成后，全局刷新能力值（无需刷新页面，雷达图自动更新）
      try {
        const { useAbilityStore } = await import('../../store/ability')
        const abilityStore = useAbilityStore()
        await abilityStore.refreshAbility()
      } catch (_) { /* 非关键路径 */ }
    } else {
      console.warn('[Quiz] ⚠️ nodeId 为空，无法保存错题')
    }
  }, 400)
}

function resetAll() {
  userAnswers.value = {}
  allSubmitted.value = false
  showWrongOnly.value = false
}

watch(() => props.quizItems, () => {
  userAnswers.value = {}
  allSubmitted.value = false
  showWrongOnly.value = false
})

function difficultyLabel(d) {
  const map = { easy: '简单', medium: '中等', hard: '困难' }
  return map[d] || d
}
function bloomLabel(b) {
  const map = { remember: '记忆', understand: '理解', apply: '应用', analyze: '分析', evaluate: '评价', create: '创造' }
  return map[b] || b
}
function typeLabel(t) {
  const map = { choice: '选择题', fill_blank: '填空题', short_answer: '简答题' }
  return map[t] || t
}
</script>

<style lang="scss" scoped>
.quiz-display {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

/* ── 头部 ── */
.quiz-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  background: #fff;
  border-bottom: 1px solid #e5e6eb;
  flex-shrink: 0;

  .quiz-title-row {
    display: flex;
    align-items: center;
    gap: 8px;
    .quiz-icon { font-size: 18px; }
    h3 { font-size: 15px; font-weight: 700; color: #1d2129; margin: 0; }
    .quiz-count {
      font-size: 12px; color: #86909c;
      background: #f2f3f5; padding: 2px 10px; border-radius: 10px;
    }
    .quiz-progress {
      font-size: 12px; color: #c84c5a;
      background: rgba(200,76,90,.08);
      padding: 2px 10px; border-radius: 10px;
      font-weight: 500;
    }
  }
}

/* ── 工具栏 ── */
.quiz-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 20px;
  background: #fff;
  border-bottom: 1px solid #f0f1f3;
  flex-shrink: 0;
  flex-wrap: wrap;
  gap: 10px;

  .toolbar-hint {
    font-size: 12px; color: #86909c;
  }
}

.result-summary {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;

  .result-emoji { font-size: 22px; }
  .result-text { font-size: 14px; font-weight: 700; color: #1d2129; white-space: nowrap; }
  .result-score {
    font-size: 14px; color: #4e5969;
    strong { color: #aa3948; font-size: 18px; }
  }
  .result-percent {
    font-size: 12px; color: #86909c;
  }
  .result-breakdown {
    display: flex; gap: 6px;
    font-size: 11px; font-weight: 600;
    .breakdown-correct { color: #059669; }
    .breakdown-wrong { color: #dc2626; }
    .breakdown-unreached { color: #94a3b8; }
  }
  .result-bar-wrap {
    flex: 1;
    height: 5px; background: #e5e6eb; border-radius: 3px;
    overflow: hidden; min-width: 60px;
    .result-bar {
      height: 100%; border-radius: 3px;
      transition: width .6s cubic-bezier(.4,0,.2,1);
      background: linear-gradient(90deg, #aa3948, #10b981);
    }
  }

  &.pass .result-bar { background: linear-gradient(90deg, #10b981, #34d399); }
  &.fail .result-bar { background: linear-gradient(90deg, #f59e0b, #ef4444); }
  &.pass .result-emoji + .result-text { color: #059669; }
  &.fail .result-emoji + .result-text { color: #dc2626; }
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toggle-wrong {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px; color: #4e5969;
  cursor: pointer;
  user-select: none;
  padding: 4px 10px;
  border-radius: 6px;
  transition: all .2s;

  &:hover { background: #f2f3f5; }

  input[type="checkbox"] {
    accent-color: #ef4444;
    cursor: pointer;
  }

  .wrong-badge {
    font-size: 11px; font-weight: 600;
    background: rgba(239, 68, 68, .12);
    color: #dc2626;
    padding: 1px 7px; border-radius: 8px;
  }
}

.action-btn {
  padding: 6px 14px;
  border: 1px solid #e5e6eb;
  border-radius: 8px;
  background: #fff;
  font-size: 12px;
  color: #4e5969;
  cursor: pointer;
  transition: all .2s;
  white-space: nowrap;

  &:hover { border-color: #aa3948; color: #aa3948; background: rgba(79,70,229,.04); }

  &.submit-btn {
    background: linear-gradient(135deg, #aa3948, #c84c5a);
    color: white;
    border-color: transparent;
    font-weight: 600;
    &:hover { opacity: .9; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(79,70,229,.3); }
    &:disabled { opacity: .6; cursor: not-allowed; transform: none; box-shadow: none; }
  }

  &.retry-btn {
    color: #f59e0b;
    border-color: rgba(245, 158, 11, .3);
    &:hover { background: rgba(245, 158, 11, .06); border-color: #f59e0b; }
  }
}

/* ── 题目列表 ── */
.quiz-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* ── 题目卡片 ── */
.quiz-card {
  background: #fff;
  border: 1px solid #e5e6eb;
  border-radius: 12px;
  padding: 18px 20px;
  transition: all .3s;

  &:hover {
    border-color: rgba(79,70,229,.2);
    box-shadow: 0 2px 12px rgba(79,70,229,.06);
  }

  &.correct {
    border-color: rgba(16, 185, 129, .35);
    background: linear-gradient(135deg, #f0fdf4, #ecfdf5);
  }
  &.wrong {
    border-color: rgba(239, 68, 68, .3);
    background: linear-gradient(135deg, #fef2f2, #fff5f5);
  }
  &.unreached {
    border-color: rgba(148, 163, 184, .3);
    background: #fafbfc;
  }

  .qc-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 10px;

    .qc-num {
      width: 26px; height: 26px;
      border-radius: 8px;
      background: linear-gradient(135deg, #aa3948, #a93546);
      color: white;
      font-size: 12px; font-weight: 700;
      display: flex; align-items: center; justify-content: center;
      flex-shrink: 0;
      transition: all .3s;

      &.num-correct {
        background: linear-gradient(135deg, #10b981, #34d399);
      }
      &.num-wrong {
        background: linear-gradient(135deg, #ef4444, #f87171);
      }
      &.num-unreached {
        background: linear-gradient(135deg, #94a3b8, #cbd5e1);
        color: #475569;
      }
    }

    .qc-tags {
      display: flex; gap: 6px; flex-wrap: wrap;
    }

    .qc-tag {
      font-size: 11px; padding: 2px 8px; border-radius: 6px;
      font-weight: 500;
      background: #f2f3f5; color: #86909c;

      &.diff-easy { background: rgba(16, 185, 129, .1); color: #059669; }
      &.diff-medium { background: rgba(245, 158, 11, .1); color: #d97706; }
      &.diff-hard { background: rgba(239, 68, 68, .1); color: #dc2626; }
      &.bloom { background: rgba(79, 70, 229, .08); color: #aa3948; }
      &.type-tag { background: rgba(200,76,90, .08); color: #c84c5a; font-weight: 600; }
      &.weak { background: rgba(245, 158, 11, .12); color: #d97706; }
    }
  }

  .qc-knowledge {
    font-size: 12px; color: #c84c5a;
    margin-bottom: 8px;
    padding: 4px 10px;
    background: rgba(200,76,90, .06);
    border-radius: 6px;
    display: inline-block;
  }

  .qc-question {
    font-size: 14px; font-weight: 600; color: #1d2129;
    line-height: 1.7; margin-bottom: 12px;
  }
}

/* ── 选项 ── */
.qc-options {
  display: flex; flex-direction: column; gap: 8px;
}

.qc-option {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 14px;
  border: 1px solid #e5e6eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all .2s;
  font-size: 13px; color: #4e5969;

  &:hover {
    border-color: rgba(79,70,229,.3);
    background: rgba(79,70,229,.03);
  }

  &.selected {
    border-color: #aa3948;
    background: rgba(79,70,229,.06);
    color: #aa3948;
  }

  &.correct {
    border-color: rgba(16, 185, 129, .5) !important;
    background: rgba(16, 185, 129, .08) !important;
    color: #059669 !important;
    .opt-label { background: #10b981 !important; color: white !important; }
  }

  &.wrong {
    border-color: rgba(239, 68, 68, .4) !important;
    background: rgba(239, 68, 68, .06) !important;
    color: #dc2626 !important;
    .opt-label { background: #ef4444 !important; color: white !important; }
  }

  input[type="radio"] { display: none; }

  .opt-label {
    width: 24px; height: 24px;
    border-radius: 6px;
    background: rgba(79,70,229,.1);
    color: #aa3948;
    font-size: 12px; font-weight: 700;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
    transition: all .2s;
  }

  .opt-text { flex: 1; }

  .opt-icon {
    font-size: 14px; font-weight: 700;
    color: #10b981;
  }
}

/* ── 输入区（填空/简答） ── */
.qc-input-area {
  margin-top: 4px;
  textarea {
    width: 100%;
    padding: 12px 14px;
    border: 1px solid #e5e6eb;
    border-radius: 8px;
    font-size: 13px;
    color: #1d2129;
    line-height: 1.6;
    resize: vertical;
    background: #f9fafb;
    transition: border-color .2s;
    font-family: inherit;

    &:focus {
      outline: none;
      border-color: #aa3948;
      background: #fff;
      box-shadow: 0 0 0 3px rgba(79,70,229,.08);
    }

    &:disabled {
      background: #f3f4f6;
      color: #86909c;
      cursor: not-allowed;
    }
  }
}

/* ── 答案解析 ── */
.qc-explanation {
  margin-top: 14px;
  padding: 14px 16px;
  background: #fbfcfd;
  border: 1px solid #e5e6eb;
  border-radius: 8px;

  .explain-header {
    display: flex; align-items: center; gap: 6px;
    margin-bottom: 10px;
    font-size: 13px; font-weight: 600;
    color: #c84c5a;
    svg { flex-shrink: 0; }

    &.explain-correct { color: #059669; }
    &.explain-wrong { color: #dc2626; }
    &.explain-unreached { color: #94a3b8; }
  }

  .explain-content {
    .answer-row {
      display: flex; align-items: baseline; gap: 4px;
      margin-bottom: 8px;
      .answer-label { font-size: 12px; color: #86909c; }
      .answer-value {
        font-size: 14px; font-weight: 700;
        color: #aa3948;
        background: rgba(79,70,229,.08);
        padding: 2px 10px; border-radius: 4px;
      }
    }
    .explain-text {
      font-size: 13px; color: #4e5969; line-height: 1.7;
    }
  }
}

/* ── 空状态 ── */
.empty-wrong {
  text-align: center;
  padding: 40px 20px;
  font-size: 15px; font-weight: 600;
  color: #10b981;
}

/* ── 过渡动画 ── */
.expand-enter-active,
.expand-leave-active {
  transition: all .3s ease;
  overflow: hidden;
}
.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
  margin-top: 0;
  margin-bottom: 0;
  padding-top: 0;
  padding-bottom: 0;
}
</style>

