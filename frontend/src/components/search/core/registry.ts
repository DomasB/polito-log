import type {
    BasePlugin,
    FilterPlugin,
    OperatorPlugin,
    ActionPlugin,
    GlobalSuggestionPlugin,
    SearchContext,
    Suggestion
} from './types'

export class SearchRegistry {
    private plugins: Map<string, BasePlugin> = new Map()
    private filterKeys: Map<string, string> = new Map() // key -> pluginId
    private operatorSymbols: Map<string, string> = new Map() // symbol -> pluginId
    private actionTriggers: Map<string, string> = new Map() // trigger -> pluginId

    register(plugin: BasePlugin) {
        if (this.plugins.has(plugin.id)) {
            console.warn(`Plugin with ID ${plugin.id} is already registered. Overwriting.`)
        }
        this.plugins.set(plugin.id, plugin)

        if (plugin.type === 'filter') {
            const p = plugin as FilterPlugin
            p.keys.forEach(key => {
                this.filterKeys.set(key, plugin.id)
            })
        } else if (plugin.type === 'operator') {
            const p = plugin as OperatorPlugin
            this.operatorSymbols.set(p.symbol, plugin.id)
        } else if (plugin.type === 'action') {
            const p = plugin as ActionPlugin
            this.actionTriggers.set(p.trigger, plugin.id)
        }
    }

    getPlugin(id: string): BasePlugin | undefined {
        return this.plugins.get(id)
    }

    getFilterByKey(key: string): FilterPlugin | undefined {
        const id = this.filterKeys.get(key)
        return id ? (this.plugins.get(id) as FilterPlugin) : undefined
    }

    getOperatorBySymbol(symbol: string): OperatorPlugin | undefined {
        const id = this.operatorSymbols.get(symbol)
        return id ? (this.plugins.get(id) as OperatorPlugin) : undefined
    }

    getActionByTrigger(trigger: string): ActionPlugin | undefined {
        const id = this.actionTriggers.get(trigger)
        return id ? (this.plugins.get(id) as ActionPlugin) : undefined
    }

    getAllFilters(): FilterPlugin[] {
        return Array.from(this.plugins.values())
            .filter(p => p.type === 'filter') as FilterPlugin[]
    }

    getAllPlugins(): BasePlugin[] {
        return Array.from(this.plugins.values())
    }

    async getGlobalSuggestions(context: SearchContext): Promise<Suggestion[]> {
        const suggestionPlugins = Array.from(this.plugins.values())
            .filter(p => p.type === 'global-suggestion') as GlobalSuggestionPlugin[]

        const results = await Promise.all(suggestionPlugins.map(p => p.getSuggestions(context)))
        return results.flat()
    }
}

export const searchRegistry = new SearchRegistry()
