# Database Migration Instructions

## Initialize Alembic (Already Done)
```bash
poetry run alembic init alembic
```

## Create Initial Migration
```bash
poetry run alembic revision --autogenerate -m "initial"
```

## Apply Migrations
```bash
poetry run alembic upgrade head
```

## Additional Commands

### Create New Migration
```bash
poetry run alembic revision --autogenerate -m "description_of_changes"
```

### Downgrade One Step
```bash
poetry run alembic downgrade -1
```

### View Migration History
```bash
poetry run alembic history
```

### Check Current Version
```bash
poetry run alembic current
```
