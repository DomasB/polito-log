import { describe, it, expect } from 'vitest'
import { nextTick } from 'vue'
import { mount, type DOMWrapper } from '@vue/test-utils'
import SuggestionList from './SuggestionList.vue'
import type { Suggestion } from '../core/types'

const suggestions: Suggestion[] = [
    { label: 'verified', value: 'verified', type: 'value' },
    { label: 'pending', value: 'pending', type: 'value' }
]

// Dispatch real events: test-utils can't set read-only fields like `detail`
async function fire(el: DOMWrapper<Element>, type: string, init: PointerEventInit = {}) {
    const Ctor = type === 'click' ? MouseEvent : PointerEvent
    el.element.dispatchEvent(new Ctor(type, { bubbles: true, cancelable: true, ...init }))
    await nextTick()
}

function mountList() {
    return mount(SuggestionList, {
        props: { suggestions, activeIndex: -1, listboxId: 'lb' }
    })
}

describe('SuggestionList', () => {
    it('renders a listbox with options', () => {
        const wrapper = mountList()
        expect(wrapper.find('[role="listbox"]').attributes('id')).toBe('lb')
        const options = wrapper.findAll('[role="option"]')
        expect(options.map(o => o.attributes('id'))).toEqual(['lb-0', 'lb-1'])
    })

    it('selects on a primary-button tap', async () => {
        const wrapper = mountList()
        const option = wrapper.findAll('[role="option"]')[0]!
        await fire(option, 'pointerdown', { button: 0, pointerId: 1 })
        await fire(option, 'pointerup', { button: 0, pointerId: 1 })
        await fire(option, 'click', { detail: 1 })
        expect(wrapper.emitted('select')).toEqual([[suggestions[0]]])
    })

    it('does not select a drag released over an item', async () => {
        const wrapper = mountList()
        const [first, second] = wrapper.findAll('[role="option"]')
        await fire(first!, 'pointerdown', { button: 0, pointerId: 1 })
        await fire(second!, 'pointerup', { button: 0, pointerId: 1 })
        // A press that starts outside any item
        await fire(second!, 'pointerup', { button: 0, pointerId: 2 })
        expect(wrapper.emitted('select')).toBeUndefined()
    })

    it('ignores non-primary buttons and cancelled pointers', async () => {
        const wrapper = mountList()
        const option = wrapper.findAll('[role="option"]')[0]!
        await fire(option, 'pointerdown', { button: 2, pointerId: 1 })
        await fire(option, 'pointerup', { button: 2, pointerId: 1 })
        await fire(option, 'pointerdown', { button: 0, pointerId: 1 })
        await fire(option, 'pointercancel', { pointerId: 1 })
        await fire(option, 'pointerup', { button: 0, pointerId: 1 })
        expect(wrapper.emitted('select')).toBeUndefined()
    })

    it('selects on a synthetic click from a screen reader or keyboard', async () => {
        const wrapper = mountList()
        await fire(wrapper.findAll('[role="option"]')[1]!, 'click', { detail: 0 })
        expect(wrapper.emitted('select')).toEqual([[suggestions[1]]])
    })
})
