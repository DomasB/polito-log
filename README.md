# Polito-log

Open source platform for collecting and monitoring political statements and actions of parties and individuals.

## Features
- Adding political statements with metadata and sources
- Querying statements by various parameters
- Easy data entry (assisted by ML models)
- Advanced data analysis

## Development

App is developed using Claude Code and human programming.

### Tech stack
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

CI/CD
- Github Actions: runs the backend and frontend tests on every push to `main` and every PR
- Railway: deploys each service from GitHub, after CI on that commit passes

See [DEPLOYMENT.md](DEPLOYMENT.md) for how deploys work.

## Contributing
All contributions are welcome. Please read [CONTRIBUTING](CONTRIBUTING.md) on how you can help.


