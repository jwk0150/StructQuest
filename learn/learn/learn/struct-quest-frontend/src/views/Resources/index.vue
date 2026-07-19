<template>
  <div class="adventure-page" :class="`theme-${currentLevel.theme}`">
    <header class="adventure-topbar">
      <div class="brand-block">
        <span class="brand-mark">DV</span>
        <div>
          <strong>DataVerse</strong>
          <small>剧情模式：{{ currentLevel.world }}</small>
        </div>
      </div>
      <div class="topbar-center">
        <span>{{ currentLevel.storyTitle }}</span>
        <strong>当前知识：{{ currentLevel.concept }}</strong>
      </div>
      <button class="ghost-btn" @click="$router.push('/app')">返回首页</button>
    </header>

    <main class="adventure-layout">
      <aside class="task-panel panel-surface">
        <div class="panel-title">
          <span>任务栏</span>
          <small>{{ completedLevels.length }}/{{ levels.length }} 完成</small>
        </div>
        <button
          v-for="(level, index) in levels"
          :key="level.id"
          class="task-item"
          :class="{ active: currentLevel.id === level.id, done: completedLevels.includes(level.id) }"
          @click="selectLevel(index)"
        >
          <i>{{ index + 1 }}</i>
          <div>
            <strong>{{ level.title }}</strong>
            <small>{{ level.concept }}</small>
          </div>
        </button>
        <div class="reward-box">
          <span>奖励徽章</span>
          <div class="badge-row">
            <b v-for="level in levels" :key="level.id" :class="{ unlocked: completedLevels.includes(level.id) }">{{ level.badge }}</b>
          </div>
        </div>
      </aside>

      <section class="scene-shell panel-surface">
        <div class="scene-header">
          <div>
            <span>{{ selectedTheme.name }} · {{ currentLevel.world }}</span>
            <strong>{{ currentLevel.storyTitle }}</strong>
          </div>
          <button class="primary-mini" @click="openMiniGame">开始小游戏</button>
        </div>
        <div ref="sceneHost" class="scene-host">
          <canvas ref="sceneCanvas" class="three-canvas"></canvas>
          <div ref="playerRef" class="scene-actor player" :style="currentLevel.playerStyle">学生</div>
          <button ref="npcRef" class="scene-actor npc" :style="currentLevel.npcStyle" @click="showNpcDialogue">
            {{ currentLevel.npcName }}
          </button>
          <button
            ref="goalRef"
            class="knowledge-object"
            :style="currentLevel.goalStyle"
            @click="openMiniGame"
          >
            <span>{{ currentLevel.goalIcon }}</span>
            <strong>{{ currentLevel.goalName }}</strong>
            <small>点击学习</small>
          </button>
          <div class="floating-tip">点击场景角色或知识物体推进剧情</div>
        </div>
      </section>

      <aside class="ai-panel panel-surface">
        <div class="panel-title">
          <span>AI助手</span>
          <small>Story Agent</small>
        </div>
        <div class="ai-card narrative-card">
          <span>当前剧情</span>
          <p>{{ currentLevel.scene }}</p>
        </div>
        <div class="ai-card">
          <span>NPC 对话</span>
          <p>{{ npcDialogue }}</p>
        </div>
        <div class="ai-card hint-card">
          <span>AI 提示</span>
          <p>{{ choiceFeedback }}</p>
        </div>
        <div class="ai-card knowledge-card-small">
          <span>知识讲解</span>
          <p>{{ currentLevel.knowledge }}</p>
        </div>
      </aside>
    </main>

    <footer class="bottom-dock panel-surface">
      <button :class="{ active: dockTab === 'dialogue' }" @click="dockTab = 'dialogue'">对话</button>
      <button :class="{ active: dockTab === 'bag' }" @click="dockTab = 'bag'">背包</button>
      <button :class="{ active: dockTab === 'ai' }" @click="dockTab = 'ai'">AI讲解</button>
      <button class="dock-next" :disabled="!solved" @click="nextLevel">下一步</button>
      <p>{{ dockText }}</p>
    </footer>

    <div v-if="miniGameOpen" class="modal-backdrop" @click.self="miniGameOpen = false">
      <section ref="miniGameRef" class="mini-game-modal panel-surface">
        <div class="modal-head">
          <div>
            <span>小游戏</span>
            <strong>{{ currentLevel.missionTitle }}</strong>
          </div>
          <button @click="miniGameOpen = false">×</button>
        </div>
        <div class="choice-strip">
          <button
            v-for="choice in currentLevel.choices"
            :key="choice.id"
            :class="{ selected: selectedChoice === choice.id }"
            @click="chooseStory(choice.id)"
          >
            {{ choice.text }}
          </button>
        </div>
        <p class="mission-text">{{ currentLevel.mission }}</p>
        <div class="node-board" @dragover.prevent>
          <div
            v-for="(node, index) in nodes"
            :key="node.id"
            class="game-node"
            draggable="true"
            :class="{ dragging: draggingIndex === index }"
            @dragstart="dragStart(index)"
            @dragenter.prevent="dragEnter(index)"
            @dragover.prevent
            @drop.prevent="dropNode(index)"
            @dragend="dragEnd"
          >
            {{ node.label }}
          </div>
        </div>
        <div class="target-row">
          <span>目标顺序</span>
          <strong>{{ currentLevel.targetOrder.join(' → ') }}</strong>
        </div>
        <div class="modal-actions">
          <button class="primary-action" @click="checkAnswer">检查答案</button>
          <button class="secondary-action" @click="shuffleNodes">打乱重来</button>
          <button class="secondary-action" @click="playScenePulse">播放动画</button>
        </div>
        <p class="game-feedback" :class="{ correct: solved, wrong: checked && !solved }">{{ gameFeedback }}</p>
      </section>
    </div>

    <div v-if="knowledgeOpen" class="modal-backdrop" @click.self="knowledgeOpen = false">
      <section class="knowledge-summary panel-surface">
        <span>知识总结</span>
        <h3>{{ currentLevel.concept }}</h3>
        <p>{{ summaryText }}</p>
        <button class="primary-action" @click="knowledgeOpen = false">收下徽章</button>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import * as THREE from 'three'
import { gsap } from 'gsap'

const themes = [
  { id: 'story', name: 'AI生成剧情', desc: '根据画像换皮肤' },
  { id: 'challenge', name: '挑战模式', desc: '先玩再讲' },
]

const levels = [
  {
    id: 'avl', theme: 'forest', badge: '树', title: '树之森林', concept: 'AVL 树', world: '树之森林', storyTitle: '修复失衡的世界树',
    goalIcon: 'AVL', goalName: '世界树', npcName: '森林长老', missionTitle: '恢复 AVL 平衡',
    scene: '世界树左侧枝干过重，长老请求你通过一次旋转恢复平衡。',
    mission: '把节点拖成右旋之后的平衡顺序。提示：10 左边挂 8，8 左边挂 5，需要右旋。',
    targetOrder: ['8', '5', '10', '20'],
    knowledge: 'AVL 树会在插入或删除后检查平衡因子，失衡时通过左旋或右旋恢复高度平衡。',
    choices: [
      { id: 'right', text: '对 10 执行右旋，让 8 成为新的局部根。', correct: true },
      { id: 'wrong1', text: '继续往左插入，让树自然长高。', correct: false },
      { id: 'wrong2', text: '删除最小节点，暂时不考虑旋转。', correct: false },
    ],
    playerStyle: { left: '42%', top: '61%' }, npcStyle: { left: '24%', top: '48%' }, goalStyle: { left: '58%', top: '35%' },
  },
  {
    id: 'stack', theme: 'ruins', badge: '栈', title: '古墓回廊', concept: 'Stack / LIFO', world: '神秘古墓', storyTitle: '回溯机关',
    goalIcon: 'LIFO', goalName: '石门机关', npcName: '守墓人', missionTitle: '按原路返回',
    scene: '你依次进入 A、B、C、D 四个房间，机关启动后只能从最后进入的房间开始退出。',
    mission: '拖出正确返回顺序。最后进入的房间必须最先离开。',
    targetOrder: ['D', 'C', 'B', 'A'],
    knowledge: '栈遵守后进先出，最后压入的元素最先弹出。函数调用、撤销操作都常用栈。',
    choices: [
      { id: 'right', text: '从 D 开始返回，然后 C、B、A。', correct: true },
      { id: 'wrong1', text: '从入口 A 开始返回。', correct: false },
      { id: 'wrong2', text: '随机找一个门出去。', correct: false },
    ],
    playerStyle: { left: '47%', top: '60%' }, npcStyle: { left: '23%', top: '43%' }, goalStyle: { left: '62%', top: '34%' },
  },
  {
    id: 'queue', theme: 'station', badge: '队', title: '地铁站台', concept: 'Queue / FIFO', world: '线性王国', storyTitle: '排队进站',
    goalIcon: 'FIFO', goalName: '检票口', npcName: '站务员', missionTitle: '维护队列秩序',
    scene: '乘客 A、B、C、D 已经排队，E 刚到。站务员要求按到达顺序检票。',
    mission: '拖出正确检票顺序。队列只能从队首出队。',
    targetOrder: ['A', 'B', 'C', 'D', 'E'],
    knowledge: '队列遵守先进先出，先进入队列的元素先被处理。',
    choices: [
      { id: 'right', text: '先检票 A，再依次处理后面的乘客。', correct: true },
      { id: 'wrong1', text: '让 D 先走，因为他看起来更急。', correct: false },
      { id: 'wrong2', text: '让 E 插到最前面。', correct: false },
    ],
    playerStyle: { left: '37%', top: '61%' }, npcStyle: { left: '70%', top: '46%' }, goalStyle: { left: '55%', top: '39%' },
  },
  {
    id: 'graph', theme: 'city', badge: '图', title: '城市地图', concept: 'BFS 最短路', world: '图论大陆', storyTitle: '消防救援路线',
    goalIcon: 'BFS', goalName: '城市路网', npcName: '调度员', missionTitle: '逐层搜索',
    scene: '消防员从起点出发，要最快覆盖附近街区，先搜索第一层，再进入第二层。',
    mission: '拖出 BFS 的层序扩展顺序。',
    targetOrder: ['起点', '第一层A', '第一层B', '第二层C', '第二层D'],
    knowledge: 'BFS 按层扩展，常用于无权图中寻找最短路径。',
    choices: [
      { id: 'right', text: '先搜索离起点最近的一整层。', correct: true },
      { id: 'wrong1', text: '沿一条街一直走到底。', correct: false },
      { id: 'wrong2', text: '跳过第一层，直接去远处。', correct: false },
    ],
    playerStyle: { left: '33%', top: '61%' }, npcStyle: { left: '18%', top: '45%' }, goalStyle: { left: '62%', top: '38%' },
  },
  {
    id: 'hash', theme: 'library', badge: '哈', title: '哈希图书馆', concept: 'Hash Table', world: '哈希实验室', storyTitle: '姓名到书架',
    goalIcon: 'Hash', goalName: '编号书架', npcName: '管理员', missionTitle: '快速定位',
    scene: '输入姓名“张三”，系统要立刻定位到书架 07，而不是一本本查找。',
    mission: '拖出哈希表查找流程。',
    targetOrder: ['张三', 'hash()', '书架 07', '直接取书'],
    knowledge: '哈希表用函数把 key 映射到位置，从而接近 O(1) 查找。',
    choices: [
      { id: 'right', text: '先计算 hash，再定位书架。', correct: true },
      { id: 'wrong1', text: '从第一排开始一本一本找。', correct: false },
      { id: 'wrong2', text: '随机打开一个书架。', correct: false },
    ],
    playerStyle: { left: '43%', top: '62%' }, npcStyle: { left: '21%', top: '45%' }, goalStyle: { left: '62%', top: '35%' },
  },
]

