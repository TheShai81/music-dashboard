#!/usr/bin/env python3
"""Quick script to create the database and run schema.sql"""
import mysql.connector
import re

# Connect without specifying database first
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="DatabasesClass"
)

cur = conn.cursor()

# Read schema.sql
with open('schema/schema.sql', 'r') as f:
    schema = f.read()

# Remove comments and split into statements
# Handle multi-line statements properly
statements = []
current = ""
for line in schema.split('\n'):
    # Skip comment lines
    if line.strip().startswith('--'):
        continue
    # Remove inline comments
    line = re.sub(r'--.*$', '', line)
    current += line + '\n'
    # If line ends with semicolon, it's a complete statement
    if ';' in line:
        stmt = current.strip()
        if stmt:
            statements.append(stmt)
        current = ""

# Execute statements
for statement in statements:
    statement = statement.strip()
    if statement:
        try:
            cur.execute(statement)
            conn.commit()
        except mysql.connector.Error as e:
            # Ignore "already exists" errors
            if 'exists' not in str(e).lower():
                print(f"Note: {e}")

cur.close()
conn.close()
print("✓ Schema executed successfully!")

