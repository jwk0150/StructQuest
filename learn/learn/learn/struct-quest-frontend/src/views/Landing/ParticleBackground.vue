<template>
  <canvas
    ref="canvasRef"
    class="particle-canvas"
    :style="{ opacity: isReady ? 1 : 0 }"
  />
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

const canvasRef = ref(null)
const isReady = ref(false)

// ═══════════════════════════════════
// PARTICLE SYSTEM CONFIG
// ═══════════════════════════════════
const CONFIG = {
  particleCount: 120,
  colors: ['#4F7CFF', '#818CF8', '#6366F1', '#A78BFA', '#93C5FD'],
  maxRadius: 3,
  minRadius: 1.2,
  connectionDistance: 140,
  lineWidth: 0.6,
  speed: 0.35,
  morphSpeed: 0.025,
  holdDuration: 2800,    // ms to hold formation
  morphInterval: 5500,   // ms between morph cycles
  mouseRadius: 180,      // mouse repulsion radius
  mouseForce: 0.6,
}

// ═══════════════════════════════════
// DATA STRUCTURE PATTERNS
// ═══════════════════════════════════
const PATTERNS = [
  {
    name: 'binary-tree',
    generate(cx, cy, w, h) {
      const points = []
      const levels = [
        { y: cy - 150, nodes: 1, spread: 0 },
        { y: cy - 70, nodes: 2, spread: 100 },
        { y: cy + 10, nodes: 4, spread: 200 },
        { y: cy + 90, nodes: 8, spread: 320 },
      ]
      levels.forEach((level) => {
        for (let i = 0; i < level.nodes; i++) {
          const x = cx + (i - (level.nodes - 1) / 2) * (level.spread / Math.max(level.nodes - 1, 1))
          points.push({ x, y: level.y + (Math.random() - 0.5) * 16 })
        }
      })
      return points
    },
  },
  {
    name: 'graph-network',
    generate(cx, cy, w, h) {
      const points = []
      const nodeCount = 30
      const radius = 200
      for (let i = 0; i < nodeCount; i++) {
        const angle = (i / nodeCount) * Math.PI * 2 + (Math.random() - 0.5) * 0.3
        const r = radius * (0.4 + Math.random() * 0.6)
        points.push({
          x: cx + Math.cos(angle) * r,
          y: cy + Math.sin(angle) * r * 0.7,
        })
      }
      // Add central hub nodes
      for (let i = 0; i < 8; i++) {
        const angle = (i / 8) * Math.PI * 2
        const r = radius * (0.15 + Math.random() * 0.25)
        points.push({
          x: cx + Math.cos(angle) * r,
          y: cy + Math.sin(angle) * r * 0.7,
        })
      }
      return points
    },
  },
  {
    name: 'linked-list',
    generate(cx, cy, w, h) {
      const points = []
      const count = 18
      const startX = cx - 320
      const gap = 38
      for (let i = 0; i < count; i++) {
        points.push({
          x: startX + i * gap + (Math.random() - 0.5) * 10,
          y: cy + (Math.random() - 0.5) * 30,
        })
      }
      return points
    },
  },
  {
    name: 'spiral',
    generate(cx, cy, w, h) {
      const points = []
      const turns = 4
      const totalPoints = 50
      for (let i = 0; i < totalPoints; i++) {
        const t = i / totalPoints
        const angle = t * Math.PI * 2 * turns
        const r = t * 220
        points.push({
          x: cx + Math.cos(angle) * r,
          y: cy + Math.sin(angle) * r * 0.6,
        })
      }
      return points
    },
  },
  {
    name: 'grid-array',
    generate(cx, cy, w, h) {
      const points = []
      const cols = 10
      const rows = 8
      const cellW = 58
      const cellH = 44
      const startX = cx - (cols * cellW) / 2
      const startY = cy - (rows * cellH) / 2
      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          if (Math.random() > 0.3) {
            points.push({
              x: startX + c * cellW + (Math.random() - 0.5) * 12,
              y: startY + r * cellH + (Math.random() - 0.5) * 12,
            })
          }
        }
      }
      return points
    },
  },
]

// ═══════════════════════════════════
// STATE
// ═══════════════════════════════════
let ctx = null
let w = 0, h = 0
let cx = 0, cy = 0
let particles = []
let mouseX = -999, mouseY = -999
let animId = null
let currentPattern = 0
let morphTimer = 0
let holdTimer = 0
let state = 'idle' // idle | morphing | holding

