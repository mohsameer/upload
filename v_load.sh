#/bin/sh


VAULT_HOST=${GLUU_VAULT_HOST:=localhost}
VAULT_PORT=${GLUU_VAULT_PORT:=8200}

CONFIG_FILES=./consul/*
VAULT_FILES=./vault/*
VAULT_TOKEN=$1


for f in $VAULT_FILES
do
  FILENAME=$(echo "$f" | sed "s/.*\///")
  echo "Processing $FILENAME file to vault..."
  VALUE=$(base64 $f -w0)
  curl -v -H "X-Vault-Token: ${VAULT_TOKEN}" -X POST -d "{\"value\":\"$VALUE\"}" http://${VAULT_HOST}:${VAULT_PORT}/v1/secret/icrypto/${FILENAME}
done
