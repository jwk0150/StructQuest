/**
 * AI 算法实验室 - 预设算法引擎
 * 包含 15 个核心算法的动画步骤生成器
 */

// ============================================================
// 工具函数
// ============================================================

const BAR_COLORS = [
  '#d97982', '#ec4899', '#f43f5e', '#f97316', '#eab308',
  '#22c55e', '#14b8a6', '#06b6d4', '#b94b5a', '#c84c5a'
]

function getBarColor(i) {
  return BAR_COLORS[i % BAR_COLORS.length]
}

function normalizeHeights(arr, valKey = 'value') {
  const maxVal = Math.max(...arr.map(d => d[valKey]), 1)
  arr.forEach(d => d.height = Math.round((d[valKey] / maxVal) * 88) + 10)
  return arr
}

function clone(arr) {
  return JSON.parse(JSON.stringify(arr))
}

function buildSortBars(data) {
  const bars = data.map((v, i) => ({
    value: v,
    state: 'normal',
    color: getBarColor(i),
    height: 0
  }))
  return normalizeHeights(bars)
}

function makeStep(narration, bars, codeLine, codeExplanation) {
  return { narration, bars: clone(bars), codeLine, codeExplanation }
}

// ============================================================
// 1. 冒泡排序
// ============================================================
export function bubbleSortSteps(data) {
  const bars = buildSortBars(data)
  const steps = []
  steps.push(makeStep(`开始冒泡排序，共 ${data.length} 个元素`, bars, 0,
    '外层循环控制排序轮数，每轮将最大元素"沉"到末尾'))

  for (let i = 0; i < bars.length - 1; i++) {
    for (let j = 0; j < bars.length - 1 - i; j++) {
      bars[j].state = 'comparing'
      bars[j + 1].state = 'comparing'
      steps.push(makeStep(`比较 a[${j}]=${bars[j].value} 和 a[${j + 1}]=${bars[j + 1].value}`, bars, 3,
        `比较相邻元素，如果前大后小就交换`))

      if (bars[j].value > bars[j + 1].value) {
        bars[j].state = 'swapping'
        bars[j + 1].state = 'swapping'
        steps.push(makeStep(`${bars[j].value} > ${bars[j + 1].value}，交换它们`, bars, 4,
          `前 > 后，交换位置`))
        ;[bars[j], bars[j + 1]] = [bars[j + 1], bars[j]]
        bars[j].state = 'swapping'
        bars[j + 1].state = 'swapping'
        steps.push(makeStep(`交换完成：a[${j}]=${bars[j].value}, a[${j + 1}]=${bars[j + 1].value}`, bars, 4,
          `交换后较小值在前`))
      }
      bars[j].state = 'normal'
      bars[j + 1].state = 'normal'
    }
    bars[bars.length - 1 - i].state = 'sorted'
    steps.push(makeStep(`第 ${i + 1} 轮结束，a[${bars.length - 1 - i}]=${bars[bars.length - 1 - i].value} 归位`, bars, 1,
      `每轮将未排序部分的最大值确定到末尾`))
  }
  bars.forEach(b => b.state = 'sorted')
  steps.push(makeStep('排序完成！所有元素已按升序排列 ✅', bars, -1, '冒泡排序结束'))
  return steps.map((s, i) => ({ ...s, step: i + 1 }))
}

// ============================================================
// 2. 快速排序
// ============================================================
export function quickSortSteps(data) {
  const bars = buildSortBars(data)
  const steps = []
  steps.push(makeStep(`开始快速排序：选择 Pivot 分割数组`, bars, 0,
    '分治策略：选基准 → 分区 → 递归'))

  function partition(low, high) {
    const pivot = bars[high]
    pivot.state = 'pivot'
    steps.push(makeStep(`选 Pivot = ${pivot.value} (index ${high})`, bars, 8,
      '选择最后一个元素作为 pivot（基准值）'))

    let i = low - 1
    for (let j = low; j < high; j++) {
      bars[j].state = 'comparing'
      const cond = bars[j].value < pivot.value
      steps.push(makeStep(
        `比较 a[${j}]=${bars[j].value} 与 Pivot=${pivot.value}：${cond ? '<，交换' : '≥，跳过'}`,
        bars, 11,
        cond ? `${bars[j].value} < ${pivot.value}，移到左侧` : `${bars[j].value} ≥ ${pivot.value}，保持不动`
      ))
      if (cond) {
        i++
        if (i !== j) {
          ;[bars[i], bars[j]] = [bars[j], bars[i]]
          steps.push(makeStep(`交换 a[${i}] 和 a[${j}]`, bars, 13, `较小元素放到 i 之前`))
        }
      }
      bars.forEach((d, idx) => { if (idx !== high) d.state = 'normal' })
    }
    pivot.state = 'normal'
    ;[bars[i + 1], bars[high]] = [bars[high], bars[i + 1]]
    bars[i + 1].state = 'sorted'
    steps.push(makeStep(`Pivot ${pivot.value} 归位到 index ${i + 1}`, bars, 16, 'Pivot 放到最终正确位置'))
    return i + 1
  }

  function qs(low, high) {
    if (low >= high) {
      if (low === high) bars[low].state = 'sorted'
      return
    }
    const pi = partition(low, high)
    qs(low, pi - 1)
    qs(pi + 1, high)
  }

  qs(0, bars.length - 1)
  bars.forEach(b => b.state = 'sorted')
  steps.push(makeStep('快速排序完成！✅', bars, -1, '平均 O(n log n)，最坏 O(n²)'))
  return steps.map((s, i) => ({ ...s, step: i + 1 }))
}

