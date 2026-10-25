import type { OperatorPlugin } from '../../core/types'

export const EqualsOperator: OperatorPlugin = {
  id: 'equals',
  type: 'operator',
  symbols: [':', '='],
  label: 'Equals',
}
