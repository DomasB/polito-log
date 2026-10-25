import type {
  BasePlugin,
  FilterPlugin,
  OperatorPlugin,
  ActionPlugin,
  GlobalSuggestionPlugin,
  SearchPlugin,
  SearchContext,
  Suggestion,
} from './types'

function isFilter(p: BasePlugin | undefined): p is FilterPlugin {
  return p?.type === 'filter'
}

function isOperator(p: BasePlugin | undefined): p is OperatorPlugin {
  return p?.type === 'operator'
}

function isAction(p: BasePlugin | undefined): p is ActionPlugin {
  return p?.type === 'action'
}

function isGlobalSuggestion(p: BasePlugin | undefined): p is GlobalSuggestionPlugin {
  return p?.type === 'global-suggestion'
}

function escapeRegExp(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

export class SearchRegistry {
  private plugins: Map<string, BasePlugin> = new Map()
  private filterKeys: Map<string, string> = new Map() // key -> pluginId
  private operatorSymbols: Map<string, string> = new Map() // symbol -> pluginId
  private actionTriggers: Map<string, string> = new Map() // trigger -> pluginId
  private filterPattern: RegExp | null = null

  register(plugin: SearchPlugin) {
    if (this.plugins.has(plugin.id)) {
      console.warn(`Plugin with ID ${plugin.id} is already registered. Overwriting.`)
    }
    this.plugins.set(plugin.id, plugin)
    this.filterPattern = null

    if (isFilter(plugin)) {
      plugin.keys.forEach((key) => {
        this.filterKeys.set(key, plugin.id)
      })
    } else if (isOperator(plugin)) {
      plugin.symbols.forEach((symbol) => {
        this.operatorSymbols.set(symbol, plugin.id)
      })
    } else if (isAction(plugin)) {
      this.actionTriggers.set(plugin.trigger, plugin.id)
    }
  }

  unregister(id: string) {
    const plugin = this.plugins.get(id)
    if (!plugin) return
    this.plugins.delete(id)
    this.filterPattern = null
    for (const index of [this.filterKeys, this.operatorSymbols, this.actionTriggers]) {
      for (const [k, pluginId] of index) if (pluginId === id) index.delete(k)
    }
  }

  /**
   * Matches `key<operator>value`, where the operator is one of the registered
   * symbols (longest first, so `!=` wins over `=`). Rebuilt after registration.
   * Returns null when no operators are registered.
   */
  getFilterPattern(): RegExp | null {
    if (this.filterPattern) return this.filterPattern
    const symbols = [...this.operatorSymbols.keys()]
    if (symbols.length === 0) return null
    const alternation = symbols
      .sort((a, b) => b.length - a.length)
      .map(escapeRegExp)
      .join('|')
    this.filterPattern = new RegExp(`^([\\p{L}\\p{N}_]+)(${alternation})(.*)$`, 'u')
    return this.filterPattern
  }

  getPlugin(id: string): BasePlugin | undefined {
    return this.plugins.get(id)
  }

  getFilterByKey(key: string): FilterPlugin | undefined {
    const id = this.filterKeys.get(key)
    const p = id ? this.plugins.get(id) : undefined
    return isFilter(p) ? p : undefined
  }

  getOperatorBySymbol(symbol: string): OperatorPlugin | undefined {
    const id = this.operatorSymbols.get(symbol)
    const p = id ? this.plugins.get(id) : undefined
    return isOperator(p) ? p : undefined
  }

  getActionByTrigger(trigger: string): ActionPlugin | undefined {
    const id = this.actionTriggers.get(trigger)
    const p = id ? this.plugins.get(id) : undefined
    return isAction(p) ? p : undefined
  }

  getAllFilters(): FilterPlugin[] {
    return Array.from(this.plugins.values()).filter(isFilter)
  }

  getAllPlugins(): BasePlugin[] {
    return Array.from(this.plugins.values())
  }

  async getGlobalSuggestions(context: SearchContext): Promise<Suggestion[]> {
    const suggestionPlugins = Array.from(this.plugins.values()).filter(isGlobalSuggestion)
    const results = await Promise.all(suggestionPlugins.map((p) => p.getSuggestions(context)))
    return results.flat()
  }
}

export const searchRegistry = new SearchRegistry()