// ============================================================
// 3. 归并排序
// ============================================================
export function mergeSortSteps(data) {
  const bars = buildSortBars(data)
  const steps = []
  steps.push(makeStep(`开始归并排序：将数组递归分割再合并`, bars, 0,
    '分治策略：先分割到底，再两两合并'))

  function mergeSort(low, high) {
    if (low >= high) return
    const mid = Math.floor((low + high) / 2)

    mergeSort(low, mid)
    mergeSort(mid + 1, high)
    merge(low, mid, high)
  }

  function merge(low, mid, high) {
    for (let k = low; k <= high; k++) bars[k].state = 'comparing'

    const left = bars.slice(low, mid + 1).map(b => b.value)
    const right = bars.slice(mid + 1, high + 1).map(b => b.value)
    let i = 0, j = 0, k = low

    while (i < left.length && j < right.length) {
      if (left[i] <= right[j]) {
        bars[k].value = left[i]
        bars[k].state = 'swapping'
        i++
      } else {
        bars[k].value = right[j]
        bars[k].state = 'swapping'
        j++
      }
      k++
    }
    while (i < left.length) { bars[k].value = left[i]; i++; k++ }
    while (j < right.length) { bars[k].value = right[j]; j++; k++ }
    normalizeHeights(bars)
    for (let m = low; m <= high; m++) bars[m].state = 'normal'
    steps.push(makeStep(`合并区间 [${low}..${high}]`, bars, 14,
      `将两个有序子数组合并为一个有序数组`))
  }

  mergeSort(0, bars.length - 1)
  bars.forEach(b => b.state = 'sorted')
  normalizeHeights(bars)
  steps.push(makeStep('归并排序完成！✅', bars, -1, '时间复杂度 O(n log n)，空间复杂度 O(n)'))
  return steps.map((s, i) => ({ ...s, step: i + 1 }))
}

// ============================================================
// 4. 插入排序
// ============================================================
export function insertionSortSteps(data) {
  const bars = buildSortBars(data)
  const steps = []
  steps.push(makeStep(`开始插入排序：将每个元素插入到已排序部分`, bars, 0,
    '像一个一个整理扑克牌，每张牌插入到正确位置'))
  bars[0].state = 'sorted'

  for (let i = 1; i < bars.length; i++) {
    let key = bars[i].value
    bars[i].state = 'pivot'
    steps.push(makeStep(`取出 key = ${key} (index ${i})`, bars, 3, '记录当前待插入值'))
    let j = i - 1
    while (j >= 0 && bars[j].value > key) {
      bars[j].state = 'comparing'
      steps.push(makeStep(`${bars[j].value} > ${key}，右移`, bars, 5, `${bars[j].value} 比 key 大，向右挪一位`))
      bars[j + 1].value = bars[j].value
      normalizeHeights(bars)
      bars[j].state = 'normal'
      j--
    }
    bars[j + 1].value = key
    normalizeHeights(bars)
    bars[j + 1].state = 'sorted'
    steps.push(makeStep(`key = ${key} 插入到 index ${j + 1}`, bars, 7, 'key 放到正确位置'))
    for (let k = 0; k <= i; k++) bars[k].state = 'sorted'
  }
  steps.push(makeStep('插入排序完成！✅', bars, -1, '最好 O(n)，最坏 O(n²)'))
  return steps.map((s, i) => ({ ...s, step: i + 1 }))
}

// ============================================================
// 5. 选择排序
// ============================================================
export function selectionSortSteps(data) {
  const bars = buildSortBars(data)
  const steps = []
  steps.push(makeStep(`开始选择排序：每次选择最小值放到前面`, bars, 0,
    '每轮从未排序部分选最小元素，放到已排序末尾'))

  for (let i = 0; i < bars.length - 1; i++) {
    let minIdx = i
    bars[i].state = 'pivot'
    for (let j = i + 1; j < bars.length; j++) {
      bars[j].state = 'comparing'
      steps.push(makeStep(`比较 a[${minIdx}]=${bars[minIdx].value} 与 a[${j}]=${bars[j].value}`, bars, 4,
        `当前最小值: ${bars[minIdx].value}，与 a[${j}] 比较`))
      if (bars[j].value < bars[minIdx].value) {
        bars[minIdx].state = 'normal'
        minIdx = j
        bars[minIdx].state = 'pivot'
        steps.push(makeStep(`发现更小值：a[${j}]=${bars[j].value}，更新最小值`, bars, 4, `更新最小值为 ${bars[j].value}`))
      }
      bars[j].state = 'normal'
    }
    if (minIdx !== i) {
      [bars[i], bars[minIdx]] = [bars[minIdx], bars[i]]
      steps.push(makeStep(`交换 a[${i}] 和 a[${minIdx}]`, bars, 6, `将最小值 ${bars[i].value} 放到位置 ${i}`))
    }
    bars[i].state = 'sorted'
    steps.push(makeStep(`第 ${i + 1} 轮结束，a[${i}]=${bars[i].value} 归位`, bars, 1, `已排序 ${i + 1} 个元素`))
  }
  bars[bars.length - 1].state = 'sorted'
  steps.push(makeStep('选择排序完成！✅', bars, -1, '无论数据怎样，总是 O(n²)'))
  return steps.map((s, i) => ({ ...s, step: i + 1 }))
}

