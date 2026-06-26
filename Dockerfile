FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cloud Run sets $PORT; this default runs the chat API.
# For full deployment, run mcp_server and chat_api as two separate
# Cloud Run services and point chat_api's MCP_SERVER_URL at the deployed
# mcp_server's public URL.
ENV PORT=8080
EXPOSE 8080

CMD ["python", "agents/chat_api.py"]
