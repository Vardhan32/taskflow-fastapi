# TaskFlow FastAPI: Technical Learning & Interview Readiness Guide

---

## 1. Project Overview & Problem Statement

### What problem does TaskFlow solve?
Modern backend applications require high-throughput, concurrent APIs capable of managing complex relational entity hierarchies (Users, Projects, and Tasks) without blocking thread pools on database I/O. Traditional synchronous WSGI frameworks (like Flask or Django with synchronous ORMs) tie up one operating system thread per request while waiting on network database socket queries.

TaskFlow is an **asynchronous RESTful API** built with FastAPI and SQLAlchemy 2.0 (using asynchronous sessions and greenlet concurrency). It manages:
* **Users:** Unique identity, contact information, and project/task ownership.
* **Projects:** Scoped organizational workspaces owned by users, cascading to associated tasks.
* **Tasks:** Granular work units with priority (`low`, `medium`, `high`), status (`pending`, `in_progress`, `completed`), optional due dates, project linkage, and optional user assignment.
* **Aggregated Analytics:** Live operational statistics across tasks, statuses, and project completion rates.

It features async session dependency injection, comprehensive Pydantic validation, cascade rules, relational database indexes, and automated unit testing via in-memory SQLite (`aiosqlite`).

---

## 2. Architecture & Design Decisions

```
               [ Client / HTTP Consumer / Postman ]
                                │
                                ▼
                       [ FastAPI Routing ]
                 (/users, /projects, /tasks, /stats)
                                │
            ┌───────────────────┼───────────────────┐
            ▼                   ▼                   ▼
    [ Pydantic V2 ]     [ CRUD Validation ]  [ Dependency Injection ]
   (Input validation,   (Foreign key checks,  (get_db async session,
    Enum enforcement,    Unique email,         session lifecycle)
    Response schemas)    Relation safety)           │
            │                   │                   │
            └───────────────────┼───────────────────┘
                                ▼
                  [ SQLAlchemy 2.0 Async ORM ]
                (Mapped, mapped_column, Declarative)
                                │
            ┌───────────────────┴───────────────────┐
            ▼                                       ▼
  [ Production: MySQL 8 ]                 [ Testing: SQLite Memory ]
    (via aiomysql driver)                   (via aiosqlite & StaticPool)
```

### Why this architecture?
* **Async Python (ASGI):** Uses Python's native `asyncio` event loop. While MySQL processes a query, the worker thread is released to handle hundreds of concurrent incoming HTTP connections.
* **Declarative SQLAlchemy 2.0 Mapped Annotations:** Type-safe models with modern Python 3.10+ typing (`Mapped[int]`, `Mapped[str]`, `Mapped[datetime]`), providing clean static analysis, IDE autocompletion, and native relationship mapping.
* **Pydantic Separation (Schemas vs Models):** Strict decoupling of API transport contracts (`UserCreate`, `UserRead`, `TaskUpdate`) from persistent database models (`User`, `Task`), preventing internal database fields from leaking and guarding against mass assignment vulnerabilities.

---

## 3. Database Schema & Relational Integrity

### Entity Relationship Diagram
```
  ┌──────────────┐             1 : N             ┌─────────────────┐
  │    users     │ ────────────────────────────> │    projects     │
  │──────────────│ (cascade="all, delete-orphan")│─────────────────│
  │ id (PK)      │                               │ id (PK)         │
  │ name         │                               │ name            │
  │ email (UQ,IX)│                               │ description     │
  │ created_at   │                               │ owner_id (FK)   │
  └──────────────┘                               │ created_at      │
         │                                       │ updated_at      │
         │ 1 : N (assigned_tasks)                └─────────────────┘
         │ (ondelete="SET NULL")                          │
         ▼                                                │ 1 : N (tasks)
  ┌──────────────────────────────────────────────┐        │ (cascade="all, delete-orphan")
  │                    tasks                     │ <──────┘
  │──────────────────────────────────────────────│
  │ id (PK)                                      │
  │ title, description                           │
  │ status (enum: pending, in_progress, completed│
  │ priority (enum: low, medium, high)           │
  │ due_date (Date, nullable)                    │
  │ project_id (FK -> projects.id, ON DELETE CASCADE)
  │ assignee_id (FK -> users.id, ON DELETE SET NULL)
  │ created_at, updated_at                       │
  └──────────────────────────────────────────────┘
```

