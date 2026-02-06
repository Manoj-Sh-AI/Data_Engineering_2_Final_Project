cat > Makefile << 'EOF'
.PHONY: help setup install deploy start test clean

help:
	@echo "Available commands:"
	@echo "  make setup    - Setup GCP resources"
	@echo "  make install  - Install dependencies"
	@echo "  make deploy   - Deploy infrastructure"
	@echo "  make start    - Start data pipeline"
	@echo "  make test     - Run tests"
	@echo "  make clean    - Cleanup resources"

install:
	pip install -r requirements.txt

setup:
	bash scripts/01_setup_gcp.sh

deploy:
	bash scripts/02_deploy_infra.sh

start:
	bash scripts/03_start_pipeline.sh

test:
	pytest tests/ -v --cov=src

clean:
	bash scripts/05_cleanup.sh

docker-build:
	docker build -t streaming-consumer:latest .

docker-run:
	docker run -p 8080:8080 --env-file .env streaming-consumer:latest
EOF
