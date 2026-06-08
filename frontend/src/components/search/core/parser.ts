import type { SearchToken, TextToken, FilterToken } from './types'
import { searchRegistry } from './registry'

export class SearchParser {
    parse(input: string): SearchToken[] {
        const tokens: SearchToken[] = []

        // Simple tokenizer: split by spaces, but respect quotes (future improvement)
        // For now, let's do a basic split and refine later for quotes.
        const rawTokens = input.trim().split(/\s+/)

        for (const raw of rawTokens) {
            if (!raw) continue

            const token = this.parseSingleToken(raw)
            tokens.push(token)
        }

        return tokens
    }

    private parseSingleToken(raw: string): SearchToken {
        // 1. Check for Filter Pattern: key:value or key>value etc.
        // We need to find the operator.
        // Iterate through all registered operators to see if one exists in the string.
        // Note: This might be slow if we have many operators. Optimization: Regex construction.

        // For now, let's assume standard operators like ':', '=', '>', '<', '!='
        // We can get them from registry if we expose them, or just hardcode common ones for the first pass.
        // But to be truly extensible, we should ask the registry.

        // Let's try to find the first occurrence of any registered operator symbol.
        // Ideally we want the longest match first? Or just the first one found?
        // 'created_at>=2023' -> operator is '>='

        // We need to access the registry's operator symbols. 
        // Since registry is a singleton (or passed in), we use it.

        // This is a bit tricky without direct access to the map keys efficiently.
        // Let's assume a standard set for now or iterate.
        // A better approach for the parser is to have a Regex built from registered operators.

        // Let's try a heuristic: split by the first non-alphanumeric char that is an operator?
        // Or just look for ':' as the primary separator for now, as per requirements.
        // The architecture mentions "Iterate through registered plugins".

        // Let's support ':' and '=' for now as a start.
        const match = raw.match(/^([a-zA-Z0-9_]+)([:=><!~]+)(.*)$/)

        if (match && match.length >= 4) {
            const key = match[1]
            const opSymbol = match[2]
            const value = match[3]!

            if (!key || !opSymbol) return {
                id: crypto.randomUUID(),
                type: 'text',
                value: raw,
                raw
            } as TextToken

            const filterPlugin = searchRegistry.getFilterByKey(key)
            const operatorPlugin = searchRegistry.getOperatorBySymbol(opSymbol)

            if (filterPlugin && operatorPlugin) {
                // Validate if filter supports this operator
                if (filterPlugin.supportedOperators.includes(operatorPlugin.id)) {
                    try {
                        const parsedValue = filterPlugin.parseValue(value)
                        // Validate value
                        if (filterPlugin.validate) {
                            const validation = filterPlugin.validate(parsedValue)
                            if (validation !== true) {
                                // Validation failed, treat as text? Or invalid token?
                                // For now, treat as text if invalid.
                                return {
                                    id: crypto.randomUUID(),
                                    type: 'text',
                                    value: raw,
                                    raw
                                }
                            }
                        }

                        return {
                            id: crypto.randomUUID(),
                            type: 'filter',
                            filterKey: key,
                            operator: opSymbol,
                            value: parsedValue,
                            pluginId: filterPlugin.id,
                            raw
                        } as FilterToken
                    } catch (e) {
                        // Parse error, fallback to text
                    }
                }
            }
        }

        // Fallback to TextToken
        return {
            id: crypto.randomUUID(),
            type: 'text',
            value: raw,
            raw
        } as TextToken
    }
}

export const searchParser = new SearchParser()
