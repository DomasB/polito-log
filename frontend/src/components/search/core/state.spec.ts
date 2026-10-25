import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { nextTick } from 'vue'
import { useSearch, MAX_SUGGESTIONS } from './state'
import { SearchRegistry } from './registry'
import { StatusPlugin } from '../plugins/filters/StatusPlugin'
import { EqualsOperator, NotEqualsOperator } from '../plugins/operators/EqualsOperator'
import type { FilterPlugin, FilterToken, SearchContext, Suggestion } from './types'

function enter() {
  return new KeyboardEvent('keydown', { key: 'Enter' })
}

describe('useSearch', () => {
  let registry: SearchRegistry

  beforeEach(() => {
    registry = new SearchRegistry()
    registry.register(EqualsOperator)
    registry.register(NotEqualsOperator)
    registry.register(StatusPlugin)
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('adds a text token on Enter', () => {
    const { buffer, tokens, handleKeyDown } = useSearch(registry)
    buffer.value = 'test'

    const event = enter()
    vi.spyOn(event, 'preventDefault')
    handleKeyDown(event)

    expect(tokens.value).toHaveLength(1)
    expect(tokens.value[0]!.type).toBe('text')
    expect(tokens.value[0]!.raw).toBe('test')
    expect(buffer.value).toBe('')
    expect(event.preventDefault).toHaveBeenCalled()
  })

  it('turns a typed filter into a filter token on Enter', () => {
    const { buffer, tokens, handleKeyDown } = useSearch(registry)
    buffer.value = 'status:verified'
    handleKeyDown(enter())

    const token = tokens.value[0] as FilterToken
    expect(token.type).toBe('filter')
    expect(token.operatorId).toBe('equals')
    expect(token.value).toBe('verified')
    expect(token.error).toBeUndefined()
  })

  it('turns an invalid typed filter into an error token on Enter', () => {
    const { buffer, tokens, handleKeyDown } = useSearch(registry)
    buffer.value = 'status:xyz'
    handleKeyDown(enter())

    const token = tokens.value[0] as FilterToken
    expect(token.type).toBe('filter')
    expect(token.error).toBeDefined()
  })

  it('builds a filter token from a selected value suggestion', () => {
    const { buffer, tokens, selectSuggestion } = useSearch(registry)
    buffer.value = 's!=ver'
    selectSuggestion({ label: 'verified', value: 'verified', type: 'value' })

    const token = tokens.value[0] as FilterToken
    expect(token.raw).toBe('s!=verified')
    expect(token.operatorId).toBe('not-equals')
    expect(token.error).toBeUndefined()
  })

  it('removes the last token on Backspace', () => {
    const { buffer, tokens, addToken, handleKeyDown } = useSearch(registry)
    addToken({ id: '1', type: 'text', value: 'test', raw: 'test' })
    buffer.value = ''

    handleKeyDown(new KeyboardEvent('keydown', { key: 'Backspace' }))

    expect(tokens.value).toHaveLength(0)
  })

  it('lets a plugin intercept a key', () => {
    const onKeyDown = vi.fn<() => boolean>(() => true) // Return true to handle
    registry.register({
      id: 'test-keyboard',
      type: 'action' as const,
      trigger: '>',
      command: 'test',
      execute: () => {},
      onKeyDown,
    })
    const { handleKeyDown } = useSearch(registry)

    handleKeyDown(new KeyboardEvent('keydown', { key: 'Tab' }))

    expect(onKeyDown).toHaveBeenCalled()
  })

  describe('suggestions', () => {
    beforeEach(() => {
      vi.useFakeTimers()
    })

    it('drops a stale slow response', async () => {
      const pending: { input: string; signal?: AbortSignal; resolve: (s: Suggestion[]) => void }[] =
        []
      const slow: FilterPlugin = {
        id: 'slow',
        type: 'filter',
        keys: ['slow'],
        supportedOperators: ['equals'],
        parseValue: (raw) => raw,
        getSuggestions: (input: string, context: SearchContext) =>
          new Promise((resolve) => pending.push({ input, signal: context.signal, resolve })),
      }
      registry.register(slow)
      const { buffer, suggestions } = useSearch(registry)

      buffer.value = 'slow:a'
      await nextTick()
      await vi.advanceTimersByTimeAsync(150)
      buffer.value = 'slow:b'
      await nextTick()
      await vi.advanceTimersByTimeAsync(150)

      expect(pending.map((p) => p.input)).toEqual(['a', 'b'])
      expect(pending[0]!.signal?.aborted).toBe(true)

      pending[1]!.resolve([{ label: 'b', value: 'b', type: 'value' }])
      await vi.advanceTimersByTimeAsync(0)
      pending[0]!.resolve([{ label: 'a', value: 'a', type: 'value' }])
      await vi.advanceTimersByTimeAsync(0)

      expect(suggestions.value.map((s) => s.value)).toEqual(['b'])
    })

    it('debounces requests while typing', async () => {
      const getSuggestions = vi.fn<() => Promise<never[]>>(async () => [])
      registry.register({ ...StatusPlugin, id: 'spy', keys: ['spy'], getSuggestions })
      const { buffer } = useSearch(registry)

      for (const text of ['spy:', 'spy:a', 'spy:ab']) {
        buffer.value = text
        await nextTick()
        await vi.advanceTimersByTimeAsync(50)
      }
      await vi.advanceTimersByTimeAsync(150)

      expect(getSuggestions).toHaveBeenCalledTimes(1)
      expect(getSuggestions).toHaveBeenCalledWith('ab', expect.anything())
    })

    it(`caps suggestions at ${MAX_SUGGESTIONS}`, async () => {
      registry.register({
        ...StatusPlugin,
        id: 'many',
        keys: ['many'],
        getSuggestions: async () =>
          Array.from({ length: 25 }, (_, i) => ({
            label: `v${i}`,
            value: `v${i}`,
            type: 'value' as const,
          })),
      })
      const { buffer, suggestions } = useSearch(registry)

      buffer.value = 'many:'
      await nextTick()
      await vi.advanceTimersByTimeAsync(150)

      expect(suggestions.value).toHaveLength(MAX_SUGGESTIONS)
    })

    it('suggests nothing for an unknown key', async () => {
      const { buffer, suggestions } = useSearch(registry)
      buffer.value = 'status:'
      await nextTick()
      await vi.advanceTimersByTimeAsync(150)
      expect(suggestions.value.length).toBeGreaterThan(0)

      buffer.value = 'foo:'
      await nextTick()
      await vi.advanceTimersByTimeAsync(150)
      expect(suggestions.value).toEqual([])
    })

    it('close() clears suggestions and cancels a pending request', async () => {
      const { buffer, suggestions, activeIndex, close } = useSearch(registry)
      buffer.value = 'status:'
      await nextTick()
      await vi.advanceTimersByTimeAsync(150)
      activeIndex.value = 0

      close()
      expect(suggestions.value).toEqual([])
      expect(activeIndex.value).toBe(-1)

      buffer.value = 'status:v'
      await nextTick()
      close()
      await vi.advanceTimersByTimeAsync(150)
      expect(suggestions.value).toEqual([])
    })
  })
})
