#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
change_router.pyのunittestプログラム。
シリアルのテストにserialtest.pyを利用しCIツール上でもテスト可能となっている。
"""

import unittest
import change_router
import RPi.GPIO as GPIO
import time
import serialtest
import platform
import os
import tempfile

comport = '/dev/tnt1'  # Jenkins上でテストする場合のデバイス名

# GPIOのinputメソッドを退避
tmp_input = GPIO.input

# Windows上はCOM12 、Jenkins上では/dev/tnt0
if platform.uname()[0] == 'Windows':
    comport = 'COM12'


class ChangeRouterTestCase(unittest.TestCase):
    """
    ChangeRouterクラスのテスト
    """

    def setUp(self):
        """
        テスト毎の事前準備。1つのChangeRouterのインスタンスを作成。

        :return:
        """
        print('before test')
        self.cr = change_router.ChangeRouter()

        # 前回のGPIO状態ファイルの削除
        path_name = os.path.join(tempfile.gettempdir(), change_router.temp_GPIO_filename)
        if os.path.exists(path_name):
            os.remove(path_name)

    def tearDown(self):
        """
        テスト毎の事後処理。ChangeRouterのシリアルポートのクローズ。

        :return:
        """
        print('after test')
        self.cr.com.close()

    @staticmethod
    def change_GPIO_input(ch):
        """
        GPIOの状態をセットするメソッド
        chが0で初期状態に戻す

        :param ch:int
        :return:
        """

        # GPIOのinputメソッドを再定義する
        def new_input(input_ch):
            if input_ch == ch:
                return False
            else:
                return True

        if ch != 0:
            GPIO.input = new_input
        else:
            GPIO.input = tmp_input

    def test_write_log(self):
        """
        write_logのテスト

        :return:
        """

        logname = "write_log.log"
        pathname = os.path.join(tempfile.gettempdir(), logname)
        with open(pathname, 'w') as f:
            f.write("")

        expected = "test"
        self.cr.set_log(logname)
        self.cr.write_log("test")

        with open(pathname, 'r') as f:
            actual = f.read()
        self.assertEqual(expected, actual)

    def test_write_log2(self):
        """
        write_logのテスト

        :return:
        """

        logname = "write_log.log"
        pathname = os.path.join(tempfile.gettempdir(), logname)
        with open(pathname, 'w') as f:
            f.write("")

        expected = str(change_router.gpio_tsub)
        self.cr.set_log(logname)
        self.cr.write_log(change_router.gpio_tsub)

        with open(pathname, 'r') as f:
            actual = f.read()
        self.assertEqual(expected, actual)

    def test_ChangerRouter_log(self):
        """
        logのパラメータを付与した時のコンストラクタのテスト

        :return:
        """
        logname = "write_log.log"
        pathname = os.path.join(tempfile.gettempdir(), logname)
        with open(pathname, 'w') as f:
            f.write("")

        # setupによるインスタンスcloseし、新たにlog付きでインスタンス生成
        self.cr.com.close()
        self.cr = change_router.ChangeRouter(log=logname)

        expected = "test"
        self.cr.set_log(logname)
        self.cr.write_log("test")

        with open(pathname, 'r') as f:
            actual = f.read()
        self.assertEqual(expected, actual)


    def test_bcc1(self):
        """
        bbcのテスト1。3文字分のデータを与えてテスト。

        :return:
        """
        expected = 0x60  # a ^ b ^ c = 0x61 ^ 0x62 ^ 0x63 = 0x60
        actual = ord(self.cr.bbc('abc'))
        self.assertEqual(expected, actual)

    def test_bcc2(self):
        """
        bbcのテスト2。4文字文のデータを与えてテスト。

        :return:
        """
        expected = 0x0F  # 1 ^ 2 ^ 4 ^ 8 = 0x31 ^ 0x32 ^ 0x34 ^ 0x38= 0x0F
        actual = ord(self.cr.bbc('1248'))
        self.assertEqual(expected, actual)

    def test_get_information(self):
        """
        get_informationのテスト。127chの場合の電文でテスト。

        :return:
        """
        expected = "10" + "0" + "00" + "00" + "127" + "000" + chr(0x03)
        actual = self.cr.get_information('127')
        self.assertEqual(expected, actual)

    def test_get_full_information(self):
        """
        get_full_informationのテスト。127chの場合のテスト。

        :return:
        """
        test_message = "10" + "0" + "00" + "00" + "127" + "000" + chr(0x03)
        expected = chr(0x02) + test_message + self.cr.bbc(test_message)
        actual = self.cr.get_full_information('127')
        self.assertEqual(expected, actual)

    def test_get_crosspoint_set(self):
        """
        get_crosspoint_setのテスト。127chをディスティネーション、128chをソースとしたときのテスト。

        :return:
        """
        expected = "03" + "0" + "00" + "00" + "127" + "128" + chr(0x03)
        actual = self.cr.get_crosspoint_set('127', '128')
        self.assertEqual(expected, actual)

    def test_get_full_crosspoint_set(self):
        """
        get_full_crosspoint_setのテスト。127chをディスティネーション、128chをソースとしたときのテスト。

        :return:
        """
        test_message = "03" + "0" + "00" + "00" + "127" + "128" + chr(0x03)
        expected = chr(0x02) + test_message + self.cr.bbc(test_message)
        actual = self.cr.get_full_crosspoint_set('127', '128')
        self.assertEqual(expected, actual)

    def test_get_sub_state(self):
        """
        get_sub_stateのテスト。ダミーのGPIOではOA_chが選択される。

        :return:
        """
        expected = change_router.OA_ch
        actual = self.cr.get_sub_state()
        self.assertEqual(expected, actual)

    def test_get_sub_state2(self):
        """
        get_sub_stateのテスト。ダミーのGPIOの入力を書き換えて、nSub_chになるかのテスト。

        :return:
        """

        self.change_GPIO_input(change_router.gpio_nsub)
        expected = change_router.nSub_ch
        actual = self.cr.get_sub_state()

        self.change_GPIO_input(0)
        self.assertEqual(expected, actual)

    def test_get_sub_state3(self):
        """
        get_sub_stateのテスト。ダミーのGPIOの入力を書き換えて、tSub_chになるかのテスト。

        :return:
        """
        self.change_GPIO_input(change_router.gpio_tsub)

        expected = change_router.tSub_ch
        actual = self.cr.get_sub_state()

        self.change_GPIO_input(0)
        self.assertEqual(expected, actual)

    def test_router_chr(self):
        """
        router_chrのテスト。0のデータの場合のテスト。

        :return:
        """
        expected = "'0'"
        actual = self.cr.router_chr('0')
        self.assertEqual(expected, actual)

    def test_router_chr2(self):
        """
        router_chrのテスト。0x02のデータの場合のテスト。

        :return:
        """
        expected = "STX"
        actual = self.cr.router_chr(chr(0x02))
        self.assertEqual(expected, actual)

    def test_serial_wait(self):
        """
        serial_waitのテスト。interval値を与えて、待ち時間が発生しているかを確認。

        :return:
        """
        change_router.interval = 5
        expected = time.time() + 0.5
        self.cr.serial_wait()
        actual = time.time()  # serial_waitが発生した場合、期待値より遅くなる
        print(expected, actual)
        self.assertLess(expected, actual)

    def test_serial_wait2(self):
        """
        serial_waitのテスト。ダミーでserial_wait無しの時に、結果が異なることを確認。

        :return:
        """
        change_router.interval = 5
        expected = time.time() + 0.5  # Windowsと精度がことなる為、調整値
        # self.cr.serial_wait()
        actual = time.time()  # serial_waitが発生しない場合、期待値とほぼ同じ。
        print(expected, actual)
        self.assertGreaterEqual(expected, actual)

    def test_set_crosspoint(self):
        """
        set_crosspointのテスト。ディスティネーション127ch,ソース128chの制御命令。
        成功するかどうかの確認。

        :return:
        """
        ser = serialtest.SerialTest(comport)
        ser.start()
        expected = True
        self.cr.set_crosspoint('127', '128')
        ser.stop()
        actual = ser.get_test_status()
        self.assertEqual(expected, actual)

    def test_set_crosspoint2(self):
        """
        set_crosspointのテスト。ディスティネーション127ch,ソース128chの制御命令。
        相手側に問題があった場合、失敗するかどうかの確認。

        :return:
        """
        ser = serialtest.SerialTest(comport, ng_mode=True)
        ser.start()
        expected = False
        status = self.cr.set_crosspoint('127', '128')
        ser.stop()
        actual = status
        self.assertEqual(expected, actual)

    def test_set_crosspoint_by_oa_tally(self):
        """
        set_crosspoint_by_oa_tallyのテスト。現状のGPIOの状態から、128chのディスティネーションに対して制御命令。
        成功するかの確認。デフォルトだとOA_chで、変化なし、コマンドせず完了。

        :return:
        """
        ser = serialtest.SerialTest(comport)
        ser.start()
        expected = (True, False)
        status = self.cr.set_crosspoint_by_oa_tally('128')
        ser.stop()
        actual = status
        self.assertEqual(expected, actual)

    def test_set_crosspoint_by_oa_tally2(self):
        """
        set_crosspoint_by_oa_tallyのテスト。現状のGPIOの状態から、128chのディスティネーションに対して制御命令。
        成功するかの確認。GPIOの状態をnsubとし、前回状態がないため変化あり、コマンド発行し完了。

        :return:
        """
        self.change_GPIO_input(change_router.gpio_nsub)
        ser = serialtest.SerialTest(comport)
        ser.start()
        expected = (True, True)
        status = self.cr.set_crosspoint_by_oa_tally('128')
        ser.stop()
        actual = status
        self.assertEqual(expected, actual)

    def test_set_crosspoint_by_oa_tally3(self):
        """
        set_crosspoint_by_oa_tallyのテスト。現状のGPIOの状態から、128chのディスティネーションに対して制御命令。
        成功するかの確認。GPIOの状態をnsubとするが前回の状態もnsubとする為、変化なし、コマンド発行せず完了。

        :return:
        """

        # 前回の状態ファイルの作成。ダミーの状態はnSub_ch
        with open(os.path.join(tempfile.gettempdir(), change_router.temp_GPIO_filename), 'w') as f:
            f.write(str(change_router.nSub_ch))

        self.change_GPIO_input(change_router.gpio_nsub)
        ser = serialtest.SerialTest(comport)
        ser.start()
        expected = (True, False)
        status = self.cr.set_crosspoint_by_oa_tally('128')
        ser.stop()
        actual = status
        self.assertEqual(expected, actual)

    def test_set_crosspoint_by_oa_tally4(self):
        """
        set_crosspoint_by_oa_tallyのテスト。現状のGPIOの状態から、128chのディスティネーションに対して制御命令。
        成功するかの確認。GPIOの状態をtsubとし前回の状態はnsubとする為、変化あり、コマンド発行して完了。

        :return:
        """

        # 前回の状態ファイルの作成。ダミーの状態はnSub_ch
        with open(os.path.join(tempfile.gettempdir(), change_router.temp_GPIO_filename), 'w') as f:
            f.write(str(change_router.nSub_ch))

        self.change_GPIO_input(change_router.gpio_tsub)
        ser = serialtest.SerialTest(comport)
        ser.start()
        expected = (True, True)
        status = self.cr.set_crosspoint_by_oa_tally('128')
        ser.stop()
        actual = status
        self.assertEqual(expected, actual)

    def test_get_crosspoint(self):
        """
        get_crosspointのテスト。ディスティネーション128chの情報を取得。成功するか確認。

        :return:
        """
        ser = serialtest.SerialTest(comport)
        ser.start()
        expected = True
        status = self.cr.get_crosspoint('128')
        ser.stop()
        actual = status
        self.assertEqual(expected, actual)

    def test_get_crosspoint2(self):
        """
        get_crosspointのテスト。ディスティネーション128chの情報を取得。
        相手に問題ある場合。失敗するか確認。

        :return:
        """
        ser = serialtest.SerialTest(comport, ng_mode=True)
        ser.start()
        expected = False
        status = self.cr.get_crosspoint('128')
        ser.stop()
        actual = status
        self.assertEqual(expected, actual)

    def test_GPIO_status_check(self):
        """
        GPIOの前の状態が記録されているテンポラリファイルを読み取り、現在のGPIOの状態と変化があるかを確認。
        変化があればTrueをなければFalseを返す。前の状態ファイルのない場合のテスト
        デフォルトはOA_chなので必ずFalseになる。

        :return:
        """

        expected = False

        actual = self.cr.gpio_status_check()

        self.assertEqual(expected, actual)

    def test_GPIO_status_check2(self):
        """
        GPIOの前の状態が記録されているテンポラリファイルを読み取り、現在のGPIOの状態と変化があるかを確認。
        変化があればTrueをなければFalseを返す。前の状態ファイルの中身が同じパターンテスト。
        デフォルトはOA_chなので変化はあるが必ずFalseになる。

        :return:
        """

        # 前回の状態ファイルの作成。ダミーの状態はnSub_ch
        with open(os.path.join(tempfile.gettempdir(), change_router.temp_GPIO_filename), 'w') as f:
            f.write(str(change_router.nSub_ch))

        expected = False

        actual = self.cr.gpio_status_check()

        self.assertEqual(expected, actual)

    def test_GPIO_status_check3(self):
        """
        GPIOの前の状態が記録されているテンポラリファイルを読み取り、現在のGPIOの状態と変化があるかを確認。
        変化があればTrueをなければFalseを返す。
        変化のある状態から、GPIO_status_check()を実行し、前の状態を書き込み2回目で同じになる為、
        必ずFalseになる。

        :return:
        """

        # 前回の状態ファイルの作成。ダミーの状態はnSub_ch
        with open(os.path.join(tempfile.gettempdir(), change_router.temp_GPIO_filename), 'w') as f:
            f.write(str(change_router.nSub_ch))

        # 変化があり、前回状態の書き込み
        self.cr.gpio_status_check()

        expected = False

        # 変化が無くなっているはず
        actual = self.cr.gpio_status_check()

        self.assertEqual(expected, actual)

    def test_GPIO_status_check4(self):
        """
        GPIOの前の状態が記録されているテンポラリファイルを読み取り、現在のGPIOの状態と変化があるかを確認。
        変化があればTrueをなければFalseを返す。
        前回の状態なし、GPIOをnSub_chとセットする為、変化ありとなりTrueとなる。
        必ずFalseになる。

        :return:
        """

        # ダミーGPIOのメソッドを書き換え。

        self.change_GPIO_input(change_router.gpio_nsub)

        expected = True

        # 変化が無くなっているはず
        actual = self.cr.gpio_status_check()

        self.change_GPIO_input(0)

        self.assertEqual(expected, actual)

    def test_GPIO_history_check(self):
        """
        GPIO_history_checkのテスト。比較ファイルがないためTrueになる。
        :return:
        """

        expected = True

        actual = self.cr.gpio_history_check(change_router.nSub_ch)

        self.assertEqual(expected, actual)

    def test_GPIO_history_check2(self):
        """
        GPIO_history_checkのテスト。比較ファイルをnSubとする為、イベントはｔSubでTrueになる。
        :return:
        """

        # 前回の状態ファイルの作成。ダミーの状態はnSub_ch
        with open(os.path.join(tempfile.gettempdir(), change_router.temp_GPIO_filename), 'w') as f:
            f.write(str(change_router.nSub_ch))

        expected = True

        actual = self.cr.gpio_history_check(change_router.tSub_ch)

        self.assertEqual(expected, actual)

    def test_GPIO_history_check3(self):
        """
        GPIO_history_checkのテスト。比較ファイルをnSubとする為、イベントはnSubでFalseになる。
        :return:
        """

        # 前回の状態ファイルの作成。ダミーの状態はnSub_ch
        with open(os.path.join(tempfile.gettempdir(), change_router.temp_GPIO_filename), 'w') as f:
            f.write(str(change_router.nSub_ch))

        expected = False

        actual = self.cr.gpio_history_check(change_router.nSub_ch)

        self.assertEqual(expected, actual)

    def test_GPIO_history_check4(self):
        """
        GPIO_history_checkのテスト。比較ファイルをnSubとする為、イベントはOA_chでFalseになる。
        :return:
        """

        # 前回の状態ファイルの作成。ダミーの状態はnSub_ch
        with open(os.path.join(tempfile.gettempdir(), change_router.temp_GPIO_filename), 'w') as f:
            f.write(str(change_router.nSub_ch))

        expected = False

        actual = self.cr.gpio_history_check(change_router.OA_ch)

        self.assertEqual(expected, actual)

    def test_set_event_detect(self):
        """
        ダミーのGPIOのevent_detectメソッドを呼び出し、callbackメソッドが作動さるかどうかのテスト
        nsubの接点onで前の情報なく制御命令が出るので、受信側でnsubの切り替えが来たかを確認

        :return:
        """
        expected = change_router.nSub_ch
        ser = serialtest.SerialTest(comport)
        ser.start()

        dist_ch = '128'
        self.cr.set_event_detect(dist_ch)

        GPIO.event_detect(change_router.gpio_nsub)
        actual = ser.input_ch
        ser.stop()

        self.assertEqual(expected, actual)

    def test_set_event_detect2(self):
        """
        ダミーのGPIOのevent_detectメソッドを呼び出し、callbackメソッドが作動さるかどうかのテスト
        tsubの接点onで前の情報なく制御命令が出るので、受信側でtsubの切り替えが来たかを確認

        :return:
        """
        expected = change_router.tSub_ch
        ser = serialtest.SerialTest(comport)
        ser.start()

        dist_ch = '128'
        self.cr.set_event_detect(dist_ch)

        GPIO.event_detect(change_router.gpio_tsub)
        actual = ser.input_ch
        ser.stop()

        self.assertEqual(expected, actual)

    def test_set_event_detect3(self):
        """
        ダミーのGPIOのevent_detectメソッドを呼び出し、callbackメソッドが作動さるかどうかのテスト
        nsubの接点onで前の情報をnsubとし制御命令は出ない為、受信側は初期のままかを確認

        :return:
        """

        # 前回の状態ファイルの作成。ダミーの状態はnSub_ch
        with open(os.path.join(tempfile.gettempdir(), change_router.temp_GPIO_filename), 'w') as f:
            f.write(str(change_router.nSub_ch))

        expected = '000'  # 受信側初期値ch
        ser = serialtest.SerialTest(comport)
        ser.start()

        dist_ch = '128'
        self.cr.set_event_detect(dist_ch)

        GPIO.event_detect(change_router.gpio_nsub)
        actual = ser.input_ch
        ser.stop()

        self.assertEqual(expected, actual)

    def test_set_event_detect4(self):
        """
        ダミーのGPIOのevent_detectメソッドを呼び出し、callbackメソッドが作動さるかどうかのテスト
        ありえない接点onでエラーとし制御命令は出ない為、受信側は初期のままかを確認

        :return:
        """

        # 前回の状態ファイルの作成。ダミーの状態はnSub_ch
        with open(os.path.join(tempfile.gettempdir(), change_router.temp_GPIO_filename), 'w') as f:
            f.write(str(change_router.nSub_ch))

        expected = '000'  # 受信側初期値ch
        ser = serialtest.SerialTest(comport)
        ser.start()

        dist_ch = '128'
        self.cr.set_event_detect(dist_ch)

        # ありえない信号からのイベントとする
        GPIO.event_detect(1)
        actual = ser.input_ch
        ser.stop()

        self.assertEqual(expected, actual)

    def test_cleanup(self):
        """
        GPIOの設定のクリア。問題がなければTrueが返る。

        :return:
        """
        expected = True

        actual = self.cr.cleanup()

        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
