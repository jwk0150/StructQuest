<template>
  <div class="digital-teacher-panel">
    <!-- 头部标题栏 -->
    <div class="panel-header">
      <div class="header-left">
        <span class="teacher-icon">🧑🏫</span>
        <div class="title-info">
          <span class="main-title">数字人老师</span>
          <span class="sub-title">{{ connectionStatus }}</span>
        </div>
      </div>
      <div class="header-right">
        <!-- 音色选择 -->
        <el-dropdown trigger="click" @command="handleVoiceChange">
          <el-button :icon="Microphone" size="small" circle />
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item 
                v-for="(voice, key) in voiceList" 
                :key="key"
                :command="key"
                :class="{ 'is-active': currentVoice === key }"
              >
                {{ voice.name }}
                <span style="color: #909399; font-size: 11px; margin-left: 4px;">
                  - {{ voice.desc }}
                </span>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        
        <!-- TTS 模式选择 -->
        <el-dropdown trigger="click" @command="handleTtsModeChange">
          <el-button size="small" class="mode-select-btn">
            {{ ttsModeLabel }}
            <el-icon><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="edge_tts" :class="{ 'is-active': ttsMode === 'edge_tts' }">
                🎵 Edge TTS（免费）
              </el-dropdown-item>
              <el-dropdown-item command="iflytek" :disabled="!iflytekAvailable" :class="{ 'is-active': ttsMode === 'iflytek' }">
                🧑‍🏫 讯飞虚拟人{{ iflytekAvailable ? '' : '（未配置）' }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <!-- 设置按钮 -->
        <el-button :icon="Setting" size="small" circle @click="showSettings = !showSettings" />
      </div>
    </div>

    <!-- 主内容区：左侧数字人 + 右侧对话 -->
    <div class="panel-body">
      <!-- 左侧：Live2D 数字人 -->
      <div class="teacher-visual">
        <DigitalTeacher
          ref="digitalTeacherRef"
          :is-speaking="isSpeaking"
          :volume="currentVolume"
          :voice-key="currentVoice"
          :avatar-key="currentAvatar"
          :is-processing="isTyping"
          :iflytek-config="iflytekConfig"
          @loaded="onTeacherLoaded"
          @update:voiceKey="handleVoiceChange"
          @update:avatarKey="val => currentAvatar = val"
        />
      </div>

      <!-- 右侧：对话区域 -->
      <div class="chat-section">
        <div ref="chatAreaRef" class="chat-area">
          <!-- 消息列表 -->
          <transition-group name="message" tag="div" class="messages-container">
            <div 
              v-for="msg in messages" 
              :key="msg.id" 
              :class="['message', msg.role]"
            >
              <div v-if="msg.role === 'ai'" class="avatar">🤖</div>
              <div class="bubble" v-html="renderContent(msg.content)"></div>
            </div>
            
            <!-- 正在输入指示器 -->
            <div v-if="isTyping" key="typing" class="message ai">
              <div class="avatar">🤖</div>
              <div class="bubble typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </transition-group>
        </div>
      </div>
    </div>

    <!-- 底部：输入区 + 语音控制 -->
    <div class="panel-footer">
      <!-- 语音播放控制条（有音频时显示） -->
      <div v-if="hasAudio || isSpeaking" class="audio-controls">
        <div class="audio-info">
          <el-button 
            :icon="isPlaying ? VideoPause : VideoPlay" 
            size="small"
            circle 
            @click="toggleAudioPlay"
          />
          <span class="audio-status">
            {{ audioStatusText }}
          </span>
        </div>
        <div class="progress-bar" v-if="isPlaying">
          <div class="progress-fill" :style="{ width: audioProgress + '%' }"></div>
        </div>
        <el-button 
          :icon="Close" 
          size="small" 
          text 
          type="info"
          @click="stopAudio"
        >
          停止
        </el-button>
      </div>

      <!-- 快捷标签 -->
      <div class="action-chips">
        <span 
          v-for="chip in quickChips" 
          :key="chip" 
          class="chip"
          @click="sendQuickMessage(chip)"
        >
          {{ chip }}
        </span>
      </div>

      <!-- 输入框 -->
      <div class="input-box">
        <el-input
          v-model="inputMsg"
          placeholder="向数字人老师提问..."
          @keyup.enter="sendMessage"
          :disabled="!isConnected || isTyping"
        />
        <el-button 
          type="primary" 
          :icon="Position" 
          :loading="isTyping"
          circle 
          @click="sendMessage"
        />
      </div>
    </div>

    <!-- 隐藏的音频元素 -->
    <audio 
      ref="audioPlayerRef"
      @timeupdate="onAudioTimeUpdate"
      @ended="onAudioEnded"
      @play="onAudioPlay"
      @pause="onAudioPause"
    ></audio>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, nextTick, computed } from 'vue'
