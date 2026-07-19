<template>
  <div class="profile-view">
    <!-- 用户卡片 -->
    <div class="user-card">
      <div class="user-avatar">
        <span class="avatar-text">{{ userName.charAt(0).toUpperCase() }}</span>
      </div>
      <div class="user-info">
        <h2>{{ userName }}</h2>
        <p class="user-role">{{ userRoleText }}</p>
        <div class="user-meta">
          <span class="meta-item">
            <el-icon><Clock /></el-icon>
            注册于 {{ createdAt }}
          </span>
          <span class="meta-item" v-if="knowledgeProgress">
            <el-icon><DataAnalysis /></el-icon>
            学习进度 {{ knowledgeProgress.completion_rate }}%
          </span>
        </div>
      </div>
    </div>

    <!-- ═══ 双栏布局：左侧画像 + 右侧日历 ═══ -->
    <div class="profile-main-grid">
      <!-- 左侧：个人画像区域 -->
      <div class="profile-left-col">

    <!-- 无画像提示 -->
    <el-card v-if="!dynamicProfile && !profileData" class="empty-card" shadow="never">
      <div class="empty-content">
        <span class="empty-icon">📊</span>
        <h3>尚未完成学习画像</h3>
        <p>完成新手引导问卷，让 AI 为你定制个性化学习路径</p>
        <el-button type="primary" @click="$router.push('/onboarding')">开始画像分析</el-button>
      </div>
    </el-card>

    <!-- ═══════════ 六维动态画像（新格式） ═══════════ -->
    <template v-if="dynamicProfile">
      <!-- 1. Knowledge（知识画像） -->
      <el-card class="profile-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span class="card-title">🧠 知识画像</span>
            <el-tag size="small">{{ levelLabel(abilityLevel) }}</el-tag>
          </div>
        </template>
        <div class="profile-grid">
          <div class="profile-cell"><span class="cell-label">能力等级</span><span class="cell-value primary">{{ levelLabel(abilityLevel) }}</span></div>
          <div class="profile-cell"><span class="cell-label">学习风格</span><span class="cell-value success">{{ styleLabel(learningStyle) }}</span></div>
          <div class="profile-cell"><span class="cell-label">学习节奏</span><span class="cell-value warning">{{ learningRhythm }}</span></div>
          <div class="profile-cell"><span class="cell-label">成长趋势</span><span class="cell-value info">{{ trendLabel(masteryTrend) }}</span></div>
        </div>
        <!-- 知识掌握度雷达图 -->
        <div v-if="Object.keys(knowledgeMastery).length > 0" ref="radarChartRef" class="radar-chart-container"></div>
        <div v-else class="radar-empty-hint"><p>完成诊断测试或练习后，将展示知识掌握度分布</p></div>
        <!-- 强弱项 -->
        <div class="strength-weak-row" v-if="strengths.length || weaknesses.length">
          <div v-if="strengths.length" class="sw-col">
            <span class="sw-label strong">✅ 优势</span>
            <span v-for="s in strengths.slice(0,5)" :key="s" class="sw-chip strong">{{ displayName(s) }}</span>
          </div>
          <div v-if="weaknesses.length" class="sw-col">
            <span class="sw-label weak">⚠️ 待加强</span>
            <span v-for="w in weaknesses.slice(0,5)" :key="w" class="sw-chip weak">{{ displayName(w) }}</span>
          </div>
        </div>
      </el-card>

      <!-- 2. Behavior（行为画像） -->
      <el-card class="profile-card" shadow="never">
        <template #header><div class="card-header"><span class="card-title">📈 行为画像</span><span class="card-time">{{ generatedAt }}</span></div></template>
        <div class="behavior-grid">
          <div class="behavior-stat">
            <span class="bs-label">活跃度</span>
            <el-progress :percentage="Math.round(activityScore)" :color="activityScore > 70 ? '#22c55e' : '#f59e0b'" :stroke-width="10" />
          </div>
          <div class="behavior-stat">
            <span class="bs-label">专注度</span>
            <el-progress :percentage="Math.round(focusScore)" :color="focusScore > 70 ? '#c84c5a' : '#f59e0b'" :stroke-width="10" />
          </div>
          <div class="behavior-stat">
            <span class="bs-label">信心指数</span>
            <el-progress :percentage="Math.round(confidenceScore)" :color="'#10a37f'" :stroke-width="10" />
          </div>
          <div class="behavior-stat">
            <span class="bs-label">总学习时长</span>
            <span class="bs-value-text">{{ totalStudyHours }}h</span>
          </div>
        </div>
      </el-card>

      <!-- 3. Preference（资源偏好） -->
      <el-card v-if="Object.keys(resourcePreferences).length > 0" class="profile-card" shadow="never">
        <template #header><span class="card-title">🎯 资源偏好</span></template>
        <div class="pref-bars">
          <div v-for="(score, type) in resourcePreferences" :key="type" class="pref-bar-item">
            <div class="pref-bar-label"><span>{{ type }}</span><span>{{ Math.round(score) }}%</span></div>
            <div class="pref-bar-track"><div class="pref-bar-fill" :style="{ width: score + '%', background: score > 70 ? '#22c55e' : score > 40 ? '#f59e0b' : '#94a3b8' }"></div></div>
          </div>
        </div>
      </el-card>

      <!-- 4. Error（错误画像） -->
      <el-card v-if="errorPatterns.length || primaryErrorType" class="profile-card" shadow="never">
        <template #header><span class="card-title">🔍 错误分析</span></template>
        <div class="error-info">
          <p v-if="primaryErrorType"><strong>主要错误类型：</strong>{{ primaryErrorType }}</p>
          <div v-if="errorPatterns.length" class="error-patterns">
            <span v-for="ep in errorPatterns" :key="ep" class="error-chip">{{ ep }}</span>
          </div>
        </div>
      </el-card>

      <!-- 5. Growth（成长画像） -->
      <el-card class="profile-card" shadow="never">
        <template #header><span class="card-title">📊 成长趋势</span></template>
        <div class="growth-indicator">
          <span class="growth-trend-icon">{{ trendLabel(masteryTrend) }}</span>
          <span class="growth-desc" v-if="masteryTrend === 'accelerating'">学习进入加速期，继续保持！</span>
          <span class="growth-desc" v-else-if="masteryTrend === 'steady'">稳步前进中，可以适当增加挑战。</span>
          <span class="growth-desc" v-else-if="masteryTrend === 'plateauing'">进入平台期，尝试换一种学习方式。</span>
          <span class="growth-desc" v-else-if="masteryTrend === 'declining'">近期有所下降，建议回顾基础。</span>
          <span class="growth-desc" v-else>正在积累学习数据...</span>
        </div>
      </el-card>

      <!-- 6. Risk（风险画像） -->
      <el-card class="profile-card" shadow="never">
        <template #header><span class="card-title">⚠️ 学习风险</span></template>
        <div class="risk-indicator">
          <el-tag :type="riskLevel === 'high' ? 'danger' : riskLevel === 'medium' ? 'warning' : 'success'" size="large" effect="dark">
            {{ riskLabel(riskLevel) }}
          </el-tag>
          <ul v-if="riskFactors.length" class="risk-factors">
            <li v-for="rf in riskFactors" :key="rf">{{ rf }}</li>
          </ul>
          <p v-else class="risk-ok">✅ 目前未检测到明显学习风险</p>
        </div>
      </el-card>

      <!-- AI 策略建议 -->
      <el-card v-if="dailyStrategy" class="profile-card" shadow="never">
        <template #header><span class="card-title">💡 AI 学习策略</span></template>
        <p class="strategy-text">{{ dailyStrategy }}</p>
      </el-card>

      <!-- 学习路径预览（兼容旧格式） -->
      <el-card v-if="learningPath.length" class="path-card" shadow="never">
        <template #header><span class="card-title">🗺️ 推荐学习路径（{{ learningPath.length }} 步）</span></template>
        <div class="path-list">
          <div v-for="(step, idx) in learningPath.slice(0, 8)" :key="idx" class="path-item">
            <span class="step-num">{{ idx + 1 }}</span>
            <span class="step-topic">{{ stepTitle(step, idx) }}</span>
            <el-tag size="small">{{ step.bloom_level || 'learn' }}</el-tag>
          </div>
        </div>
      </el-card>
    </template>

    <!-- ═══════════ 旧格式画像（兼容降级） ═══════════ -->
    <template v-else-if="profileData">
      <el-card v-if="profileData.ai_profile?.ability_level" class="profile-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-tag type="primary" size="small">AI 学习画像</el-tag>
            <span class="card-time">生成于 {{ generatedAt }}</span>
          </div>
        </template>
        <div class="profile-grid">
          <div class="profile-cell"><span class="cell-label">能力等级</span><span class="cell-value primary">{{ profileData.ai_profile.ability_level }}</span></div>
          <div class="profile-cell"><span class="cell-label">学习风格</span><span class="cell-value success">{{ profileData.ai_profile.learning_style }}</span></div>
          <div class="profile-cell"><span class="cell-label">认知类型</span><span class="cell-value warning">{{ profileData.ai_profile.cognitive?.mbti_style || '—' }}</span></div>
          <div class="profile-cell"><span class="cell-label">费曼适配度</span><span class="cell-value info">{{ (profileData.ai_profile.cognitive?.feynman_adaptation * 100)?.toFixed(0) || '?' }}%</span></div>
        </div>
      </el-card>

      <el-card class="persona-card" shadow="never">
        <template #header><div class="card-header"><span class="card-title">🏷️ 学习人格</span><el-tag type="success" effect="dark" round>{{ personaType || '未测试' }}</el-tag></div></template>
        <div class="persona-tags"><span v-for="tag in personaTags" :key="tag" class="persona-tag"># {{ tag }}</span></div>
        <p class="persona-desc">{{ personaDescription }}</p>
      </el-card>

      <div ref="radarChartRef" class="radar-chart-container"></div>

      <el-card v-if="learningPath.length" class="path-card" shadow="never">
        <template #header><span class="card-title">🗺️ 学习路径（{{ learningPath.length }} 步）</span></template>
        <div class="path-list">
          <div v-for="(step, idx) in learningPath.slice(0, 8)" :key="idx" class="path-item">
            <span class="step-num">{{ idx + 1 }}</span>
            <span class="step-topic">{{ stepTitle(step, idx) }}</span>
            <el-tag size="small">{{ step.bloom_level || 'learn' }}</el-tag>
          </div>
        </div>
      </el-card>
    </template>

    <!-- 学习统计（放在左侧底部） -->
    <el-card v-if="knowledgeProgress" class="progress-card" shadow="never">
      <template #header>
        <span class="card-title">🎯 知识图谱学习进度</span>
      </template>
      <div class="progress-overview">
        <div class="progress-ring">
          <el-progress type="circle" :percentage="Number(knowledgeProgress?.completion_rate) || 0" :width="120" color="#10a37f" />
        </div>
        <div class="progress-details">
          <div class="pd-item completed">
            <span class="pd-value">{{ knowledgeProgress.completed }}</span>
            <span class="pd-label">已完成</span>
          </div>
          <div class="pd-item learning">
            <span class="pd-value">{{ knowledgeProgress.in_progress }}</span>
            <span class="pd-label">学习中</span>
          </div>
          <div class="pd-item available">
            <span class="pd-value">{{ knowledgeProgress.available }}</span>
            <span class="pd-label">待开始</span>
          </div>
        </div>
      </div>
    </el-card>
      </div><!-- /profile-left-col -->

      <!-- ═══ 右侧：学习日历 ═══ -->
      <div class="profile-right-col">
        <LearningCalendar />
      </div>
    </div><!-- /profile-main-grid -->
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useSessionStore } from '../../store/session'
import profileApi from '../../api/profile'
import knowledgeApi from '../../api/knowledge'
import behaviorApi from '../../api/behavior'
import { Clock, DataAnalysis } from '@element-plus/icons-vue'
import { getStorage, setStorage, STORAGE_KEYS } from '../../utils/storage'
import LearningCalendar from '../../components/LearningCalendar.vue'
import { getNodeNameById, aggregateToChapters } from '../../data/knowledgeMap'
import { formatKnowledgeName, stepKnowledgeTitle } from '../../utils/knowledgeNames'
import * as echarts from 'echarts'

