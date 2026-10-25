import { searchRegistry } from '../core/registry'
import { EqualsOperator, NotEqualsOperator } from './operators/EqualsOperator'
import { StatusPlugin } from './filters/StatusPlugin'

// Registered once at module load, so remounting SmartSearch doesn't re-register.
searchRegistry.register(EqualsOperator)
searchRegistry.register(NotEqualsOperator)
searchRegistry.register(StatusPlugin)
