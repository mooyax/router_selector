#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
ダミー応答プログラム
素材分配ルーターと同じようにシリアルデバイスに応答する。
"""

import serial
import time
from array import array
import threading
import platform

# シリアルコードの正引き辞書、逆引き辞書
router_dict = {0x02: 'STX',  0x03: 'ETX', 0x17: 'ETB', 0x06: 'ACK', 0x15: 'NAK', 0x04: 'EOT'}
router_r_dict = {v: k for k, v in list(router_dict.items())}

comport = '/dev/ttyUSB0'
# Windows上はCOM11、raspberry piでは/dev/ttyUSB0、Jenkins上では/dev/tnt0
if platform.uname()[0] == 'Windows':
    comport = 'COM11'


class SerialTest:
    """
    素材分配ルーターと同等のシリアルの送受信をするダミープログラム。
    """
    interval = 1  # 待ち時間 (s)
    run_status = True  # 継続して待ち続けるかのフラグ
    test_status = False  # テストの結果のフラグ　初期値は失敗
    ng_mode = False  # 応答の失敗モード　初期値はFalse
    my_name = 'Sir'
    output_ch = '000'
    input_ch = '000'

    def __init__(self, port_name, ng_mode=False):
        """
        コンストラクタ。NGの場合の振る舞いもできること、シリアルデバイスも変更可能に引数を取る。

        :param port_name: str
        :param ng_mode: bool
        """
        if 'COM' in port_name:
            self.com = serial.Serial(
                port=port_name,  # テスト時COM11、Raspberry pi接続しCOM1
                baudrate=9600,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=5,  # 0ならread()はすぐ読み出し
                xonxoff=0,
                rtscts=0,
                writeTimeout=5,
                dsrdtr=None)

        else:
            self.com = serial.serial_for_url(
                port_name,
                timeout=1,
                writeTimeout=5)

        self.ng_mode = ng_mode

    def serial_wait(self, stime):
        """
        シリアルの応答待ち
        """
        self.com.flush()
        time.sleep(stime)

    @staticmethod
    def bbc(data):
        """
        文字列データから、文字を全てXORで演算した結果の文字コードを返す。

        :param data: str
        :return: chr
        """
        result = ord(data[0])
        for data_item in data[1:]:
            result = result ^ ord(data_item)
        return chr(result)

    @staticmethod
    def send_status(channel):
        """
        ダミーの状態返信用電文。ディスティネーションchに対して全てソース123chと返信する電文。

        :param channel:str
        :return:str
        """
        messages = "10"+"1"+"00"+"00"+channel+"123" + chr(router_r_dict['ETX'])
        return chr(router_r_dict['STX']) + messages + SerialTest.bbc(messages)

    def b_parser(self, i_array):
        """
        受信した電文を解析し、内容に応じて返信する。

        :param i_array: array
        :return: null
        """
        if i_array[0] != router_r_dict['STX']:
            return
        if chr(i_array[1])+chr(i_array[2]) == '03':
            print("%s:クロスポイント制御" % self.my_name)
            self.output_ch = chr(i_array[8])+chr(i_array[9])+chr(i_array[10])
            self.input_ch = chr(i_array[11])+chr(i_array[12])+chr(i_array[13])

            if not self.ng_mode:
                print('%s>ACK' % self.my_name)
                self.com.write(chr(router_r_dict['ACK']))
            else:
                print('%s>NAK' % self.my_name)
                self.com.write(chr(router_r_dict['NAK']))

        elif chr(i_array[1])+chr(i_array[2]) == '10':
            print("%s:クロスポイント状態問い合わせ" % self.my_name)
            if not self.ng_mode:
                print('%s>ACK' % self.my_name)
                self.com.write(chr(router_r_dict['ACK']))
            else:
                print('%s>NAK' % self.my_name)
                self.com.write(chr(router_r_dict['NAK']))
                return

            for d_item in SerialTest.send_status('127'):
                self.com.write(d_item)
        self.test_status = True  # 受信データが正しく、適切に応答を返したので成功とする

    def start(self):
        """
        電文の受信待ちスレッドをスタートさせる。

        :return:
        """
        print('%s:start' % self.my_name)
        self.run_status = True
        self.com.flushInput()
        self.com.flushOutput()
        print(self.com.portstr)

        thread = threading.Thread(target=self.run)
        thread.start()

    def run(self):
        """
        電文の送受信対応するスレッドの本体。

        :return:
        """
        while self.run_status:
            # 受信
            b_array = array('B')
            d_len = self.com.inWaiting()  # 受信バッファにたまってる数を確認
            if d_len > 0:
                d = self.com.read(d_len)
                b_array.extend(array('B', d))  # b_arrayの後ろから追加
                print(self.my_name + ':' + str([hex(x) for x in b_array]))
                self.b_parser(b_array)

            self.serial_wait(1)

    def stop(self):
        """
        電文の送受信対応するスレッドを停止させる。run_statusにて判断している為、この値のみを変更。

        :return:
        """
        print('%s:stop' % self.my_name)
        self.run_status = False
        self.serial_wait(5)

    def get_test_status(self):
        """
        電文送受信のスレッドのステータス。

        :return:bool
        """
        return self.test_status


if __name__ == '__main__':
    serial = SerialTest('COM11')
    serial.run()
