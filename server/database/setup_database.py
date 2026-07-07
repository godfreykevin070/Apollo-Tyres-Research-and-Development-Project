#!/usr/bin/env python3
"""
Database Setup Script for Apollo Tyres Simulation Framework
Creates all tables, indexes, and initial data
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
import sys
import argparse
from pathlib import Path

BASE_DIR = os.path.join(Path(__file__).resolve().parent.parent,'database')

def get_db_config():
    """Get database configuration from environment or prompt"""
    config = {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'port': os.environ.get('DB_PORT', '5432'),
        'user': os.environ.get('DB_USER', 'postgres'),
        'password': os.environ.get('DB_PASSWORD', 'postgres'),
        'database': os.environ.get('DB_NAME', 'apollo_tyres')
    }
    
    # Prompt for password if not set
    if not config['password']:
        import getpass
        config['password'] = getpass.getpass(f"Password for {config['user']}: ")
    
    return config

def create_database(conn_params, db_name='apollo_tyres'):
    """Create database if it doesn't exist"""
    conn = psycopg2.connect(**conn_params)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    # Check if database exists
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
    exists = cur.fetchone()
    
    if not exists:
        print(f"Creating database: {db_name}")
        cur.execute(f"CREATE DATABASE {db_name}")
    else:
        print(f"Database {db_name} already exists")
    
    cur.close()
    conn.close()
    return db_name

def execute_sql_file(conn, sql_file):
    """Execute an entire SQL file."""
    with open(sql_file, "r", encoding="utf-8") as f:
        sql = f.read()

    cur = conn.cursor()

    try:
        cur.execute(sql)
        conn.commit()
        print("  ✓ Schema executed successfully")
        return 1, 0

    except Exception as e:
        conn.rollback()
        print(f"  ✗ Error executing {sql_file}")
        print(e)
        raise

    finally:
        cur.close()

def check_connection(conn_params):
    """Test database connection"""
    try:
        conn = psycopg2.connect(**conn_params)
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Setup Apollo Tyres database')
    parser.add_argument('--host', default='localhost', help='Database host')
    parser.add_argument('--port', default='5432', help='Database port')
    parser.add_argument('--user', default='postgres', help='Database user')
    parser.add_argument('--password', help='Database password')
    parser.add_argument('--database', default='apollo_tyres', help='Database name')
    parser.add_argument('--schema', default=f'{BASE_DIR}/schema.sql', help='Schema file path')

    args = parser.parse_args()
    
    # Get config from args or environment
    db_config = {
        'host': args.host,
        'port': args.port,
        'user': args.user,
        'password': args.password or os.environ.get('DB_PASSWORD', ''),
        'database': args.database
    }
    
    # Get password if not provided
    if not db_config['password']:
        import getpass
        db_config['password'] = getpass.getpass(f"Password for {db_config['user']}: ")
    
    print("=" * 60)
    print("Apollo Tyres Database Setup")
    print("=" * 60)
    print(f"Host: {db_config['host']}")
    print(f"Port: {db_config['port']}")
    print(f"User: {db_config['user']}")
    print(f"Database: {db_config['database']}")
    print("=" * 60)
    
    # Test connection to postgres
    postgres_config = db_config.copy()
    postgres_config['database'] = 'postgres'
    
    if not check_connection(postgres_config):
        print("\n✗ Cannot connect to PostgreSQL. Please check:")
        print("  1. PostgreSQL is running")
        print("  2. Credentials are correct")
        print("  3. Host and port are accessible")
        sys.exit(1)
    
    print("✓ Connection successful")
    
    # Create database
    try:
        db_name = create_database(postgres_config, db_config['database'])
        print(f"✓ Database {db_name} ready")
    except Exception as e:
        print(f"✗ Failed to create database: {e}")
        sys.exit(1)
    
    # Connect to the new database
    db_config['database'] = db_name
    conn = psycopg2.connect(**db_config)
    
    # Execute schema
    schema_file = Path(args.schema)
    if not schema_file.exists():
        print(f"✗ Schema file not found: {schema_file}")
        sys.exit(1)
    
    print(f"\n📄 Executing schema: {schema_file}")
    success, errors = execute_sql_file(conn, schema_file)
    print(f"  ✓ {success} statements executed successfully")
    if errors > 0:
        print(f"  ⚠ {errors} statements had errors (mostly skipped duplicates)")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ Database setup completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()