const sessionStore = useSessionStore()

// ═══════════ 数据状态 ═══════════
const profileData = ref(null)       // 老格式（兼容）
const dynamicProfile = ref(null)    // 新格式：六维动态画像
const knowledgeProgress = ref(null)
const loading = ref(true)

const userName = computed(() => sessionStore.user?.username || '学生')
const userRoleText = computed(() => {
  if (personaType.value) return personaType.value
  if (abilityLevel.value) return levelLabel(abilityLevel.value) + ' · ' + styleLabel(learningStyle.value)
  if (learningStyle.value) return styleLabel(learningStyle.value)
  return '尚未完成学习画像'
})
const createdAt = computed(() => {
  const d = dynamicProfile.value?.updated_at || profileData.value?.generated_at
  return d ? new Date(d).toLocaleDateString('zh-CN') : '—'
})

// ═══════════ 六维画像字段 ═══════════
const abilityLevel = computed(() => dynamicProfile.value?.ability_level || '')
const learningStyle = computed(() => dynamicProfile.value?.learning_style || '')
const learningRhythm = computed(() => dynamicProfile.value?.learning_rhythm || '')
const confidenceScore = computed(() => dynamicProfile.value?.confidence_score || 0)
const activityScore = computed(() => dynamicProfile.value?.activity_score || 0)
const focusScore = computed(() => dynamicProfile.value?.focus_score || 0)
const riskLevel = computed(() => dynamicProfile.value?.risk_level || 'low')
const riskFactors = computed(() => dynamicProfile.value?.risk_factors || [])
const knowledgeMastery = computed(() => dynamicProfile.value?.knowledge_mastery || {})
const resourcePreferences = computed(() => dynamicProfile.value?.resource_preferences || {})
const errorPatterns = computed(() => dynamicProfile.value?.error_patterns || [])
const primaryErrorType = computed(() => dynamicProfile.value?.primary_error_type || '')
const strengths = computed(() => dynamicProfile.value?.strengths || [])
const weaknesses = computed(() => dynamicProfile.value?.weaknesses || [])
const dailyStrategy = computed(() => dynamicProfile.value?.daily_strategy || '')
const masteryTrend = computed(() => dynamicProfile.value?.mastery_trend || 'stable')
const totalStudyHours = computed(() => dynamicProfile.value?.total_study_hours || 0)
const summary = computed(() => dynamicProfile.value?.summary || '')

