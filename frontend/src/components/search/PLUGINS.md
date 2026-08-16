# Smart Search Component Architecture (v3 - Fully Extensible)

## 1. The "Everything is a Plugin" Philosophy
We move beyond just "Filter Plugins". The search bar is a command center. To support this, we introduce multiple plugin categories. This ensures that as requirements grow (e.g., adding "Saved Searches" or "Complex Operators"), the core logic remains untouched.

## 2. Plugin Categories

### 2.1 Filter Plugins (The "What")
*   **Role**: Handle specific keys (e.g., `status`, `date`).
*   **Responsibilities**: Parsing values, validating, providing value suggestions, rendering tokens.
*   **Example**: `DateFilterPlugin`, `UserFilterPlugin`.

### 2.2 Operator Plugins (The "How")
*   **Role**: Define how values are compared.
*   **Responsibilities**: Parsing operators (`:`, `>`, `!=`), validating compatibility with Filter Plugins.
*   **Example**:
    *   `EqualityOperator` (`:`, `=`)
    *   `RangeOperator` (`>`, `<`)
    *   `RegexOperator` (`~`)
*   **Extensibility**: Allows adding domain-specific operators (e.g., `~` for logs, `@` for spatial search).

### 2.3 Action Plugins (The "Do")
*   **Role**: Execute commands instead of filtering data.
*   **Syntax**: Typically prefixed (e.g., `> save`, `/help`).
*   **Responsibilities**: Execute a function when submitted.
*   **Example**: `SaveViewAction`, `ExportAction`, `ClearCacheAction`.

### 2.4 Global Suggestion Plugins (The "Discover")
*   **Role**: Provide suggestions when the input is empty or doesn't match a specific filter key.
*   **Responsibilities**: Return a list of suggestions.
*   **Example**:
    *   `RecentSearchesPlugin`: Shows history.
    *   `SavedViewsPlugin`: Shows bookmarked queries.
    *   `TrendingQueriesPlugin`: Shows what others are searching.

## 3. Updated Interfaces

```typescript
// core/types.ts

export type PluginType = 'filter' | 'operator' | 'action' | 'global-suggestion';

export interface BasePlugin {
  id: string;
  type: PluginType;
}

// 1. Filter Plugin (Refined)
export interface FilterPlugin extends BasePlugin {
  type: 'filter';
  keys: string[]; // Keys this plugin handles (e.g., ['date', 'created_at'])
  supportedOperators: string[]; // IDs of operators this filter supports
  parseValue: (raw: string) => any;
  getSuggestions: (input: string, context: SearchContext) => Promise<Suggestion[]>;
  component?: Component; // Custom Token Renderer
}

// 2. Operator Plugin
export interface OperatorPlugin extends BasePlugin {
  type: 'operator';
  symbol: string; // e.g., ">="
  label: string;  // e.g., "Greater than or equal"
}

// 3. Action Plugin
export interface ActionPlugin extends BasePlugin {
  type: 'action';
  trigger: string; // e.g., ">"
  command: string; // e.g., "export"
  execute: (args: string[]) => void | Promise<void>;
}

// 4. Global Suggestion Plugin
export interface GlobalSuggestionPlugin extends BasePlugin {
  type: 'global-suggestion';
  getSuggestions: (context: SearchContext) => Promise<Suggestion[]>;
}
```

## 4. The Registry (The Brain)

The Registry now acts as a dependency injection container.

```typescript
class SearchRegistry {
  register(plugin: BasePlugin) { ... }
  
  getFilter(key: string): FilterPlugin | undefined { ... }
  getOperator(symbol: string): OperatorPlugin | undefined { ... }
  getActions(): ActionPlugin[] { ... }
  
  // The Master Suggestion Aggregator
  async getGlobalSuggestions(context: SearchContext): Promise<Suggestion[]> {
    // Aggregates results from all GlobalSuggestionPlugins
    // e.g., [RecentSearches, SavedViews]
  }
}
```

## 5. Updated Parsing Flow

1.  **Check for Action**: Does input start with `>`?
    *   Yes -> Delegate to `ActionPlugin`.
2.  **Tokenize**: Split by whitespace.
3.  **Identify Filters**:
    *   Does token match `key<operator>value` pattern?
    *   Extract `key` -> Find `FilterPlugin`.
    *   Extract `operator` -> Find `OperatorPlugin`.
    *   Validate: Does `FilterPlugin` support `OperatorPlugin`?
    *   Yes -> Create `FilterToken`.
    *   No -> Treat as `TextToken`.

## 6. Future-Proofing Scenarios

*   **Scenario**: We need to support "Natural Language" queries.
    *   **Solution**: Add a `TransformerPlugin` pipeline that runs *before* the main parser.
    *   `"errors last week"` -> Transformer -> `"status:error date:last-week"` -> Parser.
*   **Scenario**: We need to search across multiple datasets (Logs vs. Metrics).
    *   **Solution**: The `SearchContext` passed to plugins includes the `datasetId`. Plugins can return different suggestions based on the dataset.
