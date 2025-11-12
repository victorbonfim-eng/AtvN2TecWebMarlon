.PHONY: install build deploy test clean

# Instalar dependências
install:
	cd lambda_abre_ticket && pip install -r requirements.txt -t .
	cd lambda_processamento_ticket && pip install -r requirements.txt -t .

# Build do projeto SAM
build:
	sam build

# Deploy do projeto
deploy:
	sam deploy

# Deploy guiado (primeira vez)
deploy-guided:
	sam deploy --guided

# Testar localmente
test-abre:
	sam local invoke AbreTicketFunction -e events/test-abre-ticket.json

test-processamento:
	sam local invoke ProcessamentoTicketFunction -e events/test-processamento-ticket.json

# Limpar arquivos temporários
clean:
	rm -rf .aws-sam
	rm -rf lambda_abre_ticket/__pycache__
	rm -rf lambda_processamento_ticket/__pycache__
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