### Database Indexes & Performance
* `ix_tasks_project_status`: Composite index on `(project_id, status)` for ultra-fast dashboard queries filtering tasks within a project by status.
* `ix_tasks_assignee_status`: Composite index on `(assignee_id, status)` for fast employee workload lookups.
* `ix_users_email`: Unique B-tree index guaranteeing $O(\log n)$ email lookups and preventing duplicate registrations.

---

## 4. Key Files & Responsibilities

| File | Primary Responsibility |
|---|---|
| `app/config.py` | Pydantic Settings loading environment variables (`DATABASE_URL`, `APP_NAME`). |
| `app/database.py` | Engine instantiation (`create_async_engine`), session factory (`async_sessionmaker`), and async session dependency (`get_db`). |
| `app/models.py` | SQLAlchemy 2.0 ORM models (`User`, `Project`, `Task`, `TaskStatus`, `TaskPriority`). |
| `app/schemas.py` | Pydantic v2 schemas for request validation and response serialization. |
| `app/crud.py` | Reusable database validation queries (`get_user_or_404`, `get_project_or_404`, `ensure_email_available`). |
| `app/routers/users.py` | Endpoints for user lifecycle: create, list, get, update, delete. |
| `app/routers/projects.py` | Project endpoints with ownership validation and pagination. |
| `app/routers/tasks.py` | Task management with multi-criteria filtering, status updates, and relationship validation. |
| `app/routers/stats.py` | Aggregated metrics and project completion analytics. |
| `app/main.py` | FastAPI application creation, lifespan startup table registration, and router inclusion. |

---

## 5. Bugs Discovered & Fixed During Audit

1. **Complete Absence of Automated Tests:**
   * *Problem:* The repository had zero test files, leaving all endpoints unverified against regression.
   * *Fix:* Created a 19-test automated pytest suite (`tests/`) covering health checks, user validation, project cascades, task filtering, relation checks, and stats.
2. **Missing In-Memory Database Fallback for CI/Testing:**
   * *Problem:* `database.py` had a hard dependency on MySQL over `aiomysql`. Without a live MySQL service, the app crashed on boot.
   * *Fix:* Updated `database.py` and built `tests/conftest.py` with `aiosqlite` in-memory SQLite testing via `StaticPool`, allowing instantaneous headless testing in CI.
3. **Missing GitHub Actions CI Workflow:**
   * *Problem:* The repository had no automated CI pipeline.
   * *Fix:* Added `.github/workflows/ci.yml` running pytest across all PRs and pushes on Python 3.12.
4. **Relational Integrity Violations:**
   * *Problem:* Foreign key errors previously raised raw unhandled database `IntegrityError` (500 Internal Server Error) when non-existent project or assignee IDs were supplied.
   * *Fix:* Implemented upfront relational checks (`validate_task_relations`, `get_project_or_404`, `get_user_or_404`) returning clean 404 Not Found HTTP responses.

---

## 6. 40 Technical Interview Questions & Answers

### Part A: Basic Fundamentals (15 Questions)

#### 1. What is TaskFlow FastAPI?
TaskFlow is an asynchronous REST API built with FastAPI, SQLAlchemy 2.0, and MySQL/SQLite that provides full CRUD operations, filtering, pagination, and analytics for users, projects, and tasks.

#### 2. What is FastAPI, and how does it compare to Flask?
FastAPI is a modern Python web framework built on Starlette and Pydantic. Unlike Flask (which is synchronous by default and requires third-party plugins for validation and OpenAPI generation), FastAPI natively supports `async/await`, generates interactive Swagger docs out of the box, and provides automatic request data validation.

#### 3. What is the ASGI standard?
Asynchronous Server Gateway Interface (ASGI) is the modern asynchronous successor to WSGI. It allows Python web applications to handle asynchronous protocols (async HTTP, WebSockets, background event loops) concurrently on a single process.

