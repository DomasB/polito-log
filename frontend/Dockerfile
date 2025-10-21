# Multi-stage build for optimized production frontend

# Stage 1: Build the application
FROM node:20-alpine as builder

WORKDIR /app

# Declare build argument for API URL
# Railway passes environment variables as build args automatically
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
# Vite will replace import.meta.env.VITE_API_URL with the actual value during build
RUN npm run build

# Stage 2: Serve the static files with nginx
FROM nginx:alpine

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom nginx configuration template
COPY nginx.conf /etc/nginx/conf.d/default.conf.template

# Copy and set up entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Expose port (Railway will set PORT environment variable)
EXPOSE ${PORT:-8080}

# Health check - uses PORT env variable with fallback to 8080
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:${PORT:-8080}/health || exit 1

# Start nginx with custom entrypoint that handles PORT substitution
ENTRYPOINT ["/docker-entrypoint.sh"]