function createParticle() {
  const angle = Math.random() * Math.PI * 2
  const radius = Math.random() * Math.min(w, h) * 0.45
  return {
    x: cx + Math.cos(angle) * radius,
    y: cy + Math.sin(angle) * radius,
    vx: (Math.random() - 0.5) * 0.5,
    vy: (Math.random() - 0.5) * 0.5,
    tx: 0,
    ty: 0,
    radius: CONFIG.minRadius + Math.random() * (CONFIG.maxRadius - CONFIG.minRadius),
    color: CONFIG.colors[Math.floor(Math.random() * CONFIG.colors.length)],
    alpha: 0.3 + Math.random() * 0.5,
    phase: Math.random() * Math.PI * 2,
  }
}

function initParticles() {
  particles = []
  for (let i = 0; i < CONFIG.particleCount; i++) {
    particles.push(createParticle())
  }
}

function assignTargets(pattern) {
  const targets = pattern.generate(cx, cy, w, h)
  // Assign targets to particles (some particles get targets, others stay random)
  const shuffled = [...particles].sort(() => Math.random() - 0.5)
  shuffled.forEach((p, i) => {
    if (i < targets.length) {
      p.tx = targets[i].x
      p.ty = targets[i].y
    } else {
      // Extra particles drift to random positions near the pattern
      const t = targets[i % targets.length]
      p.tx = t.x + (Math.random() - 0.5) * 120
      p.ty = t.y + (Math.random() - 0.5) * 120
    }
  })
}

// ═══════════════════════════════════
// UPDATE LOOP
// ═══════════════════════════════════
function update(dt) {
  // State machine timing
  if (state === 'idle') {
    morphTimer += dt
    if (morphTimer > CONFIG.morphInterval) {
      morphTimer = 0
      state = 'morphing'
      currentPattern = (currentPattern + 1) % PATTERNS.length
      assignTargets(PATTERNS[currentPattern])
    }
  } else if (state === 'morphing') {
    // Check if particles have reached targets
    let allSettled = true
    for (const p of particles) {
      const dx = p.tx - p.x
      const dy = p.ty - p.y
      if (Math.abs(dx) > 2 || Math.abs(dy) > 2) {
        allSettled = false
        break
      }
    }
    if (allSettled) {
      state = 'holding'
      holdTimer = 0
    }
  } else if (state === 'holding') {
    holdTimer += dt
    if (holdTimer > CONFIG.holdDuration) {
      state = 'idle'
      morphTimer = 0
    }
  }

  // Update each particle
  for (const p of particles) {
    if (state === 'morphing') {
      // Move toward target
      const dx = p.tx - p.x
      const dy = p.ty - p.y
      p.x += dx * CONFIG.morphSpeed
      p.y += dy * CONFIG.morphSpeed
      // Small jitter
      p.x += (Math.random() - 0.5) * 0.3
      p.y += (Math.random() - 0.5) * 0.3
    } else if (state === 'holding') {
      // Micro-vibrations while holding
      p.x += Math.sin(Date.now() * 0.003 + p.phase) * 0.15
      p.y += Math.cos(Date.now() * 0.003 + p.phase) * 0.15
    } else {
      // Free float (idle)
      p.x += p.vx * CONFIG.speed
      p.y += p.vy * CONFIG.speed

      // Slight attraction to center
      const dxc = cx - p.x
      const dyc = cy - p.y
      p.vx += dxc * 0.00008
      p.vy += dyc * 0.00008

      // Random direction changes
      p.vx += (Math.random() - 0.5) * 0.015
      p.vy += (Math.random() - 0.5) * 0.015

      // Damping
      p.vx *= 0.999
      p.vy *= 0.999

      // Speed limit
      const speed = Math.sqrt(p.vx * p.vx + p.vy * p.vy)
      if (speed > 0.8) {
        p.vx = (p.vx / speed) * 0.8
        p.vy = (p.vy / speed) * 0.8
      }

      // Boundary bounce
      if (p.x < 0) { p.x = 0; p.vx *= -0.5 }
      if (p.x > w) { p.x = w; p.vx *= -0.5 }
      if (p.y < 0) { p.y = 0; p.vy *= -0.5 }
      if (p.y > h) { p.y = h; p.vy *= -0.5 }
    }

    // Mouse repulsion
    const mdx = p.x - mouseX
    const mdy = p.y - mouseY
    const mdist = Math.sqrt(mdx * mdx + mdy * mdy)
    if (mdist < CONFIG.mouseRadius && mdist > 0) {
      const force = (1 - mdist / CONFIG.mouseRadius) * CONFIG.mouseForce
      p.x += (mdx / mdist) * force * 2
      p.y += (mdy / mdist) * force * 2
    }
  }
}