// ============================================================
// 6. 堆排序
// ============================================================
export function heapSortSteps(data) {
  const bars = buildSortBars(data)
  const steps = []
  steps.push(makeStep(`开始堆排序：先建大根堆，再逐一取堆顶`, bars, 0,
    '利用堆结构：建堆 O(n)，每次取堆顶 O(log n)'))

  const n = bars.length

  function heapify(size, i) {
    let largest = i
    const l = 2 * i + 1
    const r = 2 * i + 2

    if (l < size) {
      bars[l].state = 'comparing'
      bars[largest].state = 'comparing'
    }
    if (l < size && bars[l].value > bars[largest].value) largest = l
    bars.forEach(b => b.state = 'normal')

    if (r < size) {
      bars[r].state = 'comparing'
      bars[largest].state = 'comparing'
    }
    if (r < size && bars[r].value > bars[largest].value) largest = r
    bars.forEach(b => b.state = 'normal')

    if (largest !== i) {
      bars[i].state = 'swapping'
      bars[largest].state = 'swapping'
      ;[bars[i], bars[largest]] = [bars[largest], bars[i]]
      steps.push(makeStep(`堆化：交换 a[${i}]=${bars[i].value} 和 a[${largest}]=${bars[largest].value}`, bars, 8,
        `父节点 < 子节点，下沉`))
      heapify(size, largest)
    }
  }

  // 建堆
  for (let i = Math.floor(n / 2) - 1; i >= 0; i--) {
    heapify(n, i)
  }
  for (let i = 0; i < n; i++) bars[i].state = 'normal'
  steps.push(makeStep('大根堆构建完成！堆顶为最大值', bars, 0, '堆顶元素是当前最大值'))

  // 排序
  for (let i = n - 1; i > 0; i--) {
    bars[0].state = 'swapping'
    bars[i].state = 'swapping'
    ;[bars[0], bars[i]] = [bars[i], bars[0]]
    steps.push(makeStep(`取堆顶 ${bars[i].value}，放到位置 ${i}`, bars, 3, `将最大值与末尾交换`))
    bars[i].state = 'sorted'
    heapify(i, 0)
  }
  bars[0].state = 'sorted'
  steps.push(makeStep('堆排序完成！✅', bars, -1, '时间复杂度 O(n log n)，空间 O(1)'))
  return steps.map((s, i) => ({ ...s, step: i + 1 }))
}

// ============================================================
// 7. 二分查找
// ============================================================
export function binarySearchSteps(data, target) {
  const sorted = [...data].sort((a, b) => a - b)
  const bars = buildSortBars(sorted)
  const steps = []
  steps.push(makeStep(`二分查找：在有序数组中找 ${target}`, bars, 0, '前提：数组必须有序，每次排除一半'))

  let low = 0, high = bars.length - 1

  while (low <= high) {
    const mid = Math.floor((low + high) / 2)
    for (let i = low; i <= high; i++) bars[i].state = 'comparing'
    bars[mid].state = 'pivot'
    const cond = bars[mid].value === target ? 'equal'
      : bars[mid].value < target ? 'less' : 'greater'
    steps.push(makeStep(
      `mid=${mid}: a[${mid}]=${bars[mid].value} ${cond === 'equal' ? '== 找到了!' : cond === 'less' ? '< target，往右找' : '> target，往左找'}`,
      bars, 3,
      `比较中间值和目标值`
    ))
    if (bars[mid].value === target) {
      bars[mid].state = 'sorted'
      steps.push(makeStep(`找到目标 ${target} 在 index ${mid}！✅`, bars, -1, '二分查找 O(log n)'))
      return steps.map((s, i) => ({ ...s, step: i + 1 }))
    } else if (bars[mid].value < target) {
      low = mid + 1
    } else {
      high = mid - 1
    }
    bars.forEach(b => b.state = 'normal')
  }
  steps.push(makeStep(`${target} 不在数组中`, bars, -1, '未找到目标值'))
  return steps.map((s, i) => ({ ...s, step: i + 1 }))
}

// ============================================================
// 8-9. BFS / DFS (图遍历)
// ============================================================
function buildGraphState(adjList, layout) {
  const nodes = Object.keys(adjList).map(id => ({
    id,
    x: layout[id].x,
    y: layout[id].y,
    label: id,
    state: 'normal' // normal | visiting | visited | current | queue
  }))
  return { nodes, adjList }
}

// 预设图
const DEMO_GRAPH_ADJ = {
  A: ['B', 'C'],
  B: ['A', 'D', 'E'],
  C: ['A', 'F'],
  D: ['B'],
  E: ['B', 'F'],
  F: ['C', 'E']
}
const DEMO_GRAPH_LAYOUT = {
  A: { x: 200, y: 50 },
  B: { x: 100, y: 180 },
  C: { x: 300, y: 180 },
  D: { x: 30,  y: 320 },
  E: { x: 170, y: 320 },
  F: { x: 300, y: 320 }
}

