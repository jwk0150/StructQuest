/**
 * Local Storage Utilities
 */

const PREFIX = 'learn-'

/**
 * Get item from localStorage
 */
export function getStorage(key, defaultValue = null) {
  try {
    const item = localStorage.getItem(PREFIX + key)
    return item ? JSON.parse(item) : defaultValue
  } catch (error) {
    console.error('Error reading from localStorage:', error)
    return defaultValue
  }
}

/**
 * Set item in localStorage
 */
export function setStorage(key, value) {
  try {
    localStorage.setItem(PREFIX + key, JSON.stringify(value))
    return true
  } catch (error) {
    console.error('Error writing to localStorage:', error)
    return false
  }
}

/**
 * Remove item from localStorage
 */
export function removeStorage(key) {
  try {
    localStorage.removeItem(PREFIX + key)
    return true
  } catch (error) {
    console.error('Error removing from localStorage:', error)
    return false
  }
}

/**
 * Clear all app-related items from localStorage
 */
export function clearStorage() {
  try {
    const keys = Object.keys(localStorage)
    keys.forEach(key => {
      if (key.startsWith(PREFIX)) {
        localStorage.removeItem(key)
      }
    })
    return true
  } catch (error) {
    console.error('Error clearing localStorage:', error)
    return false
  }
}

/**
 * Check if key exists in localStorage
 */
export function hasStorage(key) {
  return localStorage.getItem(PREFIX + key) !== null
}

/**
 * Session Storage wrappers
 */
export const sessionStorage = {
  get: (key, defaultValue = null) => {
    try {
      const item = window.sessionStorage.getItem(PREFIX + key)
      return item ? JSON.parse(item) : defaultValue
    } catch (error) {
      return defaultValue
    }
  },
  
  set: (key, value) => {
    try {
      window.sessionStorage.setItem(PREFIX + key, JSON.stringify(value))
      return true
    } catch (error) {
      return false
    }
  },
  
  remove: (key) => {
    try {
      window.sessionStorage.removeItem(PREFIX + key)
      return true
    } catch (error) {
      return false
    }
  }
}

// Storage keys
export const STORAGE_KEYS = {
  TOKEN: 'token',
  USER: 'user',
  THEME: 'theme',
  REMEMBER_ME: 'remember-me',
  LAST_VISIT: 'last-visit',
  PROFILE: 'profile-data',   // 画像数据本地备份（DB 失败时的容错）
  ONBOARDING_DONE: 'onboarding-done',  // 新手引导完成标记
}
