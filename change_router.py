#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
raspberry pi上にて、池上の素材分配ルータをOATally接点によって制御するプログラム。
"""

import serial
import time
import RPi.GPIO as GPIO
import platform
import os
import tempfile
import datetime

timeout = 5  # タイムアウト値（s）
interval = 0.1  # 待ち時間 (s)
nSub_ch = '024'  # nSubの素材分配ルータsource番号
tSub_ch = '028'  # tSubの素材分配ルータsource番号
OA_ch = '043'  # OA outの素材分配ルータsource番号

gpio_tsub = 2
gpio_nsub = 3

select_sw = {gpio_nsub: nSub_ch, gpio_tsub: tSub_ch}

GPIO.setmode(GPIO.BCM)  # BCMの番号で指定する
GPIO.setup(gpio_tsub, GPIO.IN)
GPIO.setup(gpio_nsub, GPIO.IN)

comport = '/dev/ttyUSB0'
# Windows上はCOM12、raspberry piでは/dev/ttyUSB0、Jenkins上では/dev/tnt0
if platform.uname()[0] == 'Windows':
    comport = 'COM12'  # COM12
    print(comport)

router_dict = {0x02: 'STX',  0x03: 'ETX', 0x17: 'ETB',
               0x06: 'ACK', 0x15: 'NAK', 0x04: 'EOT'}
router_r_dict = {v: k for k, v in list(router_dict.items())}

temp_GPIO_filename = 'GPIO_status.txt'

debug_filename = "change_router.log"


class ChangeRouter:
    """GPIOの接点信号により素材分配ルータを制御するクラス"""
    # TODO 問題が起こった時にメール通知する機能の追加。

    def __init__(self, log="off"):
        """
        引数無しコンストラクタ。
        シリアルの初期化。

        """

        if log != "off":
            self.set_log(log)
        else:
            self.log = log

        try:
            self.com = serial.Serial(
              port=comport,
              baudrate=9600,
              bytesize=8,
              parity='N',
              stopbits=1,
              timeout=5,
              writeTimeout=5,
              )

        except serial.SerialException:
            self.com = serial.Serial(
                port='/dev/tnt0',
                baudrate=9600,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=5,
                writeTimeout=5)

    def set_log(self, log_name):
        """
        ログをtemp領域にセットする

        :param log_name:
        :return:
        """
        self.log = os.path.join(tempfile.gettempdir(), log_name)

    def write_log(self, message):
        """
        logにメッセージを書き込む

        :param message:
        :return:
        """

        if self.log != "off":
            with open(self.log, 'a') as f:
                f.write(str(message))
        else:
            print(message)

    @staticmethod
    def get_sub_state():
        """
        GPIOの状態から、素材分配ルータのソースチャンネルを返す。

        :return: str
        """
        tsub_state = GPIO.input(gpio_tsub)
        nsub_state = GPIO.input(gpio_nsub)

        select_ch = nSub_ch

        if tsub_state and not nsub_state:
            select_ch = nSub_ch
        if not tsub_state and nsub_state:
            select_ch = tSub_ch
        if tsub_state and nsub_state:
            select_ch = OA_ch
        return select_ch

    @staticmethod
    def bbc(data):
        """
        文字列データから、文字を全てXORで演算した結果の文字コードを返す。

        :param data: str
        :return: chr
        """
        result = ord(data[0])
        for d in data[1:]:
            result = result ^ ord(d)
        return chr(result)

    @staticmethod
    def get_information(channel):
        """
        素材ルータの調べたいｃｈに対してのBBC演算でチェックする為の問い合わせ文字列を返す。

        :param channel: str
        :return: str
        """
        send_txt = "10" + "0" + "00" + "00"
        send_txt += channel + "000"
        send_txt += chr(router_r_dict['ETX'])
        return send_txt

    @staticmethod
    def get_crosspoint_set(dist, source):
        """
        素材分配ルータにディスティネーションとソースのｃｈからBBC演算でチェックする為の制御する電文を返す。

        :param dist: str
        :param source: str
        :return: str
        """
        send_txt = "03" + "0" + "00" + "00"
        send_txt += dist + source
        send_txt += chr(router_r_dict['ETX'])
        return send_txt

    @staticmethod
    def router_chr(character):
        """
        文字を対応する制御コードに変換、それ以外はデータとして出力。

        :param character:
        :return: str
        """
        try:
            return router_dict[ord(character)]
        except KeyError:
            return "'%s'" % character

    def serial_wait(self):
        """ シリアルデバイスの応答待ち
        """
        self.com.flush()
        time.sleep(interval)

    def get_full_information(self, dist):
        """
        素材分配ルーターにディスティネーションｃｈの情報を取得するための文字列取得。

        :param dist: str
        :return: str
        """
        text_message = self.get_information(dist)
        return chr(router_r_dict['STX']) \
            + text_message \
            + self.bbc(text_message)

    def get_full_crosspoint_set(self, dist, source):
        """
        ディスティネーションch,ソースchから素材分配ルータの制御電文の文字列取得。

        :param dist: str
        :param source: str
        :return: str
        """
        text_message = self.get_crosspoint_set(dist, source)
        return chr(router_r_dict['STX']) \
            + text_message \
            + self.bbc(text_message)

    def get_crosspoint(self, dist):
        """
        シリアルデバイスにディスティネーションchから情報を取得する電文を送信し、得た情報を標準出力に表示、
        成功失敗の結果を返す。

        :param dist: str
        :return: bool
        """

        status = False  # 成功したかのフラグ 初期値は失敗 　
        next_time = time.time()+timeout

        for x in self.get_full_information(dist):
            self.write_log(">" + self.router_chr(x))
            self.com.write(x)

        self.serial_wait()

        # 応答受信処理
        while time.time() < next_time:
            if self.com.in_waiting > 0:
                # 受信データはbytes 型
                receipt_data = self.com.read(1)
                if self.router_chr(receipt_data) == 'ACK':
                    self.write_log("<" + self.router_chr(receipt_data) + "\n")
                    break
                else:
                    return status

        self.serial_wait()

        while time.time() < next_time:
            if self.com.in_waiting > 0:
                # 受信データはbytes 型
                receipt_data = self.com.read(1)
                if self.router_chr(receipt_data) == 'STX':
                    self.write_log("<" + self.router_chr(receipt_data) + "\n")
                else:
                    break

            d_len = self.com.inWaiting()  # 受信バッファにたまってる数を確認
            if d_len > 0:
                receipt_data = self.com.read(d_len)
                if self.bbc(receipt_data[:-1]) == receipt_data[-1]:
                    self.write_log('bbc checksum is ok!\n')
                    expect = ("1010000%s%s" % (receipt_data[7:10],
                                               receipt_data[10:13])) \
                        + chr(router_r_dict['ETX'])
                    if expect == receipt_data[:14]:
                        self.write_log('data is correct\n')
                    else:
                        break

                    self.write_log("output channel is %s, input channel is %s"
                                   % (receipt_data[7:10], receipt_data[10:13]))
                self.write_log("<" + receipt_data[:13])
                self.write_log("<" + self.router_chr(receipt_data[13:14]))
                self.write_log("<" + self.router_chr(receipt_data[14:15]))
                status = True
                break
        return status

    def set_crosspoint(self, dist, source):
        """
        シリアルデバイスにディスティネーションch,ソースchから制御する電文を送信し、
        成功失敗の結果を返す。

        :param dist: str
        :param source: str
        :return: bool
        """
        status = False  # 成功したかのフラグ 初期値は失敗 　

        for x in self.get_full_crosspoint_set(dist, source):
            self.write_log(">" + self.router_chr(x))
            self.com.write(x)
        self.serial_wait()

        next_time = time.time()+timeout
        # 応答受信処理
        while time.time() < next_time:
            if self.com.in_waiting > 0:
                # 受信データはbytes 型
                receipt_data = self.com.read(1)
                if self.router_chr(receipt_data) == 'ACK':
                    self.write_log("<" + self.router_chr(receipt_data) + "\n")
                    status = True
                    break
                else:
                    self.write_log("crosspoint set error!!\n")
                    break

        return status

    def set_crosspoint_by_oa_tally(self, dist):
        """
        OA Tally信号の接点信号の状態(GPIOの状態)に基づいて、ソースchを決定し、
        NsubかTsubへの変化のあった時だけディスティネーションchに対して制御する電文を送信する。
        変化がない場合も成功として、タプルの１番目のTrueを返す。2番目に変化があったかどうかを返す。

        :param dist:
        :return: bool,bool
        """
        state = True
        ck_change = False

        if self.gpio_status_check():
            ck_change = True
            self.write_log("change state!\n")
            state = self.set_crosspoint(dist, self.get_sub_state())
        else:
            self.write_log("not change state!\n")

        return state, ck_change

    def gpio_status_check(self):
        """
        GPIOの前回の状態が記録してあるテンポラリファイルの内容と現在の状態を比較して
        NsubかTsubへの変化があればTrueを、なければFalseを返す。

        :return: bool
        """
        now_status = self.get_sub_state()
        old_status = ''

        path_name = os.path.join(tempfile.gettempdir(), temp_GPIO_filename)
        if os.path.isfile(path_name):
            with open(path_name, 'r') as f:
                old_status = f.read()

        if now_status == old_status:
            result = False
        else:
            if now_status == OA_ch:
                result = False
            else:
                result = True

                # 変化があったので書き込み処理
                with open(path_name, 'w') as f:
                    f.write(now_status)

        self.write_log("gpio_status_check is %s\n" % result)
        return result

    def gpio_history_check(self, input_ch):
        """
        GPIOの前回の状態が記録してあるテンポラリファイルの内容とイベントのピン番号のｃｈと比較して
        NsubかTsubへの変化があればTrueを、なければFalseを返す。

        :return:
        """

        now_status = input_ch

        old_status = ''

        path_name = os.path.join(tempfile.gettempdir(), temp_GPIO_filename)
        if os.path.isfile(path_name):
            with open(path_name, 'r') as f:
                old_status = f.read()

        if now_status == old_status:
            result = False
        else:
            if now_status == OA_ch:
                result = False
            else:
                result = True

                # 変化があったので書き込み処理
                with open(path_name, 'w') as f:
                    f.write(now_status)

        self.write_log("gpio_history_check is %s\n" % result)
        return result

    def set_event_detect(self, dist_ch):
        """
        GPIOイベントメッセージを受けるとset_crosspointを実行するようにセットする。

        :param dist_ch:
        :return: bool
        """

        # callbackメソッド
        def input_select(gpio_input):
            try:
                select_ch = select_sw[gpio_input]
                if self.gpio_history_check(select_ch):
                    self.set_crosspoint(dist_ch, select_ch)
            except KeyError:
                return
            # 送信時の時刻を出力
            self.write_log('\n%s\n' % datetime.datetime.now())
            self.write_log(str(gpio_input)+"\n")

        GPIO.add_event_detect(gpio_tsub, GPIO.FALLING,
                              callback=input_select, bouncetime=300)
        GPIO.add_event_detect(gpio_nsub, GPIO.FALLING,
                              callback=input_select, bouncetime=300)

        return True

    @staticmethod
    def cleanup():
        """"
        GPIOのクルーンアップ

        :return: bool
        """

        GPIO.cleanup()

        return True


if __name__ == '__main__':
    # ポーリングの場合の処理
    cr = ChangeRouter()
    # cr.write_log("状態確認")
    # cr.get_crosspoint('128')
    cr.write_log("制御指令")
    cr.set_crosspoint_by_oa_tally('128')

    cr.write_log("ソースch=%s" % cr.get_sub_state())
