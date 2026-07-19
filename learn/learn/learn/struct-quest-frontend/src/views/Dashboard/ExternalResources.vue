<template>
  <section class="external-section">
    <div class="external-header">
      <div class="external-header-left">
        <h2 class="external-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #d97982;">
            <circle cx="12" cy="12" r="10"/>
            <line x1="2" y1="12" x2="22" y2="12"/>
            <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
          </svg>
          外部精选资源
        </h2>
        <span class="external-subtitle">{{ profileSummary }}</span>
      </div>
      <button
        class="refresh-btn"
        :class="{ 'is-loading': isRefreshing }"
        :disabled="isRefreshing"
        @click="handleRefresh"
      >
        <svg v-if="!isRefreshing" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
        </svg>
        <svg v-else class="spin-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/>
          <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/>
          <line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/>
          <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"/>
        </svg>
        {{ refreshBtnText }}
      </button>
    </div>

    <!-- 错误提示 -->
    <div v-if="errorMsg" class="external-error-msg">{{ errorMsg }}</div>

    <!-- 骨架屏：首次加载中且无数据 -->
    <div v-if="isLoading && resources.length === 0" class="external-loading">
      <div class="loading-skeleton-grid">
        <div v-for="i in 4" :key="'skel-' + i" class="skeleton-card"></div>
      </div>
    </div>

    <!-- 资源卡片 -->
    <div v-else-if="resources.length > 0" class="external-grid">
      <a
        v-for="(item, idx) in resources"
        :key="item.id || idx"
        class="external-card animate-in"
        :class="{ 'is-broken': isBrokenUrl(item.url), 'is-placeholder': item.url === '#' }"
        :style="{ animationDelay: (0.06 * idx) + 's' }"
        :href="isBrokenUrl(item.url) ? undefined : item.url"
        :target="isBrokenUrl(item.url) ? undefined : '_blank'"
        rel="noopener noreferrer"
        @click.middle.stop
        @click.prevent="handleCardClick(item)"
      >
        <div class="external-card-top">
          <div class="external-card-cover" :style="{ background: sourceGradient(item.source) }">
            <img
              v-if="item.cover_image"
              :src="item.cover_image"
              :alt="item.title"
              class="cover-img"
              @error="$event.target.style.display = 'none'"
            />
            <span v-else class="cover-icon">{{ item.source_icon }}</span>
            <span class="external-card-source-badge" :style="{ background: item.source_color }">
              {{ item.source_label }}
            </span>
          </div>
          <div class="external-card-body">
            <h4 class="external-card-title">{{ item.title }}</h4>
            <p class="external-card-summary">{{ item.summary || item.ai_recommend_reason || '暂无摘要' }}</p>
            <div v-if="item.ai_recommend_reason" class="ai-reason">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#d97982" stroke-width="2"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
              <span>{{ item.ai_recommend_reason }}</span>
            </div>
            <div v-if="item.tags && item.tags.length > 0" class="external-tags">
              <span v-for="(tag, ti) in item.tags.slice(0, 3)" :key="ti" class="ext-tag">{{ tag }}</span>
            </div>
          </div>
        </div>
        <div class="external-card-footer">
          <span class="ext-author" v-if="item.author">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            {{ item.author }}
          </span>
          <span class="ext-difficulty" :class="'diff-' + (item.difficulty || 'intermediate')">
            {{ difficultyLabel(item.difficulty) }}
          </span>
          <span class="ext-heat" v-if="item.heat_score">
            🔥 {{ Math.round(item.heat_score) }}
          </span>
        </div>
      </a>
    </div>

    <!-- 空状态 -->
    <div v-else class="external-empty">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="1.5" opacity="0.6">
        <circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
      </svg>
      <p>暂无外部资源</p>
      <p class="empty-hint">点击「更新资源」按钮从全网抓取最新学习内容</p>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { http } from '../../utils/request'

// ══════════════════════ State ══════════════════════

// ★ 初始化时直接填充 mock 数据，用户立即看到内容
const resources = ref(getMockData())
const isLoading = ref(false)
const isRefreshing = ref(false)
const profileSummary = ref('由AI为你精选')
const errorMsg = ref('')

// 按钮文字
const refreshBtnText = computed(() => isRefreshing.value ? '正在抓取...' : '更新资源')

