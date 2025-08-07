#!/usr/bin/env python3
"""
JARVIS AI - Database Administration Service
Web-based database administration and management interface
"""

import asyncio
import logging
import os
import json
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

import asyncpg
import redis.asyncio as aioredis
import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Query, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pydantic import BaseModel, Field
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import secrets

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Prometheus metrics
ADMIN_REQUESTS = Counter('jarvis_admin_requests_total', 'Total admin requests', ['endpoint', 'status'])
ADMIN_QUERIES = Counter('jarvis_admin_queries_total', 'Total admin queries', ['type'])

# Configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "memory-db")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "jarvis_memory")
POSTGRES_USER = os.getenv("POSTGRES_USER", "jarvis")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "jarvis_secure_2024")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme")
BACKUP_PATH = os.getenv("BACKUP_PATH", "/app/backups")
ARCHIVE_PATH = os.getenv("ARCHIVE_PATH", "/app/archives")

# Security
security = HTTPBasic()

# Pydantic models
class QueryRequest(BaseModel):
    query: str = Field(..., description="SQL query to execute")
    limit: Optional[int] = Field(default=100, description="Result limit")
    explain: bool = Field(default=False, description="Show query execution plan")

class QueryResult(BaseModel):
    query: str
    columns: List[str]
    rows: List[List[Any]]
    row_count: int
    execution_time_ms: float
    explain_plan: Optional[List[Dict[str, Any]]] = None

class TableInfo(BaseModel):
    table_name: str
    row_count: int
    size_bytes: int
    size_human: str
    columns: List[Dict[str, str]]
    indexes: List[Dict[str, str]]

class DatabaseStats(BaseModel):
    database_name: str
    size_bytes: int
    size_human: str
    table_count: int
    connection_count: int
    version: str
    uptime: str

class BackupInfo(BaseModel):
    filename: str
    size_bytes: int
    size_human: str
    created_at: datetime
    type: str

# FastAPI app
app = FastAPI(
    title="JARVIS Database Admin",
    description="Web-based database administration and management interface",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
start_time = datetime.utcnow()
postgres_pool: Optional[asyncpg.Pool] = None
redis_client: Optional[aioredis.Redis] = None

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify admin credentials"""
    is_correct_username = secrets.compare_digest(credentials.username, "admin")
    is_correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@app.on_event("startup")
async def startup_event():
    """Initialize database connections"""
    global postgres_pool, redis_client
    
    try:
        # Initialize PostgreSQL connection pool
        postgres_pool = await asyncpg.create_pool(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            min_size=1,
            max_size=5
        )
        
        # Initialize Redis connection
        redis_client = aioredis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD if REDIS_PASSWORD else None,
            decode_responses=True
        )
        
        logger.info("Database admin service started")
        
    except Exception as e:
        logger.error("Failed to initialize database admin", error=str(e))
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup connections"""
    global postgres_pool, redis_client
    
    if postgres_pool:
        await postgres_pool.close()
    if redis_client:
        await redis_client.close()
    
    logger.info("Database admin service shutting down")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Quick database check
        async with postgres_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "uptime_seconds": (datetime.utcnow() - start_time).total_seconds()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }

@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/", response_class=HTMLResponse)
async def admin_dashboard(username: str = Depends(verify_credentials)):
    """Admin dashboard HTML"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>JARVIS Database Admin</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
            .card { background: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .btn { background: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
            .btn:hover { background: #2980b9; }
            .btn-danger { background: #e74c3c; }
            .btn-danger:hover { background: #c0392b; }
            table { width: 100%; border-collapse: collapse; }
            th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background-color: #f2f2f2; }
            textarea { width: 100%; height: 150px; font-family: monospace; }
            .status-healthy { color: #27ae60; }
            .status-warning { color: #f39c12; }
            .status-error { color: #e74c3c; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🤖 JARVIS Database Administration</h1>
            <p>Logged in as: <strong>{username}</strong> | Server Time: <span id="serverTime"></span></p>
        </div>
        
        <div class="card">
            <h2>Quick Actions</h2>
            <button class="btn" onclick="loadDatabaseStats()">Database Stats</button>
            <button class="btn" onclick="loadTables()">View Tables</button>
            <button class="btn" onclick="loadBackups()">Manage Backups</button>
            <button class="btn" onclick="showQueryInterface()">SQL Query</button>
            <button class="btn btn-danger" onclick="showMaintenance()">Maintenance</button>
        </div>
        
        <div id="content" class="card">
            <h2>Welcome to JARVIS Database Admin</h2>
            <p>Select an action above to get started.</p>
            <div id="status">Loading system status...</div>
        </div>
        
        <script>
            function updateTime() {
                document.getElementById('serverTime').textContent = new Date().toLocaleString();
            }
            setInterval(updateTime, 1000);
            updateTime();
            
            async function loadDatabaseStats() {
                const response = await fetch('/api/database/stats');
                const data = await response.json();
                document.getElementById('content').innerHTML = `
                    <h2>Database Statistics</h2>
                    <table>
                        <tr><th>Database</th><td>${data.database_name}</td></tr>
                        <tr><th>Size</th><td>${data.size_human}</td></tr>
                        <tr><th>Tables</th><td>${data.table_count}</td></tr>
                        <tr><th>Connections</th><td>${data.connection_count}</td></tr>
                        <tr><th>Version</th><td>${data.version}</td></tr>
                        <tr><th>Uptime</th><td>${data.uptime}</td></tr>
                    </table>
                `;
            }
            
            async function loadTables() {
                const response = await fetch('/api/database/tables');
                const tables = await response.json();
                let html = '<h2>Database Tables</h2><table><tr><th>Table</th><th>Rows</th><th>Size</th><th>Actions</th></tr>';
                tables.forEach(table => {
                    html += `<tr>
                        <td>${table.table_name}</td>
                        <td>${table.row_count}</td>
                        <td>${table.size_human}</td>
                        <td><button class="btn" onclick="viewTable('${table.table_name}')">View</button></td>
                    </tr>`;
                });
                html += '</table>';
                document.getElementById('content').innerHTML = html;
            }
            
            async function viewTable(tableName) {
                const response = await fetch(`/api/database/table/${tableName}`);
                const table = await response.json();
                let html = `<h2>Table: ${table.table_name}</h2>`;
                html += `<p>Rows: ${table.row_count} | Size: ${table.size_human}</p>`;
                html += '<h3>Columns</h3><table><tr><th>Column</th><th>Type</th></tr>';
                table.columns.forEach(col => {
                    html += `<tr><td>${col.column_name}</td><td>${col.data_type}</td></tr>`;
                });
                html += '</table>';
                document.getElementById('content').innerHTML = html;
            }
            
            function showQueryInterface() {
                document.getElementById('content').innerHTML = `
                    <h2>SQL Query Interface</h2>
                    <textarea id="queryText" placeholder="Enter your SQL query here..."></textarea><br>
                    <button class="btn" onclick="executeQuery()">Execute Query</button>
                    <button class="btn" onclick="explainQuery()">Explain Query</button>
                    <div id="queryResult"></div>
                `;
            }
            
            async function executeQuery() {
                const query = document.getElementById('queryText').value;
                const response = await fetch('/api/database/query', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({query: query})
                });
                const result = await response.json();
                displayQueryResult(result);
            }
            
            function displayQueryResult(result) {
                let html = `<h3>Query Result (${result.row_count} rows, ${result.execution_time_ms}ms)</h3>`;
                if (result.columns.length > 0) {
                    html += '<table><tr>';
                    result.columns.forEach(col => html += `<th>${col}</th>`);
                    html += '</tr>';
                    result.rows.forEach(row => {
                        html += '<tr>';
                        row.forEach(cell => html += `<td>${cell}</td>`);
                        html += '</tr>';
                    });
                    html += '</table>';
                }
                document.getElementById('queryResult').innerHTML = html;
            }
            
            // Load initial status
            loadDatabaseStats();
        </script>
    </body>
    </html>
    """.format(username=username)
    
    return HTMLResponse(content=html_content)

