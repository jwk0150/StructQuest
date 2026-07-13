import { defineStore } from 'pinia'

export const useChatStore = defineStore('chat', {
  state: () => ({
    sessions: [],
    currentSessionId: null,
    messages: {},
    isStreaming: false,
    aiStatus: 'idle' // thinking, analyzing, recommending, idle
  }),

  getters: {
    currentSession: (state) => {
      return state.sessions.find(s => s.id === state.currentSessionId)
    },

    currentMessages: (state) => {
      return state.messages[state.currentSessionId] || []
    },

    sortedSessions: (state) => {
      return [...state.sessions].sort((a, b) => {
        return new Date(b.updatedAt) - new Date(a.updatedAt)
      })
    }
  },

  actions: {
    createSession(title = '新对话') {
      const session = {
        id: `session-${Date.now()}`,
        title,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      }
      this.sessions.push(session)
      this.messages[session.id] = []
      this.currentSessionId = session.id
      return session
    },

    selectSession(sessionId) {
      if (this.sessions.find(s => s.id === sessionId)) {
        this.currentSessionId = sessionId
      }
    },

    deleteSession(sessionId) {
      const index = this.sessions.findIndex(s => s.id === sessionId)
      if (index !== -1) {
        this.sessions.splice(index, 1)
        delete this.messages[sessionId]
        
        if (this.currentSessionId === sessionId) {
          this.currentSessionId = this.sessions[0]?.id || null
        }
      }
    },

    addMessage(message) {
      if (!this.currentSessionId) {
        this.createSession()
      }

      const msg = {
        id: `msg-${Date.now()}`,
        sessionId: this.currentSessionId,
        createdAt: new Date().toISOString(),
        ...message
      }

      if (!this.messages[this.currentSessionId]) {
        this.messages[this.currentSessionId] = []
      }
      this.messages[this.currentSessionId].push(msg)

      // Update session
      const session = this.sessions.find(s => s.id === this.currentSessionId)
      if (session) {
        session.updatedAt = new Date().toISOString()
        // Auto-title from first user message
        if (this.messages[this.currentSessionId].length === 1 && message.role === 'user') {
          session.title = message.content.slice(0, 30) + (message.content.length > 30 ? '...' : '')
        }
      }

      return msg
    },

    updateMessage(messageId, content) {
      const messages = this.messages[this.currentSessionId]
      if (messages) {
        const msg = messages.find(m => m.id === messageId)
        if (msg) {
          msg.content = content
        }
      }
    },

    setStreaming(isStreaming) {
      this.isStreaming = isStreaming
    },

    setAIStatus(status) {
      this.aiStatus = status
    },

    clearMessages(sessionId) {
      if (sessionId && this.messages[sessionId]) {
        this.messages[sessionId] = []
        const session = this.sessions.find(s => s.id === sessionId)
        if (session) {
          session.updatedAt = new Date().toISOString()
        }
      }
    },

    reset() {
      this.sessions = []
      this.currentSessionId = null
      this.messages = {}
      this.isStreaming = false
      this.aiStatus = 'idle'
    }
  }
})
