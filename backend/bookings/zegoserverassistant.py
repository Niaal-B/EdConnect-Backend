#!/usr/bin/env python -u
# coding:utf-8
import json
import random
import time
import struct
import binascii
from Crypto.Cipher import AES

ERROR_CODE_SUCCESS = 0                              # Successfully obtained authentication token
ERROR_CODE_APP_ID_INVALID = 1                       # Invalid appID parameter when calling the method
ERROR_CODE_USER_ID_INVALID = 3                      # Invalid userID parameter when calling the method
ERROR_CODE_SECRET_INVALID = 5                       # Invalid secret parameter when calling the method
ERROR_CODE_EFFECTIVE_TIME_IN_SECONDS_INVALID = 6    # Invalid effective_time_in_seconds parameter when calling the method


class TokenInfo:
    def __init__(self, token, error_code, error_message):
        self.token = token
        self.error_code = error_code
        self.error_message = error_message


def __make_nonce():
    return random.getrandbits(31)


def __make_random_iv():
    str = '0123456789abcdefghijklmnopqrstuvwxyz'
    iv = ""
    for i in range(16):
        index = int(random.random() * 16)
        iv += str[index]
    return iv


def __aes_pkcs5_padding(cipher_text, block_size):
    padding_size = len(cipher_text) if (len(cipher_text) == len(
        cipher_text.encode('utf-8'))) else len(cipher_text.encode('utf-8'))
    padding = block_size - padding_size % block_size
    if padding < 0:
        return None
    padding_text = chr(padding) * padding
    return cipher_text + padding_text


def __aes_encrypy(plain_text, key, iv):
    cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8'))
    content_padding = __aes_pkcs5_padding(plain_text, 16)
    encrypt_bytes = cipher.encrypt(content_padding.encode('utf-8'))
    return encrypt_bytes


def generate_token04(app_id, user_id, secret, effective_time_in_seconds, payload):
    '''Basic description
        Method to obtain token
    Detailed description

    Args:
        app_id: The digital ID distributed by Zego, which is a unique identifier for each developer
        user_id: User ID
        secret: The key required for AES encryption in the calculation process of the authentication token, a 32-byte string
        effective_time_in_seconds token: Validity period of the token, in seconds
        payload: Payload

    Returns:
        TokenInfo: Contains three objects, token, error_code, error_message
    '''

    if type(app_id) != int or app_id == 0:
        return TokenInfo("", ERROR_CODE_APP_ID_INVALID, "appID invalid")
    if type(user_id) != str or user_id == "":
        return TokenInfo("", ERROR_CODE_USER_ID_INVALID, "userID invalid")
    if type(secret) != str or len(secret) != 32:
        return TokenInfo("", ERROR_CODE_SECRET_INVALID, "secret must be a 32 byte string")
    if type(effective_time_in_seconds) != int or effective_time_in_seconds <= 0:
        return TokenInfo("", ERROR_CODE_EFFECTIVE_TIME_IN_SECONDS_INVALID, "effective_time_in_seconds invalid")
    create_time = int(time.time())
    expire_time = create_time + effective_time_in_seconds
    nonce = __make_nonce()

    _token = {"app_id": app_id, "user_id": user_id, "nonce": nonce,
              "ctime": create_time, "expire": expire_time, "payload": payload}
    plain_text = json.dumps(_token, separators=(',', ':'), ensure_ascii=False)

    iv = __make_random_iv()

    encrypt_buf = __aes_encrypy(plain_text, secret, iv)

    result_size = len(encrypt_buf) + 28
    result = bytearray(result_size)

    big_endian_expire_time = struct.pack("!q", expire_time)
    result[0: 0 + len(big_endian_expire_time)] = big_endian_expire_time[:]

    big_endian_iv_size = struct.pack("!h", len(iv))
    result[8: 8 + len(big_endian_iv_size)] = big_endian_iv_size[:]

    buffer = bytearray(iv.encode('utf-8'))
    result[10: 10 + len(buffer)] = buffer[:]

    big_endian_buf_size = struct.pack("!h", len(encrypt_buf))
    result[26: 26 + len(big_endian_buf_size)] = big_endian_buf_size[:]

    result[28: len(result)] = encrypt_buf[:]

    token = "04" + binascii.b2a_base64(result, newline=False).decode()

    return TokenInfo(token, ERROR_CODE_SUCCESS, "success")