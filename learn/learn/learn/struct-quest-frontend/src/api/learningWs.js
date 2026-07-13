/**
 * 学习系统 WebSocket 客户端
 *
 * 连接 /api/learning/ws/session，实时接收 Agent 流式推送：
 *   status → agent_log → resource → step_progress → assessment_result → session_complete
 *
 * 使用方式:
 *   const ws = useLearningWebSocket()
 *   ws.connect()
 *   ws.on('resource', (data) => { ... })
 *   ws.startSession({ subject: '数据结构', goal: '掌握链表' })
 *   ws.submitAnswer('我的答案是...')
 */

class LearningWebSocket {
  constructor() {
    this.ws = null
    this._listeners = {}
    this._connected = false
    this._state = null // 当前会话状态（用于 submit_answer）
    this._retryTimer = null
    this._maxRetries = 5
    this._retryCount = 0
  }

  /**
   * 建立 WebSocket 连接
   */
  connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return this
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.hostname
    const port = window.location.port || (protocol === 'wss:' ? '443' : '80')
    // 开发环境走 Vite proxy，生产环境走实际端口
    const wsUrl = import.meta.env.DEV
      ? `${protocol}//${host}:${port}${import.meta.env.BASE_URL || ''}api/learning/ws/session`
      : `${protocol}//${host}:${port}/api/learning/ws/session`

    console.log(`[LearningWS] 正在连接: ${wsUrl}`)

    try {
      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        console.log('[LearningWS] ✅ 已连接')
        this._connected = true
        this._retryCount = 0
        this.emit('connected', {})
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          const type = data.type || 'unknown'
          console.log(`[LearningWS] ← ${type}`, data)
          this.emit(type, data)

          // 保存最新状态用于续传
          if (data.final_state) {
            this._state = data.final_state
          }
          if (type === 'session_complete' && data.final_state) {
            this._state = data.final_state
          }
        } catch (e) {
          console.error('[LearningWS] 消息解析失败:', e)
        }
      }

      this.ws.onclose = () => {
        console.log('[LearningWS] 🔌 连接断开')
        this._connected = false
        this._scheduleReconnect()
      }

      this.ws.onerror = (err) => {
        console.error('[LearningWS] ❌ 错误:', err)
        this.emit('error', { message: '连接错误' })
      }
    } catch (e) {
      console.error('[LearningWS] 创建连接失败:', e)
      this.emit('error', { message: e.message })
    }

    return this
  }

  /**
   * 启动学习会话
   */
  startSession({ subject, goal, userId = 'default', maxIterations = 5 }) {
    this._ensureConnected()
    this.send({
      action: 'start',
      subject,
      goal,
      user_id: userId,
      max_iterations: maxIterations,
    })
    return this
  }

  /**
   * 提交答案触发测评
   */
  submitAnswer(answer) {
    this._ensureConnected()
    this.send({
      action: 'submit_answer',
      answer,
    })
    return this
  }

  /**
   * 取消当前会话
   */
  cancel() {
    this.send({ action: 'cancel' })
    return this
  }

  /**
   * 断开连接
   */
  disconnect() {
    if (this._retryTimer) {
      clearTimeout(this._retryTimer)
      this._retryTimer = null
    }
    if (this.ws) {
      this.ws.close(1000, '客户端主动断开')
      this.ws = null
    }
    this._connected = false
    return this
  }

  /**
   * 获取当前保存的会话状态
   */
  getState() {
    return this._state
  }

  /** 是否已连接 */
  get connected() {
    return this._connected && this.ws?.readyState === WebSocket.OPEN
  }

  /* ─── 事件系统 ─── */

  on(event, callback) {
    if (!this._listeners[event]) {
      this._listeners[event] = []
    }
    this._listeners[event].push(callback)
    return this
  }

  off(event, callback) {
    if (this._listeners[event]) {
      this._listeners[event] = this._listeners[event].filter(cb => cb !== callback)
    }
    return this
  }

  emit(event, data) {
    const handlers = this._listeners[event]
    if (handlers) {
      handlers.forEach(cb => {
        try { cb(data) } catch (e) { console.error(`[LearningWS] 事件处理错误 (${event}):`, e) }
      })
    }
  }

  /* ─── 内部方法 ─── */

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
      console.log('[LearningWS] →', data.action || 'raw', data)
    } else {
      console.warn('[LearningWS] 未连接，无法发送:', data)
      this.emit('error', { message: '未连接到服务器' })
    }
  }

  _ensureConnected() {
    if (!this.connected) {
      console.warn('[LearningWS] 自动重连...')
      this.connect()
    }
  }

  _scheduleReconnect() {
    if (this._retryCount >= this._maxRetries) {
      console.log(`[LearningWS] 达到最大重试次数 (${this._maxRetries})，停止重连`)
      this.emit('max_retries_exceeded', {})
      return
    }
    const delay = Math.min(1000 * Math.pow(2, this._retryCount), 10000)
    this._retryCount++
    console.log(`[LearningWS] 将在 ${delay}ms 后第 ${this._retryCount} 次重连`)
    this._retryTimer = setTimeout(() => this.connect(), delay)
  }
}

