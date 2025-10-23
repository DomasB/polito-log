#!/bin/bash

# dev.sh - Development startup script for Polito-Log Backend
# This script starts the Docker daemon (if needed) and runs docker-compose

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Polito-Log Backend - Development Setup${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Function to check if Docker daemon is running
check_docker_daemon() {
    if $USE_SUDO docker info >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to check and fix Docker permissions
check_docker_permissions() {
    # Try running docker without sudo
    if docker ps >/dev/null 2>&1; then
        USE_SUDO=""
        return 0
    fi

    # Check if it's a permission issue
    if docker ps 2>&1 | grep -q "permission denied"; then
        echo -e "${YELLOW}→ Docker permission issue detected${NC}"

        # Check if docker group exists and user is in it
        if getent group docker >/dev/null 2>&1; then
            if ! groups | grep -q docker; then
                echo -e "${YELLOW}  Adding current user to docker group...${NC}"
                sudo usermod -aG docker "$USER"
                echo -e "${GREEN}✓ User added to docker group${NC}"
                echo -e "${YELLOW}⚠ You need to log out and log back in for group changes to take effect${NC}"
                echo -e "${YELLOW}  OR run: newgrp docker${NC}"
                echo -e "${YELLOW}  For now, using sudo for docker commands...${NC}"
                USE_SUDO="sudo"
            else
                echo -e "${YELLOW}  User is in docker group but permissions not active${NC}"
                echo -e "${YELLOW}  Try running: newgrp docker${NC}"
                echo -e "${YELLOW}  For now, using sudo for docker commands...${NC}"
                USE_SUDO="sudo"
            fi
        else
            echo -e "${YELLOW}  Docker group doesn't exist, using sudo...${NC}"
            USE_SUDO="sudo"
        fi

        # Test with sudo
        if sudo docker ps >/dev/null 2>&1; then
            return 0
        else
            return 1
        fi
    fi

    return 1
}

# Function to start Docker daemon
start_docker_daemon() {
    echo -e "${YELLOW}→ Docker daemon is not running. Attempting to start...${NC}"

    # Check if running on Linux with systemd
    if command -v systemctl &> /dev/null; then
        echo -e "${BLUE}  Using systemctl to start Docker...${NC}"
        if sudo systemctl start docker; then
            echo -e "${GREEN}✓ Docker daemon started successfully${NC}"
            sleep 2
            return 0
        else
            echo -e "${RED}✗ Failed to start Docker daemon with systemctl${NC}"
            return 1
        fi

    # Check if running on macOS or Windows (Docker Desktop)
    elif [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        echo -e "${YELLOW}  Please start Docker Desktop manually${NC}"
        echo -e "${YELLOW}  Waiting for Docker Desktop to start...${NC}"

        # Wait up to 60 seconds for Docker to start
        for i in {1..60}; do
            if check_docker_daemon; then
                echo -e "${GREEN}✓ Docker daemon is now running${NC}"
                return 0
            fi
            sleep 1
            echo -n "."
        done

        echo ""
        echo -e "${RED}✗ Docker daemon did not start within 60 seconds${NC}"
        return 1

    # Fallback for other systems
    else
        echo -e "${YELLOW}  Trying to start Docker service...${NC}"
        if sudo service docker start 2>/dev/null; then
            echo -e "${GREEN}✓ Docker daemon started successfully${NC}"
            sleep 2
            return 0
        else
            echo -e "${RED}✗ Could not start Docker daemon automatically${NC}"
            echo -e "${YELLOW}  Please start Docker manually and run this script again${NC}"
            return 1
        fi
    fi
}

# Function to check if docker-compose is installed
check_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="$USE_SUDO docker-compose"
        return 0
    elif $USE_SUDO docker compose version &> /dev/null 2>&1; then
        COMPOSE_CMD="$USE_SUDO docker compose"
        return 0
    else
        return 1
    fi
}

# Main execution
main() {
    # Change to script directory
    cd "$SCRIPT_DIR"

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}✗ Docker is not installed${NC}"
        echo -e "${YELLOW}  Please install Docker: https://docs.docker.com/get-docker/${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ Docker is installed${NC}"

    # Initialize USE_SUDO variable
    USE_SUDO=""

    # Check if Docker daemon is running
    if check_docker_daemon; then
        echo -e "${GREEN}✓ Docker daemon is running${NC}"
    else
        if ! start_docker_daemon; then
            echo -e "${RED}✗ Cannot proceed without Docker daemon${NC}"
            exit 1
        fi
    fi

    # Check Docker permissions first
    if ! check_docker_permissions; then
        echo -e "${RED}✗ Cannot access Docker${NC}"
        echo -e "${YELLOW}  Please check Docker installation and permissions${NC}"
        exit 1
    fi

    if [ -n "$USE_SUDO" ]; then
        echo -e "${YELLOW}⚠ Running Docker commands with sudo${NC}"
    else
        echo -e "${GREEN}✓ Docker permissions OK${NC}"
    fi


    # Check if docker-compose is installed
    if ! check_docker_compose; then
        echo -e "${RED}✗ docker-compose is not installed${NC}"
        echo -e "${YELLOW}  Please install docker-compose: https://docs.docker.com/compose/install/${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ docker-compose is available${NC}"
    echo ""

    # Parse command line arguments
    ACTION="${1:-up}"
    EXTRA_ARGS="${@:2}"

    case "$ACTION" in
        up|start)
            echo -e "${BLUE}→ Starting services...${NC}"
            $COMPOSE_CMD up -d $EXTRA_ARGS
            echo ""
            echo -e "${GREEN}✓ Services started successfully!${NC}"
            echo ""
            echo -e "${BLUE}Access points:${NC}"
            echo -e "  • Backend API:  ${GREEN}http://localhost:8000${NC}"
            echo -e "  • Swagger UI:   ${GREEN}http://localhost:8000/api/v1/docs${NC}"
            echo -e "  • ReDoc:        ${GREEN}http://localhost:8000/api/v1/redoc${NC}"
            echo -e "  • PostgreSQL:   ${GREEN}localhost:5432${NC}"
            echo ""
            echo -e "${YELLOW}View logs:${NC} $COMPOSE_CMD logs -f backend"
            echo -e "${YELLOW}Stop services:${NC} ./dev.sh down"
            ;;

        down|stop)
            echo -e "${BLUE}→ Stopping services...${NC}"
            $COMPOSE_CMD down $EXTRA_ARGS
            echo -e "${GREEN}✓ Services stopped${NC}"
            ;;

        restart)
            echo -e "${BLUE}→ Restarting services...${NC}"
            $COMPOSE_CMD down
            $COMPOSE_CMD up -d $EXTRA_ARGS
            echo -e "${GREEN}✓ Services restarted${NC}"
            ;;

        logs)
            $COMPOSE_CMD logs -f ${EXTRA_ARGS:-backend}
            ;;

        ps|status)
            $COMPOSE_CMD ps
            ;;

        build)
            echo -e "${BLUE}→ Building services...${NC}"
            $COMPOSE_CMD build $EXTRA_ARGS
            echo -e "${GREEN}✓ Build complete${NC}"
            ;;

        rebuild)
            echo -e "${BLUE}→ Rebuilding and restarting services...${NC}"
            $COMPOSE_CMD down
            $COMPOSE_CMD build $EXTRA_ARGS
            $COMPOSE_CMD up -d
            echo -e "${GREEN}✓ Services rebuilt and started${NC}"
            ;;

        clean)
            echo -e "${YELLOW}⚠ This will remove all containers and volumes (data will be lost)${NC}"
            read -p "Are you sure? (y/N) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                echo -e "${BLUE}→ Cleaning up...${NC}"
                $COMPOSE_CMD down -v
                echo -e "${GREEN}✓ Cleanup complete${NC}"
            else
                echo -e "${YELLOW}Cancelled${NC}"
            fi
            ;;

        shell|bash)
            SERVICE="${2:-backend}"
            echo -e "${BLUE}→ Opening shell in $SERVICE container...${NC}"
            $COMPOSE_CMD exec $SERVICE bash
            ;;

        help|--help|-h)
            echo -e "${BLUE}Usage:${NC} ./dev.sh [command] [options]"
            echo ""
            echo -e "${BLUE}Commands:${NC}"
            echo -e "  ${GREEN}up, start${NC}      Start all services (default)"
            echo -e "  ${GREEN}down, stop${NC}     Stop all services"
            echo -e "  ${GREEN}restart${NC}        Restart all services"
            echo -e "  ${GREEN}logs${NC}           View logs (default: backend)"
            echo -e "  ${GREEN}ps, status${NC}     Show running containers"
            echo -e "  ${GREEN}build${NC}          Build/rebuild images"
            echo -e "  ${GREEN}rebuild${NC}        Build and restart services"
            echo -e "  ${GREEN}clean${NC}          Remove containers and volumes"
            echo -e "  ${GREEN}shell, bash${NC}    Open shell in container (default: backend)"
            echo -e "  ${GREEN}help${NC}           Show this help message"
            echo ""
            echo -e "${BLUE}Examples:${NC}"
            echo -e "  ./dev.sh                    # Start services"
            echo -e "  ./dev.sh up --profile tools # Start with pgAdmin"
            echo -e "  ./dev.sh logs               # View backend logs"
            echo -e "  ./dev.sh logs db            # View database logs"
            echo -e "  ./dev.sh shell              # Open shell in backend"
            echo -e "  ./dev.sh rebuild backend    # Rebuild backend only"
            ;;

        *)
            echo -e "${YELLOW}Unknown command: $ACTION${NC}"
            echo -e "Run ${GREEN}./dev.sh help${NC} for usage information"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