@app.get("/api/database/stats", response_model=DatabaseStats)
async def get_database_stats(username: str = Depends(verify_credentials)):
    """Get database statistics"""
    ADMIN_REQUESTS.labels(endpoint='stats', status='success').inc()
    
    async with postgres_pool.acquire() as conn:
        # Database size
        size_result = await conn.fetchrow("""
            SELECT pg_size_pretty(pg_database_size(current_database())) as size_human,
                   pg_database_size(current_database()) as size_bytes
        """)
        
        # Table count
        table_count = await conn.fetchval("""
            SELECT count(*) FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        
        # Connection count
        connection_count = await conn.fetchval("""
            SELECT count(*) FROM pg_stat_activity
        """)
        
        # Version
        version = await conn.fetchval("SELECT version()")
        
        # Uptime
        uptime_result = await conn.fetchrow("""
            SELECT current_timestamp - pg_postmaster_start_time() as uptime
        """)
        
        return DatabaseStats(
            database_name=POSTGRES_DB,
            size_bytes=size_result['size_bytes'],
            size_human=size_result['size_human'],
            table_count=table_count,
            connection_count=connection_count,
            version=version.split(',')[0],
            uptime=str(uptime_result['uptime']).split('.')[0]
        )

@app.get("/api/database/tables", response_model=List[TableInfo])
async def get_tables(username: str = Depends(verify_credentials)):
    """Get list of database tables"""
    ADMIN_REQUESTS.labels(endpoint='tables', status='success').inc()
    
    async with postgres_pool.acquire() as conn:
        tables = await conn.fetch("""
            SELECT schemaname, tablename, 
                   pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size_human,
                   pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        """)
        
        result = []
        for table in tables:
            table_name = table['tablename']
            
            # Get row count
            row_count = await conn.fetchval(f"SELECT count(*) FROM {table_name}")
            
            # Get columns
            columns = await conn.fetch("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = $1
                ORDER BY ordinal_position
            """, table_name)
            
            # Get indexes
            indexes = await conn.fetch("""
                SELECT indexname, indexdef 
                FROM pg_indexes 
                WHERE schemaname = 'public' AND tablename = $1
            """, table_name)
            
            result.append(TableInfo(
                table_name=table_name,
                row_count=row_count,
                size_bytes=table['size_bytes'],
                size_human=table['size_human'],
                columns=[dict(row) for row in columns],
                indexes=[dict(row) for row in indexes]
            ))
        
        return result

@app.get("/api/database/table/{table_name}", response_model=TableInfo)
async def get_table_info(table_name: str, username: str = Depends(verify_credentials)):
    """Get detailed information about a specific table"""
    ADMIN_REQUESTS.labels(endpoint='table_info', status='success').inc()
    
    # Validate table name to prevent SQL injection
    if not table_name.replace('_', '').isalnum():
        raise HTTPException(status_code=400, detail="Invalid table name")
    
    async with postgres_pool.acquire() as conn:
        # Check if table exists
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = $1
            )
        """, table_name)
        
        if not table_exists:
            raise HTTPException(status_code=404, detail="Table not found")
        
        # Get table size
        size_result = await conn.fetchrow(f"""
            SELECT pg_size_pretty(pg_total_relation_size('{table_name}')) as size_human,
                   pg_total_relation_size('{table_name}') as size_bytes
        """)
        
        # Get row count
        row_count = await conn.fetchval(f"SELECT count(*) FROM {table_name}")
        
        # Get columns
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = $1
            ORDER BY ordinal_position
        """, table_name)
        
        # Get indexes
        indexes = await conn.fetch("""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE schemaname = 'public' AND tablename = $1
        """, table_name)
        
        return TableInfo(
            table_name=table_name,
            row_count=row_count,
            size_bytes=size_result['size_bytes'],
            size_human=size_result['size_human'],
            columns=[dict(row) for row in columns],
            indexes=[dict(row) for row in indexes]
        )