function buildBFS_DFS_Steps(algo) {
  const steps = []
  const state = buildGraphState(DEMO_GRAPH_ADJ, DEMO_GRAPH_LAYOUT)
  const visited = new Set()
  const queue = algo === 'bfs' ? ['A'] : []
  const stack = algo === 'dfs' ? ['A'] : []

  steps.push({
    narration: algo === 'bfs' ? 'BFS 从 A 开始，用队列逐层遍历' : 'DFS 从 A 开始，用递归深度优先',
    type: 'graph',
    graphState: clone(state),
    codeLine: 0,
    codeExplanation: algo === 'bfs' ? 'BFS 使用队列，先进先出，逐层扩散' : 'DFS 使用栈/递归，一路到底再回溯'
  })

  function addStep(current, action) {
    steps.push({
      narration: action,
      type: 'graph',
      graphState: clone(state),
      codeLine: algo === 'bfs' ? 4 : 7,
      codeExplanation: action
    })
  }

  if (algo === 'bfs') {
    while (queue.length > 0) {
      const node = queue.shift()
      if (visited.has(node)) continue
      visited.add(node)
      state.nodes.find(n => n.id === node).state = 'current'
      addStep(node, `访问 ${node}，将其邻居加入队列`)

      for (const neighbor of DEMO_GRAPH_ADJ[node]) {
        if (!visited.has(neighbor) && !queue.includes(neighbor)) {
          queue.push(neighbor)
          state.nodes.find(n => n.id === neighbor).state = 'queue'
          addStep(neighbor, `${neighbor} 加入队列待访问`)
        }
      }
      state.nodes.find(n => n.id === node).state = 'visited'
    }
  } else {
    function dfs(node) {
      if (visited.has(node)) return
      visited.add(node)
      state.nodes.find(n => n.id === node).state = 'current'
      addStep(node, `访问 ${node}`)
      state.nodes.find(n => n.id === node).state = 'visited'

      for (const neighbor of DEMO_GRAPH_ADJ[node]) {
        if (!visited.has(neighbor)) {
          state.nodes.find(n => n.id === neighbor).state = 'queue'
          addStep(neighbor, `准备深入 ${neighbor}`)
          dfs(neighbor)
        }
      }
    }
    dfs('A')
  }

  steps.push({
    narration: `${algo === 'bfs' ? 'BFS' : 'DFS'} 遍历完成！✅`,
    type: 'graph',
    graphState: clone(state),
    codeLine: -1,
    codeExplanation: '时间复杂度 O(V+E)'
  })

  return steps.map((s, i) => ({ ...s, step: i + 1 }))
}

export function bfsSteps() { return buildBFS_DFS_Steps('bfs') }
export function dfsSteps() { return buildBFS_DFS_Steps('dfs') }

// ============================================================
// 10. BST 插入
// ============================================================
const BST_LAYOUT = {
  root: { x: 300, y: 30 },
  L1:   { x: 150, y: 120 },
  R1:   { x: 450, y: 120 },
  L2L:  { x: 60,  y: 220 },
  L2R:  { x: 240, y: 220 },
  R1L:  { x: 360, y: 220 },
  R1R:  { x: 540, y: 220 }
}

export function bstInsertSteps() {
  const values = [50, 30, 70, 20, 40, 60, 80]
  const steps = []
  const nodes = [] // { value, x, y, state, highlight }
  const edges = [] // { from, to }

  const layoutMap = {
    50: { x: 400, y: 30 },
    30: { x: 220, y: 140 },
    70: { x: 580, y: 140 },
    20: { x: 120, y: 260 },
    40: { x: 320, y: 260 },
    60: { x: 480, y: 260 },
    80: { x: 680, y: 260 }
  }

  function addTreeStep(narration, highlightValue, codeLine, codeExplanation) {
    const state = {
      nodes: clone(nodes).map(n => ({
        ...n,
        highlight: n.value === highlightValue
      })),
      edges: clone(edges)
    }
    steps.push({ narration, type: 'tree', treeState: state, codeLine, codeExplanation })
  }

  function insert(value) {
    if (nodes.length === 0) {
      nodes.push({ value, x: layoutMap[value].x, y: layoutMap[value].y, state: 'current' })
      addTreeStep(`插入根节点 ${value}`, value, 1, '空树时，新节点成为根')
      nodes[0].state = 'normal'
      return
    }

    let current = nodes[0]
    current.state = 'current'
    addTreeStep(`从根节点 ${current.value} 开始，插入 ${value}`, current.value, 2, `比较 ${value} 和当前节点`)

    const path = []
    while (true) {
      path.push(current)
      if (value < current.value) {
        const leftChild = nodes.find(n => n.value === current.value && n._left)
        if (!leftChild && !edges.some(e => e.from === current.value && e.side === 'left')) {
          const pos = layoutMap[value]
          nodes.push({ value, x: pos.x, y: pos.y, state: 'inserting' })
          edges.push({ from: current.value, to: value, side: 'left' })
          addTreeStep(`${value} < ${current.value}，插入为 ${current.value} 的左子节点`, value, 4,
            `新节点值 < 当前节点，走左子树`)
          break
        } else {
          current.state = 'normal'
          current = nodes.find(n => n.value === (leftChild?.value || edges.find(e => e.from === current.value && e.side === 'left')?.to))
          current.state = 'current'
          addTreeStep(`${value} < ${current.value}，继续向左`, current.value, 3, `继续向左子树搜索`)
        }
      } else {
        const rightChild = nodes.find(n => n.value === current.value && n._right)
        if (!rightChild && !edges.some(e => e.from === current.value && e.side === 'right')) {
          const pos = layoutMap[value]
          nodes.push({ value, x: pos.x, y: pos.y, state: 'inserting' })
          edges.push({ from: current.value, to: value, side: 'right' })
          addTreeStep(`${value} > ${current.value}，插入为 ${current.value} 的右子节点`, value, 5,
            `新节点值 > 当前节点，走右子树`)
          break
        } else {
          current.state = 'normal'
          current = nodes.find(n => n.value === (rightChild?.value || edges.find(e => e.from === current.value && e.side === 'right')?.to))
          current.state = 'current'
          addTreeStep(`${value} > ${current.value}，继续向右`, current.value, 4, `继续向右子树搜索`)
        }
      }
    }
    path.forEach(p => p.state = 'normal')
    const newNode = nodes.find(n => n.value === value)
    if (newNode) newNode.state = 'normal'
  }

  steps.push({
    narration: 'BST 插入演示：依次插入 50, 30, 70, 20, 40, 60, 80',
    type: 'tree', treeState: { nodes: [], edges: [] },
    codeLine: 0, codeExplanation: 'BST 规则：左子树 < 根 < 右子树'
  })

  for (const v of values) {
    insert(v)
  }

  steps.push({
    narration: 'BST 构建完成！中序遍历可得有序序列 ✅',
    type: 'tree', treeState: { nodes: clone(nodes), edges: clone(edges) },
    codeLine: -1, codeExplanation: 'BST 平均查找 O(log n)，最坏 O(n)'
  })

  return steps.map((s, i) => ({ ...s, step: i + 1 }))
}

