import { describe, it, expect } from 'vitest'
import { reduceValues } from './reduce'
import type { FilterValue } from './types'

// 'a|!b' -> FilterValue[]
function values(term: string): FilterValue[] {
  return term.split('|').map((v) => ({ value: v.replace(/^!/, ''), negated: v.startsWith('!') }))
}

describe('reduceValues', () => {
  it.each([
    ['a', { kind: 'in', values: ['a'] }],
    ['a|b|a', { kind: 'in', values: ['a', 'b'] }],
    ['!a', { kind: 'not-in', values: ['a'] }],
    ['!a|!a', { kind: 'not-in', values: ['a'] }],
    ['b|!a', { kind: 'not-in', values: ['a'] }],
    ['a|!a', { kind: 'any' }],
    ['!a|b|a', { kind: 'any' }],
    ['!a|!b', { kind: 'any' }],
    ['a|!a|!b', { kind: 'any' }],
  ])('reduces %s', (term, expected) => {
    expect(reduceValues(values(term))).toEqual(expected)
  })
})
