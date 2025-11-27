# DNAT Executor API
# This service orchestrates execution requests and communicates with SGX enclaves

FROM python:3.10-slim

WORKDIR /app

# Install curl for CAS uploads
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY enclave/ ./enclave/

# Environment variables
ENV PORT=8080
ENV DEBUG=false
ENV BLOCKCHAIN_RPC=http://host.docker.internal:8545
ENV IPFS_GATEWAY=http://host.docker.internal:5001/api/v0/cat
ENV ENCLAVE_PATH=/app/enclave

EXPOSE 8080

CMD ["python", "app.py"]

