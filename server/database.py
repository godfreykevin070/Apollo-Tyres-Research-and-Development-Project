import asyncpg
from typing import Optional
import logging
from config import config

logger = logging.getLogger(__name__)

class Database:
    _instance: Optional['Database'] = None
    _pool: Optional[asyncpg.Pool] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self):
        """Create connection pool to PostgreSQL"""
        if self._pool is None:
            try:
                self._pool = await asyncpg.create_pool(
                    config.DATABASE_URL,
                    min_size=1,
                    max_size=10,
                    command_timeout=60
                )
                await self.init_tables()
                logger.info("Database connected successfully")
            except Exception as e:
                logger.error(f"Database connection failed: {e}")
                raise
        return self._pool

    async def close(self):
        """Close connection pool"""
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def execute(self, query: str, *args):
        """Execute a query and return result"""
        pool = await self.connect()
        async with pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def execute_one(self, query: str, *args):
        """Execute a query and return one row"""
        pool = await self.connect()
        async with pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def execute_val(self, query: str, *args):
        """Execute a query and return a single value"""
        result = await self.execute_one(query, *args)
        return result[0] if result else None

    async def init_tables(self):
        """Initialize database tables"""
        queries = [
            # Users table
            """
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(20) PRIMARY KEY,
                email VARCHAR(255) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL DEFAULT 'engineer',
                name VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
            """,
            
            # Projects table
            """
            CREATE TABLE IF NOT EXISTS projects (
                id SERIAL PRIMARY KEY,
                project_name VARCHAR(255) NOT NULL,
                region VARCHAR(100) NOT NULL,
                department VARCHAR(100) NOT NULL,
                tyre_size VARCHAR(100) NOT NULL,
                protocol VARCHAR(50) NOT NULL,
                status VARCHAR(50) DEFAULT 'Not Started',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                user_email VARCHAR(255) REFERENCES users(email),
                inputs JSONB DEFAULT '{}'::jsonb,
                previous_status VARCHAR(50)
            )
            """,
            
            # Activity logs table
            """
            CREATE TABLE IF NOT EXISTS activity_logs (
                id SERIAL PRIMARY KEY,
                user_email VARCHAR(255) NOT NULL,
                user_name VARCHAR(255),
                activity_type VARCHAR(100),
                action VARCHAR(255) NOT NULL,
                description TEXT,
                status VARCHAR(50) DEFAULT 'success',
                ip_address VARCHAR(100),
                browser VARCHAR(100),
                device_type VARCHAR(50),
                related_entity_id INT,
                related_entity_type VARCHAR(100),
                project_name VARCHAR(255),
                metadata JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Protocol data tables
            """
            CREATE TABLE IF NOT EXISTS mf62_project_data (
                id BIGSERIAL PRIMARY KEY,
                project_id INT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                number_of_runs INT,
                tests VARCHAR(255),
                ips VARCHAR(255),
                loads VARCHAR(255),
                inclination_angle VARCHAR(255),
                slip_angle VARCHAR(255),
                slip_ratio VARCHAR(255),
                test_velocity VARCHAR(255),
                job VARCHAR(255),
                old_job VARCHAR(255),
                template_tydex VARCHAR(255),
                tydex_name VARCHAR(255),
                p VARCHAR(255),
                l VARCHAR(255),
                foltran VARCHAR(255),
                python_script VARCHAR(255),
                run_start_time TIMESTAMP,
                run_end_time TIMESTAMP,
                run_duration_seconds INT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
            """,
            
            # MF52 project data
            """
            CREATE TABLE IF NOT EXISTS mf52_project_data (
                id BIGSERIAL PRIMARY KEY,
                project_id INT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                number_of_runs INT,
                tests VARCHAR(255),
                inflation_pressure VARCHAR(255),
                loads VARCHAR(255),
                inclination_angle VARCHAR(255),
                slip_angle VARCHAR(255),
                slip_ratio VARCHAR(255),
                test_velocity VARCHAR(255),
                job VARCHAR(255),
                old_job VARCHAR(255),
                template_tydex VARCHAR(255),
                tydex_name VARCHAR(255),
                p VARCHAR(255),
                l VARCHAR(255),
                foltran VARCHAR(255),
                python_script VARCHAR(255),
                run_start_time TIMESTAMP,
                run_end_time TIMESTAMP,
                run_duration_seconds INT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
            """,
            
            # FTire project data
            """
            CREATE TABLE IF NOT EXISTS ftire_project_data (
                id BIGSERIAL PRIMARY KEY,
                project_id INT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                number_of_runs INT,
                tests VARCHAR(255),
                loads VARCHAR(255),
                inflation_pressure VARCHAR(255),
                test_velocity VARCHAR(255),
                longitudinal_slip VARCHAR(255),
                slip_angle VARCHAR(255),
                inclination_angle VARCHAR(255),
                cleat_orientation VARCHAR(255),
                job VARCHAR(255),
                old_job VARCHAR(255),
                template_tydex VARCHAR(255),
                tydex_name VARCHAR(255),
                p VARCHAR(255),
                l VARCHAR(255),
                foltran VARCHAR(255),
                python_script VARCHAR(255),
                run_start_time TIMESTAMP,
                run_end_time TIMESTAMP,
                run_duration_seconds INT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
            """,
            
            # CDTire project data
            """
            CREATE TABLE IF NOT EXISTS cdtire_project_data (
                id BIGSERIAL PRIMARY KEY,
                project_id INT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                number_of_runs INT,
                test_name VARCHAR(255),
                inflation_pressure VARCHAR(255),
                velocity VARCHAR(255),
                preload VARCHAR(255),
                camber VARCHAR(255),
                slip_angle VARCHAR(255),
                displacement VARCHAR(255),
                slip_range VARCHAR(255),
                cleat VARCHAR(255),
                road_surface VARCHAR(255),
                job VARCHAR(255),
                old_job VARCHAR(255),
                template_tydex VARCHAR(255),
                tydex_name VARCHAR(255),
                p VARCHAR(255),
                l VARCHAR(255),
                foltran VARCHAR(255),
                python_script VARCHAR(255),
                run_start_time TIMESTAMP,
                run_end_time TIMESTAMP,
                run_duration_seconds INT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
            """,
            
            # Custom project data
            """
            CREATE TABLE IF NOT EXISTS custom_project_data (
                id BIGSERIAL PRIMARY KEY,
                project_id INT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                number_of_runs INT,
                tests VARCHAR(255),
                inflation_pressure VARCHAR(255),
                loads VARCHAR(255),
                inclination_angle VARCHAR(255),
                slip_angle VARCHAR(255),
                slip_ratio VARCHAR(255),
                test_velocity VARCHAR(255),
                cleat_orientation VARCHAR(255),
                displacement VARCHAR(255),
                job VARCHAR(255),
                old_job VARCHAR(255),
                template_tydex VARCHAR(255),
                tydex_name VARCHAR(255),
                p VARCHAR(255),
                l VARCHAR(255),
                foltran VARCHAR(255),
                python_script VARCHAR(255),
                run_start_time TIMESTAMP,
                run_end_time TIMESTAMP,
                run_duration_seconds INT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
            """,
            
            # Tydex files
            """
            CREATE TABLE IF NOT EXISTS tydex_files (
                id SERIAL PRIMARY KEY,
                project_id INT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                protocol VARCHAR(50) NOT NULL,
                filename VARCHAR(255) NOT NULL,
                content TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(project_id, filename)
            )
            """,
            
            # Protocol drafts
            """
            CREATE TABLE IF NOT EXISTS protocol_drafts (
                id SERIAL PRIMARY KEY,
                project_id INT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                protocol VARCHAR(50) NOT NULL,
                inputs_json JSONB DEFAULT '{}'::jsonb,
                matrix_json JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(project_id, protocol)
            )
            """,
        ]
        
        pool = await self.connect()
        async with pool.acquire() as conn:
            for query in queries:
                try:
                    await conn.execute(query)
                except Exception as e:
                    logger.warning(f"Table creation warning: {e}")
        
        # Create indexes
        index_queries = [
            "CREATE INDEX IF NOT EXISTS idx_projects_user_email ON projects(user_email)",
            "CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)",
            "CREATE INDEX IF NOT EXISTS idx_activity_user_email ON activity_logs(user_email)",
            "CREATE INDEX IF NOT EXISTS idx_activity_created_at ON activity_logs(created_at)",
        ]
        
        async with pool.acquire() as conn:
            for query in index_queries:
                try:
                    await conn.execute(query)
                except Exception as e:
                    logger.warning(f"Index creation warning: {e}")

db = Database()