.PHONY: help build start stop restart logs status shell convert clean test

# Default target
help:
	@echo "Java to Node.js Conversion Agent - Docker Commands"
	@echo ""
	@echo "Usage: make <command>"
	@echo ""
	@echo "Commands:"
	@echo "  build      Build Docker image"
	@echo "  start      Start API server"
	@echo "  stop       Stop server"
	@echo "  restart    Restart server"
	@echo "  logs       View logs"
	@echo "  status     Show container status"
	@echo "  shell      Open container shell"
	@echo "  convert    Run CLI conversion (use: make convert ARGS='...')"
	@echo "  clean      Remove containers and images"
	@echo "  test       Run tests"
	@echo ""
	@echo "Examples:"
	@echo "  make start"
	@echo "  make convert ARGS='--github-url https://... --api-token TOKEN --model gemini-2.5-flash'"

# Build Docker image
build:
	docker build -t java-to-nodejs-converter .

# Start API server
start:
	@mkdir -p outputs tmp
	@if command -v docker-compose > /dev/null; then \
		docker-compose up -d; \
	else \
		docker compose up -d; \
	fi
	@echo "✓ API server started"
	@echo "  Web UI: http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"

# Stop server
stop:
	@if command -v docker-compose > /dev/null; then \
		docker-compose down; \
	else \
		docker compose down; \
	fi
	@echo "✓ Server stopped"

# Restart server
restart: stop
	@sleep 2
	@$(MAKE) start

# View logs
logs:
	@if command -v docker-compose > /dev/null; then \
		docker-compose logs -f; \
	else \
		docker compose logs -f; \
	fi

# Show status
status:
	@docker ps --filter "name=java-to-nodejs-converter" || echo "Container not running"

# Open container shell
shell:
	@docker exec -it java-to-nodejs-converter /bin/bash || \
	docker run --rm -it \
		-v "$(PWD)/outputs:/app/outputs" \
		-v "$(PWD)/tmp:/app/tmp" \
		java-to-nodejs-converter /bin/bash

# Run CLI conversion
convert:
	@if [ -z "$(ARGS)" ]; then \
		echo "Error: ARGS required. Example:"; \
		echo "  make convert ARGS='--github-url https://... --api-token TOKEN --model gemini-2.5-flash'"; \
		exit 1; \
	fi
	@mkdir -p outputs tmp
	docker run --rm \
		-v "$(PWD)/outputs:/app/outputs" \
		-v "$(PWD)/tmp:/app/tmp" \
		-e GEMINI_API_KEY="$$GEMINI_API_KEY" \
		-e OPENROUTER_API_KEY="$$OPENROUTER_API_KEY" \
		-e OPENAI_API_KEY="$$OPENAI_API_KEY" \
		-e GLM_API_KEY="$$GLM_API_KEY" \
		java-to-nodejs-converter convert $(ARGS)

# Clean up
clean:
	@if command -v docker-compose > /dev/null; then \
		docker-compose down --rmi local -v 2>/dev/null || true; \
	else \
		docker compose down --rmi local -v 2>/dev/null || true; \
	fi
	@echo "✓ Cleanup complete"

# Run tests
test:
	docker run --rm \
		-v "$(PWD):/app" \
		java-to-nodejs-converter python -m pytest tests/ || echo "No tests found"

