import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { StatementResponse } from '@/api/types.gen'

vi.mock('@/api/sdk.gen', () => ({
  getStatementsApiV1StatementsGet: vi.fn<(...args: unknown[]) => unknown>(),
  searchStatementsApiV1StatementsSearchGet: vi.fn<(...args: unknown[]) => unknown>()
}))

import { getStatementsApiV1StatementsGet, searchStatementsApiV1StatementsSearchGet } from '@/api/sdk.gen'
import { useStatements } from './useStatements'

type Result = { data?: StatementResponse[]; error?: unknown }

function statement(id: number): StatementResponse {
  return { id } as StatementResponse
}

/** A mocked SDK call that resolves when told to, and rejects like fetch when aborted. */
function deferred() {
  let resolve!: (r: Result) => void
  let signal: AbortSignal | undefined
  const impl = (options: { signal?: AbortSignal }) => {
    signal = options.signal
    return new Promise<Result>((res, rej) => {
      resolve = res
      signal?.addEventListener('abort', () => rej(new DOMException('Aborted', 'AbortError')))
    })
  }
  return { impl, resolve: (r: Result) => resolve(r), get signal() { return signal } }
}

describe('useStatements list requests', () => {
  beforeEach(() => {
    vi.mocked(getStatementsApiV1StatementsGet).mockReset()
    vi.mocked(searchStatementsApiV1StatementsSearchGet).mockReset()
  })

  it('aborts a superseded request and keeps loading until the latest finishes', async () => {
    const first = deferred()
    const second = deferred()
    vi.mocked(getStatementsApiV1StatementsGet).mockImplementationOnce(first.impl as never)
    vi.mocked(searchStatementsApiV1StatementsSearchGet).mockImplementationOnce(second.impl as never)

    const { statements, loading, error, fetchStatements, searchStatements } = useStatements()
    const firstDone = fetchStatements()
    const secondDone = searchStatements('climate')

    await firstDone
    expect(first.signal?.aborted).toBe(true)
    expect(loading.value).toBe(true)
    expect(error.value).toBeNull()

    second.resolve({ data: [statement(2)] })
    await secondDone
    expect(loading.value).toBe(false)
    expect(statements.value.map(s => s.id)).toEqual([2])
  })

  it('ignores a stale response that arrives after a newer one', async () => {
    // The first response ignores the abort, as if it had already arrived
    let resolveFirst!: (r: Result) => void
    const second = deferred()
    vi.mocked(searchStatementsApiV1StatementsSearchGet)
      .mockImplementationOnce((() => new Promise<Result>(res => { resolveFirst = res })) as never)
      .mockImplementationOnce(second.impl as never)

    const { statements, searchStatements } = useStatements()
    const firstDone = searchStatements('a')
    const secondDone = searchStatements('ab')

    second.resolve({ data: [statement(2)] })
    await secondDone
    resolveFirst({ data: [statement(1)] })
    await firstDone

    expect(statements.value.map(s => s.id)).toEqual([2])
  })
})
