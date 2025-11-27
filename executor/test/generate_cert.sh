#!/bin/bash
# Generate client certificate for CAS authentication

mkdir -p conf
openssl req -x509 -newkey rsa:4096 \
  -out conf/client.crt \
  -keyout conf/client.key \
  -days 365 -nodes -sha256 \
  -subj "/CN=dnat-client"

echo "Certificate generated:"
echo "  conf/client.crt"
echo "  conf/client.key"