// ══════════════════════ Helpers ══════════════════════

/** 已知失效的URL模式（用于前端预检） */
const BROKEN_PATTERNS = [
  /zhihu\.com\/question\/\d+\/promise-aplus/,   // 知乎404页面
  /zhihu\.com\/question\/xxx\//,                 // 无效知乎链接
  /example\.com/,
  /^#$/,                                        // 空占位
  /^javascript:/,                               // 协议注入
]

/** 判断URL是否可能失效 */
function isBrokenUrl(url) {
  if (!url || url === '#' || url.startsWith('javascript:')) return true
  return BROKEN_PATTERNS.some(pattern => pattern.test(url))
}

/** 处理卡片点击（验证后跳转） */
function handleCardClick(item) {
  if (isBrokenUrl(item.url)) {
    errorMsg.value = '该链接暂时无法访问，已自动标记为失效'
    // 标记该条目为broken
    item._is_broken = true
    setTimeout(() => { errorMsg.value = '' }, 3000)
    return
  }
  window.open(item.url, '_blank', 'noopener,noreferrer')
}

var SOURCE_MAP = {
  csdn: 'linear-gradient(135deg, #fc5531, #ff7a45)',
  zhihu: 'linear-gradient(135deg, #0084ff, #4dabf5)',
  juejin: 'linear-gradient(135deg, #1e80ff, #74b4ff)',
  github: 'linear-gradient(135deg, #24292e, #6e7681)',
  bilibili: 'linear-gradient(135deg, #00a1d6, #3dc9e0)',
  douyin: 'linear-gradient(135deg, #fe2c55, #ff6a8a)',
}
function sourceGradient(source) {
  return SOURCE_MAP[source] || SOURCE_MAP.github
}

function difficultyLabel(diff) {
  var map = { beginner: '入门', intermediate: '进阶', advanced: '高级' }
  return map[diff] || '进阶'
}

// ══════════════════════ Data Fetching ════════════════════════

/** 从后端加载推荐数据 */
async function loadFromAPI() {
  isLoading.value = true
  try {
    var res = await http.get('/recommendations/resources?limit=8')
    var data = res.recommendations || []
    if (data.length > 0) {
      resources.value = data
      profileSummary.value = res.user_profile_summary || '由AI为你精选'
    }
  } catch (err) {
    console.warn('[ExternalResources] API加载失败，使用本地数据:', err)
  } finally {
    isLoading.value = false
  }
}

/** 手动刷新：触发爬虫 → 重新加载 */
async function handleRefresh() {
  if (isRefreshing.value) return
  isRefreshing.value = true
  errorMsg.value = ''

  try {
    // 步骤1: 触发后端爬虫（带超时控制和错误处理）
    console.log('[ExternalResources] 触发爬虫更新...')
    
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 15000)
    
    var refreshRes
    try {
      refreshRes = await http.post('/recommendations/refresh', { 
        keyword: '算法 数据结构 面试 前端',
        timeout: 15000,
        signal: controller.signal,
      }, { timeout: 16000 })
    } catch (fetchErr) {
      clearTimeout(timeoutId)
      if (fetchErr.name === 'AbortError') {
        throw { message: '请求超时，爬取时间过长，部分资源可能较慢' }
      }
      throw fetchErr
    } finally {
      clearTimeout(timeoutId)
    }
    
    console.log('[ExternalResources] 爬虫结果:', refreshRes)

    var crawled = (refreshRes && refreshRes.crawled_count) || 0
    var added = (refreshRes && refreshRes.new_count) || 0
    var msg = (refreshRes && refreshRes.message) || ''
    var failedUrls = (refreshRes && refreshRes.failed_urls) || []
    var inaccessible = (refreshRes && refreshRes.inaccessible_count) || 0

    // 步骤2: 重新拉取推荐列表（过滤掉无法访问的资源）
    try {
      var res = await http.get('/recommendations/resources?limit=12&filter_invalid=true')
      var data = res.recommendations || []
      
      // 前端二次过滤：排除已知无效/不可访问的链接
      const validData = data.filter(item => {
        if (item._is_broken || item._inaccessible) return false
        if (!item.url || item.url === '#' || item.url.startsWith('javascript:')) return false
        return true
      })
      
      if (validData.length > 0) {
        resources.value = validData
      }

      // 记录无法访问的链接数量
      if (failedUrls.length > 0 || inaccessible > 0) {
        console.warn(`[ExternalResources] ${inaccessible}个资源无法访问，${failedUrls.length}条链接失效`)
      }
    } catch (e) {
      console.warn('[ExternalResources] GET推荐失败:', e)
    }

    // 更新提示信息（更详细）
    if (added > 0) {
      profileSummary.value = '已新增 ' + added + ' 条资源'
    } else if (crawled > 0) {
      if (inaccessible > 0) {
        profileSummary.value = `抓取了 ${crawled} 条 (${inaccessible}条不可访问已自动过滤)`
      } else {
        profileSummary.value = `抓取了 ${crawled} 条（均为已有资源）`
      }
    } else if (msg) {
      profileSummary.value = msg || '数据已刷新'
    }
  } catch (err) {
    console.error('[ExternalResources] 刷新失败详情:', err)
    var detail = ''
    if (err) {
      detail = err.detail || err.message || JSON.stringify(err)
      // 更友好的错误提示
      if (err.name === 'AbortError' || err.code === 'ECONNABORTED') {
        detail = '⏱️ 请求超时，网络较慢或目标站点响应慢'
      } else if (err.message?.includes('fetch') || err.code === 'ECONNREFUSED' || err.code === 'ENOTFOUND') {
        detail = '🌐 网络连接失败，请检查网络后重试'
      } else if (err.code === 'ECONNRESET') {
        detail = '🔒 连接被重置，目标服务器拒绝连接'
      }
    }
    errorMsg.value = '更新失败: ' + detail
    setTimeout(function() { errorMsg.value = '' }, 5000)
  } finally {
    isRefreshing.value = false
  }
}

