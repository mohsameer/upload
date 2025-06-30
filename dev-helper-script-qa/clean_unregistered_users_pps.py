import requests
import base64
import json
import logging
from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster, QueryOptions
from couchbase.options import ClusterOptions, ClusterTimeoutOptions
from datetime import timedelta
import sys
import csv
import os
from flask import Flask

app = Flask(__name__)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s:%(levelname)s:%(message)s",
    datefmt="%Y-%m-%d %I:%M:%S%p",
)

# have to be retrieved from Sameer or bitwarden
CB_URL=os.environ.get('CB_URL')
CB_USER=os.environ.get('CB_USER')
CB_PASS=os.environ.get('CB_PASS')
CB_BUCKET="icrypto_persistent_ha"
OIDC_BUCKET = "oidc"
IDM_AUTH_HEADER_VALUE =  os.environ.get('IDM_AUTH_HEADER_VALUE') # PPD
# Change to false to run delete queries. DRY_RUN=true only prints which entries should be deleted.
DRY_RUN=False
DELETE_LIMIT=200000
DELETE_CHUNK = 100
IDM_DELETE_URL = "http://idm-server.services.svc.cluster.local:8080/midpoint/ws/services/scim2/Users/"
IDM_SEARCH_URL = "http://idm-server.services.svc.cluster.local:8080/midpoint/ws/services/scim2/Users/.search"

# IDM is available from VPN, for CB probably do port forwarding and run the script localy? or just leave CB_URL as is and run from couchbase VM (if idm.pps.co.za resolves)
timeout_options=ClusterTimeoutOptions(connect_timeout=timedelta(seconds=72000))
try:
    cb_cluster = Cluster(CB_URL, ClusterOptions(PasswordAuthenticator(CB_USER, CB_PASS), timeout_options=timeout_options))
    cb_cluster.wait_until_ready(timedelta(seconds=5))
    cb_cluster.bucket(OIDC_BUCKET)
except Exception as e:
    raise e
logging.info("Connection to Couchbase established")

filename = "idmUserIds.csv"
delimiter = ","  # Specify your custom delimiter here
idmUserIds = []
idm2icryptoIdDict = {}
icrypto2idmIdDict = {}
idmId2saIdDict = {}

def getUserIdsFromCSV():
    with open(filename, "r", newline="") as file:
        reader = csv.reader(file, delimiter=delimiter)
        for row in reader:
            idmUserId = row[0]
            icryptoUserId = row[1]
            saID = row[2]
            idm2icryptoIdDict[idmUserId] = icryptoUserId
            idmId2saIdDict[idmUserId] = saID
    return idm2icryptoIdDict

def deleteInCbIdmId(icryptoUserId):
    if DRY_RUN:
        logging.info("DRY_RUN Id to remove: "+icryptoUserId)
    else:
        try:
            logging.info("DELETING Idm entry from db:"+icryptoUserId)
            sql_query = 'DELETE FROM `icrypto_persistent_ha` WHERE META().id = "idm_'+icryptoUserId+'"'
            result = cb_cluster.query(sql_query)
            result.execute()
        except Exception as e:
            logging.error(e)
            logging.error("Exception during delete for id: "+str(icryptoUserId))
            raise

def deleteInCbMfaData(icryptoUserId):
    if DRY_RUN:
        logging.info("DRY_RUN Id to remove: "+icryptoUserId)
    else:
        try:
            logging.info("DELETING mfa entry from db:"+icryptoUserId)
            sql_query = 'DELETE FROM `icrypto_persistent_ha` WHERE META().id = "MFA_USER_'+icryptoUserId+'"'
            result = cb_cluster.query(sql_query)
            result.execute()
        except Exception as e:
            logging.error(e)
            logging.error("Exception during delete for id: "+str(icryptoUserId))
            raise

def deleteInOidcBucket(idnumber):
    if DRY_RUN:
        logging.info("DRY_RUN Id to remove: "+idnumber)
    else:
        try:
            logging.info("DELETING oidc entry for :"+idnumber)
            sql_query = 'DELETE FROM `oidc` WHERE saID = "'+idnumber+'" and meta().id like "people_%"'
            result = cb_cluster.query(sql_query)
            result.execute()
        except Exception as e:
            logging.error(e)
            logging.error("Exception during delete for id: "+str(icryptoUserId))
            raise