import { Position, Microphone, Setting, Close, VideoPlay, VideoPause, ArrowDown } from '@element-plus/icons-vue'
import DigitalTeacher from '../DigitalTeacher/index.vue'
import { marked } from 'marked'

// ==================== 响应式状态 ====================

const inputMsg = ref('')
const messages = ref([])           // 消息列表
const isConnected = ref(false)     // WebSocket 连接状态
const isTyping = ref(false)        // AI 是否正在生成回复
const isSpeaking = ref(false)      // 数字人是否正在说话（语音播放中）
const isPlaying = ref(false)       // 音频是否正在播放
const hasAudio = ref(false)        // 是否有可用的音频数据
const currentVolume = ref(0)       // 当前音量（用于口型同步）
const audioProgress = ref(0)       // 音频播放进度
const showSettings = ref(false)
const currentVoice = ref('xiaoxiao') // 当前选择的音色
const currentAvatar = ref('teacher_female') // 当前选择的数字人形象
const enableTTS = ref(true)         // 是否启用 TTS
const iflytekAvailable = ref(false) // 讯飞虚拟人是否可用
const iflytekConfig = ref({})      // 讯飞配置（从后端获取）
const ttsMode = ref('iflytek')     // 当前 TTS 模式: iflytek / edge_tts

// Refs
const chatAreaRef = ref(null)
const digitalTeacherRef = ref(null)
const audioPlayerRef = ref(null)

// 可用音色列表
const voiceList = reactive({
  xiaoxiao: { name: '温柔女声', desc: '温柔亲切' },
  yunxi: { name: '阳光男声', desc: '阳光开朗' },
  xiaoyi: { name: '知性女声', desc: '知性专业' },
  yunyang: { name: '沉稳男声', desc: '沉稳厚重' },
  xiaobei: { name: '活泼女声', desc: '活泼可爱' },
  xiaozhen: { name: '亲和女声', desc: '自然亲切' }
})

// 快捷提问标签
const quickChips = [
  '解释一下这个概念',
  '给我举个例子',
  '用通俗的话说',
  '这和XX有什么区别',
  '帮我总结一下'
]

// 计算属性
const connectionStatus = computed(() => {
  return isConnected.value ? '已连接 🟢' : '未连接 🔴'
})

const ttsModeLabel = computed(() => {
  const labels = {
    edge_tts: '🎵 Edge TTS',
    iflytek: '🧑‍🏫 讯飞虚拟人',
  }
  return labels[ttsMode.value] || '🧑‍🏫 讯飞'
})

const audioStatusText = computed(() => {
  if (isSpeaking.value && isPlaying.value) {
    return '正在讲解...'
  }
  if (hasAudio.value && !isPlaying.value) {
    return '讲解完成'
  }
  return ''
})

// WebSocket 实例
let ws = null

// 消息 ID 计数器
let messageIdCounter = 0

// ==================== 方法 ====================

/**
 * 渲染消息内容（支持 Markdown）
 * 修复了 marked 可能输出乱码的问题，添加字符集校验
 */