// ============================================================
// 11-12. AVL 左旋 / 右旋
// ============================================================
function buildAVLRotateSteps(direction) {
  const steps = []
  const isLeft = direction === 'left'

  // 简体版：用预设坐标 + 动画
  const initialNodes = isLeft
    ? [
        { value: 30, x: 300, y: 80, state: 'unbalanced' },
        { value: 20, x: 180, y: 200, state: 'normal' },
        { value: 40, x: 420, y: 200, state: 'normal' },
        { value: 50, x: 500, y: 320, state: 'normal' }
      ]
    : [
        { value: 50, x: 300, y: 80, state: 'unbalanced' },
        { value: 30, x: 180, y: 200, state: 'normal' },
        { value: 60, x: 420, y: 200, state: 'normal' },
        { value: 20, x: 100, y: 320, state: 'normal' }
      ]

  const initialEdges = isLeft
    ? [
        { from: 30, to: 20, side: 'left' },
        { from: 30, to: 40, side: 'right' },
        { from: 40, to: 50, side: 'right' }
      ]
    : [
        { from: 50, to: 30, side: 'left' },
        { from: 50, to: 60, side: 'right' },
        { from: 30, to: 20, side: 'left' }
      ]

  steps.push({
    narration: isLeft ? 'AVL 左旋：节点 30 平衡因子 = -2（右边太重），需要左旋' : 'AVL 右旋：节点 50 平衡因子 = +2（左边太重），需要右旋',
    type: 'tree', treeState: { nodes: clone(initialNodes), edges: clone(initialEdges) },
    codeLine: 0, codeExplanation: `当节点平衡因子 ${isLeft ? '< -1' : '> 1'}，需要旋转恢复平衡`
  })

  // Show the pivot
  const pivotNodes = clone(initialNodes)
  const pivotEdges = clone(initialEdges)
  const pivotNode = pivotNodes.find(n => n.value === (isLeft ? 40 : 30))
  pivotNode.state = 'pivot'
  steps.push({
    narration: isLeft ? '以 30 的右子节点 40 为旋转轴（新根）' : '以 50 的左子节点 30 为旋转轴（新根）',
    type: 'tree', treeState: { nodes: pivotNodes, edges: pivotEdges },
    codeLine: 1, codeExplanation: isLeft ? '左旋：右子节点上移，原根下沉为左子节点' : '右旋：左子节点上移，原根下沉为右子节点'
  })

  // After rotation
  const afterNodes = isLeft
    ? [
        { value: 40, x: 300, y: 80, state: 'sorted' },
        { value: 30, x: 180, y: 200, state: 'normal' },
        { value: 20, x: 100, y: 320, state: 'normal' },
        { value: 50, x: 420, y: 200, state: 'normal' }
      ]
    : [
        { value: 30, x: 300, y: 80, state: 'sorted' },
        { value: 20, x: 180, y: 200, state: 'normal' },
        { value: 50, x: 420, y: 200, state: 'normal' },
        { value: 60, x: 500, y: 320, state: 'normal' }
      ]

  const afterEdges = isLeft
    ? [
        { from: 40, to: 30, side: 'left' },
        { from: 40, to: 50, side: 'right' },
        { from: 30, to: 20, side: 'left' }
      ]
    : [
        { from: 30, to: 20, side: 'left' },
        { from: 30, to: 50, side: 'right' },
        { from: 50, to: 60, side: 'right' }
      ]

  steps.push({
    narration: isLeft
      ? '旋转完成！40 成为新根，30 下沉为左子节点，原 40 的左子树挂到 30 的右子树 ✅'
      : '旋转完成！30 成为新根，50 下沉为右子节点，原 30 的右子树挂到 50 的左子树 ✅',
    type: 'tree', treeState: { nodes: afterNodes, edges: afterEdges },
    codeLine: 7, codeExplanation: isLeft ? '旋转 O(1)，恢复了 AVL 平衡' : '旋转 O(1)，恢复了 AVL 平衡'
  })

  return steps.map((s, i) => ({ ...s, step: i + 1 }))
}

export function avlRotateLeftSteps() { return buildAVLRotateSteps('left') }
export function avlRotateRightSteps() { return buildAVLRotateSteps('right') }

