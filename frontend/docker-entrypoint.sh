#!/bin/sh
set -e

# Replace PORT placeholder in nginx config with actual PORT from Railway
# Default to 8080 if PORT is not set (for local development)
export PORT=${PORT:-8080}

# Use envsubst to replace $PORT in nginx config template
envsubst '${PORT}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

# Start nginx
exec nginx -g 'daemon off;'
