import type { SearchToken } from '../core/types'

/** Spoken description of a chip, e.g. "filter status: verified". */
export function describeToken(token: SearchToken): string {
    if (token.type === 'text') return `search term ${token.value}`
    return `filter ${token.filterKey}${token.operator} ${token.value}`
}
