import type { SearchQuery, SearchToken } from './types'
import { reduceValues } from './reduce'
import type { StatementStatus } from '@/api/types.gen'

/** Build the query consumers apply. Error tokens are shown but not applied. */
export function toSearchQuery(tokens: SearchToken[]): SearchQuery {
  const text: string[] = []
  const filters: SearchQuery['filters'] = []
  for (const token of tokens) {
    if (token.type === 'text') {
      text.push(token.value)
    } else if (!token.error) {
      filters.push({
        pluginId: token.pluginId,
        key: token.filterKey,
        operatorId: token.operatorId,
        values: token.values,
      })
    }
  }
  return { text: text.join(' '), filters }
}

/** Query params for GET /statements/search/. */
export interface StatementSearchParams {
  q?: string
  status?: StatementStatus[]
  status_not?: StatementStatus[]
}

/** Each filter becomes `<pluginId>` or `<pluginId>_not`; a filter matching anything is dropped. */
export function toStatementSearchParams(query: SearchQuery): StatementSearchParams {
  const params: Record<string, string | string[]> = {}
  if (query.text) params.q = query.text
  for (const filter of query.filters) {
    const reduced = reduceValues(filter.values)
    if (reduced.kind === 'any') continue
    const name = reduced.kind === 'in' ? filter.pluginId : `${filter.pluginId}_not`
    params[name] = reduced.values.map(String)
  }
  return params as StatementSearchParams
}
