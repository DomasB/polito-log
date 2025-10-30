@echo off
setlocal enabledelayedexpansion

:: dev.cmd - Development startup script for Polito-Log Backend (Windows)
:: This script checks Docker Desktop and runs docker-compose

:: Enable ANSI color codes in Windows 10+
for /f "tokens=4-7 delims=[.] " %%i in ('ver') do (
    if %%i GEQ 10 (
        :: Enable virtual terminal processing for colors
        reg add HKCU\Console /v VirtualTerminalLevel /t REG_DWORD /d 1 /f >nul 2>&1
    )
)

:: Colors for output (ANSI escape codes)
set "RED=[31m"
set "GREEN=[32m"
set "YELLOW=[33m"
set "BLUE=[34m"
set "NC=[0m"

:: Script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo %BLUE%━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%NC%
echo %BLUE%  Polito-Log Backend - Development Setup%NC%
echo %BLUE%━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%NC%
echo.

:: Check if Docker is installed
where docker >nul 2>&1
if errorlevel 1 (
    echo %RED%✗ Docker is not installed%NC%
    echo %YELLOW%  Please install Docker Desktop: https://docs.docker.com/desktop/install/windows/%NC%
    exit /b 1
)

echo %GREEN%✓ Docker is installed%NC%

:: Check if Docker daemon is running
docker info >nul 2>&1
if errorlevel 1 (
    echo %YELLOW%→ Docker daemon is not running%NC%
    echo %YELLOW%  Please start Docker Desktop and wait for it to be ready...%NC%
    echo %YELLOW%  Waiting up to 60 seconds for Docker to start...%NC%

    set /a WAIT_COUNT=0
    :wait_docker
    set /a WAIT_COUNT+=1
    if !WAIT_COUNT! GTR 60 (
        echo.
        echo %RED%✗ Docker daemon did not start within 60 seconds%NC%
        echo %YELLOW%  Please start Docker Desktop manually and run this script again%NC%
        exit /b 1
    )

    docker info >nul 2>&1
    if errorlevel 1 (
        echo|set /p="."
        timeout /t 1 /nobreak >nul
        goto wait_docker
    )
    echo.
    echo %GREEN%✓ Docker daemon is now running%NC%
) else (
    echo %GREEN%✓ Docker daemon is running%NC%
)

:: Check if docker-compose is available
set "COMPOSE_CMD="
docker-compose version >nul 2>&1
if not errorlevel 1 (
    set "COMPOSE_CMD=docker-compose"
) else (
    docker compose version >nul 2>&1
    if not errorlevel 1 (
        set "COMPOSE_CMD=docker compose"
    ) else (
        echo %RED%✗ docker-compose is not available%NC%
        echo %YELLOW%  Please install Docker Compose: https://docs.docker.com/compose/install/%NC%
        exit /b 1
    )
)

echo %GREEN%✓ docker-compose is available%NC%
echo.

:: Parse command line arguments
set "ACTION=%~1"
if "%ACTION%"=="" set "ACTION=up"

:: Collect extra arguments
set "EXTRA_ARGS="
shift
:parse_args
if "%~1"=="" goto args_done
set "EXTRA_ARGS=!EXTRA_ARGS! %~1"
shift
goto parse_args
:args_done

:: Execute commands
if /i "%ACTION%"=="up" goto cmd_up
if /i "%ACTION%"=="start" goto cmd_up
if /i "%ACTION%"=="debug" goto cmd_debug
if /i "%ACTION%"=="down" goto cmd_down
if /i "%ACTION%"=="stop" goto cmd_down
if /i "%ACTION%"=="restart" goto cmd_restart
if /i "%ACTION%"=="logs" goto cmd_logs
if /i "%ACTION%"=="ps" goto cmd_ps
if /i "%ACTION%"=="status" goto cmd_ps
if /i "%ACTION%"=="build" goto cmd_build
if /i "%ACTION%"=="rebuild" goto cmd_rebuild
if /i "%ACTION%"=="clean" goto cmd_clean
if /i "%ACTION%"=="shell" goto cmd_shell
if /i "%ACTION%"=="bash" goto cmd_shell
if /i "%ACTION%"=="help" goto cmd_help
if /i "%ACTION%"=="--help" goto cmd_help
if /i "%ACTION%"=="-h" goto cmd_help

echo %YELLOW%Unknown command: %ACTION%%NC%
echo Run %GREEN%dev.cmd help%NC% for usage information
exit /b 1

:cmd_up
echo %BLUE%→ Starting services...%NC%
%COMPOSE_CMD% up -d %EXTRA_ARGS%
if errorlevel 1 (
    echo %RED%✗ Failed to start services%NC%
    exit /b 1
)
echo.
echo %GREEN%✓ Services started successfully!%NC%
echo.
echo %BLUE%Access points:%NC%
echo   • Backend API:  %GREEN%http://localhost:8000%NC%
echo   • Swagger UI:   %GREEN%http://localhost:8000/api/v1/docs%NC%
echo   • ReDoc:        %GREEN%http://localhost:8000/api/v1/redoc%NC%
echo   • PostgreSQL:   %GREEN%localhost:5432%NC%
echo.
echo %YELLOW%View logs:%NC% dev.cmd logs
echo %YELLOW%Stop services:%NC% dev.cmd down
goto end

