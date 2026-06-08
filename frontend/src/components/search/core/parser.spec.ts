import { describe, it, expect, beforeEach } from 'vitest'
import { SearchParser } from './parser'
import { SearchRegistry } from './registry'
import { StatusPlugin } from '../plugins/filters/StatusPlugin'

describe('SearchParser', () => {
    let parser: SearchParser
    let registry: SearchRegistry

    beforeEach(() => {
        // We need to mock the global registry or use dependency injection.
        // The current implementation uses a singleton export.
        // For testing, we might need to reset the singleton or mock it.
        // Since we can't easily reset the singleton in this setup without changing code,
        // we will assume the singleton is used and register plugins there.

        // Ideally, Parser should take Registry as a dependency.
        // But for now, let's just register the plugin to the global registry.
        const { searchRegistry: globalRegistry } = require('./registry')
        globalRegistry.register(StatusPlugin)

        const { searchParser: globalParser } = require('./parser')
        parser = globalParser
    })

    it('should parse simple text', () => {
        const tokens = parser.parse('hello world')
        expect(tokens).toHaveLength(2)
        expect(tokens[0].type).toBe('text')
        if (tokens[0].type === 'text') {
            expect(tokens[0].value).toBe('hello')
        }
        expect(tokens[1].type).toBe('text')
        if (tokens[1].type === 'text') {
            expect(tokens[1].value).toBe('world')
        }
    })

    it('should parse a known filter', () => {
        const input = 'status:verified'
        const tokens = parser.parse(input)

        expect(tokens).toHaveLength(1)
        expect(tokens[0]!.type).toBe('filter')

        if (tokens[0]!.type === 'filter') {
            expect(tokens[0]!.filterKey).toBe('status')
            expect(tokens[0]!.operator).toBe(':')
            expect(tokens[0]!.value).toBe('verified')
        }
    })

    it('should parse mixed content', () => {
        const input = 'status:critical error'
        const tokens = parser.parse(input)

        expect(tokens).toHaveLength(2)
        expect(tokens[0]!.type).toBe('filter')
        expect(tokens[1]!.type).toBe('text')

        if (tokens[1]!.type === 'text') {
            expect(tokens[1]!.value).toBe('error')
        }
    })

    it('should fallback to text for unknown filters', () => {
        const input = 'foo:bar'
        const tokens = parser.parse(input)

        expect(tokens).toHaveLength(1)
        expect(tokens[0]!.type).toBe('text')
        if (tokens[0]!.type === 'text') {
            expect(tokens[0]!.value).toBe('foo:bar')
        }
    })
})
