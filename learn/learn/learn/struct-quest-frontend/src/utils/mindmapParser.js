/**
 * 思维导图解析器
 * 支持 Markmap 格式（# ## ### + -）和旧版 Mermaid 缩进格式
 * 输出 ECharts tree 数据结构
 */

/**
 * 统一解析入口
 * @param {string} text - 思维导图文本
 * @returns {{ name: string, children: Array } | null}
 */
export function parseMindmap(text) {
  if (!text) return null
  const trimmed = text.trim()

  // 优先 Markmap 格式
  if (trimmed.startsWith('#') || trimmed.match(/^# |^## /m)) {
    return parseMarkmap(trimmed)
  }
  // 旧版 Mermaid 缩进格式
  if (trimmed.startsWith('mindmap')) {
    return parseMermaidIndent(trimmed)
  }
  // 自动检测
  if (trimmed.match(/^# /m)) {
    return parseMarkmap(trimmed)
  }
  return parseMermaidIndent(trimmed)
}

/**
 * Markmap 格式解析: # 根 / ## 一级 / ### 二级 / - 叶子
 */
function parseMarkmap(text) {
  const lines = text.split('\n')
  const root = { name: '', children: [] }
  const stack = []

  for (const rawLine of lines) {
    const line = rawLine.replace(/\r$/, '').trim()
    if (!line) continue

    const headingMatch = line.match(/^(#{1,4})\s+(.+)/)
    if (headingMatch) {
      const level = headingMatch[1].length
      const name = headingMatch[2].trim()
      const node = { name, children: level < 4 ? [] : undefined }

      if (level === 1) {
        root.name = name
        stack.length = 0
        stack.push({ level, node: root })
      } else {
        while (stack.length > 0 && stack[stack.length - 1].level >= level) {
          stack.pop()
        }
        const parent = stack[stack.length - 1]?.node
        if (parent) {
          if (!parent.children) parent.children = []
          parent.children.push(node)
        }
        stack.push({ level, node })
      }
      continue
    }

    const bulletMatch = line.match(/^[-*]\s+(.+)/)
    if (bulletMatch) {
      const name = bulletMatch[1].trim()
      const parent = stack[stack.length - 1]?.node
      if (parent) {
        if (!parent.children) parent.children = []
        parent.children.push({ name })
      }
    }
  }

  const limitChildren = (n, max = 15) => {
    if (n.children && n.children.length > max) n.children = n.children.slice(0, max)
    if (n.children) n.children.forEach(c => limitChildren(c, max))
  }
  limitChildren(root)

  return root.children.length > 0 ? root : null
}

/**
 * 旧版 Mermaid 缩进格式
 */
function parseMermaidIndent(text) {
  const lines = text.split('\n')
  const root = { name: '', children: [] }
  const depthStack = [{ depth: -1, parent: root }]

  for (const rawLine of lines) {
    const line = rawLine.replace(/\r$/, '')
    if (!line.trim() || line.trim().startsWith('mindmap')) continue

    const leadingSpaces = line.match(/^(\s*)/)
    const indent = leadingSpaces ? leadingSpaces[0].length : 0
    const text = line.trim()
    if (!text) continue

    const cleanText = text
      .replace(/^\(\((.+)\)\)$/, '$1')
      .replace(/^\(\(/, '').replace(/\)\)$/, '')
      .replace(/^\[\[(.+)\]\]$/, '$1')
      .replace(/^\[\[/, '').replace(/\]\]$/, '')
      .replace(/^\((.+)\)$/, '$1')
      .replace(/^\[(.+)\]$/, '$1')
      .trim()

    const node = { name: cleanText, children: [] }

    while (depthStack.length > 0 && depthStack[depthStack.length - 1].depth >= indent) {
      depthStack.pop()
    }
    const parent = depthStack[depthStack.length - 1]?.parent
    if (parent) parent.children.push(node)
    depthStack.push({ depth: indent, parent: node })
  }

  const limitChildren = (n, max = 10) => {
    if (n.children && n.children.length > max) n.children = n.children.slice(0, max)
    if (n.children) n.children.forEach(c => limitChildren(c, max))
  }
  limitChildren(root)

  return root.children.length > 0 ? root : null
}
