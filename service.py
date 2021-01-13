# -*- coding:utf-8 -*-

import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import time
import logging
import serial2tcp
import os

logging.basicConfig(
    filename = 'd:\\\\serial2tcp\\'+'serial2tcp-service.log',
    level = logging.DEBUG, 
    format="%(asctime)s %(levelname)s %(message)s"
)

class OrenoSvc (win32serviceutil.ServiceFramework):
    _svc_name_ = "serial2tcp-Service"
    _svc_display_name_ = "serial2tcp Service"
    _svc_description_= "COM11ポートにてIkegami DCC-057のシリアルを受けてSW-P-88用にTCPパケットに変換"

    # Class の初期化     
    def __init__(self,args):
        win32serviceutil.ServiceFramework.__init__(self,args)
        self.stop_event = win32event.CreateEvent(None,0,0,None)
        socket.setdefaulttimeout(60)
        self.stop_requested = False
        # serial2TcpをCOM11ポートで作成
        self.s2t = serial2tcp.Serial2Tcp('COM11')
    '''
     - サービス停止時に呼ばれるメソッド
      - win32event.SetEvent で win32event.CreateEvent(None,0,0,None) で作成したイベントハンドル（非シグナル）がセットされる
    '''
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        logging.info('サービスを停止します ...')
        self.s2t.stop()

    '''
     - サービス開始時に呼ばれるメソッド
      - servicemanager.LogMsg でログを出力している
      - self.s2t.start() を呼ぶ
    '''
    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_,'')
        )
        logging.info('serial2tcp Service を開始します...')
        # loop 
        self.s2t.run() 



if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(OrenoSvc)