# FlightVault Docker Deployment

## Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/AvishkarPatil/FlightVault.git
cd FlightVault
```

2. **Start with Docker Compose**
```bash
docker-compose up -d
```

3. **Load sample data**
```bash
docker-compose exec flightvault python setup/data_loader.py
```

4. **Access the application**
- Frontend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Services

- **MariaDB**: Database with system versioning
- **FlightVault**: Backend API + Frontend

## Environment Variables

- `DB_HOST`: Database host (default: mariadb)
- `DB_USER`: Database user (default: root)
- `DB_PASSWORD`: Database password (default: flightvault123)
- `DB_NAME`: Database name (default: flightvault)

## CLI Usage

```bash
# Check status
docker-compose exec flightvault python src/cli/flightvault.py status

# View timeline
docker-compose exec flightvault python src/cli/flightvault.py timeline

# Test recovery
docker-compose exec flightvault python src/cli/flightvault.py recover --dry-run
```

## Stopping

```bash
docker-compose down
```

## Development

```bash
# Rebuild after changes
docker-compose up --build
```