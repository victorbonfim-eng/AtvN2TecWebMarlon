# Sistema de Tickets de Troca de Aparelhos na Garantia

Sistema serverless desenvolvido na AWS para gerenciamento de tickets de troca de aparelhos celulares na garantia, seguindo as melhores práticas de computação em nuvem, baixo custo e escalabilidade.

## 🏗️ Arquitetura

### Diagrama da Arquitetura

![Arquitetura do Sistema](arq/Captura%20de%20Tela%202025-11-11%20às%2020.55.04.png)

> **Nota:** O diagrama acima ilustra o fluxo completo do sistema, desde a requisição do usuário até a notificação final.

### Fluxo do Sistema

```
👤 Usuário
  ↓
🌐 API Gateway
  ↓
⚡ Lambda ABRE_TICKET
  ↓
📬 SQS (TICKETS_PENDENTES)
  ↓
⚡ Lambda PROCESSAMENTO_TICKET
  ↓
💾 DynamoDB          📧 SNS (NOTIFICA_USER)
```

### Componentes

| Componente | Descrição | Responsabilidade |
|------------|-----------|------------------|
| **🌐 API Gateway** | Endpoint REST | Recebe requisições HTTP e roteia para Lambda |
| **⚡ ABRE_TICKET** | Lambda Function | Valida dados e cria tickets na fila |
| **📬 TICKETS_PENDENTES** | SQS Queue | Fila assíncrona para processamento |
| **⚡ PROCESSAMENTO_TICKET** | Lambda Function | Processa tickets e aplica regras de negócio |
| **💾 DynamoDB** | NoSQL Database | Armazena tickets processados |
| **📧 NOTIFICA_USER** | SNS Topic | Envia notificações por email aos usuários |

## 📋 Pré-requisitos

- AWS CLI configurado
- AWS SAM CLI instalado
- Python 3.11
- Conta AWS com permissões adequadas

## 🚀 Deploy

### 1. Instalar dependências

```bash
# Instalar dependências da Lambda ABRE_TICKET
cd lambda_abre_ticket
pip install -r requirements.txt -t .

# Instalar dependências da Lambda PROCESSAMENTO_TICKET
cd ../lambda_processamento_ticket
pip install -r requirements.txt -t .
cd ..
```

### 2. Build e Deploy com SAM

```bash
# Build do projeto
sam build

# Deploy (primeira vez)
sam deploy --guided

# Deploy subsequente
sam deploy
```

### 3. Configurar Email no SNS

Após o deploy, você receberá um email de confirmação do SNS. Confirme a assinatura para receber notificações.

## 📝 Uso da API

### Criar um Ticket

```bash
curl -X POST https://<api-id>.execute-api.<region>.amazonaws.com/dev/tickets \
  -H "Content-Type: application/json" \
  -d '{
    "nome_completo": "João Silva Santos",
    "cpf": "123.456.789-00",
    "email": "joao.silva@email.com",
    "telefone": "(11) 98765-4321",
    "endereco": {
      "rua": "Rua das Flores",
      "numero": "123",
      "complemento": "Apto 45",
      "bairro": "Centro",
      "cidade": "São Paulo",
      "estado": "SP",
      "cep": "01234-567"
    },
    "aparelho": {
      "marca": "Samsung",
      "modelo": "Galaxy S21",
      "numero_serie": "SN123456789012",
      "data_compra": "2023-11-20T00:00:00.000Z",
      "nota_fiscal": "NF-2023-001234",
      "defeito_relatado": "Tela com manchas e não liga mais"
    },
    "observacoes": "Aparelho parou de funcionar após 2 meses de uso normal."
  }'
```

### Campos Obrigatórios

- `nome_completo`: Nome completo do cliente
- `cpf`: CPF válido (formato: XXX.XXX.XXX-XX)
- `email`: Email válido
- `telefone`: Telefone de contato
- `endereco`: Objeto com:
  - `rua`: Nome da rua
  - `numero`: Número do endereço
  - `cidade`: Cidade
  - `estado`: Estado (UF)
  - `cep`: CEP
- `aparelho`: Objeto com:
  - `marca`: Marca do aparelho
  - `modelo`: Modelo do aparelho
  - `numero_serie`: Número de série (mínimo 5 caracteres)
  - `data_compra`: Data de compra (ISO 8601)
  - `nota_fiscal`: Número da nota fiscal

## 🔍 Regras de Negócio

O sistema valida os seguintes critérios para aceitar um ticket:

1. **Garantia**: Aparelho deve ter sido comprado há menos de 12 meses
2. **Nota Fiscal**: Deve ser informada e válida
3. **Número de Série**: Deve ser informado e ter pelo menos 5 caracteres

## 📊 Dados de Exemplo

O arquivo `dynamodb_data/tickets.json` contém exemplos de tickets simulando dados reais do DynamoDB.

## 🧪 Testes Locais

### Testar Lambda ABRE_TICKET

```bash
sam local invoke AbreTicketFunction -e events/test-abre-ticket.json
```

### Testar Lambda PROCESSAMENTO_TICKET

```bash
sam local invoke ProcessamentoTicketFunction -e events/test-processamento-ticket.json
```

## 📁 Estrutura do Projeto

```
.
├── lambda_abre_ticket/
│   ├── lambda_function.py
│   └── requirements.txt
├── lambda_processamento_ticket/
│   ├── lambda_function.py
│   └── requirements.txt
├── dynamodb_data/
│   └── tickets.json
├── template.yaml
└── README.md
```

## 💰 Custos

Este sistema utiliza serviços serverless da AWS com modelo pay-per-use:

- **API Gateway**: $3.50 por milhão de requisições
- **Lambda**: $0.20 por milhão de requisições + $0.0000166667 por GB-segundo
- **SQS**: Primeiros 1 milhão de requisições grátis, depois $0.40 por milhão
- **DynamoDB**: On-demand billing, $1.25 por milhão de writes, $0.25 por milhão de reads
- **SNS**: $0.50 por 100.000 notificações

Para volumes baixos a médios, o custo mensal é muito baixo.

## 🔒 Segurança

- Validação de dados de entrada
- CORS configurado no API Gateway
- IAM roles com permissões mínimas necessárias
- Validação de CPF e email

## 📈 Escalabilidade

- Arquitetura totalmente serverless
- Processamento assíncrono via SQS
- DynamoDB com auto-scaling
- Lambda com auto-scaling automático

## 🛠️ Melhorias Futuras

- [ ] Adicionar autenticação/autorização (Cognito)
- [ ] Implementar API de consulta de tickets
- [ ] Adicionar métricas e alertas (CloudWatch)
- [ ] Implementar retry logic para falhas
- [ ] Adicionar testes unitários
- [ ] Implementar versionamento de API

## 📄 Licença

Este projeto é um exemplo educacional.