function renderContent(content) {
  if (!content) return ''
  // ★ 过滤掉明显的乱码内容（全是非打印字符或重复乱码的模式）
  if (/^[\x00-\x1f\x7f-\x9f\u200b-\u200f\u2028-\u202f\uFEFF]+$/.test(content.trim())) {
    return '⚠️ 内容不可显示（编码异常）'
  }
  try {
    // 设置 marked 选项，防止特殊字符被误解
    const result = marked.parseInline 
      ? marked.parseInline(content) 
      : marked(content)
    // 额外校验：如果渲染后全是 HTML 实体乱码
    if (result && result.replace(/<[^>]*>/g, '').trim().length === 0 && content.trim().length > 10) {
      // marked 把正常中文误解析了，直接用纯文本
      return escapeHtml(content)
    }
    return result
  } catch (e) {
    console.warn('[renderContent] marked 渲染失败:', e.message)
    return escapeHtml(content)
  }
}

/**
 * 简单 HTML 转义（防止 XSS 和乱码）
 */
function escapeHtml(text) {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

/**
 * 滚动聊天区域到底部
 */
async function scrollToBottom() {
  await nextTick()
  if (chatAreaRef.value) {
    chatAreaRef.value.scrollTop = chatAreaRef.value.scrollHeight
  }
}

/**
 * 发送消息
 */
function sendMessage() {
  const msg = inputMsg.value.trim()
  if (!msg || !isConnected.value || isTyping.value) return
  
  // 添加用户消息到列表
  messages.value.push({
    id: ++messageIdCounter,
    role: 'user',
    content: msg,
    timestamp: Date.now()
  })
  
  inputMsg.value = ''
  scrollToBottom()
  
  // 通过 WebSocket 发送给后端
  sendToBackend(msg)
}

/**
 * 发送快捷消息
 */
function sendQuickMessage(chip) {
  inputMsg.value = chip
  sendMessage()
}

/**
 * 通过 WebSocket 发送消息到后端
 * 修复：过滤掉错误提示、乱码等无效历史消息
 */
function sendToBackend(text) {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    console.error('[WebSocket] 未连接')
    addSystemMessage('⚠️ 连接未就绪，请等待重新连接...')
    return
  }
  
  // ★ 清理历史消息：过滤掉以 ⚠️ 开头的错误消息和空内容
  const cleanHistory = messages.value
    .filter(m => m.id <= messageIdCounter - 1)
    .filter(m => m.content && !m.content.startsWith('⚠️'))
    .map(m => ({
      role: m.role === 'user' ? 'user' : 'assistant',
      content: m.content
    }))
  
  // 构建发送的消息格式
  const payload = {
    messages: [
      ...cleanHistory,
      { role: 'user', content: text }
    ],
    provider: 'openai',
    voice: currentVoice.value,
    avatar: currentAvatar.value,
    enable_tts: enableTTS.value,
    tts_mode: ttsMode.value
  }
  
  console.log('[WebSocket] 发送消息，历史长度:', cleanHistory.length)
  
  // 标记 AI 开始生成
  isTyping.value = true
  
  ws.send(JSON.stringify(payload))
}

/**
 * 处理后端返回的 chunk 数据
 * 修复：增加内容校验、调试日志，防止乱码累积
 */
function handleChunk(data) {
  const chunk = data.content || ''
  
  // ★ 调试日志（帮助排查乱码来源）
  console.log('[AI·chunk]', JSON.stringify(chunk).slice(0, 80))
  
  // ★ 严格校验：过滤异常 chunk
  if (!chunk) return  // 空 chunk 跳过
  if (typeof chunk !== 'string') {
    console.warn('[AI·chunk] 非字符串 chunk:', typeof chunk, chunk)
    return
  }
  
  // 找到或创建最后一条 AI 消息
  let lastAiMsg = [...messages.value].reverse().find(m => m.role === 'ai')
  
  if (!lastAiMsg || lastAiMsg.content === '⚠️ AI 服务暂不可用，请稍后重试。') {
    // 清掉之前的错误提示，重新开始
    lastAiMsg = {
      id: ++messageIdCounter,
      role: 'ai',
      content: '',
      timestamp: Date.now()
    }
    messages.value.push(lastAiMsg)
  }
  
  lastAiMsg.content += chunk
  scrollToBottom()
}

