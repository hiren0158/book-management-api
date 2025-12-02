# Docker Commands

## Start all services
```bash
docker-compose up -d
```

## Start with pgAdmin
```bash
docker-compose --profile tools up -d
```

## Stop all services
```bash
docker-compose down
```

## Stop and remove volumes
```bash
docker-compose down -v
```

## View logs
```bash
docker-compose logs -f api
docker-compose logs -f postgres
```

## Rebuild containers
```bash
docker-compose up -d --build
```

## Run migrations inside container
```bash
docker-compose exec api poetry run alembic upgrade head
```

## Access PostgreSQL CLI
```bash
docker-compose exec postgres psql -U postgres -d book_management_db
```

## Access pgAdmin
- URL: http://localhost:5050
- Email: admin@admin.com (or from .env)
- Password: admin (or from .env)

### Add Server in pgAdmin:
- Host: postgres
- Port: 5432
- Database: book_management_db
- Username: postgres (or from .env)
- Password: ToDoApp! (or from .env)
