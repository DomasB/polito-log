import type { SearchQuery, SearchToken } from './types'

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
                value: token.value
            })
        }
    }
    return { text: text.join(' '), filters }
}