// ============================================================
// 13. 链表反转
// ============================================================
export function linkedListReverseSteps() {
  const values = [1, 2, 3, 4, 5]
  const steps = []

  function makeListNode(val, x, y) {
    return { value: val, x, y, state: 'normal', next: true }
  }

  let nodes = values.map((v, i) => makeListNode(v, 80 + i * 120, 100))
  steps.push({
    narration: '链表反转：将 1→2→3→4→5 反转为 5→4→3→2→1',
    type: 'linked_list', listState: { nodes: clone(nodes), pointers: [] },
    codeLine: 0, codeExplanation: '用三个指针 prev, curr, next 迭代反转'
  })

  let prev = null
  let curr = 0 // index

  nodes[curr].state = 'current'
  steps.push({
    narration: `初始状态：prev = null, curr = ${nodes[curr].value}`,
    type: 'linked_list', listState: { nodes: clone(nodes), pointers: [{ name: 'prev', pos: -40 }, { name: 'curr', pos: curr }] },
    codeLine: 2, codeExplanation: 'prev 指向已反转部分的头，curr 指向当前节点'
  })

  while (curr < nodes.length) {
    const next = curr + 1
    if (next < nodes.length) nodes[next].state = 'next'

    steps.push({
      narration: `保存 next = ${next < nodes.length ? nodes[next].value : 'null'}`,
      type: 'linked_list', listState: { nodes: clone(nodes), pointers: [
        { name: 'prev', pos: prev !== null ? prev : -40 },
        { name: 'curr', pos: curr },
        { name: 'next', pos: next < nodes.length ? next : -40 }
      ]},
      codeLine: 4, codeExplanation: '先保存下一个节点，以免断链'
    })

    // reverse
    nodes[curr].reversed = true
    steps.push({
      narration: `反转：${nodes[curr].value}.next = ${prev !== null ? nodes[prev].value : 'null'}`,
      type: 'linked_list', listState: { nodes: clone(nodes), pointers: [
        { name: 'prev', pos: prev !== null ? prev : -40 },
        { name: 'curr', pos: curr }
      ]},
      codeLine: 5, codeExplanation: '反转当前节点的指针方向'
    })

    prev = curr
    curr = next
    nodes.forEach(n => n.state = 'normal')
    if (curr < nodes.length) nodes[curr].state = 'current'
    if (prev < nodes.length) nodes[prev].state = 'done'

    steps.push({
      narration: `移动：prev = ${prev < nodes.length ? nodes[prev].value : 'null'}, curr = ${curr < nodes.length ? nodes[curr].value : 'null'}`,
      type: 'linked_list', listState: { nodes: clone(nodes), pointers: [
        { name: 'prev', pos: prev < nodes.length ? prev : -40 },
        { name: 'curr', pos: curr < nodes.length ? curr : -40 }
      ]},
      codeLine: 6, codeExplanation: 'prev 前进到 curr，curr 前进到 next'
    })
  }

  nodes.forEach(n => n.state = 'visited')
  steps.push({
    narration: '链表反转完成！prev 指向新头节点 ✅',
    type: 'linked_list', listState: { nodes: clone(nodes), pointers: [{ name: 'prev (new head)', pos: prev }] },
    codeLine: -1, codeExplanation: '时间复杂度 O(n)，空间 O(1)'
  })

  return steps.map((s, i) => ({ ...s, step: i + 1 }))
}

// ============================================================
// 14-15. 链表插入 / 删除（简化）
// ============================================================
export function linkedListInsertSteps() {
  const values = [1, 2, 4, 5]
  const insertVal = 3
  const insertPos = 2
  const steps = []

  let nodes = values.map((v, i) => ({
    value: v, x: 60 + i * 110, y: 100, state: 'normal', next: true
  }))

  steps.push({
    narration: `链表插入：在 ${values[insertPos - 1]} 和 ${values[insertPos]} 之间插入 ${insertVal}`,
    type: 'linked_list', listState: { nodes: clone(nodes), pointers: [] },
    codeLine: 0, codeExplanation: '在链表中指定位置插入新节点'
  })

  // 找到插入位置
  nodes[insertPos - 1].state = 'current'
  steps.push({
    narration: `找到前驱节点 ${values[insertPos - 1]}（要插在它后面）`,
    type: 'linked_list', listState: { nodes: clone(nodes), pointers: [{ name: '插入位置前', pos: insertPos - 1 }] },
    codeLine: 3, codeExplanation: '遍历找到插入位置的前驱节点'
  })

  // 创建新节点
  const newNode = { value: insertVal, x: 60 + insertPos * 110 + 30, y: 220, state: 'inserting', next: true }
  nodes.push(newNode)
  steps.push({
    narration: `创建新节点 ${insertVal}`,
    type: 'linked_list', listState: { nodes: clone(nodes), pointers: [] },
    codeLine: 4, codeExplanation: 'new Node(value)'
  })

  // 重排后的节点
  const finalNodes = [1, 2, 3, 4, 5].map((v, i) => ({
    value: v, x: 60 + i * 110, y: 100, state: 'normal', next: i < 4
  }))
  finalNodes[2].state = 'sorted'

  steps.push({
    narration: `插入完成！新节点 ${insertVal} 已链接到链表中 ✅`,
    type: 'linked_list', listState: { nodes: clone(finalNodes), pointers: [] },
    codeLine: -1, codeExplanation: '链表插入 O(n) 查找 + O(1) 插入'
  })

  return steps.map((s, i) => ({ ...s, step: i + 1 }))
}

