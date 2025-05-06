#!/bin/bash

ICRYPTO_OIDC_FILTER_VERSION=1.0.0.81
LIBS_DOWNLOAD_PATH=/tmp/downloaded
CUSTOM_LIBS_PATH=/opt/jans/jetty/jans-auth/custom/libs



download_lib () {
  if [ ! -f $LIBS_DOWNLOAD_PATH/$1 ]; then
    wget -nc -q -O "$LIBS_DOWNLOAD_PATH/$1" "$2"
  else
    echo "Skip download $1"
  fi
}

echo "Installing Icrypto files"

if [ ! -d $LIBS_DOWNLOAD_PATH ]; then
  echo "Folder $LIBS_DOWNLOAD_PATH does not exist, creating"
  mkdir -p $LIBS_DOWNLOAD_PATH
fi

ls -l $LIBS_DOWNLOAD_PATH

download_lib "jans-orm-couchbase-libs-1.0.21-distribution.zip" "https://jenkins.jans.io/maven/io/jans/jans-orm-couchbase-libs/1.0.21/jans-orm-couchbase-libs-1.0.21-distribution.zip"

download_lib "opentelemetry-javaagent.jar" "https://github.com/open-telemetry/opentelemetry-java-instrumentation/releases/download/v1.29.0/opentelemetry-javaagent.jar"
download_lib "opentelemetry-api-1.29.0.jar" "https://repo1.maven.org/maven2/io/opentelemetry/opentelemetry-api/1.29.0/opentelemetry-api-1.29.0.jar"
download_lib "opentelemetry-context-1.29.0.jar" "https://repo1.maven.org/maven2/io/opentelemetry/opentelemetry-context/1.29.0/opentelemetry-context-1.29.0.jar"
download_lib "jackson-core-2.13.4.jar" "https://repo1.maven.org/maven2/com/fasterxml/jackson/core/jackson-core/2.13.4/jackson-core-2.13.4.jar"
download_lib "jackson-databind-2.13.4.jar" "https://repo1.maven.org/maven2/com/fasterxml/jackson/core/jackson-databind/2.13.4/jackson-databind-2.13.4.jar"
download_lib "jackson-annotations-2.13.4.jar" "https://repo1.maven.org/maven2/com/fasterxml/jackson/core/jackson-annotations/2.13.4/jackson-annotations-2.13.4.jar"
download_lib "icrypto-oidc-filter-$ICRYPTO_OIDC_FILTER_VERSION.jar" "https://icrypto-cdn.s3.amazonaws.com/lib/oidc-filter/icrypto-oidc-filter-$ICRYPTO_OIDC_FILTER_VERSION.jar"

echo "All files downloaded"

cp $LIBS_DOWNLOAD_PATH/jans-orm-couchbase-libs-1.0.21-distribution.zip /usr/share/java/couchbase-libs.zip
cp $LIBS_DOWNLOAD_PATH/opentelemetry-javaagent.jar /usr/share/java/opentelemetry-javaagent.jar
cp $LIBS_DOWNLOAD_PATH/opentelemetry-api-1.29.0.jar $CUSTOM_LIBS_PATH/opentelemetry-api-1.29.0.jar
cp $LIBS_DOWNLOAD_PATH/opentelemetry-context-1.29.0.jar $CUSTOM_LIBS_PATH/opentelemetry-context-1.29.0.jar
cp $LIBS_DOWNLOAD_PATH/jackson-core-2.13.4.jar $CUSTOM_LIBS_PATH/jackson-core-2.13.4.jar
cp $LIBS_DOWNLOAD_PATH/jackson-databind-2.13.4.jar $CUSTOM_LIBS_PATH/jackson-databind-2.13.4.jar
cp $LIBS_DOWNLOAD_PATH/jackson-annotations-2.13.4.jar $CUSTOM_LIBS_PATH/jackson-annotations-2.13.4.jar
cp $LIBS_DOWNLOAD_PATH/icrypto-oidc-filter-$ICRYPTO_OIDC_FILTER_VERSION.jar $CUSTOM_LIBS_PATH/icrypto-oidc-filter-$ICRYPTO_OIDC_FILTER_VERSION.jar

#echo "Insert cert"
#openssl x509 -in <(openssl s_client -connect $DOMAIN:443 -prexit 2>/dev/null) -out /tmp/server-name.crt
#keytool -importcert -noprompt -file /tmp/server-name.crt -alias server-name -keystore $JAVA_HOME/lib/security/cacerts -storepass changeit

# Changing the oidc context, needs to be this way
#sed  's,>/jans-auth<,>/oidc<,g' /opt/jans/jetty/jans-auth/webapps/jans-auth.xml > /tmp/jans-auth.xml
#cat /tmp/jans-auth.xml > /opt/jans/jetty/jans-auth/webapps/jans-auth.xml
#rm /tmp/jans-auth.xml
