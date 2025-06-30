import re
import os
import json
import time
from google.cloud import pubsub_v1
from google.oauth2 import service_account


changelog_file_path = '/Users/raviv/Downloads/ldap_audit_test.log'
last_linenumber_file = '/Users/raviv/Downloads/last_line_number'

project_id = 'pps-analytics-189714'
#project_id = 'testproject-416410'
topic_name = 'iCrypto-LDAP-Sync'
# Create a publisher client
credentials = service_account.Credentials.from_service_account_file(
    "/Users/raviv/Downloads/pps-analytics-189714-c00756f8157c.json"
)
publisher = pubsub_v1.PublisherClient(credentials=credentials)
topic_path = publisher.topic_path(project_id, topic_name)

def publish_message(message):
    print(f"Message to be published: {message}")
    data = json.dumps(message).encode('utf-8')
    future = publisher.publish(topic_path, data)
    future.result()  # Block until the message is published
    print(f"Message published: {message}")
def read_last_line_number():
    try:
        with open(last_linenumber_file, 'r') as file:
            last_line_number = int(file.readline().strip())
            return last_line_number
    except FileNotFoundError:
        return 0
    except ValueError:
        print("Error: Invalid content in the file.")
        return 0
def publish_to_topic(entry):
    publish_message(entry)

def save_linenumber_to_file(line_number):
    with open(last_linenumber_file, 'w') as f:
        f.write(str(line_number))

def monitor_change_log():
    if not os.path.exists(changelog_file_path):
        print(f"Changelog file '{changelog_file_path}' not found")
        return
    last_linenumber_saved = read_last_line_number()
    current_line_number = 0
    with open(changelog_file_path, 'r') as f:
        entry = {}
        auditLineFound = 0
        for line in f:
            current_line_number = current_line_number + 1
            if current_line_number <= last_linenumber_saved:
                continue
            if line.startswith('AuditV3--'):
                print(line)
                if re.search(r'(Add|Modify|Delete)--bindDN', line):
                    if entry:
                        publish_to_topic(entry)
                        entry = {}
                    auditLineFound = 1
                    entry['ldapAction'] = re.search(r'(Add|Modify|Delete)--bindDN', line).group(1)
                    entry['timestamp'] = re.search(r'AuditV3--(.+?)--', line).group(1)
                else:
                    auditLineFound = 0
            elif auditLineFound == 1:
                key, value = line.strip().split(': ')
                if entry['ldapAction'] == 'Delete' and key == 'entry':
                    entry['dn'] = value
                if entry['ldapAction'] == 'Add' and key == 'entry':
                    entry['dn'] = value
                if entry['ldapAction'] == 'Add' and key == 'attributes':
                    entry['attributes'] = value
                if entry['ldapAction'] == 'Modify' and key == 'object':
                    entry['dn'] = value
                if entry['ldapAction'] == 'Modify' and key == 'replace':
                    entry['attributes'] = value
                    entry['modifyOp'] = 'replace'
                if entry['ldapAction'] == 'Modify' and key == 'add':
                    entry['attributes'] = value
                    entry['modifyOp'] = 'add'
                if entry['ldapAction'] == 'Modify' and key == 'delete':
                    entry['attributes'] = value
                    entry['modifyOp'] = 'delete'
    save_linenumber_to_file(current_line_number)
    if entry:
        publish_to_topic(entry)

if __name__ == "__main__":
    while True:
        monitor_change_log()
        exit()
        #time.sleep(60)