// ═══════════════════════════════════
// RENDER
// ═══════════════════════════════════
function render() {
  ctx.clearRect(0, 0, w, h)

  // Draw connections between nearby particles
  for (let i = 0; i < particles.length; i++) {
    for (let j = i + 1; j < particles.length; j++) {
      const dx = particles[i].x - particles[j].x
      const dy = particles[i].y - particles[j].y
      const dist = Math.sqrt(dx * dx + dy * dy)
      if (dist < CONFIG.connectionDistance) {
        const alpha = (1 - dist / CONFIG.connectionDistance) * 0.12
        ctx.strokeStyle = `rgba(79, 124, 255, ${alpha})`
        ctx.lineWidth = CONFIG.lineWidth
        ctx.beginPath()
        ctx.moveTo(particles[i].x, particles[i].y)
        ctx.lineTo(particles[j].x, particles[j].y)
        ctx.stroke()
      }
    }
  }

  // Draw particles
  for (const p of particles) {
    // Outer glow
    const glowRadius = p.radius * 3
    const glow = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, glowRadius)
    glow.addColorStop(0, p.color.replace(')', ', 0.3)').replace('rgb', 'rgba'))
    glow.addColorStop(0.5, p.color.replace(')', ', 0.08)').replace('rgb', 'rgba'))
    glow.addColorStop(1, 'rgba(79,124,255,0)')

    ctx.fillStyle = glow
    ctx.beginPath()
    ctx.arc(p.x, p.y, glowRadius, 0, Math.PI * 2)
    ctx.fill()

    // Core dot
    ctx.fillStyle = p.color
    ctx.globalAlpha = state === 'idle' ? p.alpha : Math.min(1, p.alpha + 0.3)
    ctx.beginPath()
    ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2)
    ctx.fill()
    ctx.globalAlpha = 1
  }
}

// ═══════════════════════════════════
// MAIN LOOP
// ═══════════════════════════════════
let lastTime = 0
function loop(time) {
  const dt = lastTime ? time - lastTime : 16
  lastTime = time
  update(dt)
  render()
  animId = requestAnimationFrame(loop)
}

// ═══════════════════════════════════
// RESIZE
// ═══════════════════════════════════
function resize() {
  const canvas = canvasRef.value
  if (!canvas) return
  const rect = canvas.parentElement.getBoundingClientRect()
  w = rect.width
  h = rect.height
  cx = w / 2
  cy = h / 2
  const dpr = Math.min(window.devicePixelRatio || 1, 2)
  canvas.width = w * dpr
  canvas.height = h * dpr
  canvas.style.width = w + 'px'
  canvas.style.height = h + 'px'
  ctx = canvas.getContext('2d')
  ctx.scale(dpr, dpr)
}

// ═══════════════════════════════════
// MOUSE
// ═══════════════════════════════════
function onMouseMove(e) {
  const rect = canvasRef.value.getBoundingClientRect()
  mouseX = e.clientX - rect.left
  mouseY = e.clientY - rect.top
}

function onMouseLeave() {
  mouseX = -999
  mouseY = -999
}

// ═══════════════════════════════════
// LIFECYCLE
// ═══════════════════════════════════
onMounted(() => {
  resize()
  initParticles()

  window.addEventListener('resize', () => {
    resize()
    initParticles()
  })
  window.addEventListener('mousemove', onMouseMove, { passive: true })
  canvasRef.value?.parentElement?.addEventListener('mouseleave', onMouseLeave)

  animId = requestAnimationFrame(loop)
  setTimeout(() => { isReady.value = true }, 300)
})

onBeforeUnmount(() => {
  cancelAnimationFrame(animId)
  window.removeEventListener('mousemove', onMouseMove)
  canvasRef.value?.parentElement?.removeEventListener('mouseleave', onMouseLeave)
})
</script>

<style lang="scss" scoped>
.particle-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
  transition: opacity 0.8s ease;
}
</style>
