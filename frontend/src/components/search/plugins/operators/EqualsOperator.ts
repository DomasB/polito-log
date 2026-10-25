import type { OperatorPlugin } from '../../core/types'

export const EqualsOperator: OperatorPlugin = {
  id: 'equals',
  type: 'operator',
  symbols: [':', '='],
  label: 'Equals',
}

export const NotEqualsOperator: OperatorPlugin = {
  id: 'not-equals',
  type: 'operator',
  symbols: ['!='],
  label: 'Not equals',
}
