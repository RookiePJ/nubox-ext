#!/usr/bin/python3.6

# Copyright (c) 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# A simple native messaging host.

import json
import logging
import os
import struct
import sys
import traceback

from alice import Alice
from bob import Bob

# Helper function that sends a message to the webapp.
def send_message(message):
    # Write message size.
    message_utf8 = message.encode('utf-8')
    sys.stdout.buffer.write(struct.pack('i', len(message_utf8)))
    # Write the message itself.
    sys.stdout.buffer.write(message_utf8)
    sys.stdout.buffer.flush()

# read messages from the webapp.
def read_message():
    # Read the message length (first 4 bytes).
    text_length_bytes = sys.stdin.buffer.read(4)

    # Unpack message length as 4 byte integer.
    text_length = struct.unpack('i', text_length_bytes)[0]

    # Read the text (JSON object) of the message.
    text = sys.stdin.buffer.read(text_length).decode('utf-8')

    return text

def escape_message(message):
    return "\"" + message + "\""

def is_host_running():
    is_running = True

    try:
        alice_verifying_key = Alice.get_verifying_key()
        bob_encrypting_key, bob_verifying_key = Bob.get_keys()
    except:
        is_running = False

    return is_running

def parse_message(message_json):
    message = json.loads(message_json)
    msg_id = message['id']
    msg_cmd = message['cmd']

    # have a check to make sure that nucypher network is running.
    # if not, fail.
    if is_host_running() == False:
        output = {}
        output["id"] = msg_id
        output["cmd"] = "isHostRunning"
        output["type"] = "failure"
        output["result"] = "nuBox Host is not running"

        send_message(json.dumps(output))
        return

    if msg_cmd == "isHostRunning":
        output = {}
        output["id"] = msg_id
        output["cmd"] = "isHostRunning"
        output["type"] = "success"
        output["result"] = "nuBox Host is running"

        send_message(json.dumps(output))

    # get Bob's public keys
    elif msg_cmd == "bob_keys":
        output = {}
        output["id"] = msg_id
        output["cmd"] = "bob_keys"
        output["args"] = message['args']

        try:
            bob_encrypting_key, bob_verifying_key = Bob.get_keys()

            output["type"] = "success"
            output["result"] = {}
            output["result"]["bek"] = bob_encrypting_key
            output["result"]["bvk"] = bob_verifying_key
        except:
            output["type"] = "failure"

        send_message(json.dumps(output))

    # encrypt operation
    elif msg_cmd == 'encrypt':
        plaintext = message['args']['plaintext']
        label = message['args']['label']

        output = {}
        output["id"] = msg_id
        output["cmd"] = "encrypt"
        output["args"] = message['args']

        try:
            encrypted = Alice.encrypt(label, plaintext)
            output["type"] = "success"
            output["result"] = encrypted
        except Exception as e:
            output["type"] = "failure"
            output["result"] = str(e)

        send_message(json.dumps(output))

    # grant operation
    elif msg_cmd == 'grant':
        output = {}
        output["id"] = msg_id
        output["cmd"] = "grant"
        output["args"] = message['args']

        response = Bob.grant(label=message['args']['label'],
                             bob_encrypting_key=message['args']['bek'],
                             bob_verifying_key=message['args']['bvk'],
                             expiration=message['args']['expiration'])

        if response.status_code == 200:
            output["type"] = "success"
            output["result"] = "granted"
        else:
            logging.error(response.content.decode("utf-8"))
            output["type"] = "failure"
            output["result"] = "Failed to grant for this label"

        send_message(json.dumps(output))

    # revoke operation
    elif msg_cmd == 'revoke':
        label = message['args']['label']
        bvk = message['args']['bvk']

        output = {}
        output["id"] = msg_id
        output["cmd"] = "revoke"
        output["args"] = message['args']

        response = Alice.revoke(label, bvk)
        if response.status_code == 200:
            output["type"] = "success"
            output["result"] = "Revoked"
        else:
            logging.error(response.content.decode("utf-8"))
            output["type"] = "failure"
            output["result"] = "Failed to revoke for this label"

        send_message(json.dumps(output))

    # decrypt operation
    elif msg_cmd == 'decrypt':
        encrypted = message['args']['encrypted']
        label = message['args']['label']

        output = {}
        output["id"] = msg_id
        output["cmd"] = "decrypt"
        output["args"] = message['args']

        try:
            plaintext = Bob.decrypt(label, encrypted)
            output["type"] = "success"
            output["result"] = plaintext
        except:
            output["type"] = "failure"
            output["result"] = "Failed to decrypt for this label"

        send_message(json.dumps(output))


if __name__ == '__main__':
    dir = os.path.dirname(os.path.realpath(__file__))
    log_file = dir + '/err.log'
    logging.basicConfig(filename=log_file,
                        filemode='w')

    try:
        while 1:
            message_json = read_message()
            parse_message(message_json)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        err = ''.join('!! ' + line for line in lines)  # Log it or whatever here
        logging.error(err)
