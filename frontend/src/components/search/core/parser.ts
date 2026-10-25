import type { SearchToken, TextToken, FilterToken } from './types'
import { SearchRegistry, searchRegistry } from './registry'
import { generateId } from './id'

export interface FilterMatch {
    key: string
    symbol: string
    value: string
}

export class SearchParser {
    constructor(private registry: SearchRegistry = searchRegistry) {}

    /** Split `key<op>value` using the registry's operator symbols. */
    matchFilter(raw: string): FilterMatch | null {
        const match = this.registry.getFilterPattern()?.exec(raw)
        if (!match) return null
        const [, key, symbol, value] = match
        return { key: key!, symbol: symbol!, value: value! }
    }

    parse(input: string): SearchToken[] {
        // Simple tokenizer: split by whitespace (quoted values are a future improvement)
        return input
            .trim()
            .split(/\s+/)
            .filter(Boolean)
            .map(raw => this.parseSingleToken(raw))
    }

    private parseSingleToken(raw: string): SearchToken {
        const match = this.matchFilter(raw)
        const filterPlugin = match && this.registry.getFilterByKey(match.key)
        // Unknown keys (e.g. `foo:bar`) are plain text
        if (!match || !filterPlugin) return textToken(raw)

        const operatorPlugin = this.registry.getOperatorBySymbol(match.symbol)
        const token: FilterToken = {
            id: generateId(),
            type: 'filter',
            filterKey: match.key,
            operator: match.symbol,
            operatorId: operatorPlugin?.id ?? match.symbol,
            value: match.value,
            pluginId: filterPlugin.id,
            raw
        }

        if (!operatorPlugin || !filterPlugin.supportedOperators.includes(operatorPlugin.id)) {
            token.error = `${match.key} does not support "${match.symbol}"`
            return token
        }

        try {
            token.value = filterPlugin.parseValue(match.value)
        } catch (e) {
            token.error = e instanceof Error ? e.message : `Invalid value: ${match.value}`
            return token
        }

        const validation = filterPlugin.validate?.(token.value) ?? true
        if (validation !== true) {
            token.error = typeof validation === 'string' ? validation : `Invalid value: ${match.value}`
        }
        return token
    }
}

function textToken(raw: string): TextToken {
    return { id: generateId(), type: 'text', value: raw, raw }
}

export const searchParser = new SearchParser()