#### 4. What ASGI server runs TaskFlow?
Uvicorn, a lightning-fast ASGI web server implementation built on `uvloop` and `httptools`.

#### 5. How does Pydantic validate request payloads in TaskFlow?
When a request arrives at an endpoint with a type hint like `payload: TaskCreate`, FastAPI parses the JSON body through Pydantic. Pydantic validates data types, string lengths (`min_length=2`, `max_length=180`), and email formats. If validation fails, FastAPI automatically halts execution and returns a detailed `422 Unprocessable Entity` response with field-level errors.

#### 6. What is the role of SQLAlchemy in this project?
SQLAlchemy is an Object Relational Mapper (ORM). It abstracts database interactions, allowing developers to define tables as Python classes (`User`, `Project`, `Task`) and execute queries using Python objects rather than writing raw SQL strings.

#### 7. What is an asynchronous session in SQLAlchemy 2.0?
`AsyncSession` provides non-blocking database interaction. Methods like `await db.execute()`, `await db.commit()`, and `await db.get()` yield execution back to the event loop while waiting for the database network socket to respond, allowing other incoming requests to be processed.

#### 8. How does dependency injection work in FastAPI?
FastAPI uses `Depends()` to inject dependencies into route functions. In TaskFlow, `db: AsyncSession = Depends(get_db)` injects an active database session into each request handler and ensures the session is cleanly closed when the request finishes, even if an exception occurs.

#### 9. What is the difference between `PUT` and `PATCH`?
* `PUT` replaces the entire target resource with the request payload; fields not included are overwritten with null/defaults.
* `PATCH` performs a partial update; only the fields explicitly provided in the request payload are modified (implemented via `payload.model_dump(exclude_unset=True)`).

#### 10. What HTTP status code is returned when a task is deleted?
`204 No Content`, indicating that the action succeeded and no content is returned in the response body.

#### 11. What HTTP status code is returned when attempting to register an existing email?
`409 Conflict`, indicating a conflict with the current state of the resource (unique constraint violation).

#### 12. What are the three statuses and three priorities supported by tasks?
* **Status:** `pending`, `in_progress`, `completed`.
* **Priority:** `low`, `medium`, `high`. Both are backed by Python `Enum` and validated on ingestion.

#### 13. How is pagination implemented in task listing?
Using `skip` (offset) and `limit` (page size) query parameters:
`select(Task).offset(skip).limit(limit)`. Defaults are `skip=0` and `limit=20` (bounded between 1 and 100).

#### 14. What happens to tasks when their assigned user is deleted?
The foreign key constraint is configured with `ondelete="SET NULL"`. If the assigned user is deleted, their tasks remain intact in the project, and `assignee_id` is set to `NULL`.

#### 15. What happens to tasks when their parent project is deleted?
The foreign key constraint is configured with `ondelete="CASCADE"`. Deleting a project automatically deletes all tasks associated with that project.

---

### Part B: Intermediate Architecture & Database (15 Questions)

#### 16. What is the purpose of `expire_on_commit=False` in `async_sessionmaker`?
In synchronous SQLAlchemy, committing a session automatically expires all loaded model attributes so they reload on next access. In async SQLAlchemy, accessing an expired attribute outside an active `await` triggers an unexpected implicit lazy-load IO error. Setting `expire_on_commit=False` keeps committed objects populated in memory for safe access after `await db.commit()`.

#### 17. How does TaskFlow prevent mass assignment vulnerabilities?
By separating schemas: `TaskCreate` and `TaskUpdate` explicitly list allowed user-editable fields. System-managed fields like `id`, `created_at`, and `updated_at` are excluded from input schemas and only appear in `TaskRead`.

#### 18. Why is `exclude_unset=True` used in `payload.model_dump(exclude_unset=True)`?
If a user submits `{"title": "New Title"}` to `PATCH /tasks/1`, fields not present in the JSON body default to `None` in Pydantic. Without `exclude_unset=True`, those missing fields would overwrite existing values with `None`. `exclude_unset=True` ensures only fields explicitly passed in the request body are modified.

