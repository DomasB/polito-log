# Generated API Client

This directory contains **auto-generated** TypeScript code from the FastAPI backend's OpenAPI specification.

## ⚠️ Important

**DO NOT EDIT THESE FILES MANUALLY**

All files with `.gen.ts` extension are automatically generated and will be overwritten when you run `npm run generate-api`.

## How to Regenerate

1. Make sure the backend is running on `http://localhost:8000`
2. Run from frontend directory:
   ```bash
   npm run generate-api
   ```

## Generated Files

- `client.gen.ts` - HTTP client configuration
- `sdk.gen.ts` - API method functions for all endpoints
- `types.gen.ts` - TypeScript types for requests/responses
- `index.ts` - Public exports
- `core/` - Internal utilities

## Usage

See `../../../API_CLIENT.md` for complete documentation and examples.

Quick example:
```typescript
import { getStatementsApiV1StatementsGet } from '@/api/sdk.gen'

const { data, error } = await getStatementsApiV1StatementsGet({
  query: { limit: 10 }
})
```

## When to Regenerate

Regenerate whenever you:
- Add new backend endpoints
- Change API request/response schemas
- Modify backend models
- Update field names or types
