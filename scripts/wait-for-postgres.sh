#!/bin/bash
# wait-for-postgres.sh
# Wait for PostgreSQL to be ready

set -e

host="$1"
shift
cmd="$@"

echo "Waiting for PostgreSQL at $host..."

until pg_isready -h "$host" -p 5432 -U "${POSTGRES_USER:-postgres}"; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
done

echo "PostgreSQL is up - executing command"

# Initialize database tables
echo "Initializing database..."
python -c "
import sys
import time
from soccer_analytics.config.database import init_db, check_db_connection

# Wait for database to be fully ready
for i in range(30):
    if check_db_connection():
        print('Database connection successful')
        break
    print(f'Waiting for database... attempt {i+1}/30')
    time.sleep(2)
else:
    print('Failed to connect to database after 30 attempts')
    sys.exit(1)

# Initialize database schema
try:
    init_db()
    print('Database initialized successfully')
except Exception as e:
    print(f'Database initialization failed: {e}')
    sys.exit(1)
"

echo "Starting application..."
exec $cmd 