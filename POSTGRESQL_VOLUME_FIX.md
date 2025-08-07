# PostgreSQL Volume Permissions Fix

## Problem Description

The PostgreSQL container was failing to start due to permission issues with the volume mount:

```
initdb: error: could not change permissions of directory "/var/lib/postgresql/data": Operation not permitted
```

## Root Cause

- **Windows Host Filesystem**: Docker bind mounts from Windows host to Linux container create permission conflicts
- **User Mapping Issues**: The `user: "999:999"` specification conflicts with PostgreSQL's internal user management
- **Init Process**: PostgreSQL needs to initialize the database with proper ownership

## Solution Implemented

### 1. Volume Configuration Changes

**Before (Problematic):**
```yaml
volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: "./data/postgres"
```

**After (Fixed):**
```yaml
volumes:
  # Named Docker volume for PostgreSQL data persistence (Windows-compatible)
  postgres_data:
    driver: local
```

### 2. Service Configuration Changes

**Before (Problematic):**
```yaml
memory-db:
  volumes:
    - ${MEMORY_DATA_PATH:-./data/memory}:/var/lib/postgresql/data
  user: "999:999"
```

**After (Fixed):**
```yaml
memory-db:
  volumes:
    # Use named Docker volume for data persistence (Windows-compatible)
    - postgres_data:/var/lib/postgresql/data
  # Remove user specification to let PostgreSQL handle its own user management
  environment:
    - PGUSER=postgres
```

### 3. Additional Improvements

- **Start Period**: Added `start_period: 40s` to health check for proper initialization time
- **Environment Variable**: Added `PGUSER=postgres` for explicit user specification
- **Volume Persistence**: Data now persists in Docker-managed volume instead of host bind mount

## Usage

### Option 1: Run Fix Script (Recommended)

**Windows:**
```cmd
scripts\fix-postgres-volumes.bat
```

**Linux/macOS:**
```bash
scripts/fix-postgres-volumes.sh
```

### Option 2: Manual Steps

1. **Stop all services:**
   ```bash
   docker-compose down -v
   ```

2. **Remove old containers and volumes:**
   ```bash
   docker container rm -f jarvis_memory_db
   docker volume rm jarvis-ai_postgres_data
   ```

3. **Start PostgreSQL service:**
   ```bash
   docker-compose up -d memory-db
   ```

4. **Check logs:**
   ```bash
   docker-compose logs memory-db
   ```

## Technical Benefits

### Windows Compatibility
- **Named Volumes**: Docker manages volume internally, avoiding Windows filesystem permission issues
- **No Host Bind Mounts**: Eliminates Windows-Linux permission mapping conflicts
- **Proper Initialization**: PostgreSQL can properly initialize database with correct ownership

### Security Improvements
- **Container User Management**: PostgreSQL handles its own user management internally
- **No Privilege Escalation**: Removed user specification that could cause permission conflicts
- **Proper Isolation**: Database data isolated in Docker-managed volume

### Performance Benefits
- **Docker Volume Performance**: Docker volumes typically perform better than bind mounts on Windows
- **Reduced I/O Latency**: Native Docker volume storage is optimized for container workloads
- **Better Caching**: Docker volume driver can optimize caching strategies

## Verification

After applying the fix, verify the solution:

1. **Check container status:**
   ```bash
   docker ps | grep jarvis_memory_db
   ```

2. **Check PostgreSQL logs:**
   ```bash
   docker-compose logs memory-db
   ```

3. **Test database connection:**
   ```bash
   docker exec -it jarvis_memory_db psql -U jarvis -d jarvis_memory -c "SELECT version();"
   ```

4. **Verify volume:**
   ```bash
   docker volume ls | grep postgres_data
   docker volume inspect jarvis-ai_postgres_data
   ```

## Troubleshooting

### If PostgreSQL Still Fails to Start

1. **Check Docker Desktop**: Ensure Docker Desktop is running and updated
2. **Check Resources**: Verify Docker has sufficient memory allocated (>2GB recommended)
3. **Check Logs**: Review detailed logs with `docker-compose logs -f memory-db`
4. **Clean Start**: Run `docker system prune -f` and try again

### Data Recovery

If you had existing data in the old bind mount:

1. **Export existing data** (if accessible):
   ```bash
   docker run --rm -v /path/to/old/data:/backup postgres:16 pg_dumpall -U postgres > backup.sql
   ```

2. **Import to new volume**:
   ```bash
   docker exec -i jarvis_memory_db psql -U postgres < backup.sql
   ```

## Future Considerations

### Production Deployment
- Consider using external managed PostgreSQL (AWS RDS, Google Cloud SQL)
- Implement proper backup strategies with named volumes
- Use Docker Swarm or Kubernetes for production orchestration

### Development Workflow
- Named volumes persist data between container restarts
- Use `docker-compose down -v` to completely reset data during development
- Consider separate development/production compose files

## Files Modified

- `docker-compose.yml` - Updated PostgreSQL service and volume configuration
- `scripts/fix-postgres-volumes.bat` - Windows fix script
- `scripts/fix-postgres-volumes.sh` - Linux/macOS fix script
- `POSTGRESQL_VOLUME_FIX.md` - This documentation

## Success Criteria

✅ PostgreSQL container starts successfully  
✅ Database initializes without permission errors  
✅ Data persists between container restarts  
✅ Health checks pass consistently  
✅ Other services can connect to database  
✅ Compatible with Windows Docker Desktop  