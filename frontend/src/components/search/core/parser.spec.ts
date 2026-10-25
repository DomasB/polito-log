import { describe, it, expect, beforeEach } from 'vitest'
import { SearchParser } from './parser'
import { SearchRegistry } from './registry'
import { StatusPlugin } from '../plugins/filters/StatusPlugin'
import { EqualsOperator } from '../plugins/operators/EqualsOperator'
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

  it.each([':', '='])('parses a known filter with "%s"', (symbol) => {
    const token = asFilter(parser.parse(`status${symbol}verified`)[0])
    expect(token.filterKey).toBe('status')
    expect(token.operator).toBe(symbol)
    expect(token.operatorId).toBe('equals')
    expect(token.values).toEqual([{ value: 'verified', negated: false }])
    expect(token.pluginId).toBe('status')
    expect(token.error).toBeUndefined()
  })

  it('resolves key aliases', () => {
    const token = asFilter(parser.parse('s:Pending')[0])
    expect(token.pluginId).toBe('status')
    expect(token.values).toEqual([{ value: 'pending', negated: false }])
  })

  it('parses a | list with per-value negation', () => {
    const token = asFilter(parser.parse('status:Pending|!rejected|verified')[0])
    expect(token.values).toEqual([
      { value: 'pending', negated: false },
      { value: 'rejected', negated: true },
      { value: 'verified', negated: false },
    ])
    expect(token.error).toBeUndefined()
  })

  it('marks an invalid value anywhere in the list as an error token', () => {
    const token = asFilter(parser.parse('status:pending|!xyz')[0])
    expect(token.error).toBe('Invalid status: xyz')
  })

  it.each(['status:a||b', 'status:!', 'status:pending|', 'status:'])(
    'marks an empty value in %s as an error token',
    (input) => {
      expect(asFilter(parser.parse(input)[0]).error).toMatch(/^Empty value/)
    },
  )

  it('marks a repeated key as an error token suggesting the | form', () => {
    const [first, second] = parser.parse('status:pending s:!verified').map(asFilter)
    expect(first!.error).toBeUndefined()
    expect(second!.error).toBe('s takes one value; use s:pending|!verified')
  })

  it('checks repeats against existing tokens, ignoring error tokens', () => {
    const existing = parser.parse('status:xyz status:pending')
    expect(asFilter(parser.parse('status:verified', existing)[0]).error).toBe(
      'status takes one value; use status:pending|verified',
    )
    expect(asFilter(parser.parse('status:verified', existing.slice(0, 1))[0]).error).toBeUndefined()
  })

  it('no longer has a != operator', () => {
    expect(parser.parse('status!=retracted')[0]!.type).toBe('text')
  })

  it('marks an invalid value as an error token', () => {
    const token = asFilter(parser.parse('status:xyz')[0])
    expect(token.error).toBe('Invalid status: xyz')
  })

  it('treats operator junk as an invalid value', () => {
    const token = asFilter(parser.parse('status:!~')[0])
    expect(token.operator).toBe(':')
    expect(token.values).toEqual([{ value: '~', negated: true }])
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
    const tokens = parser.parse('climate status:!retracted')
    expect(tokens[0]!.type).toBe('text')
    expect(asFilter(tokens[1]).values).toEqual([{ value: 'retracted', negated: true }])
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