// 兼容旧格式
const personaType = computed(() => profileData.value?.persona_type || '')
const personaTags = computed(() => profileData.value?.persona_tags || [])
const personaDescription = computed(() => profileData.value?.persona_description || '')
const learningPath = computed(() => profileData.value?.learning_path || [])
const generatedAt = computed(() => createdAt.value)

const levelLabel = (l) => ({ beginner: '初学者', intermediate: '中等', advanced: '进阶', expert: '专家' }[l] || l)
const styleLabel = (s) => ({ visual: '视觉型', auditory: '听觉型', reading: '阅读型', hands_on: '实践型' }[s] || s)
const riskLabel = (r) => ({ low: '低风险', medium: '中风险', high: '高风险' }[r] || r)
const trendLabel = (t) => ({ improving: '📈 上升', accelerating: '🚀 快速提升', steady: '📊 稳定', plateauing: '➡️ 平台期', declining: '📉 下降', stable: '📊 稳定' }[t] || t)

// ═══════════ 知识图谱进度（全量统计） ═══════════
async function loadModeProgress() {
  try {
    const [progressRes, mapRes] = await Promise.all([
      knowledgeApi.getProgress().catch(() => null),
      knowledgeApi.getMap().catch(() => null),
    ])
    if (mapRes?.nodes) {
      let completed = 0, inProgress = 0, available = 0
      for (const node of mapRes.nodes) {
        const status = node.status || 'available'
        if (status === 'completed') completed++
        else if (status === 'in_progress' || status === 'learning') inProgress++
        else available++
      }
      const total = completed + inProgress + available
      knowledgeProgress.value = {
        total_nodes: total, completed, in_progress: inProgress, available,
        completion_rate: total > 0 ? Math.round((completed / total) * 100 * 10) / 10 : 0,
      }
    } else if (progressRes) {
      knowledgeProgress.value = progressRes
    }
  } catch (e) { console.warn('[Profile] 进度加载失败:', e) }
}

