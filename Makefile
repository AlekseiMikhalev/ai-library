lint:
	pre-commit run --all

.PHONY: start-development
start-dev: ## Start the development docker container.
	sudo docker compose -f docker-compose.dev.yml --env-file .env up

.PHONY: stop-development
stop-dev: ## Stop the development docker container.
	sudo docker compose -f docker-compose.dev.yml down
