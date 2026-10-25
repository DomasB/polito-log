import { searchRegistry } from '../core/registry'
import { EqualsOperator } from './operators/EqualsOperator'
import { StatusPlugin } from './filters/StatusPlugin'

// Registered once at module load, so remounting SmartSearch doesn't re-register.
searchRegistry.register(EqualsOperator)

/** The status filter is for moderators and admins only; the API answers 403 to anyone else. */
export function setStatusFilterEnabled(enabled: boolean) {
  if (!enabled) searchRegistry.unregister(StatusPlugin.id)
  else if (!searchRegistry.getPlugin(StatusPlugin.id)) searchRegistry.register(StatusPlugin)
}