// ══════════════════════ Mock Data ════════════════════════

function getMockData() {
  return [
    {
      id: 1,
      title: '数据结构与算法完整教程 | B站百万播放',
      url: 'https://search.bilibili.com/all?keyword=%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84+%E7%AE%97%E6%B3%95',
      source: 'bilibili',
      source_label: 'B站',
      source_color: '#00a1d6',
      source_icon: '📺',
      summary: '从零开始学数据结构，涵盖数组、链表、树、图等核心内容，配合动画演示',
      tags: ['数据结构', '算法'],
      difficulty: 'beginner',
      heat_score: 95,
      author: '某UP主',
      ai_recommend_reason: '适合初学者系统学习'
    },
    {
      id: 2,
      title: '红黑树手撕代码：从原理到实现 | CSDN',
      url: 'https://www.csdn.net/nav/ai',
      source: 'csdn',
      source_label: 'CSDN',
      source_color: '#fc5531',
      source_icon: '📝',
      summary: '图文并茂讲解红黑树的插入删除旋转，附完整C++代码实现',
      tags: ['红黑树', '二叉树'],
      difficulty: 'advanced',
      heat_score: 78,
      author: '',
      ai_recommend_reason: '覆盖面试高频考点'
    },
    {
      id: 3,
      title: '动态规划经典题解合集 | 知乎高赞回答',
      url: 'https://www.zhihu.com/search?type=content&q=%E5%8A%A8%E6%80%81%E8%A7%84%E5%88%92',
      source: 'zhihu',
      source_label: '知乎',
      source_color: '#0084ff',
      source_icon: '💡',
      summary: '背包问题、最长递增子序列等DP经典题型详解，思路清晰易懂',
      tags: ['动态规划', '面试'],
      difficulty: 'intermediate',
      heat_score: 82,
      author: '',
      ai_recommend_reason: '帮你攻克动态规划'
    },
    {
      id: 4,
      title: 'visualgo-algorithm: 可视化算法学习仓库',
      url: 'https://github.com',
      source: 'github',
      source_label: 'GitHub',
      source_color: '#24292e',
      source_icon: '💻',
      summary: '交互式算法可视化，支持排序/搜索/图论/动态规划等30+种算法演示',
      tags: ['可视化', '开源'],
      difficulty: 'intermediate',
      heat_score: 88,
      author: 'algorithm-visualizer',
      ai_recommend_reason: '直观理解算法执行过程'
    },
    {
      id: 5,
      title: '前端面试必问：手写Promise/A+规范实现',
      url: 'https://juejin.cn/search?query=Promise',
      source: 'juejin',
      source_label: '掘金',
      source_color: '#1e80ff',
      source_icon: '⛏️',
      summary: '从零实现一个符合Promises/A+规范的Promise类，逐行注释',
      tags: ['前端', '面试', 'JavaScript'],
      difficulty: 'advanced',
      heat_score: 71,
      author: '掘金作者',
      ai_recommend_reason: '前端面试必备'
    },
    {
      id: 6,
      title: '3分钟搞懂快速排序 | 抖音热门技术视频',
      url: '#',
      source: 'douyin',
      source_label: '抖音',
      source_color: '#fe2c55',
      source_icon: '🎵',
      summary: '用动画演示快速排序的分区过程，通俗易懂',
      tags: ['排序', '算法'],
      difficulty: 'beginner',
      heat_score: 65,
      author: '',
      ai_recommend_reason: '碎片时间快速掌握'
    },
    {
      id: 7,
      title: 'LeetCode Hot100 题解 | CSDN精选专栏',
      url: 'https://www.csdn.net/nav/ai',
      source: 'csdn',
      source_label: 'CSDN',
      source_color: '#fc5531',
      source_icon: '📝',
      summary: 'LeetCode热题Top100详细解析，每道题都配有复杂度分析和多解法',
      tags: ['LeetCode', '刷题'],
      difficulty: 'intermediate',
      heat_score: 90,
      author: '',
      ai_recommend_reason: '刷题党必备'
    },
    {
      id: 8,
      title: 'B站最全计算机网络教程 | 从TCP/IP到HTTP',
      url: 'https://search.bilibili.com/all?keyword=%E8%AE%A1%E7%AE%97%E6%9C%BA%E7%BD%91%E7%BB%9C',
      source: 'bilibili',
      source_label: 'B站',
      source_color: '#00a1d6',
      source_icon: '📺',
      summary: '深入浅出讲解网络协议，配合Wireshark抓包实战演示',
      tags: ['网络', '计网'],
      difficulty: 'intermediate',
      heat_score: 85,
      author: '网络课代表',
      ai_recommend_reason: '补强网络知识'
    },
  ]
}

