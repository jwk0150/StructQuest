/**
 * Learning System Types
 */

export type NodeType = 'chapter' | 'section' | 'topic'
export type NodeStatus = 'mastered' | 'learning' | 'recommended' | 'not_started'
export type TaskType = 'reading' | 'practice' | 'video' | 'quiz'
export type TaskPriority = 'high' | 'medium' | 'low'
export type TaskStatus = 'pending' | 'in_progress' | 'completed'
export type ResourceType = 'notes' | 'mindmap' | 'quiz' | 'code_example' | 'ppt_outline' | 'document' | 'diagram' | 'exercise' | 'code' | 'video'
export type DifficultyLevel = 'easy' | 'medium' | 'hard'

export interface Position {
  x: number
  y: number
}

export interface LearningNode {
  id: string
  title: string
  description: string
  type: NodeType
  status: NodeStatus
  prerequisites: string[]
  position: Position
  children?: LearningNode[]
}

export interface LearningTask {
  id: string
  title: string
  description: string
  type: TaskType
  priority: TaskPriority
  estimatedTime: number // minutes
  reason: string // AI recommendation reason
  status: TaskStatus
  nodeId: string
  scheduledDate?: Date
}

export interface LearningResource {
  id: string
  title: string
  type: ResourceType
  difficulty: DifficultyLevel
  content: string
  aiGenerated: boolean
  reason?: string
  tags: string[]
  url?: string
  duration?: number // for videos, in seconds
}

export interface LearningProgress {
  totalNodes: number
  completedNodes: number
  masteryPercentage: number
  weeklyTime: number
  streak: number
}

export interface LearningActivity {
  id: string
  type: 'lesson' | 'practice' | 'quiz' | 'video'
  title: string
  nodeId: string
  duration: number
  completedAt: Date
}

export interface LearningStats {
  totalStudyTime: number
  weeklyTrend: WeeklyStat[]
  knowledgeMastery: KnowledgeMastery[]
  weakPoints: WeakPoint[]
  heatmap: HeatmapData[]
}

export interface WeeklyStat {
  date: Date
  time: number
}

export interface KnowledgeMastery {
  topic: string
  score: number
}

export interface WeakPoint {
  topic: string
  score: number
  suggestion: string
}

export interface HeatmapData {
  date: Date
  count: number
}
