from pyDes import triple_des, ECB, PAD_PKCS5
import base64
import json
import os
import sys
import uuid

salt = "2c52e9563d96e7925132ed73"

def encrypt_client_secret(secret, key):
    cipher = triple_des(key, ECB, pad=None, padmode=PAD_PKCS5)
    encrypted = cipher.encrypt(secret.encode('utf8'), padmode=PAD_PKCS5)
    return base64.b64encode(encrypted)

if len(sys.argv) > 1:
    dec = encrypt_client_secret(sys.argv[1], salt)
    print(dec)
else:
    secret = str(uuid.uuid4())
    dec = encrypt_client_secret(secret, salt)
    print(secret)
    print(dec)
