# API Endpoints

Base URL: `http://localhost:8000`

## Health
- `GET /health`

## Users
- `POST /users`
- `GET /users`
- `GET /users/{user_id}`
- `PATCH /users/{user_id}`
- `DELETE /users/{user_id}`

## Projects
- `POST /projects`
- `GET /projects`
- `GET /projects/{project_id}`
- `PATCH /projects/{project_id}`
- `DELETE /projects/{project_id}`

## Tasks
- `POST /tasks`
- `GET /tasks`
- `GET /tasks/{task_id}`
- `PATCH /tasks/{task_id}`
- `PATCH /tasks/{task_id}/status`
- `DELETE /tasks/{task_id}`

`GET /tasks` supports filters for `project_id`, `assignee_id`, `status`, `priority`, and `due_before`.

## Statistics
- `GET /stats/overview`
- `GET /stats/projects/{project_id}`

Interactive OpenAPI documentation is available at `/docs` and `/redoc`.
