import json
import boto3
import uuid
from datetime import datetime
from typing import Dict, Any, Tuple
import os

# Clientes AWS
sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')

# Variáveis de ambiente
QUEUE_URL = os.environ.get('QUEUE_URL')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'tickets')

def validate_required_fields(data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Valida os campos obrigatórios para abertura de ticket.
    
    Retorna: (is_valid, error_message)
    """
    required_fields = {
        'nome_completo': str,
        'cpf': str,
        'email': str,
        'telefone': str,
        'endereco': dict,
        'aparelho': dict
    }
    
    # Valida campos principais
    for field, field_type in required_fields.items():
        if field not in data:
            return False, f"Campo obrigatório ausente: {field}"
        
        if not isinstance(data[field], field_type):
            return False, f"Campo {field} deve ser do tipo {field_type.__name__}"
    
    # Valida estrutura do endereço
    endereco_fields = ['rua', 'numero', 'cidade', 'estado', 'cep']
    for field in endereco_fields:
        if field not in data['endereco']:
            return False, f"Campo obrigatório no endereço: {field}"
    
    # Valida estrutura do aparelho
    aparelho_fields = ['marca', 'modelo', 'numero_serie', 'data_compra', 'nota_fiscal']
    for field in aparelho_fields:
        if field not in data['aparelho']:
            return False, f"Campo obrigatório no aparelho: {field}"
    
    # Valida formato de CPF (básico)
    cpf = data['cpf'].replace('.', '').replace('-', '')
    if len(cpf) != 11 or not cpf.isdigit():
        return False, "CPF inválido"
    
    # Valida formato de email (básico)
    if '@' not in data['email'] or '.' not in data['email'].split('@')[1]:
        return False, "Email inválido"
    
    return True, ""

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handler principal da Lambda ABRE_TICKET.
    
    Recebe dados do ticket via API Gateway e envia para fila SQS.
    """
    try:
        # Extrai o body da requisição
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        # Valida campos obrigatórios
        is_valid, error_message = validate_required_fields(body)
        if not is_valid:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'message': error_message
                })
            }
        
        # Gera ID único para o ticket
        ticket_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Monta objeto do ticket
        ticket_data = {
            'ticket_id': ticket_id,
            'status': 'PENDENTE',
            'data_abertura': timestamp,
            'nome_completo': body['nome_completo'],
            'cpf': body['cpf'],
            'email': body['email'],
            'telefone': body['telefone'],
            'endereco': body['endereco'],
            'aparelho': body['aparelho'],
            'observacoes': body.get('observacoes', ''),
            'created_at': timestamp
        }
        
        # Envia para fila SQS
        if QUEUE_URL:
            response = sqs.send_message(
                QueueUrl=QUEUE_URL,
                MessageBody=json.dumps(ticket_data),
                MessageAttributes={
                    'ticket_id': {
                        'StringValue': ticket_id,
                        'DataType': 'String'
                    },
                    'status': {
                        'StringValue': 'PENDENTE',
                        'DataType': 'String'
                    }
                }
            )
            
            return {
                'statusCode': 201,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': True,
                    'message': 'Ticket criado com sucesso',
                    'ticket_id': ticket_id,
                    'status': 'PENDENTE',
                    'sqs_message_id': response.get('MessageId')
                })
            }
        else:
            # Modo de desenvolvimento - apenas retorna sucesso
            return {
                'statusCode': 201,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': True,
                    'message': 'Ticket criado com sucesso (modo desenvolvimento)',
                    'ticket_id': ticket_id,
                    'status': 'PENDENTE',
                    'ticket_data': ticket_data
                })
            }
    
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'message': 'JSON inválido no body da requisição'
            })
        }
    
    except Exception as e:
        print(f"Erro ao processar ticket: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'message': f'Erro interno do servidor: {str(e)}'
            })
        }

