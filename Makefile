include .env

DC = docker compose
B = $(DC) build
ENTER = $(DC) run --entrypoint

start:
	$(DC) start

restart:
	$(DC) restart

up:
	$(DC) up -d

up-db:
	$(DC) up -d influx

init:
	$(DC) stop influx
	$(DC) rm influx
	rm -irf .local/influxdb2
	$(B) influx
	$(DC) up -d influx
	sleep 1
	$(DC) exec influx influx setup -u '${INFLUX_USERNAME}' -p '${INFLUX_PASSWORD}' -o '${INFLUX_ORG}' -b '${INFLUX_BUCKET}' -f
	$(DC) stop influx

build-no-cache:
	$(B) --no-cache --pull

down:
	$(DC) down
