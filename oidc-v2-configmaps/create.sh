kubectl -n authn create configmap couchbase-setup-patch --from-file=./couchbase_setup.py
kubectl -n authn create configmap couchbase-patch --from-file=./couchbase.py
kubectl -n authn create configmap icrypto-patch --from-file=./icrypto-patch.sh
kubectl -n authn create configmap log4j2 --from-file=./log4j2.xml
kubectl -n authn create configmap oidc-entrypoint --from-file=./entrypoint.sh
kubectl -n authn create configmap insert-cert --from-file=./insert-cert.sh
kubectl -n authn create configmap jans-couchbase --from-file=./jans-couchbase.properties