// 挂载后尝试从API增强（不影响已有的mock展示）
onMounted(() => {
  loadFromAPI()
})
</script>

<style lang="scss" scoped>
.external-section {
  margin-top: var(--space-8);
  animation: fadeInUp 0.4s ease both;
}

.external-error-msg {
  margin-bottom: var(--space-4);
  padding: 8px 14px;
  border-radius: var(--radius-sm);
  background: #fef2f2;
  color: #dc2626;
  font-size: 12px;
  border: 1px solid #fecaca;
}

.external-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: var(--space-5); gap: var(--space-4); flex-wrap: wrap;
}
.external-header-left {
  display: flex; align-items: baseline; gap: var(--space-3); flex-wrap: wrap;
}
.external-title {
  font-family: var(--font-display); font-size: var(--text-lg);
  font-weight: var(--font-bold); margin: 0; display: flex; align-items: center;
  gap: var(--space-2); color: var(--text-main);
}
.external-subtitle { font-size: var(--text-xs); color: var(--text-tertiary); }

.refresh-btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 7px 16px; border-radius: var(--radius-md);
  background: linear-gradient(135deg, #d97982, #e4a5aa); color: #fff; border: none;
  font-size: var(--text-xs); font-weight: var(--font-semibold); font-family: var(--font-body);
  cursor: pointer; transition: all 0.25s ease; white-space: nowrap;

  &:hover:not(:disabled) {
    box-shadow: 0 4px 14px rgba(217,121,130, 0.35);
    transform: translateY(-1px);
  }
  &:disabled { opacity: 0.7; cursor: not-allowed; }
  &.is-loading { background: linear-gradient(135deg, #a93546, #d97982); }
}

.external-grid {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: var(--space-4);
}
@media (max-width: 1024px) { .external-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 600px)   { .external-grid { grid-template-columns: 1fr; } }

.external-card {
  display: flex; flex-direction: column;
  background: var(--bg-color); border: 1px solid var(--border-color);
  border-radius: var(--radius-md); overflow: hidden;
  cursor: pointer; transition: all 0.28s ease;
  text-decoration: none; color: inherit;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
    border-color: rgba(217,121,130, 0.3);
    .external-card-cover { transform: scale(1.03); }
  }

  /* 失效链接状态 */
  &.is-broken, &.is-placeholder {
    cursor: not-allowed;
    opacity: 0.55;
    filter: grayscale(0.5);
    border-color: #fecaca;
    border-style: dashed;

    &:hover {
      transform: none !important;
      box-shadow: none !important;
      border-color: #fca5a5;
    }
  }

  /* 失效标记角标（伪元素） */
  &.is-broken::after,
  &.is-placeholder::after {
    content: '链接失效';
    position: absolute;
    top: 8px; left: 8px;
    padding: 2px 8px;
    border-radius: 6px;
    background: rgba(239,68,68,0.85);
    color: #fff;
    font-size: 9px;
    font-weight: 700;
    z-index: 2;
  }
}
.external-card-top { flex: 1; display: flex; flex-direction: column; }

.external-card-cover {
  height: 90px; position: relative;
  display: flex; align-items: center; justify-content: center;
  overflow: hidden; transition: transform 0.35s ease;

  .cover-img { width: 100%; height: 100%; object-fit: cover; }
  .cover-icon { font-size: 32px; filter: drop-shadow(0 2px 6px rgba(0,0,0,0.2)); }
}

.external-card-source-badge {
  position: absolute; top: 8px; right: 8px;
  padding: 2px 10px; border-radius: var(--radius-round);
  font-size: 10px; font-weight: var(--font-semibold); color: #fff;
  letter-spacing: 0.02em; backdrop-filter: blur(4px);
}

.external-card-body {
  padding: 12px 14px 10px; flex: 1; display: flex; flex-direction: column;
}
.external-card-title {
  font-size: var(--text-sm); font-weight: var(--font-semibold);
  color: var(--text-main); margin: 0 0 5px; line-height: 1.35;
  display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2;
  -webkit-box-orient: vertical; overflow: hidden;
}
.external-card-summary {
  font-size: 11px; color: var(--text-tertiary);
  margin: 0 0 6px; line-height: 1.45;
  display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2;
  -webkit-box-orient: vertical; overflow: hidden;
}
.ai-reason {
  display: flex; align-items: center; gap: 4px;
  font-size: 11px; color: #d97982;
  background: rgba(217,121,130, 0.06); padding: 3px 8px;
  border-radius: var(--radius-sm); width: fit-content; margin-bottom: 6px;

  span { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 180px; }
}
.external-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-top: auto; }
.ext-tag {
  font-size: 10px; padding: 1px 8px; border-radius: var(--radius-round);
  background: var(--bg-secondary); color: var(--text-secondary); border: 1px solid var(--border-light);
}
.external-card-footer {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 14px; border-top: 1px solid var(--border-light);
  font-size: 11px; color: var(--text-tertiary);

  > * { display: flex; align-items: center; gap: 3px; }
}
.ext-author {
  max-width: 120px; overflow: hidden; text-overflow: ellipsis;
  white-space: nowrap; flex: 1;
}
.ext-difficulty {
  font-weight: var(--font-medium); padding: 1px 7px; border-radius: var(--radius-round);

  &.diff-beginner   { background: #dcfce7; color: #16a34a; }
  &.diff-intermediate { background: #dbeafe; color: #2563eb; }
  &.diff-advanced   { background: #fef3c7; color: #d97706; }
}
.ext-heat { font-weight: var(--font-semibold); margin-left: auto; }

/* Skeleton */
.loading-skeleton-grid {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: var(--space-4);
}
.skeleton-card {
  height: 260px; border-radius: var(--radius-md);
  background: linear-gradient(90deg, var(--bg-secondary) 25%, var(--bg-color) 50%, var(--bg-secondary) 75%);
  background-size: 200% 100%; animation: shimmer 1.5s infinite;
}
@keyframes shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Empty */
.external-empty {
  text-align: center; padding: var(--space-12) var(--space-6); color: var(--text-tertiary);
  p { margin: 8px 0 0; font-size: var(--text-sm); }
  .empty-hint { font-size: var(--text-xs); opacity: 0.7; }
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}
.animate-in { animation: fadeInUp 0.5s ease both; }

@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.spin-icon { animation: spin 1s linear infinite; }
</style>

