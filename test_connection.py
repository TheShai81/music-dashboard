#!/usr/bin/env python3
"""Test database connection"""
from generate_load_data.db_config import get_connection

conn = get_connection()
print('✓ Database connection successful!')

cur = conn.cursor()
cur.execute('SHOW TABLES')
tables = [t[0] for t in cur.fetchall()]
print(f'✓ Found {len(tables)} tables')
for t in sorted(tables):
    print(f'  - {t}')

cur.close()
conn.close()

