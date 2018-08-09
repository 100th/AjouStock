# trading.py
# Kiwoom API를 이용해 실제 트레이딩 하는 모듈
import sys
import os
import kiwoom, main_before, main_after, settings, test
from data import skyrocket, save_csv
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QAxContainer import *


form_class = uic.loadUiType("AjouStock.ui")[0]


class AjouStock(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.kiwoom = Kiwoom()
        self.kiwoom.comm_connect()          # 키움 로그인

        self.trade_stocks_done = False      # 자동 주문

        self.timer = QTimer(self)
        self.timer.start(1000)                      # 1초에 한 번씩 주기적으로 timeout 시그널 발생
        self.timer.timeout.connect(self.timeout)    # timeout 시그널이 발생할 때 이를 처리할 슬롯으로 self.timeout을 설정
                                                    # StatusBar 위젯에 서버 연결 상태 및 현재 시간을 출력

        self.lineEdit.textChanged.connect(self.code_changed)    # lineEdit 객체가 변경될 때 호출되는 슬롯을 지정
        self.pushButton_2.clicked.connect(self.send_order)        # 현금주문

        accouns_num = int(self.kiwoom.get_login_info("ACCOUNT_CNT"))    # 계좌 정보를 QComboBox 위젯에 출력하는 코드
        accounts = self.kiwoom.get_login_info("ACCNO")                  # 로그인 정보 가져오기
        accounts_list = accounts.split(';')[0:accouns_num]              # 계좌가 여러 개인 경우 각 계좌는';'를 통해 구분

        self.comboBox.addItems(accounts_list)
        self.pushButton.clicked.connect(self.check_balance)             # 시그널과 슬롯을 연결

        self.load_buy_sell_list()                                       # 선정 종목 리스트 출력

        self.pushButton_3.clicked.connect(self.run_skyrocket)           # 급등주 포착
        self.load_skyrocket()                                           # 급등주 출력

        self.pushButton_4.clicked.connect(self.run_save_csv)            # csv 저장

        self.pushButton_5.clicked.connect(self.run_main_before)         # main before
        self.pushButton_6.clicked.connect(self.run_main_after)          # main after


    # 시간 체크 및 서버 연결 상태 확인
    def timeout(self):
        market_start_time = QTime(9, 0, 0)              # 시간이 9시를 지났고 주문이 안됐을 때 trade_stocks 호출
        current_time = QTime.currentTime()

        if current_time > market_start_time and self.trade_stocks_done is False:    # 장이 시작할 때 주문을 넣으려면 timeout에서 시간 체크
            self.trade_stocks()
            self.trade_stocks_done = True

        text_time = current_time.toString("hh:mm:ss")
        time_msg = "Current Time : " + text_time

        state = self.kiwoom.GetConnectState()
        if state == 1:
            state_msg = "Connecting server"
        else:
            state_msg = "Server not connected"

        self.statusbar.showMessage(state_msg + " | " + time_msg)


# 수동 주문 ----------------------------------------------------------------
    # 종목 명 입력하면 종목코드 자동 생성
    def code_changed(self):
        code = self.lineEdit.text()
        name = self.kiwoom.get_master_code_name(code)
        self.lineEdit_2.setText(name)


    # 수동 주문 버튼 클릭 시
    def send_order(self):
        order_type_lookup = {'신규매수': 1, '신규매도': 2, '매수취소': 3, '매도취소': 4}
        hoga_lookup = {'지정가': "00", '시장가': "03"}

        account = self.comboBox.currentText()
        order_type = self.comboBox_2.currentText()
        code = self.lineEdit.text()
        hoga = self.comboBox_3.currentText()
        num = self.spinBox.value()
        price = self.spinBox_2.value()

        self.kiwoom.send_order("send_order_req", "0101", account, order_type_lookup[order_type], code, num, price, hoga_lookup[hoga], "")
        QMessageBox.about(self, "수동 주문 완료")


    # 계좌 조회 버튼 클릭 시 (잔고 및 보유종목 호출)
    def check_balance(self):
        self.kiwoom.reset_opw00018_output()
        account_number = self.kiwoom.get_login_info("ACCNO")
        account_number = account_number.split(';')[0]

        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")

        while self.kiwoom.remained_data:
            time.sleep(0.2)
            self.kiwoom.set_input_value("계좌번호", account_number)
            self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 2, "2000")

        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00001_req", "opw00001", 0, "2000")

        item = QTableWidgetItem(self.kiwoom.d2_deposit)
        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.tableWidget.setItem(0, 0, item)

        for i in range(1, 6):
            item = QTableWidgetItem(self.kiwoom.opw00018_output['single'][i - 1])
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.tableWidget.setItem(0, i, item)

        self.tableWidget.resizeRowsToContents()

        item_count = len(self.kiwoom.opw00018_output['multi'])
        self.tableWidget_2.setRowCount(item_count)

        for j in range(item_count):
            row = self.kiwoom.opw00018_output['multi'][j]
            for i in range(len(row)):
                item = QTableWidgetItem(row[i])
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.tableWidget_2.setItem(j, i, item)

        self.tableWidget_2.resizeRowsToContents()

        self.timer2 = QTimer(self)                  # 실시간 조회 체크박스
        self.timer2.start(1000*10)                  # 10초에 한 번
        self.timer2.timeout.connect(self.timeout2)

        QMessageBox.about(self, "계좌 조회 완료")


    # 실시간 조회 체크박스 확인
    def timeout2(self):
        if self.checkBox.isChecked():
            self.check_balance()