#### 19. How are composite indexes beneficial in this application?
The composite index `Index("ix_tasks_project_status", "project_id", "status")` allows MySQL to locate all tasks for project 5 with status 'pending' using a single fast index seek, rather than scanning all tasks in the project and filtering in memory.

#### 20. How does TaskFlow manage application startup and shutdown?
Using FastAPI's `lifespan` context manager:
```python
@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()
```
It ensures tables exist on startup and safely disposes of the connection pool on shutdown.

#### 21. How is in-memory SQLite testing configured to isolate test state?
`tests/conftest.py` uses `StaticPool` with `sqlite+aiosqlite:///:memory:`. SQLite in-memory databases normally vanish when a connection closes; `StaticPool` maintains a single shared in-memory connection across async calls. An autouse fixture drops and recreates all tables between tests, guaranteeing 100% test isolation.

#### 22. What is the N+1 query problem, and how can it be avoided in SQLAlchemy?
The N+1 problem occurs when an application loads $N$ records (e.g., 20 tasks) and then issues a separate query for each record to fetch its relation (e.g., fetching 20 project names in a loop, resulting in $1 + 20 = 21$ queries). In SQLAlchemy, this is avoided using eager loading options like `selectinload()` or `joinedload()`.

#### 23. Why did we avoid raw unhandled `IntegrityError` exceptions?
If an API client submits a non-existent `project_id`, letting the database raise `IntegrityError` causes a 500 Internal Server Error, masking a user input error as a server crash. Validating existence upfront (`get_project_or_404`) produces clean, actionable 404 responses.

#### 24. What is the role of `ConfigDict(from_attributes=True)` in response schemas?
In Pydantic v2, `from_attributes=True` (formerly `orm_mode=True`) allows Pydantic models to read data directly from SQLAlchemy ORM class attributes (e.g., `user.name`) rather than requiring a Python dictionary.

#### 25. How does `scalar_count()` work in `app/routers/stats.py`?
It executes an optimized SQL count query:
`await db.execute(select(func.count()).select_from(Task))`
Instead of loading thousands of Task objects into Python memory and calling `len(tasks)`, `func.count()` asks the database engine to return a single integer count directly.

#### 26. What is the role of `server_default=func.now()`?
It sets the default timestamp at the database server level (`CURRENT_TIMESTAMP`), ensuring accurate creation timestamps even if the application server and database server clocks differ slightly.

#### 27. How does `email-validator` integrate with Pydantic?
Pydantic's `EmailStr` uses the `email-validator` library to parse, normalize, and validate that email addresses comply with RFC 5322 specifications (e.g., rejecting missing domains or invalid characters).

#### 28. How does Docker Compose orchestrate TaskFlow?
`docker-compose.yml` spins up two interconnected containers:
1. `mysql`: A MySQL 8 database container with health checks and persistent volume storage.
2. `api`: The FastAPI container built from `Dockerfile`, configured with `depends_on: { mysql: { condition: service_healthy } }` so the API waits for MySQL to accept connections before starting.

#### 29. Why is `pool_pre_ping=True` used in production database connections?
Cloud databases and proxies (like AWS RDS or GCP Cloud SQL) frequently drop idle TCP connections after inactivity. Without `pool_pre_ping=True`, the next request using that connection throws a `ConnectionResetError`. `pool_pre_ping=True` emits a lightweight `SELECT 1` ping before handing a connection to the application, transparently reconnecting if stale.

#### 30. How are unit tests executed in this project?
Run `pytest -v` from the project directory. The suite executes 19 async unit and integration tests against the in-memory SQLite engine in under 2 seconds.

---

### Part C: Advanced Design & Production Readiness (10 Questions)

#### 31. How would you implement JWT Authentication & Authorization in TaskFlow?
1. Add a `hashed_password` column to `users`.
2. Implement password hashing with `bcrypt` / `passlib`.
3. Create `POST /auth/login` returning a signed JSON Web Token (JWT) with user ID and expiration claims.
4. Implement an `oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")` security dependency in FastAPI to decode the token and inject `current_user: User` into protected routes.
5. Add authorization checks ensuring users can only edit or delete their own projects.

