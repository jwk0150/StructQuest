import { ref, watch, onMounted } from 'vue'

const THEME_KEY = 'learn-theme'

/**
 * Theme composable for managing light/dark mode
 * Supports persistence and system preference detection
 */
export function useTheme() {
  const theme = ref('light')
  const isDark = ref(false)

  /**
   * Apply theme to document
   */
  const applyTheme = (newTheme) => {
    document.documentElement.setAttribute('data-theme', newTheme)
    document.body.setAttribute('data-theme', newTheme)
    isDark.value = newTheme === 'dark'
  }

  /**
   * Toggle between light and dark themes
   */
  const toggleTheme = () => {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
  }

  /**
   * Set specific theme
   */
  const setTheme = (newTheme) => {
    if (['light', 'dark'].includes(newTheme)) {
      theme.value = newTheme
    }
  }

  /**
   * Get system preferred theme
   */
  const getSystemTheme = () => {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark'
    }
    return 'light'
  }

  /**
   * Follow system theme preference
   */
  const followSystem = () => {
    const systemTheme = getSystemTheme()
    setTheme(systemTheme)
  }

  // Watch for theme changes
  watch(theme, (newTheme) => {
    applyTheme(newTheme)
    try {
      localStorage.setItem(THEME_KEY, newTheme)
    } catch (e) {
      // localStorage 不可用时忽略
    }
  })

  // Initialize theme on mount
  onMounted(() => {
    try {
      // Check localStorage first
      const savedTheme = localStorage.getItem(THEME_KEY)
      if (savedTheme && ['light', 'dark'].includes(savedTheme)) {
        theme.value = savedTheme
        applyTheme(savedTheme)
      } else {
        // Default to light theme
        theme.value = 'light'
        applyTheme('light')
      }

      // Listen for system theme changes
      if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
          try {
            // Only auto-switch if user hasn't set a preference
            if (!localStorage.getItem(THEME_KEY)) {
              const newTheme = e.matches ? 'dark' : 'light'
              setTheme(newTheme)
            }
          } catch (e) { /* localStorage 不可用时忽略 */ }
        })
      }
    } catch (e) {
      // localStorage 不可用（无痕/隐私模式），使用默认主题
      console.warn('[Theme] localStorage 不可用，使用默认主题:', e)
      theme.value = 'light'
      applyTheme('light')
    }
  })

  return {
    theme,
    isDark,
    toggleTheme,
    setTheme,
    followSystem,
    getSystemTheme
  }
}