const currentLevelIndex = ref(0)
const selectedThemeId = ref('story')
const selectedChoice = ref(null)
const nodes = ref([])
const draggingIndex = ref(null)
const checked = ref(false)
const solved = ref(false)
const completedLevels = ref([])
const gameFeedback = ref('拖动节点，把它们排成符合规则的顺序。')
const miniGameOpen = ref(false)
const knowledgeOpen = ref(false)
const dockTab = ref('dialogue')
const sceneCanvas = ref(null)
const sceneHost = ref(null)
const playerRef = ref(null)
const npcRef = ref(null)
const goalRef = ref(null)
const miniGameRef = ref(null)

let renderer = null
let scene = null
let camera = null
let animationId = null
let sceneObjects = []
let resizeObserver = null
let mm = null

const currentLevel = computed(() => levels[currentLevelIndex.value])
const selectedTheme = computed(() => themes.find(item => item.id === selectedThemeId.value) || themes[0])
const selectedChoiceData = computed(() => currentLevel.value.choices.find(item => item.id === selectedChoice.value))
const npcDialogue = computed(() => {
  if (solved.value) return `做得好。${currentLevel.value.knowledge}`
  if (selectedChoiceData.value?.correct) return '方向对了。现在把节点拖成正确顺序，规则就会显形。'
  return '年轻的学习者，先观察“谁先进入、谁先离开”，不要急着背定义。'
})
const choiceFeedback = computed(() => {
  if (!selectedChoiceData.value) return '先点击 NPC 或选择一个剧情行动，AI 会解释它是否符合当前数据结构。'
  return selectedChoiceData.value.correct ? `正确。${currentLevel.value.knowledge}` : '这个选择违反了结构约束。回到场景里，想想操作顺序。'
})
const summaryText = computed(() => {
  if (solved.value && selectedChoiceData.value?.correct) return `你完成了 ${currentLevel.value.storyTitle}。真正掌握的是：${currentLevel.value.knowledge}`
  return `完成剧情选择和拖拽小游戏后，这里会把故事经验总结成「${currentLevel.value.concept}」。`
})
const dockText = computed(() => {
  if (dockTab.value === 'bag') return `背包：${completedLevels.value.length ? completedLevels.value.map(id => levels.find(l => l.id === id)?.badge).join('、') : '还没有徽章，完成小游戏后会获得奖励。'}`
  if (dockTab.value === 'ai') return choiceFeedback.value
  return npcDialogue.value
})

