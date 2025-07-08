# API GLPI Tickets

API para consultar tickets do GLPI com filtros por usuário, ano e status.

## 🚀 Deploy no Render

### Configuração Automática (Recomendado)

1. **Fork ou clone este repositório**
2. **Conecte ao Render:**
   - Acesse [render.com](https://render.com)
   - Clique em "New +" → "Web Service"
   - Conecte seu repositório GitHub
   - Selecione este repositório

3. **Configure o serviço:**
   - **Name:** `glpi-tickets-api` (ou qualquer nome)
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

4. **Configure as variáveis de ambiente (opcional):**
   - Se quiser usar variáveis de ambiente para as credenciais do banco, adicione-as no painel do Render

5. **Deploy:**
   - Clique em "Create Web Service"
   - Aguarde o build e deploy

### Configuração Manual

Se preferir configurar manualmente:

1. Crie um novo Web Service no Render
2. Use as configurações do arquivo `render.yaml`
3. Configure as variáveis de ambiente conforme necessário

## 📋 Endpoints da API

### Endpoints Principais

- **`GET /`** - Documentação e lista de endpoints
- **`GET /tickets/{user_id}/{ano}`** - Todos os tickets de um usuário em um ano
- **`GET /tickets/aberto/{user_id}/{ano}`** - Tickets abertos (status < 4)
- **`GET /tickets/fechado/{user_id}/{ano}`** - Tickets fechados (status > 3)
- **`GET /ticketuser/{id}`** - Tickets de um usuário (tabela glpi_tickets_users)
- **`GET /ticketuser/{id}?status=aberto`** - Tickets abertos de um usuário
- **`GET /ticketuser/{id}?status=fechado`** - Tickets fechados de um usuário

### Endpoints de Debug

- **`GET /debug/ticket/{ticket_id}`** - Verificar status de um ticket específico
- **`GET /debug/user/{user_id}/tickets`** - Listar todos os tickets de um usuário com status

## 🔧 Configuração Local

1. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Execute a aplicação:**
   ```bash
   python main.py
   ```

3. **Acesse a API:**
   - URL: `http://localhost:8000`
   - Documentação: `http://localhost:8000/docs`

## 📊 Estrutura do Banco de Dados

A API se conecta às seguintes tabelas do GLPI:
- `glpi_tickets` - Dados principais dos tickets
- `glpi_tickets_users` - Relacionamento entre tickets e usuários

## 🔒 Segurança

⚠️ **Importante:** As credenciais do banco de dados estão hardcoded no código. Para produção, recomenda-se:

1. Usar variáveis de ambiente
2. Implementar autenticação
3. Usar HTTPS
4. Configurar CORS adequadamente

## 📝 Exemplos de Uso

```bash
# Obter todos os tickets do usuário 9 em 2024
curl "https://sua-api.onrender.com/tickets/9/2024"

# Obter tickets abertos do usuário 9
curl "https://sua-api.onrender.com/ticketuser/9?status=aberto"

# Verificar status do ticket 689
curl "https://sua-api.onrender.com/debug/ticket/689"
```

## 🛠️ Tecnologias

- **FastAPI** - Framework web
- **Uvicorn** - Servidor ASGI
- **MySQL Connector** - Conexão com banco MySQL
- **Pydantic** - Validação de dados 