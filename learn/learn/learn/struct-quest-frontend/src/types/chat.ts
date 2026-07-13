/**
 * Chat System Types
 */

export type MessageRole = 'user' | 'assistant'
export type AttachmentType = 'pdf' | 'image' | 'code'
export type AIStatusType = 'thinking' | 'analyzing' | 'recommending' | 'idle'

export interface ChatSession {
  id: string
  title: string
  createdAt: Date
  updatedAt: Date
}

export interface ChatMessage {
  id: string
  sessionId: string
  role: MessageRole
  content: string
  createdAt: Date
  attachments?: ChatAttachment[]
}

export interface ChatAttachment {
  id: string
  type: AttachmentType
  name: string
  url: string
  parsedContent?: string
  size?: number
  mimeType?: string
}

export interface SSEMessageEvent {
  type: 'start' | 'chunk' | 'end' | 'error'
  content?: string
  error?: string
}
