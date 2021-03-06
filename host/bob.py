import requests
import json
from base64 import b64decode, b64encode

from alice import Alice

class Bob(object):
    bob = "http://localhost:11151"

    @staticmethod
    def get_keys():
        response = requests.get(f"{Bob.bob}/public_keys")
        json_response = json.loads(response.content)

        bob_encrypting_key = json_response['result']['bob_encrypting_key']
        bob_verifying_key = json_response['result']['bob_verifying_key']
        return bob_encrypting_key, bob_verifying_key

    @staticmethod
    def grant(label, bob_encrypting_key, bob_verifying_key, expiration):
        grant = {}
        grant["bob_verifying_key"] = bob_verifying_key
        grant["bob_encrypting_key"] = bob_encrypting_key
        grant["m"] = 1
        grant["n"] = 1
        grant["label"] = label
        grant["expiration"] = expiration

        response = requests.put(f"{Alice.alice}/grant", data=json.dumps(grant))
        return response

    @staticmethod
    def decrypt(label, encrypted):
        retrieval = {}
        retrieval["label"] = label
        retrieval["policy_encrypting_key"] = Alice.get_policy_encrypting_key(label)
        retrieval["alice_verifying_key"] = Alice.get_verifying_key()
        retrieval["message_kit"] = encrypted

        response = requests.post(f"{Bob.bob}/retrieve", data=json.dumps(retrieval))
        plaintext = json.loads(response.content)['result']['cleartexts'][0]
        return plaintext
