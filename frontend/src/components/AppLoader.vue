<script setup lang="ts">
import { ref, watch, onBeforeUnmount, useSlots } from 'vue'

// Polito-log comet loader: a teal dot sweeps along a short track, its tail
// stretching with speed. With a default slot it overlays the slotted content
// (like NSpin's `show`); without one it renders on its own.
const props = withDefaults(
  defineProps<{
    show?: boolean
    label?: string
  }>(),
  {
    show: true,
    label: 'loading',
  },
)

const slots = useSlots()
const canvas = ref<HTMLCanvasElement | null>(null)

const TEAL = '#63e2b7'
const CW = 80
const CH = 20
const TRACK_PX = 56
const DOT_R = 2
const TAIL_MIN = 2
const TAIL_MAX = 43
const HALF_CYCLE = 650

// Smooth ease-in-out: position as f(t), t ∈ [0,1]
function ease(t: number) {
  return (1 - Math.cos(Math.PI * t)) / 2
}

// Derivative of ease (normalized speed), peaks at t=0.5
function speed(t: number) {
  return Math.sin(Math.PI * t)
}

let rafId: number | null = null

function stop() {
  if (rafId !== null) {
    cancelAnimationFrame(rafId)
    rafId = null
  }
}

function start(el: HTMLCanvasElement) {
  const ctx = el.getContext('2d')
  if (!ctx) return

  const dpr = window.devicePixelRatio || 1
  el.width = CW * dpr
  el.height = CH * dpr
  ctx.scale(dpr, dpr)

  const CY = CH / 2
  const TRACK_X0 = (CW - TRACK_PX) / 2
  const TRACK_X1 = TRACK_X0 + TRACK_PX

  const draw = (dotX: number, tailX: number) => {
    ctx.clearRect(0, 0, CW, CH)

    // Track
    ctx.beginPath()
    ctx.moveTo(TRACK_X0, CY)
    ctx.lineTo(TRACK_X1, CY)
    ctx.strokeStyle = 'rgba(255,255,255,0.06)'
    ctx.lineWidth = 1.5
    ctx.lineCap = 'round'
    ctx.stroke()

    // Tail: gradient from transparent (root) to teal (dot)
    const tailGrad = ctx.createLinearGradient(tailX, 0, dotX, 0)
    tailGrad.addColorStop(0, 'rgba(99,226,183,0)')
    tailGrad.addColorStop(1, 'rgba(99,226,183,0.85)')
    ctx.beginPath()
    ctx.moveTo(tailX, CY)
    ctx.lineTo(dotX, CY)
    ctx.strokeStyle = tailGrad
    ctx.lineWidth = 1.5
    ctx.lineCap = 'round'
    ctx.stroke()

    // Glow halo around dot
    const glow = ctx.createRadialGradient(dotX, CY, 0, dotX, CY, 8)
    glow.addColorStop(0, 'rgba(99,226,183,0.40)')
    glow.addColorStop(1, 'rgba(99,226,183,0)')
    ctx.beginPath()
    ctx.arc(dotX, CY, 8, 0, Math.PI * 2)
    ctx.fillStyle = glow
    ctx.fill()

    // Dot
    ctx.beginPath()
    ctx.arc(dotX, CY, DOT_R, 0, Math.PI * 2)
    ctx.fillStyle = TEAL
    ctx.fill()
  }

  if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) {
    const mid = TRACK_X0 + TRACK_PX / 2
    draw(mid, mid - TAIL_MIN)
    return
  }

  let startTs: number | null = null

  function frame(ts: number) {
    if (startTs === null) startTs = ts
    const elapsed = (ts - startTs) % (HALF_CYCLE * 2)
    const forward = elapsed < HALF_CYCLE
    const t = forward ? elapsed / HALF_CYCLE : (elapsed - HALF_CYCLE) / HALF_CYCLE

    const eased = ease(t)
    const dotX = forward ? TRACK_X0 + eased * TRACK_PX : TRACK_X1 - eased * TRACK_PX

    const tailLen = TAIL_MIN + (TAIL_MAX - TAIL_MIN) * speed(t)
    const dir = forward ? 1 : -1
    draw(dotX, dotX - dir * tailLen)

    rafId = requestAnimationFrame(frame)
  }

  rafId = requestAnimationFrame(frame)
}

// The canvas lives inside `v-if="show"`, so (re)start whenever it mounts
watch(
  canvas,
  (el) => {
    stop()
    if (el) start(el)
  },
  { flush: 'post' },
)

onBeforeUnmount(stop)
</script>

<template>
  <div v-if="slots.default" class="app-loader-container">
    <div class="app-loader-content" :class="{ 'is-loading': props.show }">
      <slot />
    </div>
    <div v-if="props.show" class="app-loader-overlay">
      <div class="app-loader" role="status" aria-live="polite">
        <canvas ref="canvas" class="app-loader__canvas" aria-hidden="true" />
        <span class="app-loader__label">{{ props.label }}</span>
      </div>
    </div>
  </div>
  <div v-else-if="props.show" class="app-loader" role="status" aria-live="polite">
    <canvas ref="canvas" class="app-loader__canvas" aria-hidden="true" />
    <span class="app-loader__label">{{ props.label }}</span>
  </div>
</template>

<style scoped>
.app-loader-container {
  position: relative;
}

.app-loader-content {
  transition: opacity 200ms ease;
}

.app-loader-content.is-loading {
  opacity: 0.5;
  pointer-events: none;
}

.app-loader-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.app-loader {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  animation: loader-appear 180ms ease both;
}

@keyframes loader-appear {
  from {
    opacity: 0;
    transform: translateY(3px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.app-loader__canvas {
  display: block;
  width: 80px;
  height: 20px;
}

.app-loader__label {
  font-size: 11px;
  font-weight: 400;
  letter-spacing: 0.07em;
  color: rgba(255, 255, 255, 0.28);
  text-transform: lowercase;
  animation: label-breathe 2.2s ease-in-out infinite;
}

@keyframes label-breathe {
  0%,
  100% {
    opacity: 0.7;
  }
  50% {
    opacity: 1;
  }
}

@media (prefers-reduced-motion: reduce) {
  .app-loader,
  .app-loader__label {
    animation: none;
  }
}
</style>
