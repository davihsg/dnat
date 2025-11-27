#!/bin/bash
# Generate client certificate for CAS authentication

cd "$(dirname "$0")"

if [[ -f client.crt && -f client.key ]]; then
    echo "Certificates already exist"
    exit 0
fi

echo "Generating client certificate for CAS..."
openssl req -x509 -newkey rsa:4096 \
    -out client.crt \
    -keyout client.key \
    -days 365 -nodes -sha256 \
    -subj "/CN=dnat-executor"

echo "Certificate generated:"
echo "  client.crt"
echo "  client.key"

