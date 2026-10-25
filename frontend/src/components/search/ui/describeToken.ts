import type { SearchToken } from '../core/types'
import { formatValues } from '../core/parser'

/** Spoken description of a chip, e.g. "filter status: verified". */
export function describeToken(token: SearchToken): string {
  if (token.type === 'text') return `search term ${token.value}`
  return `filter ${token.filterKey}${token.operator} ${formatValues(token.values)}`
}
