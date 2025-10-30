# Debugging Backend with VSCode

This guide explains how to debug the FastAPI backend using VSCode and Docker.

## Prerequisites

- Docker and Docker Compose installed
- VSCode with Python extension installed

## Quick Start

### Step 1: Start Backend in Debug Mode

**Linux/Mac:**
```bash
cd backend
./dev.sh debug
```

**Windows:**
```cmd
cd backend
dev.cmd debug
```

The server will start and wait for the VSCode debugger to attach on port 5678.

### Step 2: Attach VSCode Debugger

1. Open the project in VSCode
2. Set breakpoints in your Python code (e.g., in `backend/app/routers/*.py`)
3. Go to Run and Debug panel (Ctrl+Shift+D / Cmd+Shift+D)
4. Select **"Python: Remote Attach (Docker)"** from the dropdown
5. Press F5 or click the green play button

The debugger will connect and execution will start. Your breakpoints will be hit when the code runs.

### Step 3: Make API Requests

- Visit http://localhost:8000/api/v1/docs
- Or use curl/Postman to make requests
- Your breakpoints will trigger when the code executes

## How It Works

When you run `./dev.sh debug` or `dev.cmd debug`, the script:

1. Uses `docker-compose.debug.yml` to override the default backend command
2. Starts the backend with `debugpy --wait-for-client`
3. Exposes port 5678 for the debugger to connect
4. Waits for VSCode to attach before starting the server

This approach is **safe** because:
- No manual editing of docker-compose.yml required
- No risk of accidentally committing debug mode
- Railway/production deployments ignore the debug file
- You can easily switch between normal and debug mode

## Files Involved

### docker-compose.debug.yml
Override file that enables debugging. Only used when explicitly specified:
```yaml
services:
  backend:
    ports:
      - "5678:5678"  # Debug port
    command: python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m uvicorn ...
```

### .vscode/launch.json
VSCode configuration for remote debugging:
```json
{
  "name": "Python: Remote Attach (Docker)",
  "type": "debugpy",
  "request": "attach",
  "connect": {
    "host": "localhost",
    "port": 5678
  },
  "pathMappings": [...]
}
```

### requirements-dev.txt
Development dependencies including debugpy:
```
debugpy==1.8.0
```

## Debugging Workflow

### Normal Development (without debugging)
```bash
./dev.sh up       # Start normally with hot reload
# Make changes, server auto-reloads
```

### Debug Mode
```bash
./dev.sh debug    # Start in debug mode
# Attach VSCode debugger (F5)
# Set breakpoints and debug
```

### Switching Between Modes
```bash
./dev.sh down     # Stop services
./dev.sh debug    # Start in debug mode
# Or
./dev.sh down
./dev.sh up       # Start in normal mode
```

## Advanced Configuration

### Without --wait-for-client

If you don't want the server to wait for the debugger, edit `docker-compose.debug.yml`:

```yaml
# Remove --wait-for-client from the command
command: python -m debugpy --listen 0.0.0.0:5678 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Then restart:
```bash
./dev.sh down
./dev.sh debug
```

The server will start immediately, and you can attach the debugger at any time.

### Debugging Startup Code

The default `--wait-for-client` flag is perfect for debugging code that runs during server startup (e.g., `app/main.py`, middleware initialization). The server won't start until you attach the debugger.

## Debugging Tips

### Setting Breakpoints
- Click in the left margin of the code editor (red dot appears)
- Or use F9 to toggle breakpoint on current line
- Conditional breakpoints: Right-click breakpoint → Edit Breakpoint

### Debug Actions
- **F5** - Continue execution
- **F10** - Step over (execute current line)
- **F11** - Step into (enter function call)
- **Shift+F11** - Step out (exit current function)
- **F9** - Toggle breakpoint
- **Shift+F5** - Disconnect debugger

### Debug Console
- View print statements and logging output
- Evaluate expressions while paused at breakpoint
- Interactive Python REPL when debugging

### Variables Panel
- Inspect local and global variables
- Watch expressions
- Call stack navigation

### Hot Reload with Debugging
The `--reload` flag still works in debug mode. When you save changes:
1. Server detects file change
2. Server restarts
3. Debugger automatically reconnects
4. Breakpoints remain active

## Troubleshooting

### Debugger Won't Connect

**Check if backend is running:**
```bash
docker ps
```
You should see `polito-log-backend` container.

**Check if debug port is exposed:**
```bash
docker port polito-log-backend
```
You should see `5678/tcp -> 0.0.0.0:5678`

**Check container logs:**
```bash
./dev.sh logs
# or
dev.cmd logs
```

Look for a line like: `Debugger is waiting for client to attach on port 5678...`

### Breakpoints Not Hitting

1. **Verify path mappings** in `.vscode/launch.json`:
   - Local: `${workspaceFolder}/backend/app`
   - Remote: `/app/app`

2. **Ensure code is being executed:**
   - Make an API request to trigger your code
   - Check if the route/function is actually called

3. **Try a different file:**
   - Set a breakpoint in `app/main.py` in a startup event
   - Restart the backend to trigger it

### Server Won't Start

1. **Check for syntax errors** in your Python code
2. **View container logs:**
   ```bash
   ./dev.sh logs
   ```
3. **Rebuild containers:**
   ```bash
   ./dev.sh rebuild
   ```

### Port 5678 Already in Use

Another debugger or application is using port 5678:

1. Find what's using the port:
   ```bash
   # Linux/Mac
   lsof -i :5678

   # Windows
   netstat -ano | findstr :5678
   ```

2. Stop the conflicting process or change the debug port in:
   - `docker-compose.debug.yml`
   - `.vscode/launch.json`

## Production Note

Debugging is **only available in development**:

- `docker-compose.debug.yml` is only used locally when you explicitly run `./dev.sh debug`
- Railway uses the Dockerfile directly (no compose files)
- Production builds don't install `requirements-dev.txt` (set by `ENVIRONMENT` build arg)
- No debug ports are exposed in production
- Zero performance overhead in production

This ensures your production deployment is lean, secure, and performant.
