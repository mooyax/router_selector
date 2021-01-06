#!/usr/bin/env python
# -*- coding:utf-8 -*-

import socket

target_ip = "127.0.0.1"
target_port = 52000
buffer_size = 4096

target_id = 12
source_id = 116

stx = bytearray.fromhex('1002')

sendmessage = bytearray.fromhex('020000')

sendmessage.append(target_id-1)
sendmessage.append(source_id-1)
sendmessage.append(0x05)

sendmessage.append((~sum(sendmessage) + 1 )& 0xff)

etx= bytearray.fromhex('1003')

for b in stx+sendmessage+etx:
    print('%02x' % b)


# 1.ソケットオブジェクトの作成
tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 1.1 タイムアウト値の設定 2秒内
tcp_client.settimeout(2)

# 2.サーバに接続
tcp_client.connect((target_ip,target_port))

# 3.サーバにデータを送信
tcp_client.send(stx+sendmessage+etx)

# 4.サーバからのレスポンスを受信
response = tcp_client.recv(buffer_size)
print("[*]Received a response : {}".format(response))

tcp_client.close()
