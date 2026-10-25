import { describe, it, expect } from 'vitest'
import { toSearchQuery, toStatementSearchParams } from './query'
import { SearchParser } from './parser'
import { SearchRegistry } from './registry'
import { StatusPlugin } from '../plugins/filters/StatusPlugin'
import { EqualsOperator } from '../plugins/operators/EqualsOperator'

const registry = new SearchRegistry()
registry.register(EqualsOperator)
registry.register(StatusPlugin)
const parser = new SearchParser(registry)

function params(input: string) {
  return toStatementSearchParams(toSearchQuery(parser.parse(input)))
}

describe('toStatementSearchParams', () => {
  it('omits everything for an empty query', () => {
    expect(params('')).toEqual({})
  })

  it('joins text into q', () => {
    expect(params('green  energy')).toEqual({ q: 'green energy' })
  })

  it('maps plain values to the key', () => {
    expect(params('tax s:pending|verified')).toEqual({ q: 'tax', status: ['pending', 'verified'] })
  })

  it('maps a single negated value to <key>_not', () => {
    expect(params('status:verified|!rejected')).toEqual({ status_not: ['rejected'] })
  })

  it('omits a filter that matches anything', () => {
    expect(params('status:!pending|!rejected')).toEqual({})
  })

  it('skips error tokens', () => {
    expect(params('status:xyz status:pending status:verified')).toEqual({ status: ['pending'] })
  })
})
