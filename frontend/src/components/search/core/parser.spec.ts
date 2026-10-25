import { describe, it, expect, beforeEach } from 'vitest'
import { SearchParser } from './parser'
import { SearchRegistry } from './registry'
import { StatusPlugin } from '../plugins/filters/StatusPlugin'
import { EqualsOperator, NotEqualsOperator } from '../plugins/operators/EqualsOperator'
import type { FilterToken, SearchToken } from './types'

function asFilter(token: SearchToken | undefined): FilterToken {
  expect(token?.type).toBe('filter')
  return token as FilterToken
}

describe('SearchParser', () => {
  let parser: SearchParser

  beforeEach(() => {
    const registry = new SearchRegistry()
    registry.register(EqualsOperator)
    registry.register(NotEqualsOperator)
    registry.register(StatusPlugin)
    parser = new SearchParser(registry)
  })

  it('parses plain text into text tokens', () => {
    const tokens = parser.parse('hello world')
    expect(tokens.map((t) => [t.type, t.raw])).toEqual([
      ['text', 'hello'],
      ['text', 'world'],
    ])
  })

  it.each([
    [':', 'equals'],
    ['=', 'equals'],
    ['!=', 'not-equals'],
  ])('parses a known filter with "%s"', (symbol, operatorId) => {
    const token = asFilter(parser.parse(`status${symbol}verified`)[0])
    expect(token.filterKey).toBe('status')
    expect(token.operator).toBe(symbol)
    expect(token.operatorId).toBe(operatorId)
    expect(token.value).toBe('verified')
    expect(token.pluginId).toBe('status')
    expect(token.error).toBeUndefined()
  })

  it('resolves key aliases', () => {
    const token = asFilter(parser.parse('s:Pending')[0])
    expect(token.pluginId).toBe('status')
    expect(token.value).toBe('pending')
  })

  it('marks an invalid value as an error token', () => {
    const token = asFilter(parser.parse('status:xyz')[0])
    expect(token.error).toBe('Invalid status: xyz')
  })

  it('treats operator junk as an invalid value', () => {
    const token = asFilter(parser.parse('status:!~')[0])
    expect(token.operator).toBe(':')
    expect(token.value).toBe('!~')
    expect(token.error).toBeDefined()
  })

  it('marks an operator the filter does not support as an error token', () => {
    const registry = new SearchRegistry()
    registry.register(EqualsOperator)
    registry.register({ id: 'gt', type: 'operator', symbols: ['>'], label: 'Greater than' })
    registry.register(StatusPlugin)
    const token = asFilter(new SearchParser(registry).parse('status>verified')[0])
    expect(token.operatorId).toBe('gt')
    expect(token.error).toBeDefined()
  })

  it('keeps unknown keys as text', () => {
    const tokens = parser.parse('foo:bar')
    expect(tokens).toHaveLength(1)
    expect(tokens[0]!.type).toBe('text')
    expect(tokens[0]!.raw).toBe('foo:bar')
  })

  it('parses mixed content', () => {
    const tokens = parser.parse('climate status!=retracted')
    expect(tokens[0]!.type).toBe('text')
    expect(asFilter(tokens[1]).operatorId).toBe('not-equals')
  })

  it('handles Unicode text and keys', () => {
    const tokens = parser.parse('žalioji energetika ąžuolas:x')
    expect(tokens.map((t) => [t.type, t.raw])).toEqual([
      ['text', 'žalioji'],
      ['text', 'energetika'],
      ['text', 'ąžuolas:x'],
    ])
    expect(parser.matchFilter('ąžuolas:x')).toEqual({ key: 'ąžuolas', symbol: ':', value: 'x' })
  })

  it('treats everything as text when no operators are registered', () => {
    const registry = new SearchRegistry()
    registry.register(StatusPlugin)
    expect(new SearchParser(registry).parse('status:verified')[0]!.type).toBe('text')
  })
})