def deleteInIdmById(idm_id):
    if DRY_RUN:
        print("DRY RUN : id to delete "+idm_id)
    else:
        response_delete = requests.delete(IDM_DELETE_URL+idm_id,headers={"Authorization": IDM_AUTH_HEADER_VALUE}) 
        print("Deleting " + idm_id + ", result: " + str(response_delete.status_code))
        if response_delete.status_code == 204:
            print("Record with idm_id " + idm_id + " deleted completely from idm")
        else:
            print("Record with idm_id " + idm_id + " failed to delete completely from idm")

def countOfSaIdUsers(idnumber):
    sql_query = 'select count(*) from `icrypto_persistent_ha` where meta().id like "idm_%" and saID="'+idnumber+'"'
    row_iter = cb_cluster.query(sql_query)
    return row_iter

def checkAndDeleteByIdNumber(idnumber):
    if DRY_RUN:
        logging.info("DRY_RUN Id to remove: "+idnumber)
    else:
        try:
            saIdUsersCount = list(countOfSaIdUsers(idnumber))[0]["$1"]
            logging.info(saIdUsersCount)
            if saIdUsersCount > 0:
                logging.info("DELETING id number entries if more :"+idnumber)
                sql_query = 'DELETE FROM `icrypto_persistent_ha` WHERE META().id like "idm_%" and saID="'+idnumber+'"'
                result = cb_cluster.query(sql_query)
                result.execute()
        except Exception as e:
            logging.error(e)
            logging.error("Exception during delete for id: "+str(idnumber))
            raise

def deleteInOidcBucket(idnumber):
    if DRY_RUN:
        logging.info("DRY_RUN Id to remove: "+idnumber)
    else:
        try:
            logging.info("DELETING oidc entry for :"+idnumber)
            sql_query = 'DELETE FROM `oidc` WHERE saID = "'+idnumber+'" and meta().id like "people_%"'
            result = cb_cluster.query(sql_query)
            result.execute()
        except Exception as e:
            logging.error(e)
            logging.error("Exception during delete for id: "+str(icryptoUserId))
            raise

def cleanUpEntries(idmIdEntry, icryptoUserId, idNumber):
    cb_cluster.bucket(CB_BUCKET)
    deleteInIdmById(idmIdEntry)
    deleteInCbIdmId(icryptoUserId)
    deleteInCbMfaData(icryptoUserId)
    checkAndDeleteByIdNumber(idNumber)
    cb_cluster.bucket(OIDC_BUCKET)
    deleteInOidcBucket(idNumber)

@app.route('/api/clean/id/<idnumber>')
def cleanSaIdEntry(idnumber):
    response = requests.post(IDM_SEARCH_URL,
                        json={"filter": "saID eq \"{id}\"".replace("{id}", idnumber)},
                        headers={"Authorization": IDM_AUTH_HEADER_VALUE})
    if response.status_code == 200:
        data = response.json()
        if(data["totalResults"] == 1):
            idmIdEntry = data["Resources"][0]["id"]
            icryptoUserId = data["Resources"][0]["urn:ietf:params:scim:schemas:extension:custom:2.0:User"]["icryptoUserId"]
            print(idmIdEntry, "->", icryptoUserId)
            try:
                cleanUpEntries(idmIdEntry, icryptoUserId, idnumber)
            except Exception as e:
                raise e
    return f'Hello, {idnumber}!'

if __name__ == '__main__':
    app.run()
else:
    idm2icryptoIdDict = getUserIdsFromCSV()
    for idmIdEntry in idm2icryptoIdDict:
        print(idmIdEntry, "->", idm2icryptoIdDict[idmIdEntry])
        try:
            cleanUpEntries(idmIdEntry, idm2icryptoIdDict[idmIdEntry], idmId2saIdDict[idmIdEntry])
        except Exception as e:
            raise e