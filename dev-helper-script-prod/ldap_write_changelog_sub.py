import os
import json
import ldap
from google.cloud import pubsub_v1
from google.oauth2 import service_account

# icrypto ldap configuration
icrypto_ldap_server = 'ldap://10.200.110.173:1389'
icrypto_ldap_bind_dn = 'uid=svc_icrypto,cn=admins,secauthority=default'
icrypto_ldap_bind_password = '1Crypt0QAUser'
icrypto_ldap_conn = ''
# ibm ldap configuration
ibm_ldap_server = 'ldap://10.200.110.173:1389'
ibm_ldap_bind_dn = 'uid=svc_icrypto,cn=admins,secauthority=default'
ibm_ldap_bind_password = '1Crypt0QAUser'
ibm_ldap_conn = ''

# Set the path to your service account JSON file
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/raviv/Downloads/testproject-416410-fe0987ae7daa.json"

# Google Cloud project ID
project_id = 'testproject-416410'
topic_name = 'test-topic'

# Pub/Sub subscription name
subscription_name = 'test-topic-sub'

# Create a subscriber client
credentials = service_account.Credentials.from_service_account_file(
    "/Users/raviv/Downloads/testproject-416410-fe0987ae7daa.json"
)
subscriber = pubsub_v1.SubscriberClient(credentials=credentials)

# Get the fully qualified subscription path
subscription_path = subscriber.subscription_path(project_id, subscription_name)

def connect_ldap(server, bind_dn, bind_password):
    try:
        conn = ldap.initialize(server)
        conn.simple_bind_s(bind_dn, bind_password)
        print("Connection to ldap established")
        return conn
    except Exception as e:
        print(f"Got exception while connecting to ldap '{e}'")
def handle_add(dn, attributes):
    attributes_to_add = get_dn_details(dn, attributes)
    create_ldap_entry(dn, attributes_to_add)

def handle_modify(dn, attributes, op):
    attributes_to_add = get_dn_details(dn, attributes)
    modify_ops = []
    if op == 'replace':
        modify_ops = [(ldap.MOD_REPLACE, attr, value) for attr, value in attributes_to_add]
    elif op == 'delete':
        modify_ops = [(ldap.MOD_DELETE, attr, None) for attr, value in attributes_to_add]
    elif op == 'modify':
        modify_ops = [(ldap.MOD_ADD, attr, value) for attr, value in attributes_to_add]
    else:
        print("Not a valid operation")
    if modify_ops:
        modify_ldap_entry(dn, modify_ops)

def handle_delete(dn):
    try:
        icrypto_ldap_conn.delete_s(dn)
        print(f"LDAP entry '{dn}' deleted successfully.")
    except ldap.LDAPError as e:
        print(f"Failed to delete LDAP entry '{dn}': {e}")

def get_dn_details(dn, attributes_required):
    attributes_needed_list = attributes_required.split(', ')
    result = icrypto_ldap_conn.search_s(dn, ldap.SCOPE_BASE, '(objectClass=*)', [])
    if result:
        # Extract the entry and its attributes
        dn, entry = result[0]
        attributes = {}
        for attr, values in entry.items():
            if not attr in attributes_needed_list:
                print(f"Skipping this attribute {attr}")
                continue
            # Skip userPassword attribute
            if attr.lower() == 'userpassword':
                continue
            # Convert each value to string if it's bytes
            if isinstance(values, list):
                encoded_values = [value.decode('utf-8') if isinstance(value, bytes) else value for value in values]
            else:
                encoded_values = values.decode('utf-8') if isinstance(values, bytes) else values
            attributes[attr] = encoded_values
        ldap_attrs = [(key, [value.encode('utf-8') for value in values]) for key, values in attributes.items()]
        return ldap_attrs
    else:
        print(f"No entry found for DN: {dn}")

def create_ldap_entry(dn, attributes):
    # Add the entry
    try:
        print(f"Adding dn {dn} entry with attributes {attributes}")
        icrypto_ldap_conn.add_s(dn, attributes)
        print(f"LDAP entry created successfully for DN: {dn}")
    except ldap.ALREADY_EXISTS:
        print(f"LDAP entry already exists for DN: {dn}")
    except ldap.LDAPError as e:
        print(f"LDAP error occurred: {e}")
    finally:
        pass

def modify_ldap_entry(dn, attributes):
    try:
        print(f"Modifying dn {dn} entry with attributes {attributes}")
        icrypto_ldap_conn.modify_s(dn, attributes)
        print(f"LDAP entry updated successfully for DN: {dn}")
    except ldap.ALREADY_EXISTS:
        print(f"LDAP entry already exists for DN: {dn}")
    except ldap.LDAPError as e:
        print(f"LDAP error occurred: {e}")
    finally:
        pass

# Function to handle incoming Pub/Sub messages
def handle_message(message):
    # Extract message data
    message_data = json.loads(message.data.decode('utf-8'))

    # Extract LDAP action and DN from message data
    ldap_action = message_data.get('ldapAction')
    dn = message_data.get('dn')

    if ldap_action == 'Delete':
        print("Got a message to delete")
        handle_delete(dn)
    elif ldap_action == 'Add':
        print("Got a message to Add")
        attributes = message_data.get('attributes')
        handle_add(dn, attributes)
    elif ldap_action == 'Modify':
        print("Got a message to Modify")
        attributes = message_data.get('attributes')
        modifyOp = message_data.get('modifyOp')
        handle_modify(dn, attributes, modifyOp)
    else:
        print(f"Skipping the ldapAction '{ldap_action}'")
    # Acknowledge the message
    message.ack()
    print(f"Message processed: {ldap_action} - {dn}")

# Subscribe to the Pub/Sub topic
streaming_pull_future = subscriber.subscribe(subscription_path, callback=handle_message)

icrypto_ldap_conn = connect_ldap(icrypto_ldap_server, icrypto_ldap_bind_dn, icrypto_ldap_bind_password)
# Block until the subscriber stops listening
try:
    streaming_pull_future.result()
except KeyboardInterrupt:
    streaming_pull_future.cancel()
finally:
    icrypto_ldap_conn.unbind()

print('Subscription stopped.')