// ═══════════ 知识掌握度雷达图 ═══════════
const radarChartRef = ref(null)
let radarChartInstance = null

/** 将 ID 翻译为中文名，未命中原样返回 */
function displayName(id) {
  return formatKnowledgeName(id || getNodeNameById(id))
}

function stepTitle(step, idx) {
  return stepKnowledgeTitle(step, '步骤 ' + (idx + 1))
}

async function renderKnowledgeRadar() {
  if (!radarChartRef.value) return
  const mastery = knowledgeMastery.value
  if (!mastery || Object.keys(mastery).length === 0) return

  // 聚合成 8 章分数
  const chapterScores = aggregateToChapters(mastery)
  const chapterEntries = Object.entries(chapterScores)
  if (chapterEntries.length === 0) return

  const dimensions = chapterEntries.map(([name]) => ({ name, max: 100 }))
  const values = chapterEntries.map(([, score]) => score)

  if (!radarChartInstance) radarChartInstance = echarts.init(radarChartRef.value)
  radarChartInstance.setOption({
    tooltip: { trigger: 'item' },
    radar: {
      indicator: dimensions,
      shape: 'circle', radius: '75%', center: ['50%', '55%'],
      splitNumber: 4,
      axisName: { color: '#999', fontSize: 12 },
      splitLine: { lineStyle: { color: 'rgba(128,128,128,0.2)' } },
      splitArea: { areaStyle: { color: ['rgba(16,163,127,0.02)', 'rgba(16,163,127,0.06)'] } },
    },
    series: [{
      type: 'radar',
      data: [{ value: values, name: '知识掌握度', itemStyle: { color: '#10A37F' }, areaStyle: { color: 'rgba(16,163,127,0.2)' } }],
    }],
  }, true)
}

