#!/bin/bash

APPNAME=$1
CLIENTID=$2
CONSUL_TOKEN="d94572a7-eb4c-5f5b-7548-ca399b95c1ff"
VAULT_TOKEN="s.WFKuhq08ehr8KriI8XzVvMzM"

CONSUL_URL="http://localhost:8500/v1/kv/oidc-v2/clients/"
VAULT_URL="http://localhost:8200/v1/secret/oidcv2/"
VAULT_URL_BASE="http://localhost:8200/v1/"

mkdir ${APPNAME}
cp clientjsontemplate.json ${APPNAME}/${APPNAME}.json
cp client.prop ${APPNAME}/${APPNAME}-client.prop

if [ -f "${APPNAME}/secret.txt" ]; then
  echo "secret file exists"
else
  echo "Create Secret and Upload to vault"
  python3 encrypt.py > ${APPNAME}/secret.txt
fi

cd ${APPNAME}

client_secret=$(sed -n '1p' "secret.txt")
echo $client_secret

echo "Replace Appname in ${APPNAME}.json"
sed -i "s/APPNAME/${APPNAME}/g" "${APPNAME}.json"
echo "Replacement Complete"

echo "Replace Appname in ${APPNAME}-client.prop"
sed -i "s/APPNAME/${APPNAME}/g" "${APPNAME}-client.prop"
echo "Replacement Complete"

echo "Replace secret in ${APPNAME}-client.prop" 
sed -i "s/clientsecret/${client_secret}/g" "${APPNAME}-client.prop" 
echo "Replacement Complete"

echo "Load client.json to consul"
curl -X PUT --header "X-Consul-Token: $CONSUL_TOKEN" --data-binary @${APPNAME}.json $CONSUL_URL${APPNAME}.json

echo "Loading clientID to vault"
payloadclient='{"'value'": "'"$CLIENTID"'"}'
curl -H "X-Vault-Token: $VAULT_TOKEN" --request POST --data "$payloadclient" http://localhost:8200/v1/secret/oidcv2/$APPNAME-clientId

echo "Loading secret to vault"
payloadsecret='{"'value'": "'"${client_secre}t"'"}'
curl -H "X-Vault-Token: $VAULT_TOKEN" --request POST --data "$payloadsecret" http://localhost:8200/v1/secret/oidcv2/$APPNAME-clientSecret

cat ${APPNAME}-client.prop | jq -r '. | to_entries[] | "\(.key) \(.value | @json)"' | while read -r key value; do
    echo "Loading key=$key, value=$value"
    curl \
        -H "X-Vault-Token: $VAULT_TOKEN" \
        -H "Content-Type: application/json" \
        -X POST \
        -d "{\"value\":$value}" \
        $VAULT_URL_BASE$key
done
