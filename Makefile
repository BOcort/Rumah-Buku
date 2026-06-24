## Variabel konfigurasi
DOCKER_COMPOSE = docker compose
CONTAINER_ODOO = rumah_buku_odoo
CONTAINER_DB = odoo-postgres
WEB_DB_NAME = odoo_development

## Phony targets
.PHONY: start stop restart console psql logs

help:
	@echo "Available targets:"
	@echo "  start    - Start the compose with daemon"
	@echo "  stop     - Stop the compose"
	@echo "  restart  - Restart the compose"
	@echo "  console  - Odoo interactive console"
	@echo "  psql     - PostgreSQL Interactive Shell"
	@echo "  logs     - Logs the odoo or db container"

start:
	$(DOCKER_COMPOSE) up -d

stop:
	$(DOCKER_COMPOSE) down

restart:
	$(DOCKER_COMPOSE) restart

console:
	docker exec -it $(CONTAINER_ODOO) /bin/bash

psql:
	docker exec -it $(CONTAINER_DB) psql -U odoo -d $(WEB_DB_NAME)

## Log target untuk memilih antara odoo atau db
LOG_TARGET := $(word 2, $(MAKECMDGOALS))

logs:
ifeq ($(LOG_TARGET), odoo)
	$(DOCKER_COMPOSE) logs -f $(CONTAINER_ODOO)
else ifeq ($(LOG_TARGET), db)
	$(DOCKER_COMPOSE) logs -f $(CONTAINER_DB)
else
	@echo "Invalid log target. Use 'make logs odoo' or 'make logs db'"
endif

## Mencegah error jika argumen tambahan diberikan
$(eval $(LOG_TARGET):;@:)