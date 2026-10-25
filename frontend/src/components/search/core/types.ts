import type { Component } from 'vue'

export type PluginType = 'filter' | 'operator' | 'action' | 'global-suggestion'

export interface SearchContext {
  // Can be expanded later for datasetId, etc.
  datasetId?: string
  // Aborted when a newer suggestion request supersedes this one
  signal?: AbortSignal
}

export interface SearchInteractionContext {
  buffer: string
  tokens: SearchToken[]
  suggestions: Suggestion[]
  activeIndex: number
  // Actions
  setBuffer: (val: string) => void
  addToken: (token: SearchToken) => void
  removeToken: (index: number) => void
  selectSuggestion: (index: number) => void
  clearSuggestions: () => void
}

export interface BasePlugin {
  id: string
  type: PluginType
  // Return true if handled
  onKeyDown?: (event: KeyboardEvent, context: SearchInteractionContext) => boolean | void
}

export interface Suggestion {
  label: string
  value: string
  type?: 'value' | 'key' | 'operator'
  icon?: string
  description?: string
}

// --- Filter Plugin ---
export interface FilterPlugin extends BasePlugin {
  type: 'filter'
  keys: string[] // e.g. ['status', 's']
  supportedOperators: string[] // operator plugin IDs, e.g. ['equals']

  // Parse one raw value (an item of `a|!b`, without its `!`) into the internal representation
  parseValue: (raw: string) => unknown

  // Get suggestions for values given the current input
  getSuggestions: (input: string, context: SearchContext) => Promise<Suggestion[]>

  // Optional custom renderer for the token
  component?: Component

  // Validate one parsed value
  validate?: (value: unknown) => boolean | string
}

// --- Operator Plugin ---
export interface OperatorPlugin extends BasePlugin {
  type: 'operator'
  symbols: string[] // e.g. [':', '=']
  label: string // e.g. 'Equals'
}

// --- Action Plugin ---
export interface ActionPlugin extends BasePlugin {
  type: 'action'
  trigger: string // e.g. '>'
  command: string // e.g. 'save'
  execute: (args: string[]) => void | Promise<void>
}

// --- Global Suggestion Plugin ---
export interface GlobalSuggestionPlugin extends BasePlugin {
  type: 'global-suggestion'
  getSuggestions: (context: SearchContext) => Promise<Suggestion[]>
}

export type SearchPlugin = FilterPlugin | OperatorPlugin | ActionPlugin | GlobalSuggestionPlugin

// --- Token Definitions ---

export type TokenType = 'text' | 'filter'

export interface BaseToken {
  id: string // Unique ID for v-for
  type: TokenType
  raw: string // The original string in the input
}

export interface TextToken extends BaseToken {
  type: 'text'
  value: string
}

// One item of a `key:a|!b` value list; the items are ORed
export interface FilterValue {
  value: unknown
  negated: boolean
}

export interface FilterToken extends BaseToken {
  type: 'filter'
  filterKey: string
  operator: string // the symbol as typed, e.g. ':'
  operatorId: string // the operator plugin id, e.g. 'equals'
  values: FilterValue[]
  pluginId: string
  // Set when the operator or value is invalid; the token is shown but not applied
  error?: string
}

export type SearchToken = TextToken | FilterToken

// --- Query emitted to consumers ---

export interface SearchQuery {
  text: string
  // Filters AND together; each filter's values OR together
  filters: { pluginId: string; key: string; operatorId: string; values: FilterValue[] }[]
}
