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
    sys.stdout.write(struct.pack('I', len(message)).decode('utf-8'))
    # Write the message itself.
    sys.stdout.write(message)
    sys.stdout.flush()

# read messages from the webapp.
def read_message():
    # Read the message length (first 4 bytes).
    text_length_bytes = sys.stdin.read(4)
    if len(text_length_bytes) == 0:
        sys.exit(0)

    # Unpack message length as 4 byte integer.
    text_length = struct.unpack('i', bytes(bytearray(text_length_bytes, 'utf-8')))[0]

    # Read the text (JSON object) of the message.
    text = sys.stdin.read(text_length)

    return text

def escape_message(message):
    return "\"" + message + "\""

def parse_message(message_json):
    message = json.loads(message_json)
    msg_id = message['id']
    msg_cmd = message['cmd']

    if msg_cmd == "isHostRunning":
        output = False
        try:
            alice_verifying_key = Alice.get_verifying_key()
            bob_encrypting_key, bob_verifying_key = Bob.get_keys()
            output = True
        except:
            output = False

        if output == False:
            send_message('{"id": %s, "type": "failure", "result": false}' % (escape_message(msg_id)))
        else:
            send_message('{"id": %s, "type": "success", "result": true}' % (escape_message(msg_id)))

    elif msg_cmd == 'encrypt':
        plaintext = message['args'][0]
        label = message['args'][1]

        try:
            encrypted = Alice.encrypt(label, plaintext)
            send_message('{"id": %s, "type": "success", "result": %s}' % (escape_message(msg_id), escape_message(encrypted)))
        except:
            send_message('{"id": %s, "type": "failure"}' % (escape_message(msg_id)))

    elif msg_cmd == 'grant':
        label = message['args'][0]

        if Bob.grant(label) == True:
            send_message('{"id": %s, "type": "success"}' % (escape_message(msg_id)))
        else:
            send_message('{"id": %s, "type": "failure"}' % (escape_message(msg_id)))

    elif msg_cmd == 'decrypt':
        encrypted = message['args'][0]
        label = message['args'][1]

        try:
            plaintext = Bob.decrypt(label, encrypted)
            send_message('{"id": %s, "type": "success", "result": %s}' % (escape_message(msg_id), escape_message(plaintext)))
        except:
            send_message('{"id": %s, "type": "failure"}' % (escape_message(msg_id)))


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
