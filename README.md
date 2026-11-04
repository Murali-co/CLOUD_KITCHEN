# GourmetCloud: Cloud Kitchen Management & Online Food Ordering Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-4479A1?style=flat&logo=mysql&logoColor=white)](https://www.mysql.com)
[![Redis](https://img.shields.io/badge/Redis-7.0+-DC382D?style=flat&logo=redis&logoColor=white)](https://redis.io)
[![TailwindCSS](https://img.shields.io/badge/Tailwind-3.4-38B2AC?style=flat&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Tests](https://img.shields.io/badge/Tests-98%20Passed-brightgreen?style=flat)](docs/TEST_REPORT.md)

A production-grade, distributed Cloud Kitchen Management and Online Food Ordering System architected for dark kitchens, multi-branch food preparation fulfillment, real-time inventory recipe tracking, automated delivery logistics, and customer ordering.

---

## 1. System Technology Stack & Architectural Justifications (Requirement L)

The GourmetCloud platform utilizes a polyglot persistence architecture combining a relational source of truth with an in-memory acceleration tier. Below is the technical justification for each selected technology:

| Technology | Specification | Technical Justification & Engineering Role |
| :--- | :--- | :--- |
| **MySQL 8.0 (InnoDB)** | Relational Source of Truth | Authoritative **Source of Truth (SoT)** providing ACID transaction guarantees (`REPEATABLE READ`), write-ahead logging (WAL), B-tree indexes, referential integrity (`FOREIGN KEY` cascading/restricting), domain `CHECK` constraints, recursive CTEs (`WITH RECURSIVE`), and audit triggers. Handles financial settlement, customer records, recipe bill of materials, and historical reporting. |
| **Redis 7.0** | In-Memory NoSQL Acceleration | High-throughput sub-millisecond key-value and data structure store. Dedicated to high-frequency ephemeral state: shopping carts (`Hash` with 7-day rolling TTL), token invalidation/sessions (`Hash`), catalog response caching (`String` JSON with 1-hour TTL), live order courier telemetry, and real-time best-selling dish recommendations (`Sorted Set`). Prevents MySQL disk lock contention during high concurrency. |
| **FastAPI** | Python 3.12+ ASGI Framework | High-performance asynchronous Python backend built on Starlette and Uvicorn. Delivers native `async`/`await` non-blocking I/O, automatic OpenAPI 3.1 / Swagger documentation generation, and native integration with Python type annotations. |
| **SQLAlchemy 2.0** | Declarative ORM & Query Engine | Type-safe declarative mapping with `Mapped[]` and `mapped_column()`, connection pooling with pre-ping validation, session unit-of-work transaction management, and robust protection against SQL injection via parameterized queries. |
| **Pydantic v2** | Rust-Powered Data Validation | Strict schema validation, sanitization, and serialization/deserialization via `pydantic-core` compiled in Rust. Enforces request/response body schemas and eliminates invalid data at API boundaries. |
| **JWT & Bcrypt** | Security & Authentication | Stateless HMAC-SHA256 JSON Web Tokens (Bearer) for scalable cross-service authorization. Passwords hashed using Bcrypt with 12 salt rounds, resisting brute-force and dictionary attacks. Strict role-based access control (RBAC) across 4 roles: `CUSTOMER`, `ADMIN`, `KITCHEN_STAFF`, and `DELIVERY_PERSON`. |
| **React 18 & Vite 5** | Frontend Single Page Application | Declarative component UI utilizing React 18 concurrent rendering features. Bundled with Vite 5 leveraging native browser ES modules (ESM) for instantaneous Hot Module Replacement (HMR < 50ms) and highly optimized Rollup production builds. |
| **Tailwind CSS 3.4** | Utility-First CSS Framework | Zero runtime overhead CSS with a Just-In-Time (JIT) compiler. Supplies a consistent design system (colors, typography, responsive breakpoints) across all 33 role-specific application pages. |

---

## 2. Polyglot Architecture & End-to-End Data Flow

```text
                                  +-----------------------------+
                                  |     React 18 + Vite SPA     |
                                  |   (Tailwind CSS + Axios)    |
                                  +--------------+--------------+
                                                 |
                                         HTTPS / JSON / JWT
                                                 |
                                                 v
                                  +-----------------------------+
                                  |   FastAPI REST API Server   |
                                  |  (Pydantic v2 + Auth Guard) |
                                  +-------+--------------+------+
                                          |              |
                    (Cache-Aside / Ephemeral)          (ACID Writes / Relational)
                                          |              |
                                          v              v
                           +--------------------+  +----------------------+
                           |   Redis 7 NoSQL    |  |  MySQL 8.0 (InnoDB)  |
                           |  - Carts (Hash)    |  |  - 22 Relational Tbls|
                           |  - Sessions (Hash) |  |  - Foreign Key Rules |
                           |  - Menu (String)   |  |  - Check Constraints |
                           |  - ZSET Leaderboard|  |  - Triggers & Views  |
                           |  - Pub/Sub Channel |  |  - Stored Procedures |
                           +--------------------+  +----------------------+
```

### Why MySQL is the Primary Source of Truth and Redis is Ephemeral
1. **Financial and Transactional Invariants:** An order checkout involves inserting into `orders`, creating $N$ rows in `order_item`, recording a `payment`, deducting stock from `inventory`, creating an `inventory_movement` journal entry, and recording `coupon_usage`. If payment fails or stock is exhausted, MySQL rolls back atomically. Redis transactions (`MULTI`/`EXEC`) lack relational isolation and conditional rollback semantics.
2. **Referential Integrity:** MySQL enforces foreign keys and cascade rules at the storage engine level. In Redis, relational graphs must be maintained manually in software, which risks orphaned records.
3. **Durability Guarantee:** MySQL writes to disk with Write-Ahead Logging (WAL) and `innodb_flush_log_at_trx_commit = 1`. In contrast, Redis primarily operates in RAM; using Redis for permanent orders would risk data loss during unexpected server power events.
4. **Complex Joins & Analytics:** Complex multi-table aggregations (e.g. 7-table logistics audit, recipe bill-of-materials traversal, revenue breakdowns) are solved in MySQL via B-tree index scans, which would be inefficient if performed manually in application RAM.

---

## 3. Directory Structure

```
PROJECT/
├── README.md                      # Primary project overview and technical documentation
├── .env.example                   # Baseline environment configuration template
├── docs/                          # Comprehensive technical documentation
│   ├── DBMS_RUBRIC_COMPLIANCE.md     # Academic DBMS evaluation rubric compliance matrix & Viva Q&A
│   ├── ER_DIAGRAM.md                 # Updated 22-entity visual Mermaid ER diagram & cardinality
│   ├── RELATIONAL_SCHEMA.md          # Formal relational schema in academic notation (22 tables)
│   ├── DATA_DICTIONARY.md            # Comprehensive data dictionary for all 22 tables
│   ├── REDIS_DESIGN.md               # Redis NoSQL data structures, TTL, commands & CRUD harness
│   ├── FINAL_ARCHITECTURE_REPORT.md  # System layers, data flow, RBAC, Redis topology
│   ├── MYSQL_ROLE_PRIVILEGE_MANAGEMENT.md # MySQL 8.0 RBAC, Privilege Matrix, GRANT/REVOKE, PoLP
│   ├── DBMS_RUBRIC_COMPLIANCE.md     # Full rubric audit, Next.js proposal, Viva Q&A
│   ├── API_REFERENCE.md              # Complete REST endpoint inventory (14 modules)
│   ├── TEST_REPORT.md                # 98-test suite report, Workflows A–E, concurrency
│   ├── SECURITY_AUDIT.md             # OWASP Top 10, IDOR, SQLi, and authentication review
│   ├── PERFORMANCE_REPORT.md         # N+1 query fixes, Cache-Aside benchmarks, latency
│   ├── DEPLOYMENT_GUIDE.md           # Production runbook, systemd, Nginx, backups
│   └── DATABASE_GUIDE.md             # 22-table schema dictionary & validation queries
├── database/                      # Relational schema DDL, indexes, and academic SQL scripts
│   ├── schema.sql                    # Authoritative DDL (22 tables, constraints, trigger)
│   ├── indexes.sql                   # Performance B-Tree secondary indexes
│   ├── sample_data.sql               # Seed fixtures and baseline records
│   ├── dml_operations.sql            # Requirement M: INSERT, SELECT, UPDATE, DELETE & Transactions
│   ├── advanced_queries.sql          # Requirement N: JOINs, Nested, Correlated & Recursive CTEs
│   ├── advanced_sql_objects.sql      # Requirement O: Stored Procedures, Functions, Triggers & CTEs
│   └── role_privilege_management.sql # Requirement R: MySQL 8.0 Roles, Grants, Revoke & Test Harness
├── backend/                       # FastAPI application
│   ├── requirements.txt              # Locked Python dependencies
│   ├── pytest.ini                   # Pytest test suite configuration
│   ├── scripts/                      # Operational verification scripts
│   │   ├── verify_database.py        # Safe read-only schema and constraint verifier
│   │   └── redis_crud_demo.py        # Live Redis CRUD and NoSQL demonstration script
│   ├── app/
│   │   ├── main.py                  # ASGI FastAPI application entrypoint & lifespan
│   │   ├── core/                    # Security, hashing, JWT, configuration settings
│   │   ├── db/                      # MySQL engine, connection pooling, Redis manager
│   │   ├── models/                  # SQLAlchemy 2.x declarative entity models (22 tables)
│   │   ├── schemas/                 # Pydantic v2 schemas and validation models
│   │   ├── repositories/            # Abstracted database access routines
│   │   ├── services/                # Business logic, state machines, and calculations
│   │   └── api/
│   │       ├── router.py            # Master /api/v1 router registration
│   │       └── routes/              # 14 isolated domain endpoint routers
│   └── tests/                       # Comprehensive pytest suite (98 automated tests)
└── frontend/                      # React + Vite single page application
    ├── package.json                 # Node.js dependencies
    ├── vite.config.js               # Vite build configuration
    ├── tailwind.config.js           # Tailwind CSS theme configuration
    └── src/
        ├── App.jsx                  # Main application router and shell (33 routes)
        ├── services/api.js          # Axios API clients
        ├── components/              # Presentation components (Navbar, Modal, Alert, etc.)
        ├── context/                 # AuthContext and CartContext global state
        └── pages/                   # 33 role-specific view pages
```

---

## 4. Local Environment Setup & Verification

### 4.1 Prerequisites
- Linux (Ubuntu 22.04 / 24.04 LTS or compatible)
- Python 3.12+ with virtual environment
- Node.js 18+ and `npm`
- MySQL 8.0+
- Redis 7.0+

### 4.2 Database Verification & Demonstration Scripts
```bash
# 1. Run safe database schema and constraint verification (Non-destructive)
backend/.venv/bin/python backend/scripts/verify_database.py

# 2. Run live NoSQL Redis CRUD demonstration harness
backend/.venv/bin/python backend/scripts/redis_crud_demo.py
```

### 4.3 Automated Test Suite Execution
```bash
# Run full automated test suite (All 98 tests)
backend/.venv/bin/pytest backend/tests -v
```

### 4.4 Frontend Production Build
```bash
cd frontend
npm run build
```

---

## 5. Academic Requirement SQL Scripts

| Rubric Requirement | File Location | Key Capabilities Demonstrated |
| :--- | :--- | :--- |
| **Requirement H (ER Diagram)** | `docs/ER_DIAGRAM.md` | Full 22-entity Mermaid diagram, attributes, keys, polymorphic identity decomposition, cardinality. |
| **Requirement I (Relational Schema)** | `docs/RELATIONAL_SCHEMA.md` | Academic notation, candidate keys, composite FKs, referential action matrix, ORM mismatch audit. |
| **Requirement I (Data Dictionary)** | `docs/DATA_DICTIONARY.md` | Column types, constraints, nullability, defaults, descriptions for all 22 tables. |
| **Requirement J (DDL & Verification)** | `database/schema.sql`<br>`backend/scripts/verify_database.py` | 22 CREATE TABLE definitions, domain CHECK constraints, B-tree indexes, safe verification script. |
| **Requirement K & P (Redis NoSQL)** | `docs/REDIS_DESIGN.md`<br>`backend/scripts/redis_crud_demo.py`<br>`backend/tests/test_redis_crud.py` | Redis Hashes, Strings, TTL, Sorted Sets leaderboard, Pub/Sub, CRUD script, automated tests. |
| **Requirement M (DML Operations)** | `database/dml_operations.sql` | INSERT (single/multi-row), SELECT, UPDATE, safe DELETE, `START TRANSACTION`, `COMMIT`, `ROLLBACK`. |
| **Requirement N (Advanced Queries)** | `database/advanced_queries.sql` | INNER/LEFT/RIGHT/Multi-table JOINs, Nested queries (WHERE/FROM/SELECT), Correlated queries, `WITH RECURSIVE` date series, window functions. |
| **Requirement O (Advanced SQL Objects)**| `database/advanced_sql_objects.sql`| 3 Stored Procedures, 2 Stored Functions, Audit Triggers, 3 CTE demonstrations, CALL/SELECT harness. |
| **Requirement R (MySQL Roles & Privileges)**| `database/role_privilege_management.sql`<br>`docs/MYSQL_ROLE_PRIVILEGE_MANAGEMENT.md` | MySQL 8.0 RBAC: 4 roles, 4 users, PoLP grants, 22-table matrix, REVOKE demo, negative test proofs. |
| **Requirement Q (Next.js Proposal)** | `docs/DBMS_RUBRIC_COMPLIANCE.md` | Detailed architectural Next.js App Router migration proposal with risk assessment. |
| **Requirement T & U (Compliance & Viva)**| `docs/DBMS_RUBRIC_COMPLIANCE.md` | Comprehensive rubric compliance report, module breakdown, Viva Q&A with 12 database topics. |

---

## 6. Baseline Seed Credentials (Development)

| Role | Email | Password | Primary Dashboard |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@test.com` | `Password@123` | `/admin/dashboard` |
| **Kitchen Manager** | `manager1@test.com` | `Password@123` | `/kitchen/dashboard` |
| **Line Cook** | `staff1@test.com` | `Password@123` | `/kitchen/orders` |
| **Delivery Courier** | `driver1@test.com` | `Password@123` | `/delivery/dashboard` |
| **Customer** | `customer1@test.com` | `Password@123` | `/` |
