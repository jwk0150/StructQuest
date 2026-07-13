/**
 * PPT Generator Composable (状态管理)
 * ====================================
 *
 * 管理PPT智能生成器的三阶段流程状态：
 *   Step 1: 输入源选择（思维导图/Markdown/JSON）
 *   Step 2: 大纲编辑（可编辑表格）
 *   Step 3: 模板选择 + 渲染输出
 *
 * 使用方式：
 *   const { state, open, close, nextStep, prevStep, ... } = usePPTGenerator()
 */

import { ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// API 基础路径（根据环境变量自动切换）
const API_BASE = import.meta.env.VITE_API_BASE || '/api'

// ── 状态定义 ──

// 当前步骤：0=输入 | 1=编辑 | 2=渲染
const currentStep = ref(0)

// 对话框可见性
const dialogVisible = ref(false)

// 加载状态
const loading = ref(false)

// 渲染进度
const renderProgress = reactive({
  generating: false,
  percentage: 0,
  statusText: '',
})

// 第一阶段：输入数据
const inputData = reactive({
  source: 'existing',        // 'existing' | 'mindmap' | 'markdown' | 'json' | 'raw_text'
  content: '',               // 用户粘贴的原始内容
  existingMindmap: null,     // 从 NodeLearning 传入的思维导图数据
  targetPages: 10,           // 目标页数
  mindmapAvailable: false,   // 是否有可用思维导图
})

// 第二阶段：大纲数据（AI生成 → 用户编辑后的最终版本）
const outlineData = ref(null)       // AI生成的初始大纲
const editedOutline = ref(null)     // 用户修改后的最终大纲

// 第三阶段：渲染配置
const renderConfig = reactive({
  template: 'academic',      // 模板选择
  format: 'html',            // 输出格式
  templatesList: [],          // 可用模板列表
})

// 最终渲染结果
const renderResult = ref(null)

// 错误信息
const errorMessage = ref('')

/**
 * PPT生成器主Composable
 */
export function usePPTGenerator() {

  // ── 计算属性 ──

  const totalSteps = computed(() => 3)
  
  const canGoNext = computed(() => {
    if (currentStep.value === 0) {
      // 第一步需要至少有输入内容或思维导图
      return inputData.source === 'existing'
        ? !!inputData.existingMindmap
        : !!inputData.content.trim()
    }
    if (currentStep.value === 1) {
      return editedOutline.value && editedOutline.value.slides?.length > 0
    }
    return true
  })

  const canGoPrev = computed(() => currentStep.value > 0)

  const stepLabels = computed(() => [
    { title: '选择输入源', icon: 'Upload', desc: '从思维导图或文本导入内容' },
    { title: '编辑大纲', icon: 'EditPen', desc: '预览和调整PPT结构' },
    { title: '生成PPT', icon: 'MagicStick', desc: '选择模板并渲染输出' },
  ])

  // ── 核心方法 ──

  /**
   * 打开对话框（入口方法）
   * @param {Object} options - 配置选项
   * @param {string|Object} options.mindmapData - 已有的思维导图数据
   * @param {number} options.targetPages - 目标页数
   */
  async function open(options = {}) {
    resetState()
    
    // 接收传入的思维导图数据
    if (options.mindmapData) {
      inputData.existingMindmap = options.mindmapData
      inputData.mindmapAvailable = true
      inputData.source = 'existing'
    }
    
    if (options.targetPages) {
      inputData.targetPages = options.targetPages
    }

    // 加载可用模板列表
    await loadTemplates()

    dialogVisible.value = true
    currentStep.value = 0
  }

  function close() {
    dialogVisible.value = false
    setTimeout(resetState, 300)
  }

  function resetState() {
    currentStep.value = 0
    loading.value = false
    outlineData.value = null
    editedOutline.value = null
    renderResult.value = null
    errorMessage.value = ''
    inputData.content = ''
    inputData.source = 'existing'
    inputData.targetPages = 10
    renderConfig.template = 'academic'
    renderConfig.format = 'html'
    Object.assign(renderProgress, { generating: false, percentage: 0, statusText: '' })
  }

  function nextStep() {
    if (!canGoNext.value) {
      ElMessage.warning('请先完成当前步骤的必要操作')
      return
    }
    
    if (currentStep.value === 0) {
      // 从第一步到第二步：调用API生成大纲
      generateOutline()
    } else if (currentStep.value === 1) {
      // 从第二步到第三步：确认最终大纲
      currentStep.value++
    }
  }

  function prevStep() {
    if (canGoPrev.value) {
      currentStep.value--
    }
  }

  function goToStep(step) {
    // 只允许前进，或者返回已完成的步骤
    if (step >= 0 && step <= currentStep.value || step < currentStep.value) {
      currentStep.value = step
    }
  }

  // ── API 调用 ──

  /**
   * 第一阶段：解析思维导图，生成大纲
   */
  async function generateOutline() {
    loading.value = true
    errorMessage.value = ''
    
    try {
      const response = await fetch(`${API_BASE}/ppt/parse-mindmap`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source: inputData.source,
          content: inputData.content,
          existing_mindmap: typeof inputData.existingMindmap === 'string'
            ? inputData.existingMindmap
            : JSON.stringify(inputData.existingMindmap),
          target_pages: inputData.targetPages,
        }),
      })

      const data = await response.json()
      
      if (!response.ok || !data.success) {
        throw new Error(data.error || data.detail || '大纲生成失败')
      }

      outlineData.value = data.outline
      editedOutline.value = JSON.parse(JSON.stringify(data.outline)) // 深拷贝用于编辑
      
      ElMessage.success(`成功生成 ${data.outline.total_pages} 页大纲`)
      currentStep.value++

    } catch (error) {
      console.error('大纲生成失败:', error)
      errorMessage.value = error.message || '网络错误，请重试'
      ElMessage.error(errorMessage.value)
    } finally {
      loading.value = false
    }
  }

  /**
   * 第三阶段：渲染PPT文件
   */
  async function renderPPT() {
    loading.value = true
    
    Object.assign(renderProgress, {
      generating: true,
      percentage: 10,
      statusText: '准备渲染...',
    })

    try {
      Object.assign(renderProgress, {
        percentage: 30,
        statusText: `正在生成${renderConfig.format.toUpperCase()}文件...`,
      })

      const response = await fetch(`${API_BASE}/ppt/render`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          outline: editedOutline.value,
          format: renderConfig.format,
          template: renderConfig.template,
        }),
      })

      const data = await response.json()

      if (!response.ok || !data.success) {
        throw new Error(data.error || data.detail || '渲染失败')
      }

      Object.assign(renderProgress, {
        percentage: 100,
        statusText: '渲染完成！',
      })

      renderResult.value = data

      // 显示成功消息并打开预览
      ElMessage.success(`PPT生成成功！(${data.render_time}s)`)

      // 如果是HTML格式，可以打开新窗口预览
      if (data.format.includes('html')) {
        openPreview(data.file_url)
      }

    } catch (error) {
      console.error('渲染失败:', error)
      
      Object.assign(renderProgress, {
        generating: false,
        percentage: 0,
        statusText: '',
      })
      
      ElMessage.error(error.message || '渲染失败，请重试')
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取可用模板列表
   */
  async function loadTemplates() {
    try {
      const response = await fetch(`${API_BASE}/ppt/templates`)
      const data = await response.json()
      if (data.success) {
        renderConfig.templatesList = data.templates
      }
    } catch (error) {
      console.warn('加载模板列表失败:', error)
      // 使用默认模板列表
      renderConfig.templatesList = [
        { name: 'academic', display_name: '学术版', description: '论文答辩、课程汇报' },
        { name: 'minimal', display_name: '极简版', description: '商务简报、快速演示' },
        { name: 'presentation', display_name: '演示版', description: '产品发布、创意展示' },
      ]
    }
  }

  /**
   * 打开预览（新窗口）
   */
  function openPreview(url) {
    if (url) {
      window.open(url, '_blank', 'noopener,noreferrer')
    }
  }

  /**
   * 下载文件
   */
  function downloadFile() {
    if (renderResult.value?.file_url) {
      const link = document.createElement('a')
      link.href = renderResult.value.file_url
      link.download = renderResult.value.download_name || 'presentation.pptx'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
  }

  // ── 编辑器辅助方法 ──

  /**
   * 更新某一页的数据
   */
  function updateSlide(index, newData) {
    if (editedOutline.value?.slides?.[index]) {
      Object.assign(editedOutline.value.slides[index], newData)
    }
  }

  /**
   * 删除某一页
   */
  function removeSlide(index) {
    if (editedOutline.value?.slides) {
      ElMessageBox.confirm(
        `确定要删除第 ${index + 1} 页「${editedOutline.value.slides[index].title}」吗？`,
        '删除确认',
        { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
      ).then(() => {
        editedOutline.value.slides.splice(index, 1)
        editedOutline.value.total_pages = editedOutline.value.slides.length
        // 重新编号
        editedOutline.value.slides.forEach((slide, i) => { slide.page = i + 1 })
        ElMessage.success('已删除')
      }).catch(() => {})
    }
  }

  /**
   * 新增页面
   */
  function addSlide(afterIndex = -1) {
    if (editedOutline.value?.slides) {
      const newSlide = {
        page: editedOutline.value.slides.length + 1,
        layout: 'content',
        title: '新页面',
        bullet_points: ['请填写要点'],
        visual_suggestion: '',
      }
      if (afterIndex === -1) {
        editedOutline.value.slides.push(newSlide)
      } else {
        editedOutline.value.slides.splice(afterIndex + 1, 0, newSlide)
      }
      editedOutline.value.total_pages = editedOutline.value.slides.length
      editedOutline.value.slides.forEach((slide, i) => { slide.page = i + 1 })
    }
  }

  /**
   * 上移页面
   */
  function moveSlideUp(index) {
    if (editedOutline.value?.slides && index > 0) {
      const slides = editedOutline.value.slides
      ;[slides[index], slides[index - 1]] = [slides[index - 1], slides[index]]
      slides.forEach((s, i) => s.page = i + 1)
    }
  }

  /**
   * 下移页面
   */
  function moveSlideDown(index) {
    if (editedOutline.value?.slides && index < editedOutline.value.slides.length - 1) {
      const slides = editedOutline.value.slides
      ;[slides[index], slides[index + 1]] = [slides[index + 1], slides[index]]
      slides.forEach((s, i) => s.page = i + 1)
    }
  }

  // ── 返回公共接口 ──

  return {
    // 状态
    currentStep,
    dialogVisible,
    loading,
    renderProgress,
    inputData,
    outlineData,
    editedOutline,
    renderConfig,
    renderResult,
    errorMessage,

    // 计算属性
    totalSteps,
    canGoNext,
    canGoPrev,
    stepLabels,

    // 核心方法
    open,
    close,
    nextStep,
    prevStep,
    goToStep,

    // API
    generateOutline,
    renderPPT,
    loadTemplates,
    openPreview,
    downloadFile,

    // 编辑器
    updateSlide,
    removeSlide,
    addSlide,
    moveSlideUp,
    moveSlideDown,
  }
}
