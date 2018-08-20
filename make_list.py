# make_list.py
# Main 모듈을 통해 매매 리스트 생성. skyrocket과 save_csv 모듈 데이터 수정 가능.
# 64비트의 파이썬, 아나콘다 환경에서 실행 가능
import sys
import os
import main_before, main_after, settings
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

        self.pushButton_3.clicked.connect(self.run_skyrocket)           # 급등주 알고리즘 실행
        self.load_skyrocket()                                           # 급등주 출력

        self.pushButton_4.clicked.connect(self.run_save_csv)            # csv 저장

        self.pushButton_5.clicked.connect(self.run_main_before)         # main before
        self.pushButton_6.clicked.connect(self.run_main_after)          # main after


# 급등주 포착 ----------------------------------------------------------------
    # skyrocket.py 실행
    def run_skyrocket(self):
        skyrocket_period = self.spinBox_13.value()
        skyrocket_criteria = self.spinBox_14.value()
        skyrocket_idx = self.comboBox_4.currentText()
        skyrocket.skyrocket_run(skyrocket_period, skyrocket_criteria, skyrocket_idx)


    # skyrocket.txt 불러오기
    def load_skyrocket(self):
        f = open(os.path.join(settings.BASE_DIR, "data/list/skyrocket_list.txt"), 'rt')
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


    # Main After 실행
    def run_main_after(self):
        after_start_date = self.dateEdit_5.text()
        after_min_unit = self.spinBox_11.value()
        after_max_unit = self.spinBox_12.value()
        main_after.main_after_run(after_start_date, after_min_unit, after_max_unit)


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
