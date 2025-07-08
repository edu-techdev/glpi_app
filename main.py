from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict
import mysql.connector
import asyncio
from typing import List, Dict, Any
import uvicorn
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="API GLPI Tickets", description="API para consultar tickets do GLPI")

# Configurações do banco de dados
host = os.getenv("DB_HOST")
dbname = os.getenv("DB_NAME")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
port = int(os.getenv("DB_PORT", 3306))

class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    content: str
    date: str
    status: int
    priority: int
    users_id_recipient: int
    users_id_lastupdater: int
    date_mod: str
    date_creation: str

def conectar_bd():
    try:
        conexao = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=dbname,
            port=port
        )
        return conexao
    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao banco de dados: {err}")
        return None

async def buscar_tickets_por_usuario_ano(user_id: int, ano: int, status_filter: str = None) -> List[Dict[str, Any]]:
    conexao = conectar_bd()
    if conexao is None:
        raise HTTPException(status_code=500, detail="Erro ao conectar ao banco de dados")
    
    cursor = conexao.cursor(dictionary=True)
    try:
        # Construir query base
        query = """
        SELECT id, name, content, date, status, priority, 
               users_id_recipient, users_id_lastupdater, 
               date_mod, date_creation
        FROM glpi_tickets 
        WHERE users_id_recipient = %s 
        AND YEAR(date_creation) = %s
        """
        
        params = [user_id, ano]
        
        # Adicionar filtro de status se especificado
        if status_filter == "aberto":
            query += " AND status < 4"
        elif status_filter == "fechado":
            query += " AND status > 3"
        
        query += " ORDER BY date_creation DESC"
        
        cursor.execute(query, params)
        resultados = cursor.fetchall()
        
        # Converter objetos datetime para strings ISO de forma mais robusta
        resultados_processados = []
        for resultado in resultados:
            resultado_processado = {}
            for chave, valor in resultado.items():
                if isinstance(valor, datetime):
                    resultado_processado[chave] = valor.isoformat()
                else:
                    resultado_processado[chave] = valor
            resultados_processados.append(resultado_processado)
        
        return resultados_processados
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Erro ao executar consulta: {err}")
    finally:
        cursor.close()
        conexao.close()

@app.get("/tickets/aberto/{user_id}/{ano}")
async def obter_tickets_abertos(user_id: int, ano: int):
    """
    Retorna os tickets abertos (status < 4) de um usuário específico em um ano específico
    """
    tickets = await buscar_tickets_por_usuario_ano(user_id, ano, "aberto")
    return tickets

@app.get("/tickets/fechado/{user_id}/{ano}")
async def obter_tickets_fechados(user_id: int, ano: int):
    """
    Retorna os tickets fechados (status > 3) de um usuário específico em um ano específico
    """
    tickets = await buscar_tickets_por_usuario_ano(user_id, ano, "fechado")
    return tickets

@app.get("/tickets/{user_id}/{ano}")
async def obter_tickets(user_id: int, ano: int):
    """
    Retorna os tickets de um usuário específico em um ano específico
    """
    tickets = await buscar_tickets_por_usuario_ano(user_id, ano)
    return tickets

@app.get("/ticketvinculo/{user_id}")
async def obter_tickets_vinculo(user_id: int):
    """
    Retorna os tickets_id da tabela glpi_tickets_users onde users_id = user_id e type = 2
    """
    conexao = conectar_bd()
    if conexao is None:
        raise HTTPException(status_code=500, detail="Erro ao conectar ao banco de dados")
    cursor = conexao.cursor(dictionary=True)
    try:
        query = """
        SELECT tickets_id FROM glpi_tickets_users
        WHERE users_id = %s AND type = 2
        """
        cursor.execute(query, (user_id,))
        resultados = cursor.fetchall()
        tickets_ids = [row['tickets_id'] for row in resultados]
        return {"tickets_id": tickets_ids}
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Erro ao executar consulta: {err}")
    finally:
        cursor.close()
        conexao.close()

@app.get("/ticketuser/{id}")
async def obter_tickets_user(id: int, status: str = None):
    """
    Retorna os tickets_id da tabela glpi_tickets_users onde users_id = id e type = 2
    Pode filtrar por status: 'aberto' (status < 4) ou 'fechado' (status > 3)
    """
    conexao = conectar_bd()
    if conexao is None:
        raise HTTPException(status_code=500, detail="Erro ao conectar ao banco de dados")
    cursor = conexao.cursor(dictionary=True)
    try:
        # Primeiro, buscar os tickets_id da tabela glpi_tickets_users
        query_users = """
        SELECT tickets_id FROM glpi_tickets_users
        WHERE users_id = %s AND type = 2
        """
        cursor.execute(query_users, (id,))
        resultados_users = cursor.fetchall()
        tickets_ids = [row['tickets_id'] for row in resultados_users]
        
        if not tickets_ids:
            return {"tickets_id": []}
        
        # Se há filtro de status, buscar na tabela glpi_tickets
        if status:
            if status.lower() == "aberto":
                query_tickets = """
                SELECT * FROM glpi_tickets 
                WHERE id IN ({}) AND status < 4
                ORDER BY date_creation DESC
                """.format(','.join(['%s'] * len(tickets_ids)))
            elif status.lower() == "fechado":
                query_tickets = """
                SELECT * FROM glpi_tickets 
                WHERE id IN ({}) AND status > 3
                ORDER BY date_creation DESC
                """.format(','.join(['%s'] * len(tickets_ids)))
            else:
                raise HTTPException(status_code=400, detail="Status deve ser 'aberto' ou 'fechado'")
            
            cursor.execute(query_tickets, tickets_ids)
            resultados_tickets = cursor.fetchall()
            
            # Converter objetos datetime para strings ISO
            tickets_processados = []
            for resultado in resultados_tickets:
                ticket_processado = {}
                for chave, valor in resultado.items():
                    if isinstance(valor, datetime):
                        ticket_processado[chave] = valor.isoformat()
                    else:
                        ticket_processado[chave] = valor
                tickets_processados.append(ticket_processado)
            
            return {"tickets": tickets_processados}
        
        # Se não há filtro de status, retornar apenas os IDs
        return {"tickets_id": tickets_ids}
        
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Erro ao executar consulta: {err}")
    finally:
        cursor.close()
        conexao.close()

