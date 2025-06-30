# #!/bin/sh

# echo "Insert cert"
# openssl x509 -in <(openssl s_client -connect $DOMAIN:443 -prexit 2>/dev/null) -out /tmp/server-name.crt
# keytool -importcert -noprompt -file /tmp/server-name.crt -alias server-name -keystore $JAVA_HOME/lib/security/cacerts -storepass changeit