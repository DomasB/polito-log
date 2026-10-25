# Smart Search Component Architecture (v2 - Scalable)

## 1. Design Philosophy: The "Kernel & Plugins" Model
To prevent "God Files" (monolithic parsers or renderers) as the system grows, we adopt a **Kernel + Plugins** architecture.
*   **The Kernel**: Handles the core loop (Input -> Parse -> State -> Render). It knows *how* to process tokens but not *what* they mean.
*   **The Plugins**: Every filter type (e.g., `DateFilter`, `UserFilter`, `StatusFilter`) is a self-contained module. It defines its own syntax rules, suggestion logic, and UI components.

## 2. Directory Structure
```
src/components/search/
├── core/                   # The Kernel
│   ├── registry.ts         # Central store for registered plugins
│   ├── parser.ts           # Orchestrator that delegates to plugins
│   ├── state.ts            # Pinia store or Composable
│   └── types.ts            # Shared interfaces
├── ui/                     # Generic UI Components
│   ├── SmartSearch.vue     # Main Container
│   ├── SearchInput.vue     # The Editor
│   └── SuggestionList.vue  # Generic List Renderer
├── plugins/                # The Feature Modules (Extensible)
│   ├── base/               # Standard types (text, select)
│   │   ├── TextPlugin.ts
│   │   └── SelectPlugin.ts
│   ├── dates/              # Complex date logic
│   │   ├── DatePlugin.ts
│   │   └── DateToken.vue   # Custom renderer
│   └── index.ts            # Export default plugins
└── ARCHITECTURE.md
```

## 3. The Plugin Interface (The Contract)
This is the most critical part for extensibility.

```typescript
// core/types.ts

export interface SearchPlugin {
  // 1. Identity
  id: string;             // e.g., 'date-range'
  
  // 2. Parsing Logic (Optional override)
  // If not provided, standard "key:value" parsing is assumed.
  // Returns a Token if this plugin claims the raw string.
  parse?: (text: string) => SearchToken | null;

  // 3. Suggestion Logic
  // Called when the user is typing a value for this key.
  getSuggestions?: (input: string, context: SearchContext) => Promise<Suggestion[]>;

  // 4. Validation
  validate?: (value: any) => boolean | string; // Returns true or error message

  // 5. Rendering (The "View")
  // Vue component to render the token.
  // If null, uses the default "Pill" renderer.
  component?: Component; 
}

export interface FilterDefinition {
  key: string;            // e.g., "created_at"
  pluginId: string;       // e.g., "date-range"
  label: string;
  config?: any;           // Plugin-specific config (e.g., date format)
}
```

## 4. Component Responsibilities (Refined)

### `SmartSearch.vue` (The Orchestrator)
*   **Slots**:
    *   `#prepend`: For icons or global actions.
    *   `#append`: For submit buttons or help triggers.
    *   `#empty`: Custom empty state content.
    *   `#suggestion-item="{ suggestion }"`: Custom rendering for suggestion rows.
*   **Logic**:
    *   Bootstraps the `SearchRegistry` with provided `plugins` and `schema`.

### `SearchToken.vue` (The Dynamic Renderer)
*   **Problem**: A giant `v-if` for every token type is unmaintainable.
*   **Solution**: Dynamic Component Loading.
    ```vue
    <component 
      :is="registry.getComponent(token.pluginId)" 
      :token="token"
      @remove="$emit('remove')"
    />
    ```

### `parser.ts` (The Delegator)
*   **Problem**: Regex gets too complex.
*   **Solution**: Two-pass parsing.
    1.  **Lexing**: Split string by whitespace (respecting quotes).
    2.  **Classification**: For each segment, ask plugins: "Do you recognize this?"
        *   Iterate through registered plugins.
        *   First one to return a Token wins.
        *   Fallback to `TextPlugin` (free text).

## 5. Performance & Scalability Mitigations

### 5.1 Bottleneck: Large Suggestion Lists
*   **Risk**: Filtering 10,000 users on the client freezes the UI.
*   **Mitigation**:
    *   **Async Generators**: `getSuggestions` should support async/await.
    *   **Debounce**: Built-in debounce in the `useSuggestions` composable.
    *   **Virtual Scrolling**: `SuggestionList.vue` should use `vue-virtual-scroller` if the list > 50 items.

### 5.2 Bottleneck: Parser Complexity
*   **Risk**: Parsing a long query on every keystroke blocks the main thread.
*   **Mitigation**:
    *   **Memoization**: Cache parse results for identical strings.
    *   **Web Worker**: Move the `parser.ts` logic to a Web Worker if the plugin count grows > 20 or logic becomes heavy.

### 5.3 Maintenance: "God" Schema File
*   **Risk**: `schema.ts` becomes 5000 lines.
*   **Mitigation**:
    *   The Schema is just a JSON object. It can be split into multiple files (`users.schema.ts`, `logs.schema.ts`) and merged at runtime.
    *   It can be fetched from the Backend (HATEOAS style) so the frontend doesn't need code changes for new filters.

## 6. Testing Strategy (Plugins)

Each plugin is tested in isolation.
*   **`DatePlugin.spec.ts`**:
    *   Test that `parse("date:yesterday")` returns a valid token.
    *   Test that `getSuggestions` returns valid date options.
    *   Test that the `DateToken.vue` component renders correctly.

This allows us to add "Out-there" features (like Natural Language Parsing) as a separate `NLPPlugin` without touching the core code.