// ═══════════ 初始化 ═══════════
onMounted(async () => {
  loading.value = true

  // ★ 0. 优先从 session store 读取（避免网络延迟或 401）
  if (sessionStore.user?.profile_data) {
    const sp = sessionStore.user.profile_data
    if (sp.ability_level || sp.learning_style || sp.summary) {
      dynamicProfile.value = sp
    } else {
      profileData.value = sp
    }
  }
  // 同步 localStorage
  if (!dynamicProfile.value && !profileData.value) {
    const local = getStorage(STORAGE_KEYS.PROFILE)
    if (local) {
      if (local.ability_level || local.learning_style) {
        dynamicProfile.value = local
      } else {
        profileData.value = local
      }
    }
  }

  // 1. 加载新格式六维动态画像（API）
  if (!dynamicProfile.value) {
    try {
      const res = await behaviorApi.getDynamicProfile()
      if (res?.profile) {
        dynamicProfile.value = res.profile
      }
    } catch (e) { console.warn('[Profile] 动态画像加载失败:', e) }
  }

  // 2. 兼容：加载旧格式画像（API）
  if (!dynamicProfile.value) {
    try {
      const res = await profileApi.get()
      if (res?.profile_data) {
        profileData.value = res.profile_data
        setStorage(STORAGE_KEYS.PROFILE, res.profile_data)
      }
    } catch (e) { console.warn('[Profile] 画像加载失败:', e) }
  }

  // 3. 知识图谱进度
  await loadModeProgress()

  // 4. 渲染知识掌握雷达图
  await nextTick()
  renderKnowledgeRadar()

  loading.value = false
})
</script>

