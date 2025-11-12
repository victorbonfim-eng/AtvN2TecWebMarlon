import json
import boto3
from datetime import datetime
from typing import Dict, Any
import os

# Clientes AWS
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

# Variáveis de ambiente
DYNAMODB_TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'tickets')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')

def process_ticket(ticket_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processa o ticket e determina se será aceito ou não.
    
    Regras de negócio:
    - Verifica se o aparelho está na garantia (máximo 12 meses)
    - Verifica se tem nota fiscal válida
    - Verifica se o número de série é válido
    """
    status = 'PENDENTE'
    motivo = ''
    
    try:
        # Verifica garantia (máximo 12 meses)
        data_compra = ticket_data['aparelho'].get('data_compra')
        if data_compra:
            data_compra_obj = datetime.fromisoformat(data_compra.replace('Z', '+00:00'))
            meses_garantia = (datetime.utcnow() - data_compra_obj.replace(tzinfo=None)).days / 30
            
            if meses_garantia > 12:
                status = 'REJEITADO'
                motivo = f'Aparelho fora da garantia. Comprado há {meses_garantia:.1f} meses.'
                return {'status': status, 'motivo': motivo}
        
        # Verifica nota fiscal
        nota_fiscal = ticket_data['aparelho'].get('nota_fiscal', '')
        if not nota_fiscal or len(nota_fiscal.strip()) == 0:
            status = 'REJEITADO'
            motivo = 'Nota fiscal não informada ou inválida.'
            return {'status': status, 'motivo': motivo}
        
        # Verifica número de série
        numero_serie = ticket_data['aparelho'].get('numero_serie', '')
        if not numero_serie or len(numero_serie.strip()) < 5:
            status = 'REJEITADO'
            motivo = 'Número de série inválido ou não informado.'
            return {'status': status, 'motivo': motivo}
        
        # Se passou em todas as validações, aceita
        status = 'ACEITO'
        motivo = 'Ticket aprovado. Aparelho elegível para troca na garantia.'
        
    except Exception as e:
        status = 'REJEITADO'
        motivo = f'Erro ao processar validações: {str(e)}'
    
    return {'status': status, 'motivo': motivo}

def save_to_dynamodb(table, ticket_data: Dict[str, Any], processamento: Dict[str, Any]):
    """
    Salva ou atualiza o ticket no DynamoDB.
    """
    try:
        item = {
            'ticket_id': ticket_data['ticket_id'],
            'status': processamento['status'],
            'data_abertura': ticket_data['data_abertura'],
            'data_processamento': datetime.utcnow().isoformat(),
            'nome_completo': ticket_data['nome_completo'],
            'cpf': ticket_data['cpf'],
            'email': ticket_data['email'],
            'telefone': ticket_data['telefone'],
            'endereco': ticket_data['endereco'],
            'aparelho': ticket_data['aparelho'],
            'observacoes': ticket_data.get('observacoes', ''),
            'motivo_processamento': processamento['motivo'],
            'updated_at': datetime.utcnow().isoformat()
        }
        
        table.put_item(Item=item)
        return True
    except Exception as e:
        print(f"Erro ao salvar no DynamoDB: {str(e)}")
        return False

def notify_user(ticket_data: Dict[str, Any], processamento: Dict[str, Any]):
    """
    Envia notificação ao usuário via SNS.
    """
    if not SNS_TOPIC_ARN:
        print("SNS_TOPIC_ARN não configurado. Pulando notificação.")
        return
    
    try:
        subject = f"Status do Ticket #{ticket_data['ticket_id'][:8]}"
        
        message = f"""
Olá {ticket_data['nome_completo']},

Seu ticket de troca de aparelho foi processado.

ID do Ticket: {ticket_data['ticket_id']}
Status: {processamento['status']}
Motivo: {processamento['motivo']}

Aparelho: {ticket_data['aparelho'].get('marca')} {ticket_data['aparelho'].get('modelo')}
Número de Série: {ticket_data['aparelho'].get('numero_serie')}

Data de Abertura: {ticket_data['data_abertura']}

Em caso de dúvidas, entre em contato conosco.

Atenciosamente,
Equipe de Garantia
        """
        
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message,
            Subject=subject,
            MessageAttributes={
                'ticket_id': {
                    'DataType': 'String',
                    'StringValue': ticket_data['ticket_id']
                },
                'status': {
                    'DataType': 'String',
                    'StringValue': processamento['status']
                },
                'email': {
                    'DataType': 'String',
                    'StringValue': ticket_data['email']
                }
            }
        )
        
        print(f"Notificação enviada para {ticket_data['email']}")
    
    except Exception as e:
        print(f"Erro ao enviar notificação: {str(e)}")

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handler principal da Lambda PROCESSAMENTO_TICKET.
    
    Processa mensagens da fila SQS, valida tickets e notifica usuários.
    """
    table = dynamodb.Table(DYNAMODB_TABLE_NAME)
    
    # Processa cada record da fila SQS
    for record in event.get('Records', []):
        try:
            # Extrai o body da mensagem SQS
            body = json.loads(record['body'])
            ticket_data = body if isinstance(body, dict) else json.loads(body)
            
            print(f"Processando ticket: {ticket_data.get('ticket_id')}")
            
            # Processa o ticket (validações de negócio)
            processamento = process_ticket(ticket_data)
            
            # Atualiza status no ticket
            ticket_data['status'] = processamento['status']
            ticket_data['data_processamento'] = datetime.utcnow().isoformat()
            ticket_data['motivo_processamento'] = processamento['motivo']
            
            # Salva no DynamoDB
            save_to_dynamodb(table, ticket_data, processamento)
            
            # Notifica o usuário via SNS
            notify_user(ticket_data, processamento)
            
            print(f"Ticket {ticket_data.get('ticket_id')} processado com status: {processamento['status']}")
        
        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar JSON da mensagem SQS: {str(e)}")
            continue
        
        except Exception as e:
            print(f"Erro ao processar record: {str(e)}")
            continue
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Tickets processados com sucesso',
            'processed': len(event.get('Records', []))
        })
    }

