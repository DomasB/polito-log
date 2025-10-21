# TypeScript API Client

This frontend project uses automatically generated TypeScript client code from the FastAPI backend's OpenAPI specification.

## Overview

The API client is generated using **@hey-api/openapi-ts**, the tool recommended by FastAPI. It provides:

✅ **Full type safety** - TypeScript types for all API requests and responses
✅ **Autocomplete** - IntelliSense for all endpoints and parameters
✅ **Type checking** - Compile-time validation of API calls
✅ **Auto-sync** - Regenerate when backend changes

## Generated Files

The client is generated in `src/api/` and includes:

```
src/api/
├── client.gen.ts    # HTTP client configuration
├── sdk.gen.ts       # API method functions
├── types.gen.ts     # TypeScript types
├── index.ts         # Public exports
└── core/            # Internal utilities
```

**⚠️ Do not edit these files manually** - they are auto-generated.

## Generating the Client

### Prerequisites

1. Backend must be running on `http://localhost:8000`
2. Run backend: `cd ../backend && ./dev.sh`

### Generate

```bash
# From frontend directory
npm run generate-api
```

This fetches the OpenAPI spec from `http://localhost:8000/api/v1/openapi.json` and generates TypeScript code.

### When to Regenerate

Regenerate the client whenever you:
- Add new API endpoints in the backend
- Change request/response schemas
- Modify field names or types
- Update API documentation

## Configuration

The generator is configured in `openapi-ts.config.ts`:

```typescript
import { defineConfig } from '@hey-api/openapi-ts'

export default defineConfig({
  client: '@hey-api/client-fetch',    // Use native fetch API
  input: 'http://localhost:8000/api/v1/openapi.json',
  output: {
    path: 'src/api',
    format: 'prettier',
    lint: 'eslint'
  },
  types: {
    enums: 'javascript'               // Generate enums as const objects
  },
  services: {
    asClass: false                    // Generate functions, not classes
  }
})
```

## Usage

### Option 1: Direct API Calls

Import and call generated functions directly:

```typescript
import {
  getStatementsApiV1StatementsGet,
  createStatementApiV1StatementsPost
} from '@/api/sdk.gen'
import type { StatementCreate } from '@/api/types.gen'

// Fetch all statements
const { data, error } = await getStatementsApiV1StatementsGet({
  query: {
    skip: 0,
    limit: 10,
    active_only: true
  }
})

if (error) {
  console.error('Failed to fetch statements')
} else {
  console.log('Statements:', data)
}

// Create a statement
const newStatement: StatementCreate = {
  politician_name: 'John Doe',
  party: 'Example Party',
  statement_text: 'Policy statement here...',
  statement_date: new Date().toISOString(),
  status: 'pending'
}

const { data: created, error: createError } = await createStatementApiV1StatementsPost({
  body: newStatement
})
```

### Option 2: Using Composables (Recommended)

For Vue components, use the provided composable:

```vue
<script setup lang="ts">
import { onMounted } from 'vue'
import { useStatements } from '@/composables/useStatements'

const {
  statements,        // Reactive array of statements
  loading,           // Loading state
  error,             // Error message
  fetchStatements,   // Fetch all statements
  createStatement,   // Create new statement
  searchStatements   // Search statements
} = useStatements()

// Fetch on mount
onMounted(async () => {
  await fetchStatements({ limit: 20 })
})

// Create statement
async function addStatement() {
  await createStatement({
    politician_name: 'Jane Smith',
    party: 'Progressive Party',
    statement_text: 'New policy announcement...',
    statement_date: new Date().toISOString(),
    status: 'pending'
  })
}
</script>

<template>
  <div>
    <div v-if="loading">Loading...</div>
    <div v-if="error">{{ error }}</div>

    <div v-for="statement in statements" :key="statement.id">
      <h3>{{ statement.politician_name }}</h3>
      <p>{{ statement.statement_text }}</p>
    </div>
  </div>
</template>
```

## Available Types

All types from the backend are available in `@/api/types.gen`:

```typescript
import type {
  StatementResponse,     // Complete statement with all fields
  StatementCreate,       // For creating statements
  StatementUpdate,       // For updating statements
  StatementStatus        // Enum: pending | verified | disputed | retracted
} from '@/api/types.gen'
```

### StatementCreate

```typescript
type StatementCreate = {
  politician_name: string
  party: string
  statement_text: string
  statement_date: string              // ISO date string
  source_url?: string | null
  category?: string | null
  status?: StatementStatus            // Default: 'pending'
}
```

