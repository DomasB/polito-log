import type { FilterPlugin, Suggestion } from '../../core/types'
import type { StatementStatus } from '@/api/types.gen'

const STATUSES = ['pending', 'verified', 'disputed', 'retracted'] as const satisfies readonly StatementStatus[]

function isStatus(value: unknown): value is StatementStatus {
    return (STATUSES as readonly unknown[]).includes(value)
}

export const StatusPlugin: FilterPlugin = {
    id: 'status',
    type: 'filter',
    keys: ['status', 's'],
    supportedOperators: ['equals', 'not-equals'], // IDs of operators

    parseValue(raw: string) {
        return raw.toLowerCase()
    },

    async getSuggestions(input: string): Promise<Suggestion[]> {
        return STATUSES
            .filter(opt => opt.startsWith(input.toLowerCase()))
            .map(opt => ({
                label: opt,
                value: opt,
                type: 'value'
            }))
    },

    validate(value: unknown) {
        return isStatus(value) || `Invalid status: ${value}`
    }
}