export function linkedListDeleteSteps() {
  const values = [1, 2, 3, 4, 5]
  const deleteVal = 3
  const deletePos = 2
  const steps = []

  let nodes = values.map((v, i) => ({
    value: v, x: 60 + i * 110, y: 100, state: 'normal', next: true
  }))

  steps.push({
    narration: `链表删除：删除节点 ${deleteVal}`,
    type: 'linked_list', listState: { nodes: clone(nodes), pointers: [] },
    codeLine: 0, codeExplanation: '在链表中删除指定节点'
  })

  nodes[deletePos - 1].state = 'current'
  steps.push({
    narration: `找到 ${deleteVal} 的前驱节点 ${nodes[deletePos - 1].value}`,
    type: 'linked_list', listState: { nodes: clone(nodes), pointers: [{ name: '前驱', pos: deletePos - 1 }] },
    codeLine: 3, codeExplanation: '遍历找到待删除节点的前驱'
  })

  nodes[deletePos].state = 'deleting'
  steps.push({
    narration: `找到待删除节点 ${deleteVal}`,
    type: 'linked_list', listState: { nodes: clone(nodes), pointers: [{ name: '待删除', pos: deletePos }] },
    codeLine: 4, codeExplanation: '标记待删除节点'
  })

  // 跳过
  const finalNodes = [1, 2, 4, 5].map((v, i) => ({
    value: v, x: 60 + i * 110, y: 100, state: 'normal', next: i < 3
  }))

  steps.push({
    narration: `删除完成！前驱 ${nodes[deletePos - 1].value} 的 next 跳过 ${deleteVal}，直接指向 ${nodes[deletePos + 1].value} ✅`,
    type: 'linked_list', listState: { nodes: clone(finalNodes), pointers: [] },
    codeLine: -1, codeExplanation: '链表删除 O(n) 查找 + O(1) 删除'
  })

  return steps.map((s, i) => ({ ...s, step: i + 1 }))
}

// ============================================================
// 导出预设注册表
// ============================================================

