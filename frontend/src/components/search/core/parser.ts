import type { SearchToken, TextToken, FilterToken, FilterValue } from './types'
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

  /**
   * `existing` are tokens already committed, so a repeated key is caught
   * across commits too.
   */
  parse(input: string, existing: SearchToken[] = []): SearchToken[] {
    const applied = existing.filter(isAppliedFilter)
    // Simple tokenizer: split by whitespace (quoted values are a future improvement)
    return input
      .trim()
      .split(/\s+/)
      .filter(Boolean)
      .map((raw) => {
        const token = this.parseSingleToken(raw, applied)
        if (isAppliedFilter(token)) applied.push(token)
        return token
      })
  }

  private parseSingleToken(raw: string, applied: FilterToken[]): SearchToken {
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
      values: splitValues(match.value),
      pluginId: filterPlugin.id,
      raw,
    }

    if (!operatorPlugin || !filterPlugin.supportedOperators.includes(operatorPlugin.id)) {
      token.error = `${match.key} does not support "${match.symbol}"`
      return token
    }

    if (token.values.some((v) => v.value === '')) {
      token.error = `Empty value in ${match.key}${match.symbol}${match.value}`
      return token
    }

    for (const item of token.values) {
      const rawValue = item.value as string
      try {
        item.value = filterPlugin.parseValue(rawValue)
      } catch (e) {
        token.error = e instanceof Error ? e.message : `Invalid value: ${rawValue}`
        return token
      }
      const validation = filterPlugin.validate?.(item.value) ?? true
      if (validation !== true) {
        token.error = typeof validation === 'string' ? validation : `Invalid value: ${rawValue}`
        return token
      }
    }

    // Every current filter key is single-valued: alternatives go in one `a|b` term
    const previous = applied.find((t) => t.pluginId === token.pluginId)
    if (previous) {
      const merged = `${formatValues(previous.values)}|${formatValues(token.values)}`
      token.error = `${match.key} takes one value; use ${match.key}${match.symbol}${merged}`
    }
    return token
  }
}

/** Split `a|!b` into its items; values stay raw strings until the plugin parses them. */
function splitValues(raw: string): FilterValue[] {
  return raw.split('|').map((part) => {
    const negated = part.startsWith('!')
    return { value: negated ? part.slice(1) : part, negated }
  })
}

/** Inverse of splitValues, for display: `a|!b`. */
export function formatValues(values: FilterValue[]): string {
  return values.map((v) => `${v.negated ? '!' : ''}${String(v.value)}`).join('|')
}

function isAppliedFilter(token: SearchToken): token is FilterToken {
  return token.type === 'filter' && !token.error
}

function textToken(raw: string): TextToken {
  return { id: generateId(), type: 'text', value: raw, raw }
}

export const searchParser = new SearchParser()
