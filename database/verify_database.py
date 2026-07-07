#!/usr/bin/env python3
"""
Verify Database Setup
Checks all tables, indexes, and sample data
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import yaml
import sys
from tabulate import tabulate

def get_db_connection(config_path='config.yaml'):
    """Get database connection from config"""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        db_config = config['database']
        
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password']
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def get_tables(conn):
    """Get list of all tables"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        return [row['table_name'] for row in cur.fetchall()]

def get_table_stats(conn, table_name):
    """Get statistics for a table"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Get row count
        cur.execute(f"SELECT COUNT(*) as count FROM {table_name}")
        count = cur.fetchone()['count']
        
        # Get column count
        cur.execute("""
            SELECT COUNT(*) as count 
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = %s
        """, (table_name,))
        columns = cur.fetchone()['count']
        
        return {'rows': count, 'columns': columns}

def get_indexes(conn, table_name):
    """Get indexes for a table"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = 'public' AND tablename = %s
        """, (table_name,))
        return [(row['indexname'], row['indexdef'][:50] + '...') for row in cur.fetchall()]

def verify_sample_data(conn):
    """Verify sample data exists"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Check users
        cur.execute("SELECT COUNT(*) as count FROM users")
        user_count = cur.fetchone()['count']
        
        # Check projects
        cur.execute("SELECT COUNT(*) as count FROM projects")
        project_count = cur.fetchone()['count']
        
        # Check protocol data
        protocols = ['mf62_project_data', 'mf52_project_data', 'ftire_project_data', 
                    'cdtire_project_data', 'custom_project_data']
        protocol_counts = {}
        
        for proto in protocols:
            cur.execute(f"SELECT COUNT(*) as count FROM {proto}")
            protocol_counts[proto] = cur.fetchone()['count']
        
        return {
            'users': user_count,
            'projects': project_count,
            'protocols': protocol_counts
        }

def main():
    print("=" * 60)
    print("Database Verification")
    print("=" * 60)
    
    conn = get_db_connection()
    if not conn:
        sys.exit(1)
    
    try:
        # 1. List all tables
        print("\n📊 Tables in Database:")
        tables = get_tables(conn)
        
        table_data = []
        for table in tables:
            stats = get_table_stats(conn, table)
            table_data.append([
                table,
                stats['rows'],
                stats['columns']
            ])
        
        print(tabulate(table_data, headers=['Table', 'Rows', 'Columns'], tablefmt='grid'))
        
        # 2. Check indexes
        print("\n📇 Indexes per Table:")
        for table in ['users', 'projects', 'activity_logs']:
            if table in tables:
                indexes = get_indexes(conn, table)
                print(f"\n{table}:")
                for idx_name, idx_def in indexes:
                    print(f"  - {idx_name}")
        
        # 3. Verify sample data
        print("\n📈 Sample Data Summary:")
        sample = verify_sample_data(conn)
        print(f"  Users: {sample['users']}")
        print(f"  Projects: {sample['projects']}")
        print("  Protocol Data:")
        for proto, count in sample['protocols'].items():
            print(f"    - {proto}: {count}")
        
        # 4. Check views
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT viewname 
                FROM pg_views 
                WHERE schemaname = 'public'
                ORDER BY viewname
            """)
            views = [row['viewname'] for row in cur.fetchall()]
            
            if views:
                print(f"\n👁 Views:")
                for view in views:
                    cur.execute(f"SELECT COUNT(*) as count FROM {view}")
                    count = cur.fetchone()['count']
                    print(f"  - {view}: {count} rows")
        
        print("\n" + "=" * 60)
        print("✅ Database verification complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    main()