# Polito-Log Backend

Backend API for the Polito-Log political accountability tracking system.

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Validation**: Pydantic
- **Search**: Elasticsearch (planned)
- **Auth**: Google Auth (planned)

## Architecture

The backend follows a clean architecture pattern with clear separation of concerns:

```
app/
├── main.py           # FastAPI application entry point
├── config.py         # Application configuration
├── database.py       # Database setup and dependencies
├── models/           # SQLAlchemy ORM models
├── schemas/          # Pydantic schemas for validation
├── repositories/     # Data access layer (Repository pattern)
├── services/         # Business logic layer
└── routers/          # API route handlers
```

### Layers

1. **Models** (`models/`): SQLAlchemy ORM models representing database tables
2. **Schemas** (`schemas/`): Pydantic models for request/response validation
3. **Repositories** (`repositories/`): Data access layer with database operations
4. **Services** (`services/`): Business logic layer that uses repositories
5. **Routers** (`routers/`): FastAPI route handlers that use services

## Setup

### Option 1: Docker (Recommended)

#### Prerequisites
- Docker
- Docker Compose

#### Quick Start with dev.sh Script

The easiest way to get started is using the `dev.sh` script, which automatically handles Docker daemon startup and service management:

```bash
# Make script executable (first time only)
chmod +x dev.sh

# Start all services
./dev.sh

# Or explicitly start
./dev.sh up

# View logs
./dev.sh logs

# Stop services
./dev.sh down

# Restart services
./dev.sh restart

# Rebuild and restart
./dev.sh rebuild

# Open shell in backend container
./dev.sh shell

# View all available commands
./dev.sh help
```

#### Manual Docker Commands

If you prefer to use docker-compose directly:

1. Start all services (backend + PostgreSQL):
```bash
docker-compose up -d
```

2. View logs:
```bash
docker-compose logs -f backend
```

3. Stop services:
```bash
docker-compose down
```

4. Stop and remove all data:
```bash
docker-compose down -v
```

#### With pgAdmin (Database Management Tool)

```bash
# Using dev.sh
./dev.sh up --profile tools

# Or manually
docker-compose --profile tools up -d

# Access pgAdmin at http://localhost:5050
# Email: admin@polito-log.com
# Password: admin
```

#### Additional dev.sh Commands

```bash
# Start with pgAdmin
./dev.sh up --profile tools

# View database logs
./dev.sh logs db

# View all running containers
./dev.sh ps

# Clean up everything (removes data!)
./dev.sh clean

# Open shell in specific container
./dev.sh shell db

# Rebuild specific service
./dev.sh build backend
```

### Option 2: Local Installation

#### Prerequisites
- Python 3.11+
- PostgreSQL 14+

#### Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

4. Update the `.env` file with your database credentials:
```
DATABASE_URL=postgresql://user:password@localhost:5432/polito_log
```

#### Running the Application

Development mode with auto-reload:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Production mode:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

## API Endpoints

### Statements

- `POST /api/v1/statements/` - Create a new statement
- `GET /api/v1/statements/` - Get all statements (with pagination)
- `GET /api/v1/statements/{id}` - Get statement by ID
- `PUT /api/v1/statements/{id}` - Update a statement
- `DELETE /api/v1/statements/{id}` - Delete a statement (soft or hard)
- `GET /api/v1/statements/politician/{name}` - Get statements by politician
- `GET /api/v1/statements/party/{party}` - Get statements by party
- `GET /api/v1/statements/status/{status}` - Get statements by status
- `GET /api/v1/statements/search/?q={query}` - Search statements

### Statement Status Values

- `pending` - Statement awaiting verification
- `verified` - Statement has been verified
- `disputed` - Statement is disputed
- `retracted` - Statement has been retracted

## Database Schema

### Statements Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| politician_name | String(255) | Name of the politician |
| party | String(255) | Political party |
| statement_text | Text | The actual statement |
| source_url | String(512) | URL source (optional) |
| statement_date | DateTime | When statement was made |
| category | String(100) | Statement category (optional) |
| status | Enum | Verification status |
| is_active | Boolean | Soft delete flag |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

## Development

### Code Style

The codebase follows:
- Type hints throughout
- Comprehensive docstrings
- OOP best practices
- SOLID principles
- Repository and Service patterns

### Adding New Features

1. Create model in `models/`
2. Create schemas in `schemas/`
3. Create repository in `repositories/`
4. Create service in `services/`
5. Create router in `routers/`
6. Register router in `main.py`

## Docker Configuration

### Dockerfile
- **Multi-stage build** for optimized image size
- **Non-root user** for security
- **Health checks** for container monitoring
- **Minimal base image** (python:3.11-slim)

### docker-compose.yml Services

1. **db** (PostgreSQL 15):
   - Persistent data storage with named volumes
   - Health checks
   - Port 5432 exposed

2. **backend** (FastAPI):
   - Auto-reload in development mode
   - Source code mounted for hot reload
   - Depends on healthy database
   - Port 8000 exposed

3. **pgAdmin** (Optional):
   - Database management UI
   - Available with `--profile tools`
   - Port 5050 exposed

### Environment Variables

The following environment variables are configured in docker-compose.yml:

```
DATABASE_URL=postgresql://polito_user:polito_password@db:5432/polito_log
ENVIRONMENT=development
DEBUG=True
```

For production, create a `docker-compose.prod.yml` and override these values.
