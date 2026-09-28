# TaskFlow FastAPI

TaskFlow is a clean, interview-friendly RESTful backend service for managing users, projects, and tasks. It is built with **FastAPI**, **async SQLAlchemy**, **MySQL**, and **Docker** and demonstrates API design, relational schema modeling, validation, filtering, indexing, and structured HTTP responses.

## Why this project?

The project is intentionally scoped like a realistic entry-level backend system: large enough to demonstrate backend engineering fundamentals, but small enough to understand end-to-end and explain confidently in an interview.

## Tech Stack

- Python 3.12
- FastAPI
- SQLAlchemy 2.0 (async ORM)
- MySQL 8
- Pydantic
- Docker & Docker Compose
- Uvicorn
- Postman / Swagger UI for API testing

## Features

- 19 REST endpoints across health, users, projects, tasks, and statistics
- Async database access with SQLAlchemy `AsyncSession`
- Relational MySQL schema with foreign keys and cascading behavior
- Input validation using Pydantic schemas
- Pagination and task filtering
- Task status and priority enums
- Unique email constraint and conflict handling
- Indexed foreign keys plus composite task indexes
- Consistent HTTP status codes (`201`, `204`, `404`, `409`, `422`)
- Dockerized API and MySQL services
- Auto-generated Swagger/OpenAPI docs

## Architecture

```text
Client / Postman
      |
      v
   FastAPI
      |
      v
Pydantic validation
      |
      v
SQLAlchemy Async ORM
      |
      v
    MySQL
```

## Database Relationships

```text
User 1 ------ N Project
User 1 ------ N Task (assignee)
Project 1 --- N Task
```

Deleting a project deletes its tasks. Deleting an assignee keeps the task and sets `assignee_id` to `NULL`.

## Project Structure

```text
taskflow-fastapi/
├── app/
│   ├── routers/
│   │   ├── projects.py
│   │   ├── stats.py
│   │   ├── tasks.py
│   │   └── users.py
│   ├── config.py
│   ├── crud.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   └── schemas.py
├── docs/
│   └── API_ENDPOINTS.md
├── postman/
│   └── TaskFlow.postman_collection.json
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Run with Docker

1. Clone the repository.
2. Create your environment file:

```bash
cp .env.example .env
```

3. Start the API and MySQL:

```bash
docker compose up --build
```

4. Open:

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Example Workflow

Create a user:

```http
POST /users
Content-Type: application/json

{
  "name": "Vardhan",
  "email": "vardhan@example.com"
}
```

Create a project:

```http
POST /projects
Content-Type: application/json

{
  "name": "Interview Preparation",
  "description": "Track DSA and backend preparation",
  "owner_id": 1
}
```

Create a task:

```http
POST /tasks
Content-Type: application/json

{
  "title": "Complete graph problems",
  "priority": "high",
  "status": "pending",
  "project_id": 1,
  "assignee_id": 1
}
```

Filter tasks:

```http
GET /tasks?project_id=1&status=pending&priority=high
```

## API Documentation

A concise endpoint list is available in [`docs/API_ENDPOINTS.md`](docs/API_ENDPOINTS.md). For full request/response schemas, run the application and use Swagger UI at `/docs`.

## Interview Talking Points

This project can be used to explain:

- REST resources and HTTP methods
- CRUD operations
- request/response validation
- primary keys and foreign keys
- one-to-many relationships
- database normalization
- indexes and why they help frequent filters
- async request/database flow
- Docker containerization
- API testing with Postman and Swagger
- common status codes and defensive error handling

## Future Improvements

- JWT authentication and authorization
- Alembic database migrations
- pytest integration tests
- Redis caching
- CI/CD with GitHub Actions
- deployment to Google Cloud Run

## License

This project is intended for learning, portfolio use, and interview preparation.
