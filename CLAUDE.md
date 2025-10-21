# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the polito-log project an open source project for tracking political acountability of parties and politicians.
Core functionalities:
- Adding statements made by politicians
- Powerful quering engine to analyze statements
- Open API for data access

Core principles:
- Open source and open data
- Transparency and verifiability
- Superb UX, minimalistic UI

## Development Commands

### Backend

#### Option 1: Docker (Recommended)

```bash
# Navigate to backend directory
cd backend

# Start all services using dev.sh (handles Docker daemon automatically)
./dev.sh

# View logs
./dev.sh logs

# Stop services
./dev.sh down

# Restart after changes
./dev.sh restart

# Rebuild and restart
./dev.sh rebuild

# Start with pgAdmin for database management
./dev.sh up --profile tools

# Open shell in backend container
./dev.sh shell

# View all commands
./dev.sh help

# Access services:
# - Backend API: http://localhost:8000
# - Swagger UI: http://localhost:8000/api/v1/docs
# - ReDoc: http://localhost:8000/api/v1/redoc
# - pgAdmin (if started): http://localhost:5050
```

#### Option 2: Local Development

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database credentials

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Access API documentation
# Swagger UI: http://localhost:8000/api/v1/docs
# ReDoc: http://localhost:8000/api/v1/redoc
```

### Frontend

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Generate TypeScript API client from backend
# (requires backend to be running on http://localhost:8000)
npm run generate-api

# Run development server
npm run dev

# Access frontend at http://localhost:5173
```

**TypeScript API Client:**
- Auto-generated from FastAPI OpenAPI spec
- Full type safety for all API calls
- Regenerate after backend changes: `npm run generate-api`
- See `frontend/API_CLIENT.md` for detailed usage

## Architecture

Frontend:
 - Vue.js
 - Pinia
 - Naive UI
 - TypeScript

Backend:
 - Python 3.11+
 - FastAPI (REST API framework)
 - SQLAlchemy (ORM)
 - Pydantic (validation)
 - PostgreSQL (primary database)
 - Elasticsearch (search engine - planned)
 - Google Auth (authentication - planned)

Backend Architecture Pattern:
 - Clean Architecture with layered approach
 - Models: SQLAlchemy ORM models (database layer)
 - Schemas: Pydantic models (validation layer)
 - Repositories: Data access layer (Repository pattern)
 - Services: Business logic layer
 - Routers: API endpoint handlers
 - Strong typing throughout with Python type hints
 - Dependency injection for database sessions and services

CI/CD:
 - Github Actions
 - Railway