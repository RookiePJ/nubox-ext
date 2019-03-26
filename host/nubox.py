#!/usr/local/bin/python3.6

# Copyright (c) 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# A simple native messaging host.

import struct
import sys
import json
import traceback
import logging

# from alice import Alice
# from bob import Bob

# Helper function that sends a message to the webapp.
def send_message(message):
    # Write message size.
    sys.stdout.write(struct.pack('I', len(message)))
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
    text_length = struct.unpack('i', text_length_bytes)[0]

    # Read the text (JSON object) of the message.
    text = sys.stdin.read(text_length).decode('utf-8')

    return text

# def escape_message(message):
#     return "\"" + message + "\""

# def parse_message(message):
#     msg_id = message['id']
#     msg_cmd = message['cmd']
#
#     if msg_cmd == "isHostRunning":
#         output = False
#         try:
#             alice_verifying_key = Alice.get_verifying_key()
#             bob_encrypting_key, bob_verifying_key = Bob.get_keys()
#             output = True
#         except:
#             output = False
#
#         if output == False:
#             send_message('{"id": %s, "type": "failure", "result": false}' % (escape_message(msg_id)))
#         else:
#             send_message('{"id": %s, "type": "success", "result": true}' % (escape_message(msg_id)))

if __name__ == '__main__':
    logging.basicConfig(filename='/Users/robin/Workspace/nubox-ext/host/err.log',
                        filemode='w')

    try:
        while 1:
            message_json = read_message()
            # message = json.loads(message_json)

            # parse_message(message)
            send_message('{"id": "1", "type": "success", "result": false}')
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        err = ''.join('!! ' + line for line in lines)  # Log it or whatever here
        logging.error(err)