function makeNodes(order) {
  return order.map((label, index) => ({ id: `${currentLevel.value.id}-${label}-${index}`, label }))
}
function shuffle(list) {
  const next = [...list]
  for (let i = next.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[next[i], next[j]] = [next[j], next[i]]
  }
  return next
}
function shuffleNodes() {
  nodes.value = makeNodes(shuffle(currentLevel.value.targetOrder))
  checked.value = false
  solved.value = false
  gameFeedback.value = '拖动节点，把它们排成符合规则的顺序。'
}
function resetLevel() {
  selectedChoice.value = null
  knowledgeOpen.value = false
  shuffleNodes()
  nextTick(() => playScenePulse())
}
function selectLevel(index) {
  currentLevelIndex.value = index
  resetLevel()
}
function chooseStory(choiceId) {
  selectedChoice.value = choiceId
  gsap.fromTo('.feedback, .hint-card', { scale: 0.98 }, { scale: 1, duration: 0.35, ease: 'back.out(1.7)' })
}
function dragStart(index) {
  draggingIndex.value = index
}
function dragEnter(index) {
  if (draggingIndex.value === null || draggingIndex.value === index) return
  const next = [...nodes.value]
  const [moving] = next.splice(draggingIndex.value, 1)
  next.splice(index, 0, moving)
  nodes.value = next
  draggingIndex.value = index
}
function dropNode(index) {
  dragEnter(index)
  dragEnd()
}
function dragEnd() {
  draggingIndex.value = null
}
function checkAnswer() {
  const current = nodes.value.map(item => item.label)
  const target = currentLevel.value.targetOrder
  checked.value = true
  solved.value = current.every((item, index) => item === target[index])
  gameFeedback.value = solved.value ? `正确。${currentLevel.value.knowledge}` : '顺序还不对。回到剧情限制，想想谁应该先被处理。'
  if (solved.value && !completedLevels.value.includes(currentLevel.value.id)) completedLevels.value.push(currentLevel.value.id)
  if (solved.value) {
    knowledgeOpen.value = true
    gsap.to(goalRef.value, { y: -12, scale: 1.08, repeat: 1, yoyo: true, duration: 0.35, ease: 'power2.out' })
  }
}
function nextLevel() {
  if (!solved.value) return
  currentLevelIndex.value = (currentLevelIndex.value + 1) % levels.length
  miniGameOpen.value = false
  resetLevel()
}
function openMiniGame() {
  miniGameOpen.value = true
  nextTick(() => {
    gsap.fromTo(miniGameRef.value, { y: 24, autoAlpha: 0, scale: 0.98 }, { y: 0, autoAlpha: 1, scale: 1, duration: 0.36, ease: 'power3.out' })
  })
}
function showNpcDialogue() {
  dockTab.value = 'dialogue'
  gsap.fromTo(npcRef.value, { y: 0 }, { y: -10, repeat: 1, yoyo: true, duration: 0.25, ease: 'power2.out' })
}
function playScenePulse() {
  gsap.fromTo([playerRef.value, npcRef.value, goalRef.value].filter(Boolean), { y: 8, autoAlpha: 0.72 }, { y: 0, autoAlpha: 1, duration: 0.6, stagger: 0.08, ease: 'back.out(1.6)' })
}
function selectTheme(themeId) {
  selectedThemeId.value = themeId
  playScenePulse()
}