// 单例模式 — 全局共享一个连接
let _instance = null

export function useLearningWebSocket() {
  if (!_instance) {
    _instance = new LearningWebSocket()
  }
  return _instance}

export default LearningWebSocket


// ══════════════════════════════════════
//  流式资源生成 WebSocket
// ══════════════════════════════════════

/**
 * 专用流式资源生成 WebSocket
 * 
 * 连接 /api/learning/ws/resources，逐个接收 6 种学习资源：
 *   resource_start → resource → progress (x6) → complete
 *
 * 使用方式:
 *   const rws = new ResourceWebSocket()
 *   rws.on('resource', (data) => { 添加到列表 })
 *   rws.on('progress', ({current, total}) => { 更新进度条 })
 *   rws.on('complete', () => { 完成 })
 *   rws.generate({ subject: '数据结构', topic: '链表' })
 */
class ResourceWebSocket {
  constructor() {
    this.ws = null
    this._listeners = {}
    this._connected = false
    this._retryTimer = null
    this._resourceCount = 0
  }

  connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) return this

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.hostname
    const port = window.location.port || (protocol === 'wss:' ? '443' : '80')
    // 开发环境走 Vite proxy
    const wsUrl = import.meta.env.DEV
      ? `${protocol}//${host}:${port}${import.meta.env.BASE_URL || ''}api/learning/ws/resources`
      : `${protocol}//${host}:${port}/api/learning/ws/resources`

    console.log(`[ResourceWS] 正在连接: ${wsUrl}`)

    try {
      this.ws = new WebSocket(wsUrl)
      this._resourceCount = 0

      this.ws.onopen = () => {
        console.log('[ResourceWS] ✅ 已连接')
        this._connected = true
        this.emit('connected', {})
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          const type = data.type || 'unknown'
          console.log(`[ResourceWS] ← ${type}`, data)

          if (type === 'resource') {
            this._resourceCount++
            data._index = this._resourceCount
          }

          this.emit(type, data)
        } catch (e) {
          console.error('[ResourceWS] 消息解析失败:', e)
        }
      }

      this.ws.onclose = () => {
        console.log('[ResourceWS] 🔌 连接断开')
        this._connected = false
        this._scheduleReconnect()
      }

      this.ws.onerror = () => {
        this.emit('error', { message: '连接错误' })
      }
    } catch (e) {
      this.emit('error', { message: e.message })
    }

    return this
  }

  /**
   * 发起流式资源生成请求
   */
  generate({ subject, goal, topic, userId = 'default', difficulty = 'medium' }) {
    this.connect()
    
    // 等 WebSocket 连接建立后发送
    const trySend = () => {
      if (this.connected) {
        this.send({
          action: 'generate',
          subject: subject || topic,
          goal: goal || `深入学习${topic}`,
          topic: topic || subject,
          user_id: userId,
          difficulty,
        })
      } else {
        setTimeout(trySend, 100)
      }
    }
    setTimeout(trySend, 50)
    return this
  }

  send(data) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
      console.log('[ResourceWS] →', data.action || 'raw')
    } else {
      this.emit('error', { message: '未连接到服务器' })
    }
  }

  disconnect() {
    if (this._retryTimer) { clearTimeout(this._retryTimer); this._retryTimer = null }
    if (this.ws) { this.ws.close(1000); this.ws = null }
    this._connected = false
    return this
  }

  get connected() {
    return this._connected && this.ws?.readyState === WebSocket.OPEN
  }

  /* ─── 事件系统 ─── */

  on(event, callback) {
    if (!this._listeners[event]) this._listeners[event] = []
    this._listeners[event].push(callback)
    return this
  }

  off(event, callback) {
    if (this._listeners[event]) {
      this._listeners[event] = this._listeners[event].filter(cb => cb !== callback)
    }
    return this
  }

  emit(event, data) {
    const handlers = this._listeners[event]
    if (handlers) handlers.forEach(cb => { try { cb(data) } catch (e) {} })
  }

  _scheduleReconnect() {
    // 资源 WS 不自动重连（每次手动触发）
  }
}

// 导出
export { ResourceWebSocket }