<style lang="scss" scoped>
.profile-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 24px 28px;
}

/* ── 双栏布局（画像 + 日历）各占一半 ── */
.profile-main-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;   /* 左右各占一半 */
  gap: 20px;
  align-items: start;

  @media (max-width: 1100px) {
    grid-template-columns: 1fr;
    .profile-right-col { order: -1; } // 日历在小屏时移到上方
  }
}
.profile-left-col {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0; /* 防止grid子项溢出 */
}

/* ── 用户卡片 ── */
.user-card {
  display: flex;
  align-items: center;
  gap: 24px;
  background: #fff;
  padding: 28px 32px;
  border-radius: 16px;
  border: 1px solid var(--border-color);
  box-shadow: 4px 4px 0px rgba(0,0,0,0.05);
}

.user-avatar {
  width: 72px;
  height: 72px;
  border-radius: 18px;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark));
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.avatar-text {
  font-size: 30px;
  font-weight: 800;
  color: #fff;
  font-family: 'Space Grotesk', sans-serif;
}

.user-info {
  flex: 1;
  h2 {
    margin: 0 0 4px;
    font-size: 22px;
    font-weight: 700;
  }
  .user-role {
    color: var(--color-primary);
    font-weight: 600;
    margin: 0 0 12px;
    font-size: 14px;
  }
}

.user-meta {
  display: flex;
  gap: 20px;
  .meta-item {
    font-size: 13px;
    color: var(--text-tertiary);
    display: flex;
    align-items: center;
    gap: 4px;
  }
}

/* ── 空状态 ── */
.empty-card {
  border-style: dashed;
  :deep(.el-card__body) {
    text-align: center;
    padding: 48px;
  }
  .empty-icon { font-size: 48px; }
  h3 { margin: 12px 0 8px; }
  p { color: var(--text-tertiary); margin-bottom: 20px; }
}

/* ── 通用卡片 ── */
.profile-card, .persona-card, .stats-card, .path-card, .progress-card {
  border-radius: 14px;
  border: 1px solid #eee;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.card-title {
  font-size: 15px;
  font-weight: 700;
}
.card-time {
  font-size: 12px;
  color: var(--text-tertiary);
}

/* ── 画像网格（保留备用） ── */
.profile-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