/**
 * 处理后端流式输出结束
 */
function handleDone(data) {
  isTyping.value = false
  console.log('[AI·done] 回复完成',
    data?.full_content ? `(${data.full_content.length} 字符)` : '(无内容)')
  
  // ★ 检查是否有有效回复
  const lastAiMsg = [...messages.value].reverse().find(m => m.role === 'ai')
  if (lastAiMsg && (!lastAiMsg.content || lastAiMsg.content.trim() === '')) {
    lastAiMsg.content = '⚠️ 数字人老师暂时没有回复，请检查网络后重试。'
    console.warn('[AI·done] LLM 返回了空内容，可能 API 异常')
  }
  
  scrollToBottom()

  // 讯飞模式：发送完整文本给 iframe 播放器
  if (ttsMode.value === 'iflytek' && data?.full_content && digitalTeacherRef.value) {
    digitalTeacherRef.value.speakText(data.full_content)
  }
}

/**
 * 处理 TTS 语音开始生成
 */
function handleTtsStart() {
  console.log('[TTS] 开始合成语音...')
}

/**
 * 处理 TTS 音频数据返回
 * 兼容两种格式: audio_url (文件路径) / audio_base64 (base64字符串)
 */
function handleTtsAudio(data) {
  console.log('[TTS] 收到音频数据', data)

  let audioSrc = ''

  // 优先使用 URL 路径（后端当前格式）
  if (data.audio_url) {
    // dev server 已代理 /static → /api 到 localhost:8008，直接用相对路径即可！
    if (data.audio_url.startsWith('http')) {
      audioSrc = data.audio_url
    } else if (data.audio_url.startsWith('/static') || data.audio_url.startsWith('/api')) {
      // Vite dev server proxy 会自动转发到后端
      audioSrc = data.audio_url
    } else {
      // 其他情况拼接完整地址
      const apiBase = import.meta.env.VITE_API_BASE_URL || ''
      audioSrc = apiBase ? `${apiBase}${data.audio_url}` : data.audio_url
    }
    console.log('[TTS] 使用 URL 模式:', audioSrc)
  }
  // 兼容旧版 base64 格式
  else if (data.audio_base64) {
    audioSrc = `data:audio/mp3;base64,${data.audio_base64}`
    console.log('[TTS] 使用 Base64 模式')
  }

  if (!audioSrc) {
    console.warn('[TTS] 未收到有效音频数据', data)
    return
  }

  if (audioPlayerRef.value) {
    audioPlayerRef.value.src = audioSrc
    audioPlayerRef.value.load()  // 重新加载新源
    hasAudio.value = true

    // 自动播放
    playAudio()
  }

  // ★ 同时转发给 DigitalTeacher 组件显示
  if (digitalTeacherRef.value && digitalTeacherRef.value.handleWsMessage) {
    digitalTeacherRef.value.handleWsMessage(data)
  }
}

/**
 * 处理 TTS 错误
 */
function handleTtsError(data) {
  console.warn('[TTS] 错误:', data.message)
  // 即使 TTS 失败，也不影响文字展示
}

/**
 * 播放音频
 */
function playAudio() {
  if (!audioPlayerRef.value || !hasAudio.value) return
  
  audioPlayerRef.value.play().catch(e => {
    console.warn('[Audio] 自动播放被浏览器阻止:', e)
  })
}

/**
 * 切换播放/暂停
 */
function toggleAudioPlay() {
  if (!audioPlayerRef.value) return
  
  if (isPlaying.value) {
    audioPlayerRef.value.pause()
  } else {
    playAudio()
  }
}

/**
 * 停止音频
 */
function stopAudio() {
  if (audioPlayerRef.value) {
    audioPlayerRef.value.pause()
    audioPlayerRef.value.currentTime = 0
  }
  isPlaying.value = false
  isSpeaking.value = false
  hasAudio.value = false
  currentVolume.value = 0
}

