import type { FilterPlugin, Suggestion, SearchContext } from '../../core/types'

export const StatusPlugin: FilterPlugin = {
    id: 'status',
    type: 'filter',
    keys: ['status', 's'],
    supportedOperators: ['equals', 'not-equals'], // IDs of operators

    parseValue(raw: string) {
        return raw.toLowerCase()
    },

    async getSuggestions(input: string, context: SearchContext): Promise<Suggestion[]> {
        const options = ['pending', 'verified', 'disputed', 'retracted']
        return options
            .filter(opt => opt.startsWith(input.toLowerCase()))
            .map(opt => ({
                label: opt,
                value: opt,
                type: 'value'
            }))
    },

    validate(value: any) {
        const options = ['pending', 'verified', 'disputed', 'retracted']
        return options.includes(value) || `Invalid status: ${value}`
    }
}
