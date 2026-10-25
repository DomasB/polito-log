import type { FilterValue } from './types'

/** What a single-valued key's `a|!b|...` term matches. */
export type ReducedFilter =
  | { kind: 'in'; values: unknown[] }
  | { kind: 'not-in'; values: unknown[] }
  | { kind: 'any' }

/**
 * Reduce an OR of (optionally negated) values for a single-valued key.
 * `!a|!b` with a != b is always true, as is `a|!a`; `a|b|!c` is just `!c`.
 */
export function reduceValues(values: FilterValue[]): ReducedFilter {
  const plain = new Set(values.filter((v) => !v.negated).map((v) => v.value))
  const negated = new Set(values.filter((v) => v.negated).map((v) => v.value))
  if (negated.size === 0) return { kind: 'in', values: [...plain] }
  if (negated.size > 1) return { kind: 'any' }
  const [n] = negated
  return plain.has(n) ? { kind: 'any' } : { kind: 'not-in', values: [n] }
}
