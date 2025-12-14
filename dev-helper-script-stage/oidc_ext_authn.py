import requests
import base64
import json
import re
from requests.auth import HTTPBasicAuth
import sys
import hashlib
import textwrap


#---------
with open("./config.json") as file:
    config = json.load(file)

OIDC_VERSION = config.get("OIDC_VERSION")
OIDC_URL = config.get("OIDC_URL")
EXT_AUTH_URL = config.get("EXT_AUTH_URL")
MFA_URL = config.get("MFA_URL")
USE_CASES = config.get("USE_CASES")


def print_roundtrip(response, *args, **kwargs):
    format_headers = lambda d: '\n'.join(f'{k}: {v}' for k, v in d.items())
    print(textwrap.dedent('''
        ---------------- request ----------------
        {req.method} {req.url}
        {reqhdrs}

        {req.body}
        ---------------- response ----------------
        {res.status_code} {res.reason} {res.url}
        {reshdrs}

        {res.text}
    ''').format(
        req=response.request,
        res=response,
        reqhdrs=format_headers(response.request.headers),
        reshdrs=format_headers(response.headers),
    ))

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


def run_login(config):
    CLIENT_ID = config.get("CLIENT_ID")
    CLIENT_SECRET = config.get("CLIENT_SECRET")
    USERNAME = config.get("USERNAME")
    PASSWORD = config.get("PASSWORD")
    MFA_TYPE = config.get("MFA_TYPE", None)
    SCOPES = config.get("SCOPES")
    TOKEN_AUTH_TYPE = config.get("TOKEN_AUTH_TYPE")
    REDIRECT_URL = config.get("REDIRECT_URL")
    NAME = config.get("NAME")

    ENABLE_PCKE=True
    session = requests.Session()
    print("----------------------------------------------------------")
    print(f"-------      Running {NAME}       -------")
    print("----------------------------------------------------------")
    print("-----------------------Well-known-------------------------")

    well_known_url = f"{OIDC_URL}/{OIDC_VERSION}/.well-known/openid-configuration"
    print(f"\nCalling well-known endpoint: {well_known_url}")
    response = session.request("GET", well_known_url, allow_redirects=False, hooks={'response': print_roundtrip})

    well_known = response.json()

    print("-----------------------OIDC p1-------------------------")

    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
    }
    pkce_value="HKFMnkdkjZjkJ5JyXYPyWXVnfuzuga7PKCcWy2SuS2D"
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(pkce_value.encode("ascii")).digest()).decode('ascii')[:-1]


    # Authorize call
    print("\nCalling Authorize call")
    authorize_call = f"{well_known['authorization_endpoint']}?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URL}&response_type=code&scope={'%20'.join(SCOPES)}"
    if ENABLE_PCKE:
        authorize_call += f"&code_challenge={code_challenge}&code_challenge_method=S256"
    response = session.request("GET", authorize_call, headers=headers, allow_redirects=False, hooks={'response': print_roundtrip})

    # Authorize.htm call
    print("\nCalling Authorize htm call")
    response = session.request("GET", response.headers["Location"] or response.headers["location"], headers=headers, allow_redirects=False, hooks={'response': print_roundtrip})
    printStatus(session, response)

    # login.htm call
    print("\nCalling login.htm call")
    print(f"\n{response.headers['Location']}")
    response = session.request("GET", response.headers["Location"] or response.headers["location"], headers=headers, allow_redirects=False, hooks={'response': print_roundtrip})
    printStatus(session, response)

    print("----------------------- AUTHN-------------------------")

    print("\nCheck user call....")
    data = {
        "username": USERNAME,
        "password": ""
    }
    headers["Authorization"] = "Bearer "+session.cookies.get_dict()["x_icrypto_tai"]
    response = session.request("POST", EXT_AUTH_URL, headers=headers, json=data, hooks={'response': print_roundtrip})
    if response.status_code != 200:
        print("Login failed")
        printStatus(session, response)
        sys.exit(1)
    printStatus(session, response)

    print("\nCalling authn call....")
    data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    headers["Authorization"] = "Bearer "+session.cookies.get_dict()["x_icrypto_tai"]
    response = session.request("POST", EXT_AUTH_URL, headers=headers, json=data, hooks={'response': print_roundtrip})
    if response.status_code != 200:
        print("Login failed")
        sys.exit(1)


    print("----------------------- MFA AUTHN-------------------------")
    if MFA_TYPE is not None:
        print("\nRunning MFA calls")
        headers["Authorization"] = "Bearer "+session.cookies.get_dict()["x_icrypto_tai"]
        response = session.request("GET", MFA_URL+"/options", headers=headers, hooks={'response': print_roundtrip})
        if response.status_code != 200:
            print("MFA options failed")
            sys.exit(1)

        selected_token = None
        for option in response.json():
            if option["type"] == "EMAIL":
                selected_token = option
                break
        if selected_token is None:
            print("No email token found in " + response.text)
            sys.exit(1)

        tokenId = selected_token["tokenId"]
        print("\nSelected token: "+tokenId)


        print("----------------------- MFA TRIGGER-------------------------")
        data = {
            "tokenId": tokenId,
            "authnStep":"mfa_otp_email"
        }
        headers["Authorization"] = "Bearer "+session.cookies.get_dict()["x_icrypto_tai"]
        response = session.request("POST", MFA_URL+"/trigger", headers=headers, json=data, hooks={'response': print_roundtrip})
        if response.status_code != 200:
            print("MFA trigger failed")
            sys.exit(1)
        transactionId = response.json()["transactionId"]
        print("\nMFA Transaction ID: "+transactionId)

        print("----------------------- MFA VERIFY-------------------------")
        code = input("Enter MFA code: ")
        data = {
            "transactionId": transactionId,
            "authnStep":"mfa_otp_email",
            "code":code
        }
        headers["Authorization"] = "Bearer "+session.cookies.get_dict()["x_icrypto_tai"]
        response = session.request("POST", MFA_URL+"/verify", headers=headers, json=data, hooks={'response': print_roundtrip})
        if response.status_code != 200:
            print("MFA verify failed")
            sys.exit(1)
        next_steps = response.json()["nextSteps"]
        print("\nMFA next steps: "+str(next_steps))
        if len(next_steps) > 0:
            print("MFA failed")
            sys.exit(1)
    else:
        print("\nMFA disabled")

    print("-----------------------OIDC p2-------------------------")

    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
    }

    print("\nCalling the postlogin")
    response = session.request("GET", f"{OIDC_URL}/{OIDC_VERSION}/postlogin.htm?client_id="+CLIENT_ID, headers=headers, allow_redirects=False, hooks={'response': print_roundtrip})

    print("\nCalling the authorize.htm")
    response = session.request("GET", response.headers["Location"] or response.headers["location"], headers=headers, allow_redirects=False, hooks={'response': print_roundtrip})

    print("\nCalling the authorize call")
    response = session.request("GET", response.headers["Location"] or response.headers["location"], headers=headers, allow_redirects=False, hooks={'response': print_roundtrip})

    print("-----------------------Client-------------------------")

    code_location = response.headers["Location"] or response.headers["location"]
    code_split_str=code_location.split("code=")[1]
    code=code_split_str.split("&")[0]
    print("\nAuthorization code received: "+code)

    print("\nCalling token endpoint to get tokens")
    token_end_point = well_known["token_endpoint"]
    headers = {
        'content-type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'scope' : " ".join(SCOPES),
        'redirect_uri': REDIRECT_URL
    }

    if ENABLE_PCKE:
        data["code_verifier"] = pkce_value

    auth = None
    if TOKEN_AUTH_TYPE == "client_secret_post":
        data["client_id"]=CLIENT_ID
        data["client_secret"]=CLIENT_SECRET
    if TOKEN_AUTH_TYPE == "client_secret_basic":
        auth = HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)

    response = requests.post(token_end_point,data=data, auth=auth, hooks={'response': print_roundtrip})

    response_json = response.json()
    access_token=response_json["access_token"]

    print("-----------------------Introspect-------------------------")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type":"application/x-www-form-urlencoded"
    }
    data = {
        "token": access_token
    }
    response = requests.post(well_known['introspection_endpoint'],headers=headers, data=data, hooks={'response': print_roundtrip})

    print("-----------------------UserInfo-------------------------")
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    response = requests.get(well_known['userinfo_endpoint'],headers=headers, hooks={'response': print_roundtrip})
    printStatus(None, response)


    # # Exchange opaque to JWT token
    # print("\nCalling the introspect call")
    # introspect_endpoint=f"{OIDC_URL}/oidc/restv1/introspection"
    # data={
    #     "token": access_token,
    #     "response_as_jwt": True
    # }
    # response = requests.post(introspect_endpoint, data=data, auth=auth)
    # jwt_token = response.text
    # print(jwt_token)


for config in USE_CASES:
    run_login(config)