@app.post("/api/database/query", response_model=QueryResult)
async def execute_query(request: QueryRequest, username: str = Depends(verify_credentials)):
    """Execute SQL query"""
    ADMIN_REQUESTS.labels(endpoint='query', status='attempted').inc()
    ADMIN_QUERIES.labels(type='user_query').inc()
    
    # Basic query validation
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    # Prevent dangerous operations
    dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 'UPDATE']
    query_upper = query.upper()
    
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            logger.warning("Dangerous query blocked", query=query, user=username)
            raise HTTPException(status_code=403, detail=f"Query contains dangerous keyword: {keyword}")
    
    start_time_query = datetime.utcnow()
    
    try:
        async with postgres_pool.acquire() as conn:
            # Add LIMIT if not present
            if request.limit and 'LIMIT' not in query_upper:
                query += f" LIMIT {request.limit}"
            
            # Execute query
            if request.explain:
                explain_query = f"EXPLAIN (FORMAT JSON) {query}"
                explain_result = await conn.fetchval(explain_query)
                
            result = await conn.fetch(query)
            
            execution_time = (datetime.utcnow() - start_time_query).total_seconds() * 1000
            
            # Format results
            columns = list(result[0].keys()) if result else []
            rows = [list(row.values()) for row in result]
            
            # Convert datetime objects to strings
            for i, row in enumerate(rows):
                for j, cell in enumerate(row):
                    if isinstance(cell, datetime):
                        rows[i][j] = cell.isoformat()
            
            ADMIN_REQUESTS.labels(endpoint='query', status='success').inc()
            
            return QueryResult(
                query=query,
                columns=columns,
                rows=rows,
                row_count=len(rows),
                execution_time_ms=execution_time,
                explain_plan=explain_result if request.explain else None
            )
            
    except Exception as e:
        ADMIN_REQUESTS.labels(endpoint='query', status='error').inc()
        logger.error("Query execution failed", query=query, error=str(e))
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.get("/api/backups", response_model=List[BackupInfo])
async def list_backups(username: str = Depends(verify_credentials)):
    """List available backups"""
    backups = []
    
    for backup_path in [BACKUP_PATH, ARCHIVE_PATH]:
        backup_dir = Path(backup_path)
        if backup_dir.exists():
            for backup_file in backup_dir.glob("*.sql*"):
                stat = backup_file.stat()
                backups.append(BackupInfo(
                    filename=backup_file.name,
                    size_bytes=stat.st_size,
                    size_human=f"{stat.st_size / (1024*1024):.1f} MB",
                    created_at=datetime.fromtimestamp(stat.st_ctime),
                    type="sql" if backup_file.suffix == ".sql" else "compressed"
                ))
    
    return sorted(backups, key=lambda x: x.created_at, reverse=True)

@app.get("/api/system/status")
async def get_system_status(username: str = Depends(verify_credentials)):
    """Get system status"""
    try:
        # Database status
        async with postgres_pool.acquire() as conn:
            db_version = await conn.fetchval("SELECT version()")
            db_uptime = await conn.fetchval("SELECT current_timestamp - pg_postmaster_start_time()")
        
        # Redis status
        redis_info = await redis_client.info()
        
        return {
            "database": {
                "status": "healthy",
                "version": db_version.split(',')[0],
                "uptime": str(db_uptime).split('.')[0]
            },
            "redis": {
                "status": "healthy",
                "version": redis_info.get('redis_version', 'unknown'),
                "memory_usage": f"{redis_info.get('used_memory', 0) / (1024*1024):.1f} MB"
            },
            "admin_service": {
                "status": "healthy",
                "uptime": str(datetime.utcnow() - start_time).split('.')[0],
                "version": "1.0.0"
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def main():
    """Main entry point"""
    logging.basicConfig(level=logging.INFO)
    
    uvicorn.run(
        "database.scripts.admin_service:app",
        host="0.0.0.0",
        port=8091,
        log_level="info",
        access_log=True,
        reload=False
    )

if __name__ == "__main__":
    main()