// 音频事件处理
function onAudioTimeUpdate() {
  if (!audioPlayerRef.value) return
  const progress = (audioPlayerRef.value.currentTime / audioPlayerRef.value.duration) * 100
  audioProgress.value = progress || 0
  
  // 更新音量（用于口型同步）
  updateVolumeFromAudio()
}

function onAudioEnded() {
  isPlaying.value = false
  isSpeaking.value = false
  currentVolume.value = 0
  console.log('[Audio] 播放完毕')
}

function onAudioPlay() {
  isPlaying.value = true
  isSpeaking.value = true
  startVolumeMonitor()
  console.log('[Audio] 开始播放')
}

function onAudioPause() {
  isPlaying.value = false
  stopVolumeMonitor()
}

/**
 * 从 AudioContext 获取实时音量（用于口型同步）
 */
let volumeMonitorInterval = null

function startVolumeMonitor() {
  if (volumeMonitorInterval) clearInterval(volumeMonitorInterval)
  
  // 尝试使用 WebAudio API 获取更精确的音量
  try {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)()
    const source = audioCtx.createMediaElementSource(audioPlayerRef.value)
    const analyser = audioCtx.createAnalyser()
    source.connect(analyser)
    analyser.connect(audioCtx.destination)
    
    volumeMonitorInterval = setInterval(() => {
      const dataArray = new Uint8Array(analyser.frequencyBinCount)
      analyser.getByteFrequencyData(dataArray)
      
      const sum = dataArray.reduce((a, b) => a + b, 0)
      const avg = sum / dataArray.length
      currentVolume.value = Math.min(1, avg / 128)
    }, 50)  // 每 50ms 更新一次
  } catch (e) {
    // WebAudio 不可用时，使用简化版本
    console.warn('[Audio] WebAudio 不可用，使用简化版音量监测')
    volumeMonitorInterval = setInterval(() => {
      // 基于播放进度模拟简单的音量变化
      currentVolume.value = isPlaying.value ? 0.6 : 0
    }, 100)
  }
}

function stopVolumeMonitor() {
  if (volumeMonitorInterval) {
    clearInterval(volumeMonitorInterval)
    volumeMonitorInterval = null
  }
  currentVolume.value = 0
}

/**
 * 简化版音量更新（当 WebAudio 不可用时）
 */
function updateVolumeFromAudio() {
  // 如果已经通过 WebAudio 监测了，这里就不重复处理
  if (volumeMonitorInterval) return
  
  // 简单地根据播放状态设置音量
  currentVolume.value = isPlaying.value ? 0.5 : 0
}

/**
 * 切换音色
 */
function handleVoiceChange(voiceKey) {
  currentVoice.value = voiceKey
  console.log(`[Voice] → ${voiceList[voiceKey]?.name || voiceKey}`)
}

/**
 * 切换 TTS/数字人 模式
 */
function handleTtsModeChange(mode) {
  ttsMode.value = mode
  console.log(`[TTS-Mode] -> ${mode}`)
  // 激活/停用讯飞 iframe 播放器
  if (mode === 'iflytek' && digitalTeacherRef.value) {
    digitalTeacherRef.value.startIflytek()
  } else if (digitalTeacherRef.value) {
    digitalTeacherRef.value.stopIflytek()
  }
}

/**
 * 切换数字人形象
 */
function handleAvatarChange(avatarKey) {
  currentAvatar.value = avatarKey
  console.log(`[Avatar] → ${avatarKey}`)
}

/**
 * Live2D 模型加载完成回调
 */
function onTeacherLoaded(success) {
  if (success) {
    console.log('[DigitalTeacher] 数字人模型加载成功')
  }
}

// ==================== WebSocket 连接管理 ====================

