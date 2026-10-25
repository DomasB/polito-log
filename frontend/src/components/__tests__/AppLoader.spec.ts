import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'

import AppLoader from '../AppLoader.vue'

function stubContext() {
  const gradient = { addColorStop: vi.fn() }
  return {
    scale: vi.fn(),
    clearRect: vi.fn(),
    beginPath: vi.fn(),
    moveTo: vi.fn(),
    lineTo: vi.fn(),
    stroke: vi.fn(),
    arc: vi.fn(),
    fill: vi.fn(),
    createLinearGradient: vi.fn(() => gradient),
    createRadialGradient: vi.fn(() => gradient),
  }
}

describe('AppLoader', () => {
  const raf = vi.fn(() => 42)
  const caf = vi.fn()

  beforeEach(() => {
    vi.stubGlobal('requestAnimationFrame', raf)
    vi.stubGlobal('cancelAnimationFrame', caf)
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockImplementation(
      () => stubContext() as unknown as CanvasRenderingContext2D,
    )
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
    raf.mockClear()
    caf.mockClear()
  })

  it('renders a standalone status with the default label', () => {
    const wrapper = mount(AppLoader)

    const status = wrapper.find('[role="status"]')
    expect(status.exists()).toBe(true)
    expect(status.text()).toBe('loading')
  })

  it('shows a custom label', () => {
    const wrapper = mount(AppLoader, { props: { label: 'verifying' } })

    expect(wrapper.find('[role="status"]').text()).toBe('verifying')
  })

  it('always renders slot content and overlays the loader only while shown', async () => {
    const wrapper = mount(AppLoader, {
      props: { show: false },
      slots: { default: '<p class="content">Results</p>' },
    })

    expect(wrapper.find('.content').exists()).toBe(true)
    expect(wrapper.find('[role="status"]').exists()).toBe(false)

    await wrapper.setProps({ show: true })

    expect(wrapper.find('.content').exists()).toBe(true)
    expect(wrapper.find('[role="status"]').exists()).toBe(true)
  })

  it('cancels the animation frame on unmount', async () => {
    const wrapper = mount(AppLoader)
    await wrapper.vm.$nextTick()
    expect(raf).toHaveBeenCalled()

    wrapper.unmount()

    expect(caf).toHaveBeenCalledWith(42)
  })
})
