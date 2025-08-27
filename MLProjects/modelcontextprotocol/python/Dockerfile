FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY mcp_stock_server.py .

RUN mkdir -p logs

ENV MCP_SERVER_NAME="AILearning_DockerStockServer"
ENV MCP_SERVER_SOURCE="Docker_YFinance_Server"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import yfinance; import mcp; print('OK')" || exit 1

CMD ["python", "mcp_stock_server.py"]