function connectWebSocket() {
  // 构建 WebSocket URL（使用当前页面的 host + 后端端口）
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.hostname}:8008/ws/chat`
  
  console.log(`[WebSocket] 连接到: ${wsUrl}`)
  
  ws = new WebSocket(wsUrl)
  
  ws.onopen = () => {
    console.log('[WebSocket] 已连接')
    isConnected.value = true
    
    // ★ 只在首次连接时发送欢迎消息
    if (messages.value.length === 0) {
      addSystemMessage('你好！我是你的数字人老师，有什么可以帮助你的吗？')
    }
  }
  
  ws.onmessage = async (event) => {
    try {
      const data = JSON.parse(event.data)
      
      // ★ 兼容旧格式 error（无 type 字段）
      if (data.error && !data.type) {
        console.error('[Backend] 错误:', data.error)
        isTyping.value = false
        addSystemMessage('⚠️ ' + data.error)
        return
      }
      
      switch (data.type) {
        case 'chunk':
          handleChunk(data)
          break
        case 'done':
          handleDone(data)
          break
        case 'failover':
          // ★ 新增：处理故障切换消息
          console.log('[AI·failover] 服务切换:', data.message)
          // 在当前 AI 消息中添加提示（非阻塞）
          const failoverHint = '\n\n*(服务切换中...)*'
          const lastMsg = [...messages.value].reverse().find(m => m.role === 'ai')
          if (lastMsg && !lastMsg.content.includes('服务切换')) {
            lastMsg.content += failoverHint
          }
          scrollToBottom()
          break
        case 'tts_start':
          handleTtsStart()
          if (digitalTeacherRef.value?.handleWsMessage) {
            digitalTeacherRef.value.handleWsMessage(data)
          }
          break
        case 'tts_audio':
          handleTtsAudio(data)
          break
        case 'tts_fallback':
        case 'tts_error':
          handleTtsError(data)
          if (digitalTeacherRef.value?.handleWsMessage) {
            digitalTeacherRef.value.handleWsMessage(data)
          }
          break
        case 'error':
          // ★ 增强错误处理
          console.error('[Backend] LLM 错误:', data.message, data)
          isTyping.value = false
          // 在聊天中显示错误提示
          addSystemMessage('⚠️ AI 服务异常: ' + (data.message || '未知错误'))
          break
        default:
          console.log('[WebSocket] 未知消息类型:', data.type, data)
      }
    } catch (e) {
      console.error('[WebSocket] 解析消息失败:', e, '原始数据:', event.data?.slice(0, 200))
    }
  }
  
  ws.onerror = (err) => {
    console.error('[WebSocket] Error:', err)
    isConnected.value = false
  }
  
  ws.onclose = () => {
    console.log('[WebSocket] 断开连接')
    isConnected.value = false
    
    // 自动重连（3秒后尝试）
    setTimeout(() => {
      if (!isConnected.value) {
        connectWebSocket()
      }
    }, 3000)
  }
}

/**
 * 添加系统/AI 欢迎消息
 */
function addSystemMessage(content) {
  messages.value.push({
    id: ++messageIdCounter,
    role: 'ai',
    content: content,
    timestamp: Date.now()
  })
  scrollToBottom()
}

// ==================== 生命周期 ====================

onMounted(() => {
  // 建立 WebSocket 连接
  connectWebSocket()

  // ★ LLM 健康检查（快速发现 API 配置问题）
  fetch('/api/health')
    .then(r => r.json())
    .then(data => {
      console.log('[LLM·Health] 后端健康检查通过:', data)
      if (data.llm_ok === false) {
        console.warn('[LLM·Health] LLM 服务不可用!', data)
        addSystemMessage('⚠️ AI 推理服务暂不可用，请检查 API 配置后重启后端。')
      }
    })
    .catch(err => {
      console.error('[LLM·Health] 健康检查失败，后端可能未启动:', err)
    })

  // 检测讯飞虚拟人服务是否可用
  fetch('/api/iflytek/status')
    .then(r => r.json())
    .then(data => {
      iflytekAvailable.value = data.available === true
      if (iflytekAvailable.value) {
        console.log('[iFlytek-VH] [OK] 可用')
        if (data.config) {
          iflytekConfig.value = data.config
        }
        // 讯飞可用，默认使用讯飞模式
        handleTtsModeChange('iflytek')
      } else {
        console.log('[iFlytek-VH] [WARN] 未配置')
        ttsMode.value = 'edge_tts'
      }
    })
    .catch(() => {
      console.log('[iFlytek-VH] [INFO] 状态检测失败')
      iflytekAvailable.value = false
      ttsMode.value = 'edge_tts'
    })
})

onBeforeUnmount(() => {
  // 清理资源
  stopVolumeMonitor()
  stopAudio()
  
  if (ws) {
    ws.close()
    ws = null
  }
})
</script>

<style lang="scss" scoped>
.digital-teacher-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-height: calc(100vh - 140px);
  min-height: 480px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  border: 1px solid var(--border-color);

  /* 头部 */
  .panel-header {
    padding: 12px 16px;
    background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
    color: #fff;
    display: flex;
    justify-content: space-between;
    align-items: center;

    .header-left {
      display: flex;
      align-items: center;
      gap: 10px;

      .teacher-icon {
        font-size: 24px;
      }

      .title-info {
        display: flex;
        flex-direction: column;

        .main-title {
          font-weight: bold;
          font-size: 15px;
        }

        .sub-title {
          font-size: 11px;
          opacity: 0.85;
        }
      }
    }

    .header-right {
      display: flex;
      align-items: center;
      gap: 8px;

      :deep(.el-button) {
        background: rgba(255, 255, 255, 0.2);
        border-color: transparent;
        color: #fff;

        &:hover {
          background: rgba(255, 255, 255, 0.3);
        }
      }

      .mode-select-btn {
        font-size: 11px;
        padding: 2px 10px;
        height: auto;
        border-radius: 12px;
        background: rgba(var(--color-primary-rgb), 0.35);
        &:hover { background: rgba(var(--color-primary-rgb), 0.5); }
      }
    }
  }

  /* 主内容区：左右布局 — 数字人作为侧边预览 */
  .panel-body {
    flex: 1;
    display: flex;
    overflow: hidden;
    min-height: 0;

    /* 左侧数字人 — 超紧凑侧边栏 */
    .teacher-visual {
      width: 140px;
      min-width: 140px;
      max-width: 140px;
      padding: 6px;
      background: linear-gradient(180deg, #f8f9ff 0%, #fff 100%);
      border-right: 1px solid var(--border-color);
      display: flex;
      align-items: stretch;
      flex-shrink: 0; /* 不被压缩 */
      overflow-y: auto;
    }

    /* 右侧对话区 — 主区域 */
    .chat-section {
      flex: 1;
      display: flex;
      flex-direction: column;
      min-width: 0;

      .chat-area {
        flex: 1;
        overflow-y: auto;
        padding: 16px;
        background: var(--bg-color, #f5f7fa);

        &::-webkit-scrollbar {
          width: 6px;
        }

        &::-webkit-scrollbar-thumb {
          background-color: #dcdfe6;
          border-radius: 3px;
        }

        .messages-container {
          display: flex;
          flex-direction: column;
          gap: 14px;
        }

        /* 消息样式 */
        .message {
          display: flex;
          gap: 10px;
          
          &.ai {
            .avatar {
              width: 32px;
              height: 32px;
              border-radius: 50%;
              background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
              display: flex;
              align-items: center;
              justify-content: center;
              font-size: 18px;
              flex-shrink: 0;
            }

            .bubble {
              max-width: 85%;
              padding: 12px 16px;
              background: #fff;
              border-radius: 4px 16px 16px 16px;
              font-size: 14px;
              line-height: 1.6;
              color: #303133;
              box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
              border: 1px solid #ebeef5;
              
              // Markdown 内容样式
              :deep(p) {
                margin: 0 0 6px 0;
                
                &:last-child {
                  margin-bottom: 0;
                }
              }
              
              :deep(code) {
                background: #f5f7fa;
                padding: 2px 6px;
                border-radius: 4px;
                font-family: 'Monaco', 'Menlo', monospace;
                font-size: 13px;
                color: #e83e8c;
              }
              
              :deep(pre) {
                background: #282c34;
                color: #abb2bf;
                padding: 12px;
                border-radius: 8px;
                overflow-x: auto;
                margin: 8px 0;
                
                code {
                  background: transparent;
                  color: inherit;
                  padding: 0;
                }
              }
            }
          }

          &.user {
            justify-content: flex-end;

            .bubble {
              max-width: 80%;
              padding: 10px 16px;
              background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
              color: #fff;
              border-radius: 16px 4px 16px 16px;
              font-size: 14px;
              line-height: 1.5;
              box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
            }
          }
        }

        /* 打字动画 */
        .typing-indicator {
          display: flex;
          gap: 4px;
          padding: 16px 20px !important;

          span {
            width: 8px;
            height: 8px;
            background: #c0c4cc;
            border-radius: 50%;
            animation: typing 1.4s ease-in-out infinite;

            &:nth-child(2) {
              animation-delay: 0.2s;
            }

            &:nth-child(3) {
              animation-delay: 0.4s;
            }
          }
        }
      }
    }
  }

  /* 底部 */
  .panel-footer {
    border-top: 1px solid var(--border-color);
    background: #fff;

    /* 语音控制条 */
    .audio-controls {
      padding: 8px 16px;
      background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
      display: flex;
      align-items: center;
      gap: 12px;

      .audio-info {
        display: flex;
        align-items: center;
        gap: 8px;

        :deep(.el-button) {
          background: rgba(255, 255, 255, 0.9);
          border-color: transparent;
          color: #f5576c;

          &:hover {
            background: #fff;
          }
        }

        .audio-status {
          color: #fff;
          font-size: 13px;
          font-weight: 500;
        }
      }

      .progress-bar {
        flex: 1;
        height: 4px;
        background: rgba(255, 255, 255, 0.3);
        border-radius: 2px;
        overflow: hidden;

        .progress-fill {
          height: 100%;
          background: #fff;
          border-radius: 2px;
          transition: width 0.3s ease;
        }
      }

      :deep(.el-button--text) {
        color: rgba(255, 255, 255, 0.9);

        &:hover {
          color: #fff;
        }
      }
    }

    /* 快捷标签 */
    .action-chips {
      padding: 8px 16px;
      display: flex;
      gap: 8px;
      overflow-x: auto;
      border-bottom: 1px solid #f0f0f0;

      &::-webkit-scrollbar {
        height: 0;
      }

      .chip {
        white-space: nowrap;
        background: #f2f6fc;
        padding: 5px 12px;
        border-radius: 14px;
        font-size: 12px;
        color: var(--text-secondary);
        cursor: pointer;
        border: 1px solid var(--border-color);
        transition: all 0.2s ease;

        &:hover {
          background: linear-gradient(135deg, rgba(var(--color-primary-rgb), 0.08) 0%, rgba(var(--color-primary-rgb), 0.08) 100%);
          color: var(--color-primary);
          border-color: rgba(var(--color-primary-rgb), 0.19);
        }
      }
    }

    /* 输入框 */
    .input-box {
      padding: 12px 16px;
      display: flex;
      gap: 8px;

      :deep(.el-input__wrapper) {
        border-radius: 22px;
        background: #f5f7fa;
        box-shadow: none !important;
        border: 2px solid var(--border-color);

        &.is-focus {
          border-color: var(--color-primary);
        }
      }

      :deep(.el-button--primary) {
        background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
        border-color: transparent;
        border-radius: 50%;

        &:hover {
          opacity: 0.9;
        }
      }
    }
  }
}

/* 消息过渡动画 */
.message-enter-active {
  animation: messageIn 0.3s ease-out;
}

@keyframes messageIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  30% {
    transform: translateY(-4px);
    opacity: 1;
  }
}
</style>
