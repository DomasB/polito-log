import type { Component } from 'vue'

export type PluginType = 'filter' | 'operator' | 'action' | 'global-suggestion'



export interface SearchContext {
    // Can be expanded later for datasetId, etc.
    datasetId?: string
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
    value: any
    type?: 'value' | 'key' | 'operator'
    icon?: string
    description?: string
}

// --- Filter Plugin ---
export interface FilterPlugin extends BasePlugin {
    type: 'filter'
    keys: string[] // e.g. ['status', 's']
    supportedOperators: string[] // e.g. [':', '=', '!=']

    // Parse a raw string value into the internal representation
    parseValue: (raw: string) => any

    // Get suggestions for values given the current input
    getSuggestions: (input: string, context: SearchContext) => Promise<Suggestion[]>

    // Optional custom renderer for the token
    component?: Component

    // Validate the value
    validate?: (value: any) => boolean | string
}

// --- Operator Plugin ---
export interface OperatorPlugin extends BasePlugin {
    type: 'operator'
    symbol: string // e.g. ':'
    label: string  // e.g. 'Equals'
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

export interface FilterToken extends BaseToken {
    type: 'filter'
    filterKey: string
    operator: string
    value: any
    pluginId: string
}

export type SearchToken = TextToken | FilterToken
