/**
 * Core User Types
 */

export interface User {
  id: string
  studentId?: string
  email: string
  name: string
  avatar?: string
  hasCompletedOnboarding: boolean
  createdAt: Date
}

export interface UserProfile extends User {
  personaType: string
  personaScores: PersonaScores
}

export interface PersonaScores {
  visual: number
  practical: number
  theoretical: number
  explorer: number
  anxious: number
}

export interface UserSettings {
  theme: 'light' | 'dark'
  followSystemTheme: boolean
  notifications: boolean
  language: string
}
