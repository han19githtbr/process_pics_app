.PHONY: help install-backend install-frontend dev-backend dev-frontend dev build test clean

help:  ## Mostra ajuda
	@echo "Comandos disponíveis:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install-backend:  ## Instala dependências do backend
	cd backend && pip install -r requirements.txt

install-frontend:  ## Instala dependências do frontend
	cd frontend && npm install

install: install-backend install-frontend  ## Instala todas as dependências

dev-backend:  ## Roda backend em modo desenvolvimento
	cd backend && python src/server.py

dev-frontend:  ## Roda frontend em modo desenvolvimento
	cd frontend && npm run dev

dev:  ## Roda ambos em modo desenvolvimento
	@echo "Iniciando backend e frontend..."
	@make -j2 dev-backend dev-frontend

build-frontend:  ## Build do frontend
	cd frontend && npm run build

build: build-frontend  ## Build de tudo

clean:  ## Limpa arquivos temporários
	rm -rf backend/__pycache__ backend/.pytest_cache
	rm -rf frontend/dist frontend/node_modules
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +