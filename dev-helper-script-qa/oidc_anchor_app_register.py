import requests
import base64
import json
import re
import email
from requests.auth import HTTPBasicAuth
import sys
import hashlib
from datetime import datetime
import imaplib
import time
import os
#----------QA Example PRofit ------------
OIDC_CLIENT_ID = os.environ.get('OIDC_CLIENT_ID')
OIDC_URL = os.environ.get('OIDC_URL')
EXT_AUTH_URL = os.environ.get('EXT_AUTH_URL')
REDIRECT_URL = os.environ.get('REDIRECT_URL')
IDM_CREATE_URL = os.environ.get('IDM_CREATE_URL')
IDM_SEARCH_URL = os.environ.get('IDM_SEARCH_URL')
SCIM_AUTHORIZATION = os.environ.get('SCIM_AUTHORIZATION')
SSO_BFF_URL = os.environ.get('SSO_BFF_URL')
EXISTING_USER_ID = os.environ.get('EXISTING_USER_ID')

"""
OIDC_CLIENT_ID = "2623f77f-3e97-4215-978f-98636bde65ea"
OIDC_URL="https://qa-oidc.pps.co.za"
EXT_AUTH_URL="https://qa-sidas.pps.co.za"
REDIRECT_URL="https://sso-qa.pps.co.za/sso-bff/login/oauth2/code/oidc"
IDM_CREATE_URL = "https://qa-idm.pps.co.za/midpoint/ws/services/scim2/Users"
IDM_SEARCH_URL = "https://qa-idm.pps.co.za/midpoint/ws/services/scim2/Users/.search"
SCIM_AUTHORIZATION = "Basic QWRtaW5pc3RyYXRvcjpTaHpudndQOE5lV245Wkg="
SSO_BFF_URL = "https://sso-qa.pps.co.za/sso-bff/"
EXISTING_USER_ID="0001010609087"

#----------Preprod Example Sparkle ------------
OIDC_CLIENT_ID = "ae318769-653a-4c62-8d24-dddbc971c585"
OIDC_URL="https://oidc-pprod.pps.co.za"
EXT_AUTH_URL="https://sidas-pprod.pps.co.za"
REDIRECT_URL="https://sso-pre.pps.co.za/sso-bff/login/oauth2/code/oidc"
IDM_CREATE_URL = "https://pre-idm.pps.co.za/midpoint/ws/services/scim2/Users"
IDM_SEARCH_URL = "https://pre-idm.pps.co.za/midpoint/ws/services/scim2/Users/.search"
SCIM_AUTHORIZATION = "Basic QWRtaW5pc3RyYXRvcjpiZ3RqTmpGN3lOd2Y2d3RA"
SSO_BFF_URL = "https://sso-pre.pps.co.za/sso-bff"
EXISTING_USER_ID = "0001315549087"

#----------prod Example Sparkle ------------
OIDC_CLIENT_ID = "2e15b236-7d92-46a8-b75a-d66f09344414"
OIDC_URL="https://oidc.pps.co.za"
EXT_AUTH_URL="https://sidas.pps.co.za"
REDIRECT_URL="https://sso.pps.co.za/sso-bff/login/oauth2/code/oidc"
IDM_CREATE_URL = "https://idm.pps.co.za/midpoint/ws/services/scim2/Users"
IDM_SEARCH_URL = "https://idm.pps.co.za/midpoint/ws/services/scim2/Users/.search"
SCIM_AUTHORIZATION = "Basic Q1JFRF9NR01UX1NFUlZJQ0U6QmVhc3RWZWVyYXl5YUAyMDIz"
SSO_BFF_URL = "https://sso.pps.co.za/sso-bff"
EXISTING_USER_ID = ""
"""
USER_PASSWORD = "Password@123"
RESET_PASSWORD = "Password@1234"
TOKEN_AUTH_TYPE="client_secret_basic"
ENABLE_PCKE=False

session = requests.Session()

def getCookies(cookies):
  cookieDict = {}
  for cookie in cookies:
    cookieDict[cookie.name] = cookie.value
  return cookieDict

def getSessionValue(url, reqParam):
  paramValueDict = {}
  url = url.split("?")[1]
  params = url.split("&")
  for param in params:
    name = param.split("=")[0]
    value = param.split("=")[1]
    paramValueDict[name] = value
  return paramValueDict[reqParam]

def getPauthToken(pauth):
  b64decode = base64.b64decode(pauth)
  b64decode_json = json.loads(b64decode)
  print(b64decode_json["ptoken"])
  return b64decode_json["ptoken"]

def printStatus(session, response):
    print("Status code: ", response.status_code)
    print("Response headers: ", response.headers)
    print("Response body: ", response.text)
    if session:
        print("Session cookies: ", json.dumps(session.cookies.get_dict()))
    print("\n==============================\n\n")

def fetch_otp():
    print("Waiting for 30 sec")
    time.sleep(30)
    print("Waiting for 30 sec - Done")
    otp_list = []
        # Gmail IMAP settings
    username = 'icryptoautomation@gmail.com'  # Replace with your Gmail email address
    password = 'qomdxjrcjagttrgr'  # Replace with your Gmail password
    # Connect to Gmail's IMAP server
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(username, password)

    # Select the inbox
    mail.select("inbox")
    otp_pattern = re.compile(r'\s\d{6}')  # Regex pattern for 6-digit OTP

    # Search for all emails and fetch the last 10
    result, data = mail.search(None, "ALL")
    latest_email_id = data[0].split()[-1]

    # Fetch the latest email
    result, data = mail.fetch(latest_email_id, "(RFC822)")
    raw_email = data[0][1]

    # Decode the email message
    email_message = email.message_from_bytes(raw_email)
    subject = email_message["Subject"]
    from_ = email_message["From"]
    body = ""

    if email_message.is_multipart():
        for part in email_message.walk():
            content_type = part.get_content_type()
            if "text/plain" in content_type:
                body = part.get_payload(decode=True).decode()
                break
    else:
        body = email_message.get_payload(decode=True).decode()
    otps = otp_pattern.findall(body)
    if otps:
        otp_list.extend(otps)

    mail.close()
    mail.logout()
    print("Extracted OTPs:", otp_list)
    return otp_list

def deleteUserFromIdm(saID):
    response = requests.post(IDM_SEARCH_URL, json={"filter": "saID eq \"{id}\"".replace("{id}", saID)},
                                     headers={"Authorization": SCIM_AUTHORIZATION})
    if response.json()["totalResults"] == 1:
        print("User exists in IDM")
        idmUserId = response.json()["Resources"][0]["id"]
        print("Deleting user ..."+idmUserId)
        response = requests.request("DELETE", IDM_CREATE_URL+"/"+idmUserId, data={},
                                         headers={"Authorization": SCIM_AUTHORIZATION})
        if response.status_code != 204:
            print("Failed to delete the existing user "+saID)
            printStatus(session, response)
            sys.exit(1)

print("-----------------------OIDC p1-------------------------")

headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
}
pkce_value="HKFMnkdkjZjkJ5JyXYPyWXVnfuzuga7PKCcWy2SuS2D"
code_challenge = base64.urlsafe_b64encode(hashlib.sha256(pkce_value.encode("ascii")).digest()).decode('ascii')[:-1]
# Authorize call
print("\nCalling Authorize call")
authorize_call = f"{OIDC_URL}/oidc/restv1/authorize?client_id={OIDC_CLIENT_ID}&redirect_uri={REDIRECT_URL}&response_type=code&scope=openid%20profile%20email"
if ENABLE_PCKE:
    authorize_call += f"&code_challenge={code_challenge}&code_challenge_method=S256"

response = session.request("GET", authorize_call, headers=headers, allow_redirects=False)
printStatus(session, response)

# Authorize.htm call
print("\nCalling Authorize htm call")
response = session.request("GET", response.headers["Location"] or response.headers["location"], headers=headers, allow_redirects=False)
printStatus(session, response)

# login.htm call
print("\nCalling login.htm call")
response = session.request("GET", response.headers["Location"] or response.headers["location"], headers=headers, allow_redirects=False)
printStatus(session, response)

print("\nCalling login call")
response = session.request("GET", response.headers["Location"] or response.headers["location"], headers=headers, allow_redirects=False)
printStatus(session, response)

# Get the current date and time
current_datetime = datetime.now()
datetime_string = str(current_datetime.strftime('%Y%m%d%H%M%S'))
saID = datetime_string

print("----------------------- NEWBIE USER REGISTRATION -------------------------")
print("\nNewbie user registration using saID "+saID)
print("Calling find call for saID "+saID)
response = session.request("GET", SSO_BFF_URL+"/api/user/registration/"+saID+"/find", headers=headers, allow_redirects=False)
if response.status_code != 404:
    print("User already exists")
    printStatus(session, response)
    sys.exit(1)

givenName = "gn"+datetime_string
familyName = "fn"+datetime_string
user_data = {
              "title": "Dr",
              "email": "icryptoautomation@gmail.com",
              "givenName": givenName,
              "familyName": familyName,
              "telephoneNumber": "+27123456789",
              "emails": [
                "icryptoautomation@gmail.com"
              ],
              "mobiles": [
                "+27123456789"
              ],
              "saID": saID
            }

print("Calling register call for saID "+saID)
response = session.request("POST", SSO_BFF_URL+"/api/user/registration/register", headers=headers, json=user_data)
if response.status_code != 200:
    printStatus(session, response)
    sys.exit(1)

print("Calling generate otp for email endpoint call for saID "+saID)
response = session.request("GET", SSO_BFF_URL+"/api/user/notification/send/email/"+"icryptoautomation@gmail.com"+"/registration", headers=headers, allow_redirects=False)
if response.status_code != 200:
    printStatus(session, response)
    sys.exit(1)
otp_codes = fetch_otp()
if not otp_codes:
    print("Otp not found ....")
    sys.exit(1)

print("Calling verify email endpoint call for saID "+saID)
response = session.request("GET", SSO_BFF_URL+"/api/user/notification/verify/"+otp_codes[0].strip(), headers=headers, allow_redirects=False)
if response.status_code != 200:
    printStatus(session, response)
    sys.exit(1)

set_password_data = {
    "password" : USER_PASSWORD
}
print("Calling set password call for saID "+saID)
response = session.request("POST", SSO_BFF_URL+"/api/user/registration/setPassword", headers=headers, json=set_password_data)
if response.status_code != 200:
    printStatus(session, response)
    sys.exit(1)
response = requests.post(IDM_SEARCH_URL, json={"filter": "saID eq \"{id}\"".replace("{id}", saID)},
                                 headers={"Authorization": SCIM_AUTHORIZATION})
if response.json()["totalResults"] == 1:
    username = response.json()["Resources"][0]["urn:ietf:params:scim:schemas:extension:custom:2.0:User"]["username"]

# Doing Login Call
print("----------------------- AUTHN-------------------------")

print("\nCheck user call....")
data = {
    "username": username,
    "password": ""
}
headers["Authorization"] = "Bearer "+session.cookies.get_dict()["x_icrypto_tai"]
response = session.request("POST", EXT_AUTH_URL+"/api/authn", headers=headers, json=data)
if response.status_code != 200:
    print("Login failed")
    printStatus(session, response)
    sys.exit(1)

print("\nCalling authn call....")
data = {
    "username": username,
    "password": USER_PASSWORD
}
headers["Authorization"] = "Bearer "+session.cookies.get_dict()["x_icrypto_tai"]
response = session.request("POST", EXT_AUTH_URL+"/api/authn", headers=headers, json=data)
if response.status_code != 200:
    print("Login failed")
    printStatus(session, response)
    sys.exit(1)

print("Calling Get Options call")
headers["Authorization"] = "Bearer "+session.cookies.get_dict()["x_icrypto_tai"]
response = session.request("GET", EXT_AUTH_URL+"/mfa/api/mfa/options", headers=headers, allow_redirects=False)
if response.status_code != 200:
    print("Get options failed")
    printStatus(session, response)
    sys.exit(1)

print("Calling mfa trigger call")
response_json = response.json()
data = {
    "tokenId": response_json[0]["tokenId"],
    "authnStep": "mfa_otp_email",
    "action": "trigger"
}
headers["Authorization"] = "Bearer "+session.cookies.get_dict()["x_icrypto_tai"]
response = session.request("POST", EXT_AUTH_URL+"/mfa/api/mfa/trigger", headers=headers, json=data)
if response.status_code != 200:
    print("Login failed")
    printStatus(session, response)
    sys.exit(1)
printStatus(session, response)
response_json = response.json()
transactionId = response_json["transactionId"]

otp_codes = fetch_otp()
if not otp_codes:
    print("Otp not found ....")
    sys.exit(1)

data = {
    "transactionId": transactionId,
    "authnStep": "mfa_otp_email",
    "action": "verification",
    "code": otp_codes[0].strip()
}
print("Calling otp verify ")
headers["Authorization"] = "Bearer "+session.cookies.get_dict()["x_icrypto_tai"]
response = session.request("POST", EXT_AUTH_URL+"/mfa/api/mfa/verify", headers=headers, json=data)
if response.status_code != 200:
    print("Login failed")
    printStatus(session, response)
    sys.exit(1)
deleteUserFromIdm(saID)

print("----------------------- NEWBIE USER REGISTRATION WITH ID NUMBER -------------------------")
print("\nCreating user with just id number in IDM")
current_datetime = datetime.now()
datetime_string = str(current_datetime.strftime('%Y%m%d%H%M%S'))
saID = datetime_string

headers = {
  'Content-Type': 'application/json',
  'Authorization': SCIM_AUTHORIZATION
}
payload = {
            "urn:ietf:params:scim:schemas:extension:custom:2.0:User": {
              "saID": saID
            }
          }
response = session.request("POST", IDM_CREATE_URL, headers=headers, json=payload)
if response.status_code != 201:
    print("Creating user with just id number in IDM - Failed")
    printStatus(session, response)
    sys.exit(1)

print("Calling find call for saID "+saID)
response = session.request("GET", SSO_BFF_URL+"/api/user/registration/"+saID+"/find", headers=headers, allow_redirects=False)
if response.status_code == 404:
    print("User Not created it seems")
    printStatus(session, response)
    sys.exit(1)

givenName = "gn"+datetime_string
familyName = "fn"+datetime_string
user_data = {
              "title": "Dr",
              "email": "icryptoautomation@gmail.com",
              "givenName": givenName,
              "familyName": familyName,
              "telephoneNumber": "+27123456789",
              "emails": [
                "icryptoautomation@gmail.com"
              ],
              "mobiles": [
                "+27123456789"
              ],
              "saID": saID
            }

print("Calling register call for saID "+saID)
response = session.request("POST", SSO_BFF_URL+"/api/user/registration/register", headers=headers, json=user_data)
if response.status_code != 200:
    printStatus(session, response)
    sys.exit(1)

print("Calling generate otp for email endpoint call for saID "+saID)
response = session.request("GET", SSO_BFF_URL+"/api/user/notification/send/email/"+"icryptoautomation@gmail.com"+"/registration", headers=headers, allow_redirects=False)
if response.status_code != 200:
    printStatus(session, response)
    sys.exit(1)
otp_codes = fetch_otp()
if not otp_codes:
    print("Otp not found ....")
    sys.exit(1)

print("Calling verify email endpoint call for saID "+saID)
response = session.request("GET", SSO_BFF_URL+"/api/user/notification/verify/"+otp_codes[0].strip(), headers=headers, allow_redirects=False)
if response.status_code != 200:
    printStatus(session, response)
    sys.exit(1)

set_password_data = {
    "password" : USER_PASSWORD
}
print("Calling set password call for saID "+saID)
response = session.request("POST", SSO_BFF_URL+"/api/user/registration/setPassword", headers=headers, json=set_password_data)
if response.status_code != 200:
    printStatus(session, response)
    sys.exit(1)
deleteUserFromIdm(saID)

print("----------------------- EXISTING USER REGISTRATION -------------------------")
print("\n Trying registration for an existing user in idm")
saID = EXISTING_USER_ID
response = requests.post(IDM_SEARCH_URL, json={"filter": "saID eq \"{id}\"".replace("{id}", saID)},
                                 headers={"Authorization": SCIM_AUTHORIZATION})
if response.json()["totalResults"] == 1:
    print("User exists in IDM")
    idmUserId = response.json()["Resources"][0]["id"]
    print("Deleting user ..."+idmUserId)
    print(IDM_SEARCH_URL+"/"+idmUserId)
    response = requests.request("DELETE", IDM_CREATE_URL+"/"+idmUserId, data={},
                                     headers={"Authorization": SCIM_AUTHORIZATION})
    if response.status_code != 204:
        print("Failed to delete the existing user "+saID)
        sys.exit(1)
        printStatus(session, response)
