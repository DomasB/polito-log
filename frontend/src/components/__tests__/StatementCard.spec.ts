import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'

import StatementCard from '../StatementCard.vue'
import type { StatementResponse } from '@/api/types.gen'

const statement: StatementResponse = {
  id: 1,
  politician_name: 'Jane Doe',
  party: 'Example Party',
  statement_text: 'We will build more bike lanes.',
  source_url: 'https://example.com/source',
  statement_date: '2026-01-15T00:00:00Z',
  category: 'Transport',
  status: 'verified',
  is_active: true,
  created_at: '2026-01-15T00:00:00Z',
  updated_at: '2026-01-15T00:00:00Z',
}

describe('StatementCard', () => {
  it('renders the statement and links to its source', () => {
    const wrapper = mount(StatementCard, { props: { statement } })

    expect(wrapper.text()).toContain('Jane Doe')
    expect(wrapper.text()).toContain('(Example Party)')
    expect(wrapper.text()).toContain('We will build more bike lanes.')
    expect(wrapper.text()).toContain('verified')
    expect(wrapper.find('a').attributes('href')).toBe('https://example.com/source')
  })
})
