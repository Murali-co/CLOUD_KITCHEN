#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== GourmetCloud Database Initializer ==="
echo "Target Database: cloud_kitchen_db"

mysql cloud_kitchen_db < "$DIR/database/schema.sql"
echo "[✓] Schema tables created successfully."

mysql cloud_kitchen_db < "$DIR/database/indexes.sql"
echo "[✓] Indexes created successfully."

mysql -e "GRANT ALL PRIVILEGES ON cloud_kitchen_db.* TO 'cloud_kitchen_app'@'localhost'; FLUSH PRIVILEGES;"
echo "[✓] Granted full privileges to cloud_kitchen_app on cloud_kitchen_db."

echo "=== Database initialization complete! ==="