function setupThree() {
  if (!sceneCanvas.value || renderer) return
  renderer = new THREE.WebGLRenderer({ canvas: sceneCanvas.value, antialias: true, alpha: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
  scene = new THREE.Scene()
  camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100)
  camera.position.set(0, 6.2, 10)
  camera.lookAt(0, 0, 0)
  resizeScene()
  rebuildScene()
  resizeObserver = new ResizeObserver(resizeScene)
  resizeObserver.observe(sceneHost.value)
  animateScene()
}
function resizeScene() {
  if (!renderer || !sceneHost.value || !camera) return
  const rect = sceneHost.value.getBoundingClientRect()
  const width = Math.max(1, rect.width)
  const height = Math.max(1, rect.height)
  renderer.setSize(width, height, false)
  camera.aspect = width / height
  camera.updateProjectionMatrix()
}
function clearThreeScene() {
  if (!scene) return
  sceneObjects.forEach(obj => {
    scene.remove(obj)
    obj.traverse?.(child => {
      child.geometry?.dispose?.()
      if (Array.isArray(child.material)) child.material.forEach(mat => mat.dispose?.())
      else child.material?.dispose?.()
    })
  })
  sceneObjects = []
}
function addObject(obj) {
  scene.add(obj)
  sceneObjects.push(obj)
  return obj
}
function mat(color, roughness = 0.85) {
  return new THREE.MeshStandardMaterial({ color, roughness, metalness: 0.02 })
}
function makeTree(x, z, scale = 1) {
  const group = new THREE.Group()
  const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.08 * scale, 0.12 * scale, 0.8 * scale, 8), mat('#8d6e63'))
  trunk.position.y = 0.4 * scale
  const crown = new THREE.Mesh(new THREE.ConeGeometry(0.5 * scale, 1.25 * scale, 8), mat('#4caf50'))
  crown.position.y = 1.25 * scale
  group.add(trunk, crown)
  group.position.set(x, 0, z)
  return group
}
function makeBuilding(x, z, color = '#90a4ae') {
  const group = new THREE.Group()
  const body = new THREE.Mesh(new THREE.BoxGeometry(0.8, 1.4, 0.8), mat(color))
  body.position.y = 0.7
  const roof = new THREE.Mesh(new THREE.ConeGeometry(0.65, 0.45, 4), mat('#546e7a'))
  roof.position.y = 1.6
  roof.rotation.y = Math.PI / 4
  group.add(body, roof)
  group.position.set(x, 0, z)
  return group
}
function rebuildScene() {
  if (!scene) return
  clearThreeScene()
  const palette = {
    forest: { bg: '#dff3e5', ground: '#a5d6a7', accent: '#2e7d32' },
    ruins: { bg: '#eadfce', ground: '#b8a88a', accent: '#795548' },
    station: { bg: '#e8f4fb', ground: '#b0bec5', accent: '#607d8b' },
    city: { bg: '#e9f1ff', ground: '#b9c7d8', accent: '#3f51b5' },
    library: { bg: '#f4eadb', ground: '#d6c3a5', accent: '#8d6e63' },
  }[currentLevel.value.theme]
  scene.background = new THREE.Color(palette.bg)
  addObject(new THREE.HemisphereLight('#ffffff', palette.ground, 1.8))
  const sun = new THREE.DirectionalLight('#ffffff', 2.2)
  sun.position.set(4, 7, 5)
  addObject(sun)
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(18, 12), mat(palette.ground))
  ground.rotation.x = -Math.PI / 2
  ground.position.z = -0.8
  addObject(ground)
  for (let i = 0; i < 4; i += 1) {
    const mountain = new THREE.Mesh(new THREE.ConeGeometry(1.6 + i * 0.2, 1.6, 4), mat(i % 2 ? '#b7c8d8' : '#a7bbc9'))
    mountain.position.set(-5 + i * 3.4, 0.8, -4.8)
    mountain.rotation.y = Math.PI / 4
    addObject(mountain)
  }
  if (currentLevel.value.theme === 'forest') {
    ;[[-4,-1.4,1.1],[-2.8,-3,0.8],[-1.2,-2,1.2],[3,-2.7,1],[4.4,-1,1.3],[1.6,-3.5,.9]].forEach(([x,z,s]) => addObject(makeTree(x,z,s)))
  } else if (currentLevel.value.theme === 'ruins') {
    ;[[-3,-2],[-1.5,-2.5],[1.5,-2.4],[3,-2]].forEach(([x,z]) => {
      const pillar = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.28, 1.8, 12), mat('#9e8f7a'))
      pillar.position.set(x, 0.9, z)
      addObject(pillar)
    })
  } else if (currentLevel.value.theme === 'station') {
    const platform = new THREE.Mesh(new THREE.BoxGeometry(8, 0.18, 1.1), mat('#78909c'))
    platform.position.set(0, 0.1, -2.2)
    addObject(platform)
    for (let i = 0; i < 5; i += 1) addObject(makeBuilding(-4 + i * 2, -4, '#b0bec5'))
  } else if (currentLevel.value.theme === 'city') {
    for (let i = 0; i < 7; i += 1) addObject(makeBuilding(-5 + i * 1.7, -3.5, i % 2 ? '#90caf9' : '#9fa8da'))
  } else {
    for (let i = 0; i < 6; i += 1) {
      const shelf = new THREE.Mesh(new THREE.BoxGeometry(0.75, 1.55, 0.4), mat(i % 2 ? '#a1887f' : '#8d6e63'))
      shelf.position.set(-4.5 + i * 1.8, 0.78, -2.8)
      addObject(shelf)
    }
  }
  const glow = new THREE.Mesh(new THREE.RingGeometry(1.1, 1.35, 48), new THREE.MeshBasicMaterial({ color: palette.accent, transparent: true, opacity: 0.28, side: THREE.DoubleSide }))
  glow.rotation.x = -Math.PI / 2
  glow.position.set(1.8, 0.025, -1.1)
  addObject(glow)
}
function animateScene() {
  if (!renderer || !scene || !camera) return
  sceneObjects.forEach((obj, index) => {
    if (obj.type === 'Group') obj.rotation.y += 0.0015 + index * 0.00004
  })
  renderer.render(scene, camera)
  animationId = requestAnimationFrame(animateScene)
}
function cleanupThree() {
  if (animationId) cancelAnimationFrame(animationId)
  resizeObserver?.disconnect()
  clearThreeScene()
  renderer?.dispose()
  renderer = null
  scene = null
  camera = null
}