:cmd_debug
echo %BLUE%→ Starting services in DEBUG mode...%NC%
echo %YELLOW%⚠ Debugger will wait for VSCode to attach on port 5678%NC%
%COMPOSE_CMD% -f docker-compose.yml -f docker-compose.debug.yml up -d %EXTRA_ARGS%
if errorlevel 1 (
    echo %RED%✗ Failed to start services%NC%
    exit /b 1
)
echo.
echo %GREEN%✓ Services started in debug mode!%NC%
echo.
echo %BLUE%Access points:%NC%
echo   • Backend API:  %GREEN%http://localhost:8000%NC%
echo   • Swagger UI:   %GREEN%http://localhost:8000/api/v1/docs%NC%
echo   • ReDoc:        %GREEN%http://localhost:8000/api/v1/redoc%NC%
echo   • PostgreSQL:   %GREEN%localhost:5432%NC%
echo   • Debug Port:   %GREEN%localhost:5678%NC%
echo.
echo %BLUE%Next steps:%NC%
echo   1. Open VSCode and set breakpoints in your code
echo   2. Go to Run and Debug (Ctrl+Shift+D)
echo   3. Select 'Python: Remote Attach (Docker)'
echo   4. Press F5 to attach debugger
echo.
echo %YELLOW%View logs:%NC% dev.cmd logs
echo %YELLOW%Stop services:%NC% dev.cmd down
goto end

:cmd_down
echo %BLUE%→ Stopping services...%NC%
%COMPOSE_CMD% down %EXTRA_ARGS%
if errorlevel 1 (
    echo %RED%✗ Failed to stop services%NC%
    exit /b 1
)
echo %GREEN%✓ Services stopped%NC%
goto end

:cmd_restart
echo %BLUE%→ Restarting services...%NC%
%COMPOSE_CMD% down
if errorlevel 1 (
    echo %RED%✗ Failed to stop services%NC%
    exit /b 1
)
%COMPOSE_CMD% up -d %EXTRA_ARGS%
if errorlevel 1 (
    echo %RED%✗ Failed to start services%NC%
    exit /b 1
)
echo %GREEN%✓ Services restarted%NC%
goto end

:cmd_logs
if "%EXTRA_ARGS%"=="" (
    %COMPOSE_CMD% logs -f backend
) else (
    %COMPOSE_CMD% logs -f %EXTRA_ARGS%
)
goto end

:cmd_ps
%COMPOSE_CMD% ps
goto end

:cmd_build
echo %BLUE%→ Building services...%NC%
%COMPOSE_CMD% build %EXTRA_ARGS%
if errorlevel 1 (
    echo %RED%✗ Build failed%NC%
    exit /b 1
)
echo %GREEN%✓ Build complete%NC%
goto end

:cmd_rebuild
echo %BLUE%→ Rebuilding and restarting services...%NC%
%COMPOSE_CMD% down
if errorlevel 1 (
    echo %RED%✗ Failed to stop services%NC%
    exit /b 1
)
%COMPOSE_CMD% build %EXTRA_ARGS%
if errorlevel 1 (
    echo %RED%✗ Build failed%NC%
    exit /b 1
)
%COMPOSE_CMD% up -d
if errorlevel 1 (
    echo %RED%✗ Failed to start services%NC%
    exit /b 1
)
echo %GREEN%✓ Services rebuilt and started%NC%
goto end

:cmd_clean
echo %YELLOW%⚠ This will remove all containers and volumes (data will be lost)%NC%
choice /C YN /M "Are you sure"
if errorlevel 2 (
    echo %YELLOW%Cancelled%NC%
    goto end
)
if errorlevel 1 (
    echo %BLUE%→ Cleaning up...%NC%
    %COMPOSE_CMD% down -v
    if errorlevel 1 (
        echo %RED%✗ Cleanup failed%NC%
        exit /b 1
    )
    echo %GREEN%✓ Cleanup complete%NC%
)
goto end

:cmd_shell
set "SERVICE=%~2"
if "%SERVICE%"=="" set "SERVICE=backend"
echo %BLUE%→ Opening shell in %SERVICE% container...%NC%
%COMPOSE_CMD% exec %SERVICE% bash
goto end

:cmd_help
echo %BLUE%Usage:%NC% dev.cmd [command] [options]
echo.
echo %BLUE%Commands:%NC%
echo   %GREEN%up, start%NC%      Start all services (default)
echo   %GREEN%debug%NC%          Start services in DEBUG mode (with VSCode debugger)
echo   %GREEN%down, stop%NC%     Stop all services
echo   %GREEN%restart%NC%        Restart all services
echo   %GREEN%logs%NC%           View logs (default: backend)
echo   %GREEN%ps, status%NC%     Show running containers
echo   %GREEN%build%NC%          Build/rebuild images
echo   %GREEN%rebuild%NC%        Build and restart services
echo   %GREEN%clean%NC%          Remove containers and volumes
echo   %GREEN%shell, bash%NC%    Open shell in container (default: backend)
echo   %GREEN%help%NC%           Show this help message
echo.
echo %BLUE%Examples:%NC%
echo   dev.cmd                    # Start services
echo   dev.cmd debug              # Start with debugging enabled
echo   dev.cmd up --profile tools # Start with pgAdmin
echo   dev.cmd logs               # View backend logs
echo   dev.cmd logs db            # View database logs
echo   dev.cmd shell              # Open shell in backend
echo   dev.cmd rebuild backend    # Rebuild backend only
goto end

:end
endlocal
