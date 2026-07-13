import { defineStore } from 'pinia'

export const useThemeStore = defineStore('theme', {
  state: () => ({
    theme: localStorage.getItem('structquest-theme') || 'light',
    followSystem: localStorage.getItem('structquest-theme-follow-system') === 'true'
  }),

  getters: {
    isDark: (state) => state.theme === 'dark'
  },

  actions: {
    setTheme(newTheme) {
      this.theme = newTheme
      localStorage.setItem('structquest-theme', newTheme)
      this.applyTheme()
    },

    toggleTheme() {
      this.setTheme(this.theme === 'light' ? 'dark' : 'light')
    },

    setFollowSystem(value) {
      this.followSystem = value
      localStorage.setItem('structquest-theme-follow-system', String(value))
      if (value) {
        this.syncWithSystem()
      }
    },

    syncWithSystem() {
      if (this.followSystem && window.matchMedia) {
        const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches
        this.setTheme(isDark ? 'dark' : 'light')
      }
    },

    applyTheme() {
      document.documentElement.setAttribute('data-theme', this.theme)
      document.body.setAttribute('data-theme', this.theme)
    },

    init() {
      this.applyTheme()
      
      // Listen for system theme changes
      if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
          if (this.followSystem) {
            this.setTheme(e.matches ? 'dark' : 'light')
          }
        })
      }
    }
  }
})
