/**
 * 今日任务全局状态管理（Pinia）
 *
 * 统一管理每日任务的接取、完成状态、侧边栏徽章数字。
 * 学习行为完成后调用 autoCompleteCurrentTask() 自动完成匹配任务。
 */
import { defineStore } from 'pinia'
import studyApi from '../api/study'

export const useTaskStore = defineStore('task', {
  state: () => ({
    /** 今日任务列表（来自后端 daily-tasks） */
    tasks: [],
    /** 任务接取/完成状态映射 { task_id: { claimed, completed } } */
    statusMap: {},
    /** 侧边栏徽章数字（未接取任务数量） */
    badgeCount: 0,
    /** 是否已加载 */
    loaded: false,
    /** 加载中 */
    loading: false,
  }),

  getters: {
    /** 未接取的任务数量 */
    unclaimedCount: (state) => {
      return state.badgeCount
    },
    /** 今日任务总数 */
    totalCount: (state) => state.tasks.length,
    /** 已接取的任务列表（含状态） */
    claimedTasks: (state) => {
      return state.tasks.filter(t => state.statusMap[t.id]?.claimed)
    },
    /** 已完成的任务列表 */
    completedTasks: (state) => {
      return state.tasks.filter(t => state.statusMap[t.id]?.completed)
    },
  },

  actions: {
    /**
     * 初始化：获取每日任务列表 + 接取状态
     */
    async initTasks() {
      if (this.loading) return
      this.loading = true
      try {
        const [tasksRes, statusRes] = await Promise.all([
          studyApi.getDailyTasks().catch(() => ({ tasks: [] })),
          studyApi.getTaskStatus().catch(() => ({ status: {} })),
        ])
        this.tasks = tasksRes.tasks || []
        this.statusMap = statusRes.status || {}
        this.loaded = true
        await this._refreshBadge()
      } catch (e) {
        console.warn('[TaskStore] initTasks failed:', e)
      } finally {
        this.loading = false
      }
    },

    /**
     * 接取一个任务
     */
    async claimTask(task) {
      try {
        const res = await studyApi.claimTask({
          task_id: task.id,
          task_title: task.title,
          task_type: task.type,
          node_id: task.nodeId || null,
        })
        // 更新本地状态
        this.statusMap[task.id] = { claimed: true, completed: false }
        this.badgeCount = res.unclaimed_count ?? Math.max(0, this.badgeCount - 1)
        return true
      } catch (e) {
        console.warn('[TaskStore] claimTask failed:', e)
        return false
      }
    },

    /**
     * 学习行为完成后调用，自动完成匹配的今日任务
     * event_type: exam_submit | quiz_save | node_complete | resource_done | ai_chat | study_session
     */
    async autoComplete(eventType, nodeId) {
      try {
        const res = await studyApi.autoCompleteTasks({
          event_type: eventType,
          node_id: nodeId || null,
        })
        // 更新本地完成状态
        if (res.completed_tasks && res.completed_tasks.length > 0) {
          for (const t of res.completed_tasks) {
            if (this.statusMap[t.task_id]) {
              this.statusMap[t.task_id].completed = true
            }
          }
        }
        if (res.unclaimed_count !== undefined) {
          this.badgeCount = res.unclaimed_count
        }
        return res.completed_tasks || []
      } catch (e) {
        console.warn('[TaskStore] autoComplete failed:', e)
        return []
      }
    },

    /**
     * 仅刷新徽章数字
     */
    async _refreshBadge() {
      try {
        const res = await studyApi.getTaskBadge()
        this.badgeCount = res.count ?? 0
      } catch (e) {
        console.warn('[TaskStore] _refreshBadge failed:', e)
      }
    },
  },
})