watch(currentLevelIndex, () => {
  resetLevel()
  nextTick(() => rebuildScene())
}, { immediate: true })

onMounted(() => {
  setupThree()
  mm = gsap.matchMedia()
  mm.add('(prefers-reduced-motion: no-preference)', () => {
    gsap.from('.panel-surface', { y: 18, autoAlpha: 0, duration: 0.55, stagger: 0.08, ease: 'power2.out' })
    gsap.to('.floating-tip', { y: -8, repeat: -1, yoyo: true, duration: 1.8, ease: 'sine.inOut' })
  })
  playScenePulse()
})
onUnmounted(() => {
  mm?.revert()
  cleanupThree()
})
</script>

<style lang="scss" scoped>
.adventure-page{min-height:calc(100vh - var(--topnav-height));padding:14px 18px 16px;background:linear-gradient(180deg,#f4faf6,#e8f5e9);color:#1f3427;display:grid;grid-template-rows:auto minmax(0,1fr) auto;gap:12px;overflow:hidden;}
.panel-surface{border:1px solid rgba(255,255,255,.72);background:rgba(255,255,255,.72);box-shadow:0 18px 45px rgba(52,86,63,.12);backdrop-filter:blur(18px);border-radius:8px;}
.adventure-topbar{height:58px;display:flex;align-items:center;justify-content:space-between;gap:16px;padding:0 14px;border-radius:8px;background:rgba(255,255,255,.78);border:1px solid rgba(255,255,255,.8);box-shadow:0 10px 28px rgba(52,86,63,.08)}
.brand-block{display:flex;align-items:center;gap:10px;min-width:220px}.brand-mark{width:36px;height:36px;border-radius:8px;background:#4caf50;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:900}.brand-block strong{display:block;font-size:14px}.brand-block small,.topbar-center span{display:block;font-size:11px;color:#667c6b}.topbar-center{text-align:center}.topbar-center strong{display:block;margin-top:3px;font-size:16px;color:#284632}.ghost-btn{height:34px;padding:0 13px;border:1px solid rgba(76,175,80,.24);border-radius:8px;background:#fff;color:#2e7d32;font-weight:800;cursor:pointer}
.adventure-layout{display:grid;grid-template-columns:210px minmax(0,1fr) 300px;gap:12px;min-height:0}.task-panel,.ai-panel{padding:12px;min-height:0;overflow:auto}.panel-title{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}.panel-title span{font-weight:900;font-size:14px}.panel-title small{font-size:11px;color:#718579}.task-item{width:100%;display:flex;align-items:center;gap:9px;padding:10px;margin-bottom:8px;border:1px solid rgba(76,175,80,.14);border-radius:8px;background:rgba(255,255,255,.68);text-align:left;cursor:pointer;transition:transform .18s,border-color .18s,background .18s}.task-item:hover{transform:translateY(-1px);border-color:rgba(76,175,80,.42)}.task-item.active{background:#eef8ef;border-color:#4caf50}.task-item.done i{background:#4caf50}.task-item i{width:28px;height:28px;border-radius:8px;background:#dfeee1;color:#2e7d32;display:flex;align-items:center;justify-content:center;font-style:normal;font-weight:900}.task-item strong{display:block;font-size:12px;color:#24362b}.task-item small{font-size:10px;color:#798a7f}.reward-box{margin-top:12px;padding:11px;border-radius:8px;background:#f7fbf7;border:1px solid rgba(76,175,80,.12)}.reward-box span{font-size:12px;font-weight:900}.badge-row{display:flex;flex-wrap:wrap;gap:6px;margin-top:9px}.badge-row b{width:28px;height:28px;border-radius:8px;background:#e6e9e7;color:#a1aaa5;display:flex;align-items:center;justify-content:center;font-size:12px}.badge-row b.unlocked{background:#4caf50;color:#fff}
.scene-shell{position:relative;overflow:hidden;display:grid;grid-template-rows:auto minmax(0,1fr)}.scene-header{height:58px;display:flex;align-items:center;justify-content:space-between;padding:0 14px;border-bottom:1px solid rgba(76,175,80,.13)}.scene-header span{display:block;font-size:11px;font-weight:900;color:#4caf50;text-transform:uppercase;letter-spacing:.08em}.scene-header strong{display:block;margin-top:2px;font-size:18px}.primary-mini{height:34px;padding:0 13px;border:0;border-radius:8px;background:#4caf50;color:#fff;font-weight:900;cursor:pointer}.scene-host{position:relative;min-height:430px;overflow:hidden;background:linear-gradient(180deg,rgba(255,255,255,.16),rgba(255,255,255,.04))}.three-canvas{position:absolute;inset:0;width:100%;height:100%;display:block}.scene-actor,.knowledge-object{position:absolute;z-index:2;border:0;border-radius:8px;transform:translate(-50%,-50%);box-shadow:0 12px 30px rgba(36,54,43,.18);cursor:pointer}.scene-actor{padding:10px 12px;background:#fff;color:#23372a;font-weight:900}.player{background:#fff7e8}.npc{background:#f0fff2}.knowledge-object{min-width:112px;padding:12px 14px;background:rgba(255,255,255,.84);color:#24362b;display:grid;gap:2px;text-align:center}.knowledge-object span{font-size:18px;font-weight:900;color:#4caf50}.knowledge-object strong{font-size:14px}.knowledge-object small{font-size:10px;color:#718579}.knowledge-object:hover{outline:2px solid rgba(76,175,80,.34)}.floating-tip{position:absolute;z-index:2;left:50%;bottom:18px;transform:translateX(-50%);padding:8px 12px;border-radius:999px;background:rgba(255,255,255,.78);font-size:12px;color:#52745c;border:1px solid rgba(255,255,255,.85)}
.ai-card{padding:12px;border-radius:8px;background:rgba(255,255,255,.7);border:1px solid rgba(76,175,80,.12);margin-bottom:10px}.ai-card span{display:block;margin-bottom:6px;font-size:11px;font-weight:900;color:#2e7d32;text-transform:uppercase;letter-spacing:.08em}.ai-card p{margin:0;font-size:13px;line-height:1.65;color:#405a48}.narrative-card{background:#f5fbf6}.hint-card{background:#fffaf1}.knowledge-card-small{background:#eef8ef}
.bottom-dock{height:58px;display:flex;align-items:center;gap:8px;padding:0 12px}.bottom-dock button{height:34px;padding:0 12px;border:1px solid rgba(76,175,80,.18);border-radius:8px;background:#fff;color:#52745c;font-weight:800;cursor:pointer}.bottom-dock button.active{background:#e9f6eb;color:#2e7d32}.bottom-dock .dock-next{margin-left:auto;background:#4caf50;color:#fff;border-color:#4caf50}.bottom-dock .dock-next:disabled{opacity:.45;cursor:not-allowed}.bottom-dock p{margin:0;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:13px;color:#405a48}
.modal-backdrop{position:fixed;inset:0;z-index:500;display:flex;align-items:center;justify-content:center;background:rgba(19,37,26,.36);backdrop-filter:blur(8px)}.mini-game-modal{width:min(760px,calc(100vw - 32px));padding:16px;background:rgba(255,255,255,.92)}.modal-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}.modal-head span,.knowledge-summary span{display:block;font-size:11px;font-weight:900;color:#2e7d32;text-transform:uppercase;letter-spacing:.08em}.modal-head strong{font-size:20px}.modal-head button{width:32px;height:32px;border:0;border-radius:8px;background:#eef5ef;font-size:20px;cursor:pointer}.choice-strip{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.choice-strip button{min-height:58px;padding:9px;border:1px solid rgba(76,175,80,.16);border-radius:8px;background:#fff;text-align:left;color:#304a38;cursor:pointer}.choice-strip button.selected{border-color:#4caf50;background:#edf8ef;font-weight:900}.mission-text{font-size:13px;line-height:1.6;color:#405a48}.node-board{display:flex;flex-wrap:wrap;gap:9px;min-height:104px;padding:12px;border:1px dashed #a8c7ad;border-radius:8px;background:#f6fbf7}.game-node{min-width:76px;height:46px;padding:0 12px;border-radius:8px;background:linear-gradient(135deg,#4caf50,#26a69a);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:900;cursor:grab;box-shadow:0 10px 18px rgba(76,175,80,.22);user-select:none}.game-node.dragging{opacity:.55;transform:scale(.96)}.target-row{display:grid;gap:4px;margin-top:10px;padding:10px;border-radius:8px;background:#f8fbf8;border:1px solid rgba(76,175,80,.12)}.target-row span{font-size:10px;color:#718579;font-weight:900;text-transform:uppercase}.target-row strong{font-size:13px;color:#304a38}.modal-actions{display:flex;gap:8px;margin-top:12px}.primary-action,.secondary-action{height:36px;padding:0 14px;border-radius:8px;font-weight:900;cursor:pointer}.primary-action{border:0;background:#4caf50;color:#fff}.secondary-action{border:1px solid #c7d7ca;background:#fff;color:#52745c}.game-feedback{margin:12px 0 0;padding:10px;border-radius:8px;background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;font-size:13px}.game-feedback.correct{background:#ecfdf3;border-color:#abefc6;color:#027a48}.game-feedback.wrong{background:#fef3f2;border-color:#fecdca;color:#b42318}.knowledge-summary{width:min(460px,calc(100vw - 32px));padding:22px;background:rgba(255,255,255,.94)}.knowledge-summary h3{margin:6px 0 10px;font-size:26px}.knowledge-summary p{font-size:14px;line-height:1.7;color:#405a48}
.theme-ruins{background:linear-gradient(180deg,#f2eadc,#ded0bd)}.theme-station{background:linear-gradient(180deg,#eff8fc,#dcecf2)}.theme-city{background:linear-gradient(180deg,#eef4ff,#dfe8f8)}.theme-library{background:linear-gradient(180deg,#f8f0e4,#eadcc8)}
@media(max-width:1180px){.adventure-page{overflow:auto}.adventure-layout{grid-template-columns:1fr}.task-panel{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.panel-title,.reward-box{grid-column:1/-1}.ai-panel{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.ai-panel .panel-title{grid-column:1/-1}.ai-card{margin:0}.bottom-dock{position:sticky;bottom:0}.choice-strip{grid-template-columns:1fr}.scene-host{min-height:360px}}
@media(max-width:760px){.adventure-page{padding:10px}.adventure-topbar{height:auto;display:grid;grid-template-columns:1fr;padding:12px}.topbar-center{text-align:left}.task-panel,.ai-panel{grid-template-columns:1fr}.bottom-dock{height:auto;flex-wrap:wrap;padding:10px}.bottom-dock .dock-next{margin-left:0}.bottom-dock p{flex-basis:100%;white-space:normal}.modal-actions{flex-direction:column}.primary-action,.secondary-action{width:100%}}
</style>