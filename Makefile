.PHONY: help install run serve test dev stop

help:
	@echo "Worldsim Commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make run        - Start the server (opens browser automatically)"
	@echo "  make serve      - Start the server"
	@echo "  make test       - Run tests"
	@echo "  make dev        - Install dev dependencies"
	@echo "  make stop       - Stop all Python processes"

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

run:
	@python -m worldsim.cli

serve:
	uvicorn worldsim.server:app --reload --port 8000

test:
	python -m pytest tests/ -v

.PHONY: install run serve test dev stop