export const ALGO_PRESETS = [
  // ── 排序 ──
  {
    id: 'bubble_sort', name: '冒泡排序', icon: '🫧', category: 'sorting', difficulty: '基础',
    complexity: { time: 'O(n²)', space: 'O(1)' },
    code: `function bubbleSort(arr) {
  for (let i = 0; i < arr.length - 1; i++) {
    for (let j = 0; j < arr.length - 1 - i; j++) {
      if (arr[j] > arr[j + 1]) {
        [arr[j], arr[j + 1]] = [arr[j + 1], arr[j]]
      }
    }
  }
  return arr
}`,
    defaultData: [5, 3, 8, 2, 1, 4],
    generator: bubbleSortSteps
  },
  {
    id: 'quick_sort', name: '快速排序', icon: '⚡', category: 'sorting', difficulty: '重点',
    complexity: { time: 'O(n log n) 平均 / O(n²) 最坏', space: 'O(log n)' },
    code: `function quickSort(arr, low = 0, high = arr.length - 1) {
  if (low < high) {
    const pi = partition(arr, low, high)
    quickSort(arr, low, pi - 1)
    quickSort(arr, pi + 1, high)
  }
  return arr
}
function partition(arr, low, high) {
  const pivot = arr[high]
  let i = low - 1
  for (let j = low; j < high; j++) {
    if (arr[j] < pivot) {
      i++
      [arr[i], arr[j]] = [arr[j], arr[i]]
    }
  }
  [arr[i + 1], arr[high]] = [arr[high], arr[i + 1]]
  return i + 1
}`,
    defaultData: [8, 3, 9, 2, 1, 5, 7, 4, 6],
    generator: quickSortSteps
  },
  {
    id: 'merge_sort', name: '归并排序', icon: '🔀', category: 'sorting', difficulty: '经典',
    complexity: { time: 'O(n log n)', space: 'O(n)' },
    code: `function mergeSort(arr) {
  if (arr.length <= 1) return arr
  const mid = Math.floor(arr.length / 2)
  const left = mergeSort(arr.slice(0, mid))
  const right = mergeSort(arr.slice(mid))
  return merge(left, right)
}
function merge(left, right) {
  const result = []
  let i = 0, j = 0
  while (i < left.length && j < right.length) {
    if (left[i] <= right[j]) result.push(left[i++])
    else result.push(right[j++])
  }
  return [...result, ...left.slice(i), ...right.slice(j)]
}`,
    defaultData: [38, 27, 43, 3, 9, 82, 10],
    generator: mergeSortSteps
  },
  {
    id: 'insertion_sort', name: '插入排序', icon: '📥', category: 'sorting', difficulty: '基础',
    complexity: { time: 'O(n²)', space: 'O(1)' },
    code: `function insertionSort(arr) {
  for (let i = 1; i < arr.length; i++) {
    let key = arr[i]
    let j = i - 1
    while (j >= 0 && arr[j] > key) {
      arr[j + 1] = arr[j]
      j--
    }
    arr[j + 1] = key
  }
  return arr
}`,
    defaultData: [5, 2, 4, 6, 1, 3],
    generator: insertionSortSteps
  },
  {
    id: 'selection_sort', name: '选择排序', icon: '👆', category: 'sorting', difficulty: '基础',
    complexity: { time: 'O(n²)', space: 'O(1)' },
    code: `function selectionSort(arr) {
  for (let i = 0; i < arr.length - 1; i++) {
    let minIdx = i
    for (let j = i + 1; j < arr.length; j++) {
      if (arr[j] < arr[minIdx]) minIdx = j
    }
    [arr[i], arr[minIdx]] = [arr[minIdx], arr[i]]
  }
  return arr
}`,
    defaultData: [64, 25, 12, 22, 11],
    generator: selectionSortSteps
  },
  {
    id: 'heap_sort', name: '堆排序', icon: '⛰️', category: 'sorting', difficulty: '进阶',
    complexity: { time: 'O(n log n)', space: 'O(1)' },
    code: `function heapSort(arr) {
  const n = arr.length
  // 建堆
  for (let i = Math.floor(n / 2) - 1; i >= 0; i--)
    heapify(arr, n, i)
  // 逐个取堆顶
  for (let i = n - 1; i > 0; i--) {
    [arr[0], arr[i]] = [arr[i], arr[0]]
    heapify(arr, i, 0)
  }
  return arr
}
function heapify(arr, n, i) {
  let largest = i
  const l = 2 * i + 1, r = 2 * i + 2
  if (l < n && arr[l] > arr[largest]) largest = l
  if (r < n && arr[r] > arr[largest]) largest = r
  if (largest !== i) {
    [arr[i], arr[largest]] = [arr[largest], arr[i]]
    heapify(arr, n, largest)
  }
}`,
    defaultData: [12, 11, 13, 5, 6, 7],
    generator: heapSortSteps
  },

  // ── 搜索 ──
  {
    id: 'binary_search', name: '二分查找', icon: '🔍', category: 'search', difficulty: '基础',
    complexity: { time: 'O(log n)', space: 'O(1)' },
    code: `function binarySearch(arr, target) {
  let low = 0, high = arr.length - 1
  while (low <= high) {
    const mid = Math.floor((low + high) / 2)
    if (arr[mid] === target) return mid
    if (arr[mid] < target) low = mid + 1
    else high = mid - 1
  }
  return -1
}`,
    defaultData: [3, 7, 11, 18, 25, 33, 42, 56, 69, 77, 88, 95],
    generator: (data) => binarySearchSteps(data, 42)
  },

  // ── 树 ──
  {
    id: 'bst_insert', name: 'BST 插入', icon: '🌳', category: 'tree', difficulty: '进阶',
    complexity: { time: 'O(h), 平均 O(log n)', space: 'O(1)' },
    code: `function insert(root, value) {
  if (!root) return new Node(value)
  if (value < root.value)
    root.left = insert(root.left, value)
  else if (value > root.value)
    root.right = insert(root.right, value)
  return root
}`,
    defaultData: null,
    generator: bstInsertSteps
  },
  {
    id: 'avl_rotate_left', name: 'AVL 左旋', icon: '↩️', category: 'tree', difficulty: '重点',
    complexity: { time: 'O(1)', space: 'O(1)' },
    code: `function rotateLeft(y) {
  let x = y.right
  let T2 = x.left
  x.left = y
  y.right = T2
  // 更新高度
  y.height = max(height(y.left),
                height(y.right)) + 1
  x.height = max(height(x.left),
                height(x.right)) + 1
  return x
}`,
    defaultData: null,
    generator: avlRotateLeftSteps
  },
  {
    id: 'avl_rotate_right', name: 'AVL 右旋', icon: '↪️', category: 'tree', difficulty: '重点',
    complexity: { time: 'O(1)', space: 'O(1)' },
    code: `function rotateRight(y) {
  let x = y.left
  let T2 = x.right
  x.right = y
  y.left = T2
  // 更新高度
  y.height = max(height(y.left),
                height(y.right)) + 1
  x.height = max(height(x.left),
                height(x.right)) + 1
  return x
}`,
    defaultData: null,
    generator: avlRotateRightSteps
  },

  // ── 图 ──
  {
    id: 'graph_bfs', name: 'BFS 广度优先', icon: '🌊', category: 'graph', difficulty: '进阶',
    complexity: { time: 'O(V+E)', space: 'O(V)' },
    code: `function bfs(graph, start) {
  const visited = new Set()
  const queue = [start]
  visited.add(start)
  while (queue.length > 0) {
    const node = queue.shift()
    for (const n of graph[node]) {
      if (!visited.has(n)) {
        visited.add(n)
        queue.push(n)
      }
    }
  }
}`,
    defaultData: null,
    generator: bfsSteps
  },
  {
    id: 'graph_dfs', name: 'DFS 深度优先', icon: '🔎', category: 'graph', difficulty: '进阶',
    complexity: { time: 'O(V+E)', space: 'O(V)' },
    code: `function dfs(graph, start) {
  const visited = new Set()
  function explore(node) {
    visited.add(node)
    for (const n of graph[node]) {
      if (!visited.has(n))
        explore(n)
    }
  }
  explore(start)
}`,
    defaultData: null,
    generator: dfsSteps
  },

  // ── 链表 ──
  {
    id: 'linked_list_reverse', name: '链表反转', icon: '🔗', category: 'linked_list', difficulty: '基础',
    complexity: { time: 'O(n)', space: 'O(1)' },
    code: `function reverse(head) {
  let prev = null
  let curr = head
  while (curr) {
    let next = curr.next
    curr.next = prev
    prev = curr
    curr = next
  }
  return prev
}`,
    defaultData: null,
    generator: linkedListReverseSteps
  },
  {
    id: 'linked_list_insert', name: '链表插入', icon: '➕', category: 'linked_list', difficulty: '基础',
    complexity: { time: 'O(n)', space: 'O(1)' },
    code: `function insertAfter(prev, value) {
  const newNode = new Node(value)
  newNode.next = prev.next
  prev.next = newNode
}`,
    defaultData: null,
    generator: linkedListInsertSteps
  },
  {
    id: 'linked_list_delete', name: '链表删除', icon: '➖', category: 'linked_list', difficulty: '基础',
    complexity: { time: 'O(n)', space: 'O(1)' },
    code: `function deleteNode(prev) {
  if (!prev || !prev.next) return
  prev.next = prev.next.next
}`,
    defaultData: null,
    generator: linkedListDeleteSteps
  }
]

// 分类显示用的分组
export const CATEGORY_GROUPS = [
  { key: 'sorting', label: '排序算法' },
  { key: 'search', label: '搜索算法' },
  { key: 'tree', label: '树结构' },
  { key: 'graph', label: '图算法' },
  { key: 'linked_list', label: '线性结构' }
]

