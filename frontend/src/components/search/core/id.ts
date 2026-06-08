/**
 * Generate a unique token id.
 *
 * `crypto.randomUUID()` is only available in secure contexts (HTTPS or
 * localhost). When the dev server is accessed over a LAN IP via plain http
 * (e.g. testing on a phone), it is `undefined` and throws, which previously
 * silently aborted token creation. Fall back to a non-crypto id there.
 */
export function generateId(): string {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
        return crypto.randomUUID()
    }
    return `id-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`
}
