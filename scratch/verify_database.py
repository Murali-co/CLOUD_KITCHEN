import sys
import os
from dotenv import dotenv_values
import pymysql
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.insert(0, "/home/murali/Desktop/SEM 5 /DBMS/PROJECT/backend")
os.chdir("/home/murali/Desktop/SEM 5 /DBMS/PROJECT/backend")
from app.models import Base
from app.core.config import settings

print("=== 1. DATABASE CONNECTIVITY & TABLE CHECK ===")
env_vals = dotenv_values("/home/murali/Desktop/SEM 5 /DBMS/PROJECT/backend/.env")
conn = pymysql.connect(
    host=env_vals["DB_HOST"],
    port=int(env_vals["DB_PORT"]),
    user=env_vals["DB_USER"],
    password=env_vals["DB_PASSWORD"],
    database=env_vals["DB_NAME"]
)
cur = conn.cursor()
cur.execute("SELECT DATABASE();")
current_db = cur.fetchone()[0]
print(f"Connected to database: {current_db}")

cur.execute("SHOW TABLES;")
tables = [row[0] for row in cur.fetchall()]
print(f"Total tables found: {len(tables)}")
for i, t in enumerate(sorted(tables), 1):
    print(f" {i:2d}. {t}")

expected_21 = [
    "users", "customer", "kitchen", "staff", "delivery_person",
    "category", "menu_item", "address", "coupon", "orders",
    "order_item", "payment", "order_status_history", "ingredient",
    "inventory", "inventory_movement", "menu_item_ingredient",
    "delivery", "coupon_usage", "review", "admin_audit_log"
]

missing = set(expected_21) - set(tables)
extra = set(tables) - set(expected_21)
print(f"\nMissing tables: {missing if missing else 'None'}")
print(f"Extra tables: {extra if extra else 'None'}")

print("\n=== 2. PRIMARY KEYS, ENGINE & CHARSET CHECK ===")
cur.execute("""
    SELECT TABLE_NAME, ENGINE, TABLE_COLLATION 
    FROM information_schema.TABLES 
    WHERE TABLE_SCHEMA = %s
""", (current_db,))
table_meta = {row[0]: (row[1], row[2]) for row in cur.fetchall()}

for t in sorted(tables):
    eng, coll = table_meta.get(t, ("UNKNOWN", "UNKNOWN"))
    cur.execute(f"""
        SELECT COLUMN_NAME 
        FROM information_schema.KEY_COLUMN_USAGE 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND CONSTRAINT_NAME = 'PRIMARY'
        ORDER BY ORDINAL_POSITION
    """, (current_db, t))
    pks = [r[0] for r in cur.fetchall()]
    print(f"Table '{t}': Engine={eng}, Collation={coll}, PK={pks}")

print("\n=== 3. FOREIGN KEYS CHECK ===")
cur.execute("""
    SELECT 
        TABLE_NAME, CONSTRAINT_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
    FROM information_schema.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = %s AND REFERENCED_TABLE_NAME IS NOT NULL
    ORDER BY TABLE_NAME, CONSTRAINT_NAME, ORDINAL_POSITION
""", (current_db,))
fks = cur.fetchall()
print(f"Total foreign key column mappings found: {len(fks)}")
for row in fks:
    print(f" {row[0]}.{row[2]} -> {row[3]}.{row[4]} (Constraint: {row[1]})")

print("\n=== 4. SECONDARY INDEXES CHECK ===")
cur.execute("""
    SELECT TABLE_NAME, INDEX_NAME, NON_UNIQUE, GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) AS COLS
    FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = %s
    GROUP BY TABLE_NAME, INDEX_NAME, NON_UNIQUE
    ORDER BY TABLE_NAME, INDEX_NAME
""", (current_db,))
indexes = cur.fetchall()
print(f"Total indexes found: {len(indexes)}")
for row in indexes:
    uniq = "UNIQUE" if row[2] == 0 else "INDEX"
    print(f" {row[0]}: [{uniq}] {row[1]} ({row[3]})")

print("\n=== 5. SQLALCHEMY METADATA VS MYSQL COMPARISON ===")
engine = create_engine(settings.DATABASE_URL)
insp = inspect(engine)
db_tables = insp.get_table_names()
meta_tables = list(Base.metadata.tables.keys())

all_matched = True
for t in meta_tables:
    if t not in db_tables:
        print(f"ERROR: Model table '{t}' not in DB!")
        all_matched = False
        continue
    db_cols = {c["name"]: str(c["type"]) for c in insp.get_columns(t)}
    model_cols = {c.name: str(c.type) for c in Base.metadata.tables[t].columns}
    col_missing = set(model_cols.keys()) - set(db_cols.keys())
    col_extra = set(db_cols.keys()) - set(model_cols.keys())
    if col_missing or col_extra:
        print(f"Mismatch in '{t}': missing in DB {col_missing}, extra in DB {col_extra}")
        all_matched = False

if all_matched:
    print("SUCCESS: 100% column parity between SQLAlchemy models and MySQL database tables!")

print("\n=== 6. SESSION & SIMPLE SELECT TEST ===")
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()
try:
    for t in ["users", "kitchen", "menu_item", "orders"]:
        result = session.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
        print(f"SELECT COUNT(*) FROM {t}: {result} rows")
    print("SUCCESS: Session creation and SELECT queries executed cleanly!")
finally:
    session.close()
    conn.close()
