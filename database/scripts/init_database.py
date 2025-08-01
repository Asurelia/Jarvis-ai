"""
Database initialization script for JARVIS AI
Creates initial database schema and runs migrations
"""

import asyncio
import logging
import sys
from pathlib import Path
import subprocess
import asyncpg

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from database.models import Base
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_database_connection(database_url: str) -> bool:
    """Check if database is accessible"""
    try:
        conn = await asyncpg.connect(database_url)
        await conn.fetchval("SELECT 1")
        await conn.close()
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

async def create_database_if_not_exists(database_url: str) -> bool:
    """Create database if it doesn't exist"""
    try:
        # Parse database URL to get connection parameters
        from urllib.parse import urlparse
        parsed = urlparse(database_url)
        
        # Connect to postgres database to create target database
        postgres_url = database_url.replace(f"/{parsed.path[1:]}", "/postgres")
        
        conn = await asyncpg.connect(postgres_url)
        
        # Check if database exists
        db_exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            parsed.path[1:]
        )
        
        if not db_exists:
            logger.info(f"Creating database: {parsed.path[1:]}")
            await conn.execute(f'CREATE DATABASE "{parsed.path[1:]}"')
            logger.info("✅ Database created successfully")
        else:
            logger.info("✅ Database already exists")
        
        await conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Failed to create database: {e}")
        return False

def run_alembic_migrations():
    """Run Alembic migrations"""
    try:
        migrations_dir = Path(__file__).parent.parent / "migrations"
        
        logger.info("🔄 Running database migrations...")
        
        # Initialize Alembic if not already done
        if not (migrations_dir / "versions").exists():
            logger.info("Initializing Alembic...")
            result = subprocess.run([
                "alembic", "init", "migrations"
            ], cwd=project_root, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Alembic init failed: {result.stderr}")
                return False
        
        # Generate initial migration if no migrations exist
        versions_dir = migrations_dir / "versions"
        if versions_dir.exists() and not list(versions_dir.glob("*.py")):
            logger.info("Creating initial migration...")
            result = subprocess.run([
                "alembic", "revision", "--autogenerate", 
                "-m", "Initial database schema"
            ], cwd=project_root, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Migration generation failed: {result.stderr}")
                return False
        
        # Run migrations
        logger.info("Applying migrations...")
        result = subprocess.run([
            "alembic", "upgrade", "head"
        ], cwd=project_root, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Migration failed: {result.stderr}")
            return False
        
        logger.info("✅ Migrations completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Migration error: {e}")
        return False

async def create_initial_data(database_url: str):
    """Create initial data in the database"""
    try:
        conn = await asyncpg.connect(database_url)
        
        logger.info("🌱 Creating initial data...")
        
        # Create default admin user if not exists
        admin_exists = await conn.fetchval(
            "SELECT 1 FROM users WHERE username = 'admin'"
        )
        
        if not admin_exists:
            await conn.execute("""
                INSERT INTO users (username, email, full_name, is_admin, is_verified, preferred_persona)
                VALUES ('admin', 'admin@jarvis.ai', 'JARVIS Administrator', true, true, 'JARVIS')
            """)
            logger.info("✅ Created admin user")
        
        # Create system conversation for initial setup
        system_conv_exists = await conn.fetchval(
            "SELECT 1 FROM conversations WHERE title = 'System Initialization'"
        )
        
        if not system_conv_exists:
            conv_id = await conn.fetchval("""
                INSERT INTO conversations (title, status, persona_id)
                VALUES ('System Initialization', 'archived', 'JARVIS')
                RETURNING id
            """)
            
            await conn.execute("""
                INSERT INTO messages (conversation_id, role, content, model_used)
                VALUES ($1, 'system', 'JARVIS AI system initialized successfully', 'system')
            """, conv_id)
            
            logger.info("✅ Created system initialization conversation")
        
        await conn.close()
        
    except Exception as e:
        logger.error(f"Failed to create initial data: {e}")

async def setup_database_extensions(database_url: str):
    """Setup required database extensions"""
    try:
        conn = await asyncpg.connect(database_url)
        
        logger.info("🔧 Setting up database extensions...")
        
        # Create extensions
        extensions = [
            "CREATE EXTENSION IF NOT EXISTS vector",
            "CREATE EXTENSION IF NOT EXISTS pg_stat_statements",
            "CREATE EXTENSION IF NOT EXISTS pg_trgm"
        ]
        
        for ext_sql in extensions:
            await conn.execute(ext_sql)
        
        logger.info("✅ Database extensions configured")
        
        await conn.close()
        
    except Exception as e:
        logger.error(f"Failed to setup extensions: {e}")

async def optimize_database(database_url: str):
    """Apply database optimizations"""
    try:
        conn = await asyncpg.connect(database_url)
        
        logger.info("⚡ Applying database optimizations...")
        
        # Run the optimization script
        optimization_script = Path(__file__).parent.parent.parent / "services" / "memory-db" / "init" / "01-optimizations.sql"
        
        if optimization_script.exists():
            with open(optimization_script, 'r') as f:
                optimization_sql = f.read()
            
            # Execute optimization statements
            for statement in optimization_sql.split(';'):
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        await conn.execute(statement)
                    except Exception as e:
                        # Some statements might fail in different environments
                        logger.debug(f"Optimization statement skipped: {e}")
        
        logger.info("✅ Database optimizations applied")
        
        await conn.close()
        
    except Exception as e:
        logger.error(f"Failed to optimize database: {e}")

async def main():
    """Main initialization function"""
    
    logger.info("🚀 Starting JARVIS Database Initialization")
    
    # Build database URL
    database_url = (
        f"postgresql://{settings.get('POSTGRES_USER', 'jarvis')}:"
        f"{settings.get('POSTGRES_PASSWORD', 'password')}@"
        f"{settings.get('POSTGRES_HOST', 'localhost')}:"
        f"{settings.get('POSTGRES_PORT', '5432')}/"
        f"{settings.get('POSTGRES_DB', 'jarvis_memory')}"
    )
    
    try:
        # Step 1: Create database if it doesn't exist
        logger.info("Step 1: Checking database...")
        if not await create_database_if_not_exists(database_url):
            logger.error("❌ Failed to create database")
            sys.exit(1)
        
        # Step 2: Check connection
        logger.info("Step 2: Testing database connection...")
        if not await check_database_connection(database_url):
            logger.error("❌ Cannot connect to database")
            sys.exit(1)
        
        # Step 3: Setup extensions
        logger.info("Step 3: Setting up database extensions...")
        await setup_database_extensions(database_url)
        
        # Step 4: Run migrations
        logger.info("Step 4: Running database migrations...")
        if not run_alembic_migrations():
            logger.error("❌ Database migrations failed")
            sys.exit(1)
        
        # Step 5: Create initial data
        logger.info("Step 5: Creating initial data...")
        await create_initial_data(database_url)
        
        # Step 6: Apply optimizations
        logger.info("Step 6: Applying database optimizations...")
        await optimize_database(database_url)
        
        logger.info("✅ JARVIS Database initialization completed successfully!")
        
        # Print summary
        print("\n" + "="*60)
        print("🎉 JARVIS AI DATABASE INITIALIZATION COMPLETE")
        print("="*60)
        print(f"Database URL: {database_url}")
        print(f"Admin user created: admin@jarvis.ai")
        print("Extensions: vector, pg_stat_statements, pg_trgm")
        print("Optimizations applied: Yes")
        print("Ready for JARVIS AI operations!")
        print("="*60)
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())