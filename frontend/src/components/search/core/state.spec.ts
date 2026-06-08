import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useSearch } from './state'
import { searchRegistry } from './registry'
import type { BasePlugin, SearchInteractionContext } from './types'

describe('useSearch', () => {
    beforeEach(() => {
        // Clear registry
        // We can't easily clear the singleton registry without a method.
        // But we can register a unique plugin for testing.
    })

    it('should add token on Enter', () => {
        const { buffer, tokens, handleKeyDown } = useSearch()
        buffer.value = 'test'

        const event = new KeyboardEvent('keydown', { key: 'Enter' })
        vi.spyOn(event, 'preventDefault')

        handleKeyDown(event)

        expect(tokens.value).toHaveLength(1)
        expect(tokens.value[0]?.value).toBe('test')
        expect(buffer.value).toBe('')
        expect(event.preventDefault).toHaveBeenCalled()
    })

    it('should remove token on Backspace', () => {
        const { buffer, tokens, addToken, handleKeyDown } = useSearch()
        addToken({ id: '1', type: 'text', value: 'test', raw: 'test' })
        buffer.value = ''

        const event = new KeyboardEvent('keydown', { key: 'Backspace' })

        handleKeyDown(event)

        expect(tokens.value).toHaveLength(0)
    })

    it('should allow plugin to intercept key', () => {
        const { handleKeyDown } = useSearch()
        const onKeyDown = vi.fn(() => true) // Return true to handle

        const testPlugin = {
            id: 'test-keyboard',
            type: 'action' as const,
            trigger: '>',
            command: 'test',
            execute: () => { },
            onKeyDown
        }

        searchRegistry.register(testPlugin)

        const event = new KeyboardEvent('keydown', { key: 'Tab' })
        handleKeyDown(event)

        expect(onKeyDown).toHaveBeenCalled()
    })
})
