import { defineStore } from 'pinia'

export const usePersonaStore = defineStore('persona', {
  state: () => ({
    type: '尚未测试',
    scores: {
      visual: 0,
      practical: 0,
      theoretical: 0,
      explorer: 0,
      anxious: 0
    }
  }),
  actions: {
    setPersona(type, scores) {
      this.type = type
      this.scores = scores
    }
  }
})
