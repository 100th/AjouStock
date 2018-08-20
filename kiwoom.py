# /data/kiwoom.py
# 키움증권 API로부터 데이터 얻어오고, 내 데이터 얻어오기.

import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
import time
import pandas as pd
import sqlite3


TR_REQ_TIME_INTERVAL = 0.2

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self._create_kiwoom_instance()
        self._set_signal_slots()
        self.OnReceiveChejanData.connect(self._receive_chejan_data) #_set_signal_slots 메서드에 시그널과 슬롯을 연결


    def _create_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")


    def _set_signal_slots(self):
        self.OnEventConnect.connect(self._event_connect)
        self.OnReceiveTrData.connect(self._receive_tr_data)


    def comm_connect(self):
        self.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()


    def _event_connect(self, err_code):
        if err_code == 0:
            print("connected")
        else:
            print("disconnected")
        self.login_event_loop.exit()


    def get_code_list_by_market(self, market):
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market)
        code_list = code_list.split(';')
        return code_list[:-1]


    def get_master_code_name(self, code):
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name


    def get_connect_state(self):
        ret = self.dynamicCall("GetConnectState()")
        return ret


    def set_input_value(self, id, value):
        self.dynamicCall("SetInputValue(QString, QString)", id, value)


    def comm_rq_data(self, rqname, trcode, next, screen_no):
        self.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen_no)
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()


    def _comm_get_data(self, code, real_type, field_name, index, item_name):
        ret = self.dynamicCall("CommGetData(QString, QString, QString, int, QString)", code,
                               real_type, field_name, index, item_name)
        return ret.strip()


    def _get_repeat_cnt(self, trcode, rqname):
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return ret


    def _receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        if next == '2':
            self.remained_data = True
        else:
            self.remained_data = False

        if rqname == "opt10081_req":
            self._opt10081(rqname, trcode)
        elif rqname == "opw00001_req": #_opw00001 메서드를 호출하도록
            self._opw00001(rqname, trcode)
        elif rqname == "opw00018_req": #_opw00018 메서드를 호출하도록
            self._opw00018(rqname, trcode)

        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass


    def _opt10081(self, rqname, trcode):
        data_cnt = self._get_repeat_cnt(trcode, rqname)

        for i in range(data_cnt):
            date = self._comm_get_data(trcode, "", rqname, i, "일자")
            open = self._comm_get_data(trcode, "", rqname, i, "시가")
            high = self._comm_get_data(trcode, "", rqname, i, "고가")
            low = self._comm_get_data(trcode, "", rqname, i, "저가")
            close = self._comm_get_data(trcode, "", rqname, i, "현재가")
            volume = self._comm_get_data(trcode, "", rqname, i, "거래량")

            self.ohlcv['date'].append(date)
            self.ohlcv['open'].append(int(open))
            self.ohlcv['high'].append(int(high))
            self.ohlcv['low'].append(int(low))
            self.ohlcv['close'].append(int(close))
            self.ohlcv['volume'].append(int(volume))


    def send_order(self, rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no):
        #주식 주문에 대한 정보를 서버로 전송
        self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                         [rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no])


    def get_chejan_data(self, fid): #체결 잔고 데이터 가져오기
        ret = self.dynamicCall("GetChejanData(int)", fid)
        return ret


    def _receive_chejan_data(self, gubun, item_cnt, fid_list): #OnReceiveChejanData 이벤트가 발생할 때 호출되는 _receive_chejan_data
        print(gubun)
        print(self.get_chejan_data(9203)) #주문번호
        print(self.get_chejan_data(302)) #종목명
        print(self.get_chejan_data(900)) #주문수량
        print(self.get_chejan_data(901)) #주문가격


    def get_login_info(self, tag): #계좌 정보 및 로그인 사용자 정보를 얻어오는 메서드
        ret = self.dynamicCall("GetLoginInfo(QString)", tag)
        return ret


    def _opw00001(self, rqname, trcode): #OnReceiveTrData 이벤트가 발생할 때 수신 데이터를 가져오는 함수
        d2_deposit = self._comm_get_data(trcode, "", rqname, 0, "d+2추정예수금")
        self.d2_deposit = Kiwoom.change_format(d2_deposit) #포맷 변경


    @staticmethod
    #입력된 문자열에 대해 lstrip 메서드를 통해 문자열 왼쪽에 존재하는 '-' 또는 '0'을 제거
    #format 함수를 통해 천의 자리마다 콤마를 추가한 문자열로 변경
    def change_format(data):
        strip_data = data.lstrip('-0')
        if strip_data == '' or strip_data == '.00':
            strip_data = '0'

        format_data = format(int(float(strip_data)), ',d')
        if data.startswith('-'):
            format_data = '-' + format_data

        return format_data


    @staticmethod
    #수익률에 대한 포맷 변경
    def change_format2(data):
        strip_data = data.lstrip('-0')

        if strip_data == '':
            strip_data = '0'

        if strip_data.startswith('.'):
            strip_data = '0' + strip_data

        if data.startswith('-'):
            strip_data = '-' + strip_data

        return strip_data


    #싱글 데이터를 통해 계좌에 대한 평가 잔고 데이터를 제공하며 멀티 데이터를 통해 보유 종목별 평가 잔고 데이터를 제공
    def _opw00018(self, rqname, trcode):
        # single data
        total_purchase_price = self._comm_get_data(trcode, "", rqname, 0, "총매입금액")
        total_eval_price = self._comm_get_data(trcode, "", rqname, 0, "총평가금액")
        total_eval_profit_loss_price = self._comm_get_data(trcode, "", rqname, 0, "총평가손익금액")
        total_earning_rate = self._comm_get_data(trcode, "", rqname, 0, "총수익률(%)") #실 서버 용
        estimated_deposit = self._comm_get_data(trcode, "", rqname, 0, "추정예탁자산")

        self.opw00018_output['single'].append(total_earning_rate)
        self.opw00018_output['single'].append(Kiwoom.change_format(total_purchase_price))
        self.opw00018_output['single'].append(Kiwoom.change_format(total_eval_price))
        self.opw00018_output['single'].append(Kiwoom.change_format(total_eval_profit_loss_price))

        total_earning_rate = Kiwoom.change_format(total_earning_rate) #모의 서버 용

        # if self.get_server_gubun(): #실 서버와 모의 서버 구분
        #     total_earning_rate = float(total_earning_rate) / 100
        #     total_earning_rate = str(total_earning_rate)

        self.opw00018_output['single'].append(total_earning_rate)
        self.opw00018_output['single'].append(Kiwoom.change_format(estimated_deposit))

        # multi data
        # 멀티 데이터를 통해 보유 종목별로 평가 잔고 데이터 가져오기
        rows = self._get_repeat_cnt(trcode, rqname) #보유 종목의 개수 얻어오기
        for i in range(rows): #해당 개수 만큼 반복
            name = self._comm_get_data(trcode, "", rqname, i, "종목명")
            quantity = self._comm_get_data(trcode, "", rqname, i, "보유수량")
            purchase_price = self._comm_get_data(trcode, "", rqname, i, "매입가")
            current_price = self._comm_get_data(trcode, "", rqname, i, "현재가")
            eval_profit_loss_price = self._comm_get_data(trcode, "", rqname, i, "평가손익")
            earning_rate = self._comm_get_data(trcode, "", rqname, i, "수익률(%)")

            quantity = Kiwoom.change_format(quantity)
            purchase_price = Kiwoom.change_format(purchase_price)
            current_price = Kiwoom.change_format(current_price)
            eval_profit_loss_price = Kiwoom.change_format(eval_profit_loss_price)
            earning_rate = Kiwoom.change_format2(earning_rate)

            self.opw00018_output['multi'].append([name, quantity, purchase_price, current_price, eval_profit_loss_price, earning_rate])


    def reset_opw00018_output(self): #얻어온 데이터를 인스턴스 변수에 저장하기 위해
        self.opw00018_output = {'single': [], 'multi': []}


    # #실 서버로 접속할 때와 모의투자 서버로 접속할 때 제공되는 데이터 형식이 다르기에. 실 서버는 수익률이 소수점 없이
    # def get_server_gubun(self):
    #     ret = self.dynamicCall("KOA_Functions(QString, QString)", "GetServerGubun", "")
    #     return ret


"""
#'D+2추정예수금'을 잘 얻어오는지 확인
if __name__ == "__main__":
    app = QApplication(sys.argv)
    kiwoom = Kiwoom()
    kiwoom.comm_connect()

    kiwoom.set_input_value("계좌번호", "xxxxxxxxx")
    kiwoom.set_input_value("비밀번호", "xxxxx")
    kiwoom.comm_rq_data("opw00001_req", "opw00001", 0, "2000")

    print(kiwoom.d2_deposit)


#'계좌정보' 잘 얻어오는지 확인
if __name__ == "__main__":
    app = QApplication(sys.argv)
    kiwoom = Kiwoom()
    kiwoom.comm_connect()

    account_number = kiwoom.get_login_info("ACCNO")
    account_number = account_number.split(';')[0]

    kiwoom.set_input_value("계좌번호", account_number)
    kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")
"""
