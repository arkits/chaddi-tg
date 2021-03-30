PYTHON = python

.PHONY = about setup run

.DEFAULT_GOAL = help

about:
	@echo "chaddi-tg"

setup:
	@echo "Setting up project env"
	
run:
	cd src && ${PYTHON} chaddi.py

docker-run:
	docker-compose build chaddi-tg
	docker-compose up chaddi-tg