# buy list, sell list 읽기 ----------------------------------------------------------------
    # buy_list.txt와 sell_list.txt 읽는 함수
    def load_buy_sell_list(self):
        f = open("buy_list.txt", 'rt')
        buy_list = f.readlines()
        f.close()

        f = open("sell_list.txt", 'rt')
        sell_list = f.readlines()
        f.close()

        row_count = len(buy_list) + len(sell_list)
        self.tableWidget_3.setRowCount(row_count)

        # buy list
        for j in range(len(buy_list)):
            row_data = buy_list[j]
            split_row_data = row_data.split(';')
            split_row_data[1] = self.kiwoom.get_master_code_name(split_row_data[1].rsplit())

            for i in range(len(split_row_data)):
                item = QTableWidgetItem(split_row_data[i].rstrip())
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.tableWidget_3.setItem(j, i, item)

        # sell list
        for j in range(len(sell_list)):
            row_data = sell_list[j]
            split_row_data = row_data.split(';')
            split_row_data[1] = self.kiwoom.get_master_code_name(split_row_data[1].rstrip())

            for i in range(len(split_row_data)):
                item = QTableWidgetItem(split_row_data[i].rstrip())
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.tableWidget_3.setItem(len(buy_list) + j, i, item)

        self.tableWidget_3.resizeRowsToContents()


    # 장이 시작하면 매매 리스트에 선정된 종목에 대해 자동으로 주문하는 함수
    def trade_stocks(self):
        hoga_lookup = {'limits': "00", 'market': "03"}

        f = open("buy_list.txt", 'rt')
        buy_list = f.readlines()
        f.close()

        f = open("sell_list.txt", 'rt')
        sell_list = f.readlines()
        f.close()

        account = self.comboBox.currentText()           # 주문할 때 필요한 계좌 정보

        # 매수
        for row_data in buy_list:
            split_row_data = row_data.split(';')
            hoga = split_row_data[2]
            code = split_row_data[1]
            num = split_row_data[3]
            price = split_row_data[4]

            if split_row_data[-1].rstrip() == 'before':
                self.kiwoom.send_order("send_order_req", "0101", account, 1, code, num, price, hoga_lookup[hoga], "")

        # 매도
        for row_data in sell_list:
            split_row_data = row_data.split(';')
            hoga = split_row_data[2]
            code = split_row_data[1]
            num = split_row_data[3]
            price = split_row_data[4]

            if split_row_data[-1].rstrip() == 'before':
                self.kiwoom.send_order("send_order_req", "0101", account, 2, code, num, price, hoga_lookup[hoga], "")

        # 주문 여부 업데이트
        for i, row_data in enumerate(buy_list):
            buy_list[i] = buy_list[i].replace("before", "complete")

        f = open("buy_list.txt", 'wt')
        for row_data in buy_list:
            f.write(row_data)
        f.close()

        for i, row_data in enumerate(sell_list):
            sell_list[i] = sell_list[i].replace("before", "complete")

        f = open("sell_list.txt", 'wt')
        for row_data in sell_list:
            f.write(row_data)
        f.close()


# 급등주 포착 ----------------------------------------------------------------
    # skyrocket.py 실행
    def run_skyrocket(self):
        skyrocket_period = self.spinBox_13.value()
        skyrocket_ratio = self.spinBox_14.value()
        # TODO


    # skyrocket.txt 불러오기
    def load_skyrocket(self):
        f = open("skyrocket_list.txt", 'rt')
        skyrocket_list = f.readlines()
        f.close()

        row_count = len(skyrocket_list)
        self.tableWidget_4.setRowCount(row_count)

        for j in range(len(skyrocket_list)):
            row_data = skyrocket_list[j]
            split_row_data = row_data.split(';')

            for i in range(len(split_row_data)):
                item = QTableWidgetItem(split_row_data[i].rstrip())
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.tableWidget_4.setItem(j, i, item)

        self.tableWidget_4.resizeRowsToContents()


# 급등주 OHLCV를 csv로 저장 ----------------------------------------------------------------
    # save_csv.py 실행
    def run_save_csv(self):
        csv_start_date = self.dateEdit.text()
        save_csv.save_csv_run(csv_start_date)
        QMessageBox.about(self, "급등한 종목의 OHLCV를 csv로 저장 완료")


# Main 실행 ----------------------------------------------------------------
    # Main Before 실행
    def run_main_before(self):
        before_start_date = self.dateEdit.text()
        before_end_date = self.dateEdit_4.text()
        before_min_unit = self.spinBox_3.value()
        before_max_unit = self.spinBox_4.value()
        before_delayed = self.doubleSpinBox.value()
        before_learning = self.doubleSpinBox_2.value()
        before_balance = self.spinBox_7.value()
        before_epoch = self.spinBox_8.value()
        before_epsilon = self.doubleSpinBox_3.value()
        main_before.main_before_run(before_start_date, before_end_date, before_min_unit,
                        before_max_unit, before_delayed, before_learning, before_balance,
                        before_epoch, before_epsilon)
        QMessageBox.about(self, "강화학습 모델 생성 완료")


    # Main After 실행
    def run_main_after(self):
        after_start_date = self.dateEdit_5.text()
        after_min_unit = self.spinBox_11.value()
        after_max_unit = self.spinBox_12.value()
        main_after.main_after_run(after_start_date, after_min_unit, after_max_unit)
        QMessageBox.about(self, "시뮬레이션 실행 완료")


# 진행 상황 ----------------------------------------------------------------
    #
    def statusbar(self):
        pass
        # TODO


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ajou = AjouStock()
    ajou.show()
    app.exec_()
