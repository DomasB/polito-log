#!/bin/bash
set -e

echo "Starting application..."

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Check if migration was successful
if [ $? -eq 0 ]; then
    echo "✓ Database migrations completed successfully"
else
    echo "✗ Database migrations failed"
    exit 1
fi

# Start the application
echo "Starting uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