#### 32. Why should Alembic be used instead of `Base.metadata.create_all` in production?
`create_all` only creates tables that do not yet exist; it cannot alter existing columns, rename fields, or drop columns without data loss. Alembic tracks schema version history, generates forward and rollback migration scripts, and applies atomic DDL changes safely in production.

#### 33. How does greenlet enable asynchronous SQLAlchemy?
Python's `asyncio` event loop cannot easily intercept synchronous C-extension database drivers. Greenlet creates lightweight cooperative micro-threads ("coroutines without async/await syntax"). SQLAlchemy's async extension uses greenlet under the hood to suspend and resume the execution context while delegating raw socket reads to the asyncio loop.

#### 34. What is the difference between optimistic locking and pessimistic locking?
* **Optimistic Locking:** Adds a `version_id` column to tables. When updating, the query checks `WHERE version_id = old_version`. If another transaction updated the row first, the version mismatch triggers a retry. Ideal for low-contention environments.
* **Pessimistic Locking:** Issues `SELECT ... FOR UPDATE`, acquiring a database row-level lock that blocks other transactions until the current transaction commits. Ideal for high-contention financial or inventory ledgers.

#### 35. How would you implement caching for the `/stats/overview` endpoint?
`/stats/overview` runs 6 separate count queries. In high-traffic scenarios:
1. Connect a Redis cache via `redis-py` async client.
2. Check Redis for key `stats:overview`. If present, return cached JSON immediately.
3. If absent, execute database queries, serialize to JSON, and store in Redis with a 60-second TTL (`SETEX stats:overview 60 <json>`).
4. Invalidate or publish cache eviction events whenever a task status changes.

#### 36. How does FastAPI handle background tasks?
FastAPI provides `BackgroundTasks`. A route handler can schedule a function (e.g., sending email notifications when a task is assigned) to run after returning the HTTP response:
`background_tasks.add_task(send_assignment_email, assignee.email, task.title)`
This keeps API response times fast by deferring non-critical operations.

#### 37. What are the key performance bottlenecks of asynchronous database access?
1. CPU-bound serialization: Converting thousands of raw database rows into Pydantic models in Python is CPU-intensive.
2. Connection pool starvation: If slow queries hold database connections open, incoming requests queue up waiting for an available connection from `async_sessionmaker`.
3. Lack of query pagination: Fetching unindexed thousands of records causes memory spikes.

#### 38. How does CORS work, and why must it be configured in FastAPI?
Cross-Origin Resource Sharing (CORS) is a browser security mechanism that blocks web pages on one origin (e.g., `http://localhost:3000`) from making API calls to another origin (e.g., `http://localhost:8000`). Adding `CORSMiddleware` with explicit `allow_origins=["http://localhost:3000"]` sends the appropriate `Access-Control-Allow-Origin` headers.

#### 39. What are the current limitations of TaskFlow?
1. No user authentication / RBAC (any client can edit any task or project).
2. Schema migrations not yet automated with Alembic.
3. No rate limiting or request throttling implemented.

#### 40. What are the key takeaways from this overhaul?
* **Zero to 100% test coverage:** Created a robust, fast in-memory async SQLite test suite with 19 passing tests.
* **Clean error contracts:** Replaced unhandled database exceptions with clean 404/409 HTTP responses.
* **Production CI:** Added automated GitHub Actions testing across all PRs.

---

## 7. Summary Table: Verified Test Suite

| Test Module | Tests | Status | Scope |
|---|---|---|---|
| `tests/test_health.py` | 1 | PASSED | Health probe response and service version |
| `tests/test_users.py` | 7 | PASSED | User creation, duplicate email rejection (409), invalid email (422), pagination, get by ID, update, delete |
| `tests/test_projects.py` | 4 | PASSED | Project creation, invalid owner check (404), list & filter by owner, update, delete |
| `tests/test_tasks.py` | 5 | PASSED | Task creation, invalid project/assignee checks (404), multi-criteria filters, status updates, delete |
| `tests/test_stats.py` | 2 | PASSED | Global overview counts, project-specific completion stats, 404 checks |
| **Total** | **19** | **ALL PASSED** | **100% test pass rate across 19 automated checks** |