print("User didnt exists in IDM")
print("Calling find call for saID "+saID)
response = session.request("GET", SSO_BFF_URL+"/api/user/registration/"+saID+"/find", headers=headers, allow_redirects=False)
if response.status_code != 200:
    print("User not yet recocniled it seems")
    printStatus(session, response)
    sys.exit(1)
printStatus(session, response)
print("Calling generate otp for email endpoint call for saID "+saID)
response = session.request("GET", SSO_BFF_URL+"/api/user/notification/send/email/"+"icr*******l.com"+"/registration", headers=headers, allow_redirects=False)
print(response.text)
if response.status_code != 200:
    printStatus(session, response)
    sys.exit(1)
otp_codes = fetch_otp()
if not otp_codes:
    print("Otp not found ....")
    sys.exit(1)

print("Calling verify email endpoint call for saID "+saID)
response = session.request("GET", SSO_BFF_URL+"/api/user/notification/verify/"+otp_codes[0].strip(), headers=headers, allow_redirects=False)
if response.status_code != 200:
    printStatus(session, response)
    sys.exit(1)

set_password_data = {
    "password" : USER_PASSWORD
}
print("Calling set password call for saID "+saID)
response = session.request("POST", SSO_BFF_URL+"/api/user/registration/setPassword", headers=headers, json=set_password_data)
if response.status_code != 200:
    printStatus(session, response)
    sys.exit(1)

print("----------------------- FORGOT USER NAME -------------------------")
# Check Forgot username
print("\nChecking Forgot User name journey")
print("Calling find call for saID "+saID)
response = session.request("GET", SSO_BFF_URL+"/api/user/registration/"+saID+"/findRegisteredID", headers=headers, allow_redirects=False)
if response.status_code != 200:
    print("User not found seems")
    printStatus(session, response)
    sys.exit(1)

print("Calling generate otp for email endpoint call for saID "+saID)
response = session.request("GET", SSO_BFF_URL+"/api/user/notification/send/email/"+"icr*******ail.com"+"/forgot-username", headers=headers, allow_redirects=False)
if response.status_code != 200:
    printStatus(session, response)
    sys.exit(1)
otp_codes = fetch_otp()
if not otp_codes:
    print("Otp not found ....")
    sys.exit(1)
print("Calling verify email endpoint call for saID "+saID)
response = session.request("GET", SSO_BFF_URL+"/api/user/notification/verify/"+otp_codes[0].strip(), headers=headers, allow_redirects=False)
if response.status_code != 200:
    printStatus(session, response)
    sys.exit(1)
print("Calling get username call for saID "+saID)
response = session.request("GET", SSO_BFF_URL+"/api/user/registration/getUsername", headers=headers, allow_redirects=False)
if response.status_code != 200:
    printStatus(session, response)
    sys.exit(1)
username = response.json()["username"]
print(username)

print("----------------------- FORGOT PASSWORD -------------------------")
# Check Forgot password
print("Checking Forgot password journey")
print("Calling find call for saID "+saID)
response = session.request("GET", SSO_BFF_URL+"/api/user/registration/"+username+"/findRegisteredUserName", headers=headers, allow_redirects=False)
if response.status_code != 200:
    print("User not found seems")
    printStatus(session, response)
    sys.exit(1)

print("Calling generate otp for email endpoint call for saID "+saID)
response = session.request("GET", SSO_BFF_URL+"/api/user/notification/send/email/"+"icr*******ail.com"+"/forgot-password", headers=headers, allow_redirects=False)
if response.status_code != 200:
    printStatus(session, response)
    sys.exit(1)
otp_codes = fetch_otp()
if not otp_codes:
    print("Otp not found ....")
    sys.exit(1)
print("Calling verify email endpoint call for saID "+saID)
response = session.request("GET", SSO_BFF_URL+"/api/user/notification/verify/"+otp_codes[0].strip(), headers=headers, allow_redirects=False)
if response.status_code != 200:
    printStatus(session, response)
    sys.exit(1)
print("Calling set new password saID "+saID)
set_password_data = {
    "password" : RESET_PASSWORD
}
print("Calling set password call for saID "+saID)
response = session.request("POST", SSO_BFF_URL+"/api/user/registration/setPassword", headers=headers, json=set_password_data)
if response.status_code != 200:
    printStatus(session, response)
    sys.exit(1)