/* ★ 能力雷达图（自适应填充） */
.radar-chart-container {
  width: 100%;
  height: 300px;
  margin: 0 auto;
}
.radar-card {
  .el-card__body { padding: 16px; position: relative; }
}
.radar-empty-hint {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  z-index: 2;
  text-align: center;
  pointer-events: none;
}
.radar-empty-hint p {
  font-size: 13px;
  color: var(--text-tertiary);
  margin: 0;
  max-width: 200px;
  line-height: 1.6;
}
.profile-cell {
  background: #f8f9fb;
  border-radius: 12px;
  padding: 14px 12px;
  text-align: center;
  .cell-label {
    display: block;
    font-size: 11px;
    color: var(--text-tertiary);
    margin-bottom: 6px;
  }
  .cell-value {
    font-size: 15px;
    font-weight: 700;
    &.primary { color: #10a37f; }
    &.success { color: #22c55e; }
    &.warning { color: #E6A23C; }
    &.info { color: #409EFF; }
  }
}
.weakness-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(230,162,60,0.08);
  border-radius: 10px;
  font-size: 13px;
  color: var(--text-secondary);
  .hint-icon { font-size: 16px; }
  strong { color: #E6A23C; }
}

/* ── 人格标签 ── */
.persona-tags {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
  .persona-tag {
    padding: 4px 14px;
    background: #fbf2f3;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
    color: var(--color-primary);
  }
}
.persona-desc {
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0;
  font-size: 14px;
}

/* ── 能力分布 ── */
.stats-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.stat-item {
  .stat-head {
    display: flex;
    justify-content: space-between;
    margin-bottom: 6px;
    font-size: 13px;
    .stat-label { color: var(--text-secondary); }
    .stat-value { font-weight: 700; color: #333; }
  }
}

/* ── 学习路径 ── */
.path-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.path-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 8px;
  background: #f8f9fb;
  .step-num {
    width: 24px; height: 24px;
    border-radius: 50%;
    background: #10a37f;
    color: #fff;
    font-size: 12px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
  .step-topic { flex: 1; font-size: 13px; font-weight: 500; }
}
.more-steps {
  font-size: 12px;
  color: var(--text-tertiary);
  text-align: center;
  padding: 4px 0;
}

/* ── 学习进度 ── */
.progress-overview {
  display: flex;
  align-items: center;
  gap: 40px;
}
.progress-details {
  display: flex;
  gap: 32px;
}
.pd-item {
  text-align: center;
  .pd-value {
    display: block;
    font-size: 28px;
    font-weight: 800;
    .completed & { color: #22c55e; }
    .learning & { color: var(--color-primary); }
    .available & { color: #409EFF; }
  }
  .pd-label {
    font-size: 12px;
    color: var(--text-tertiary);
  }
}

/* ═══════════ 六维画像新样式 ═══════════ */
.behavior-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 16px 24px;
}
.behavior-stat {
  display: flex; flex-direction: column; gap: 6px;
  .bs-label { font-size: 13px; color: var(--text-secondary); font-weight: 600; }
  .bs-value-text { font-size: 24px; font-weight: 800; color: var(--text-main); }
}

.pref-bars { display: flex; flex-direction: column; gap: 10px; }
.pref-bar-item { }
.pref-bar-label { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px; }
.pref-bar-track { height: 8px; border-radius: 4px; background: var(--border-color); overflow: hidden; }
.pref-bar-fill { height: 100%; border-radius: 4px; transition: width 0.6s ease; }

.error-info {
  p { margin: 0 0 10px; font-size: 14px; color: var(--text-secondary); }
}
.error-patterns { display: flex; gap: 8px; flex-wrap: wrap; }
.error-chip {
  padding: 4px 12px; background: rgba(239,68,68,0.08); color: #ef4444;
  border-radius: 20px; font-size: 12px; font-weight: 600;
}

.growth-indicator {
  display: flex; align-items: center; gap: 16px;
  .growth-trend-icon { font-size: 20px; }
  .growth-desc { font-size: 14px; color: var(--text-secondary); }
}

.risk-indicator {
  display: flex; flex-direction: column; gap: 12px;
  .risk-factors { margin: 0; padding-left: 18px;
    li { font-size: 13px; color: var(--text-secondary); margin-bottom: 4px; }
  }
  .risk-ok { font-size: 14px; color: #22c55e; margin: 0; }
}

.strategy-text { font-size: 14px; color: var(--text-secondary); line-height: 1.6; margin: 0; }

.strength-weak-row { display: flex; gap: 20px; margin-top: 16px; }
.sw-col { flex: 1; display: flex; flex-direction: column; gap: 6px; }
.sw-label { font-size: 12px; font-weight: 700; margin-bottom: 4px;
  &.strong { color: #22c55e; }
  &.weak { color: #ef4444; }
}
.sw-chip {
  padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 500;
  &.strong { background: rgba(34,197,94,0.08); color: #16a34a; }
  &.weak { background: rgba(239,68,68,0.08); color: #dc2626; }
}
</style>





