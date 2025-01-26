# Replace the % with the desired environment, e.g. `make run-local` for local environment
# or `make run-production` for production environment

# Show configs
config-%:
	docker compose -f docker-compose.$*.yml config

# Build images
build-%:
	docker compose -f docker-compose.$*.yml build

# Run containers
start-%:
	docker compose -f docker-compose.$*.yml up -d

# Run local environment with debug mode (will wait for debugger)
start-local-debug:
	docker compose -f docker-compose.local.yml -f docker-compose.debug.yml up -d

# Enter shell
shell-%:
	docker compose -f docker-compose.$*.yml run --rm django python manage.py shell

# Stop containers
stop-%:
	docker compose -f docker-compose.$*.yml down

# Restart containers
restart-%:
	$(MAKE) stop-$*
	$(MAKE) start-$*

# Stop containers and remove all volumes
rm-vol-%:
	docker compose -f docker-compose.$*.yml down -v

# Create a superuser
csu-%:
	docker compose -f docker-compose.$*.yml run --rm django python manage.py createsuperuser

# Make migrations (local only)
mm:
	docker compose -f docker-compose.local.yml run --rm django python manage.py makemigrations

# Migrate database
migrate-%:
	docker compose -f docker-compose.$*.yml run --rm django python manage.py migrate

pytest:
	docker compose -f docker-compose.local.yml run --rm django pytest

# Pre-commit
pc:
	pipenv run pre-commit run --all-files

# Remove static volume
rm-static-vol:
	docker volume rm ai_text_game_production_django_static
