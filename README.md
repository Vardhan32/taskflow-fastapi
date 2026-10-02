# TaskFlow FastAPI

TaskFlow is a REST API for managing users, projects, and tasks. I built it with FastAPI, SQLAlchemy, MySQL, and Docker to practice building a backend application with database relationships, validation, filtering, pagination, and API documentation.

## Tech Stack

- Python 3.12
- FastAPI
- SQLAlchemy 2.0 (async ORM)
- MySQL 8
- Pydantic
- Docker & Docker Compose
- Uvicorn
- Postman and Swagger UI

## Features

- Create, view, update, and delete users, projects, and tasks
- Async database access using SQLAlchemy `AsyncSession`
- MySQL relationships using primary keys and foreign keys
- Input validation with Pydantic
- Task filtering by project, assignee, status, priority, and due date
- Pagination for task results
- Task status and priority enums
- Unique email validation and conflict handling
- Database indexes for commonly queried fields
- HTTP status handling for common API cases
- Docker setup for the API and MySQL
- Swagger/OpenAPI documentation

## How It Works

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

A user can own multiple projects, and a project can contain multiple tasks. A user can also be assigned to multiple tasks.

If a project is deleted, its tasks are deleted as well. If an assigned user is deleted, the task remains and `assignee_id` is set to `NULL`.

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

## Running the Project

Clone the repository and create the environment file:

```bash
cp .env.example .env
```

Start the API and MySQL containers:

```bash
docker compose up --build
```

Once the application is running:

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Example

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
  "name": "Website Redesign",
  "description": "Track work for the website redesign",
  "owner_id": 1
}
```

Create a task:

```http
POST /tasks
Content-Type: application/json

{
  "title": "Create landing page API",
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

A list of available endpoints is available in [`docs/API_ENDPOINTS.md`](docs/API_ENDPOINTS.md).

For request and response schemas, the application also provides Swagger UI at `/docs` and ReDoc at `/redoc`.

## Things I Want to Add

- Authentication and authorization
- Alembic migrations
- Automated tests with pytest
- Redis caching
- CI/CD with GitHub Actions
- Deployment to Google Cloud Run