### StatementResponse

```typescript
type StatementResponse = {
  id: number
  politician_name: string
  party: string
  statement_text: string
  statement_date: string
  source_url: string | null
  category: string | null
  status: StatementStatus
  is_active: boolean
  created_at: string
  updated_at: string
}
```

## Available API Methods

All backend endpoints are available as generated functions:

### Statements

```typescript
// List statements (with pagination)
getStatementsApiV1StatementsGet({ query: { skip: 0, limit: 100 } })

// Get single statement
getStatementApiV1StatementsStatementIdGet({ path: { statement_id: 1 } })

// Create statement
createStatementApiV1StatementsPost({ body: statementData })

// Update statement
updateStatementApiV1StatementsStatementIdPut({
  path: { statement_id: 1 },
  body: updates
})

// Delete statement
deleteStatementApiV1StatementsStatementIdDelete({
  path: { statement_id: 1 },
  query: { soft_delete: true }
})

// Search statements
searchStatementsApiV1StatementsSearchGet({ query: { q: 'keyword' } })

// Filter by politician
getStatementsByPoliticianApiV1StatementsPoliticianPoliticianNameGet({
  path: { politician_name: 'John Doe' }
})

// Filter by party
getStatementsByPartyApiV1StatementsPartyPartyGet({
  path: { party: 'Example Party' }
})

// Filter by status
getStatementsByStatusApiV1StatementsStatusStatusGet({
  path: { status: 'verified' }
})
```

## Error Handling

All API calls return a tuple `{ data, error }`:

```typescript
const { data, error } = await getStatementsApiV1StatementsGet()

if (error) {
  // Handle error
  if (error.status === 404) {
    console.error('Not found')
  } else if (error.status === 422) {
    console.error('Validation error:', error.detail)
  } else {
    console.error('API error:', error)
  }
} else {
  // Use data
  console.log(data)
}
```

## Composables

### useStatements

Provided composable for managing statements with reactive state:

```typescript
const {
  // Reactive state
  statements,           // Ref<StatementResponse[]>
  currentStatement,     // Ref<StatementResponse | null>
  loading,              // Ref<boolean>
  error,                // Ref<string | null>
  totalCount,           // Ref<number>

  // Computed
  hasStatements,        // ComputedRef<boolean>
  hasError,             // ComputedRef<boolean>

  // Methods
  fetchStatements,      // (options?) => Promise<void>
  fetchStatement,       // (id) => Promise<StatementResponse | null>
  createStatement,      // (data) => Promise<StatementResponse | null>
  updateStatement,      // (id, updates) => Promise<StatementResponse | null>
  deleteStatement,      // (id, soft?) => Promise<boolean>
  searchStatements,     // (query, options?) => Promise<StatementResponse[]>
  fetchByPolitician,    // (name, options?) => Promise<StatementResponse[]>
  fetchByParty,         // (party, options?) => Promise<StatementResponse[]>
  clearError,           // () => void
  reset                 // () => void
} = useStatements()
```

## Best Practices

### 1. Always Check Errors

```typescript
const { data, error } = await fetchSomething()
if (error) {
  // Handle error appropriately
  return
}
// Safe to use data
```

### 2. Use TypeScript Types

```typescript
import type { StatementCreate } from '@/api/types.gen'

// TypeScript will validate this
const statement: StatementCreate = {
  politician_name: 'Name',
  party: 'Party',
  statement_text: 'Text',
  statement_date: new Date().toISOString()
}
```

### 3. Handle Loading States

```vue
<div v-if="loading">Loading...</div>
<div v-else-if="error">{{ error }}</div>
<div v-else>{{ data }}</div>
```

### 4. Use Composables for Components

Don't call API functions directly in components. Use composables for:
- Reactive state management
- Consistent error handling
- Reusable logic

## Troubleshooting

### "Cannot find module '@/api/sdk.gen'"

**Solution:** Generate the API client first:
```bash
npm run generate-api
```

### "Cannot connect to OpenAPI endpoint"

**Solution:** Start the backend:
```bash
cd ../backend && ./dev.sh
```

### "Type errors after backend changes"

**Solution:** Regenerate the client:
```bash
npm run generate-api
```

### "Module not found: @hey-api/client-fetch"

**Solution:** Install dependencies:
```bash
npm install
```

## Learn More

- [Hey API Documentation](https://heyapi.vercel.app/)
- [FastAPI Generate Clients](https://fastapi.tiangolo.com/advanced/generate-clients/)
- [OpenAPI Specification](https://swagger.io/specification/)