@app.get("/debug/ticket/{ticket_id}")
async def debug_ticket_status(ticket_id: int):
    """
    Rota de debug para verificar o status de um ticket específico
    """
    conexao = conectar_bd()
    if conexao is None:
        raise HTTPException(status_code=500, detail="Erro ao conectar ao banco de dados")
    cursor = conexao.cursor(dictionary=True)
    try:
        query = """
        SELECT id, name, status, date_creation, date_mod
        FROM glpi_tickets 
        WHERE id = %s
        """
        cursor.execute(query, (ticket_id,))
        resultado = cursor.fetchone()
        
        if not resultado:
            return {"error": f"Ticket {ticket_id} não encontrado"}
        
        # Converter datetime para string
        if resultado.get('date_creation') and isinstance(resultado['date_creation'], datetime):
            resultado['date_creation'] = resultado['date_creation'].isoformat()
        if resultado.get('date_mod') and isinstance(resultado['date_mod'], datetime):
            resultado['date_mod'] = resultado['date_mod'].isoformat()
        
        # Adicionar classificação do status
        status = int(resultado['status'])
        if status < 4:
            resultado['classificacao'] = "aberto"
        elif status > 3:
            resultado['classificacao'] = "fechado"
        else:
            resultado['classificacao'] = "status_invalido"
        
        return resultado
        
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Erro ao executar consulta: {err}")
    finally:
        cursor.close()
        conexao.close()

@app.get("/debug/user/{user_id}/tickets")
async def debug_user_tickets(user_id: int):
    """
    Rota de debug para listar todos os tickets de um usuário com seus status
    """
    conexao = conectar_bd()
    if conexao is None:
        raise HTTPException(status_code=500, detail="Erro ao conectar ao banco de dados")
    cursor = conexao.cursor(dictionary=True)
    try:
        # Primeiro, buscar os tickets_id da tabela glpi_tickets_users
        query_users = """
        SELECT tickets_id FROM glpi_tickets_users
        WHERE users_id = %s AND type = 2
        """
        cursor.execute(query_users, (user_id,))
        resultados_users = cursor.fetchall()
        tickets_ids = [row['tickets_id'] for row in resultados_users]
        
        if not tickets_ids:
            return {"tickets": []}
        
        # Buscar dados dos tickets
        query_tickets = """
        SELECT id, name, status, date_creation, date_mod
        FROM glpi_tickets 
        WHERE id IN ({})
        ORDER BY date_creation DESC
        """.format(','.join(['%s'] * len(tickets_ids)))
        
        cursor.execute(query_tickets, tickets_ids)
        resultados_tickets = cursor.fetchall()
        
        # Processar resultados
        tickets_processados = []
        for resultado in resultados_tickets:
            # Converter datetime para string
            if resultado.get('date_creation') and isinstance(resultado['date_creation'], datetime):
                resultado['date_creation'] = resultado['date_creation'].isoformat()
            if resultado.get('date_mod') and isinstance(resultado['date_mod'], datetime):
                resultado['date_mod'] = resultado['date_mod'].isoformat()
            
            # Adicionar classificação do status
            status = int(resultado['status'])
            if status < 4:
                resultado['classificacao'] = "aberto"
            elif status > 3:
                resultado['classificacao'] = "fechado"
            else:
                resultado['classificacao'] = "status_invalido"
            
            tickets_processados.append(resultado)
        
        return {"tickets": tickets_processados}
        
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Erro ao executar consulta: {err}")
    finally:
        cursor.close()
        conexao.close()

@app.get("/")
async def root():
    return {
        "message": "API GLPI Tickets",
        "endpoints": {
            "todos_tickets": "/tickets/{user_id}/{ano}",
            "tickets_abertos": "/tickets/aberto/{user_id}/{ano}",
            "tickets_fechados": "/tickets/fechado/{user_id}/{ano}",
            "tickets_user": "/ticketuser/{id}?status=aberto|fechado",
            "debug_ticket": "/debug/ticket/{ticket_id}",
            "debug_user_tickets": "/debug/user/{user_id}/tickets"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
