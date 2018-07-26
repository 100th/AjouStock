# /data/make_data.py
# 급등주 포착 알고리즘으로 구매할 종목 추천
########### 해당 종목 엑셀 파일 저장 추가 구현 필요 ##############
import sys
from PyQt5.QtWidgets import *
from . import kiwoom
import time
from pandas import DataFrame
import datetime
import numpy as np


MARKET_KOSPI   = 0
MARKET_KOSDAQ  = 10

class MakeData:
    def __init__(self):
        self.kiwoom = kiwoom.Kiwoom()
        self.kiwoom.comm_connect()
        self.get_code_list()


    def get_code_list(self):    # 종목 코드 가져오기
        self.kospi_codes = self.kiwoom.get_code_list_by_market(MARKET_KOSPI)
        self.kosdaq_codes = self.kiwoom.get_code_list_by_market(MARKET_KOSDAQ)


    def get_ohlcv(self, code, start):   # 오늘 날짜를 시작으로 과거 거래일별로 데이터를 가져옴
        self.kiwoom.ohlcv = {'date': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}

        self.kiwoom.set_input_value("종목코드", code)
        self.kiwoom.set_input_value("기준일자", start)
        self.kiwoom.set_input_value("수정주가구분", 1)
        self.kiwoom.comm_rq_data("opt10081_req", "opt10081", 0, "0101")
        time.sleep(3.6)       # 여기가 문제 !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        df = DataFrame(self.kiwoom.ohlcv, columns=['open', 'high', 'low', 'close', 'volume'], index=self.kiwoom.ohlcv['date'])
        return df


    def check_skyrocket(self, code):     # 급등주 포착 알고리즘
        today = datetime.datetime.today().strftime("%Y%m%d")
        df = self.get_ohlcv(code, today)
        volumes = df['volume']

        if len(volumes) < 21:   # 최근에 상장된 종목이라면 데이터가 충분하지 않으므로 걸러내기
            return False

        sum_vol20 = 0   # 일별 거래량 누적
        today_vol = 0   # 조회 시작일 거래량

        for i, vol in enumerate(volumes):
            if i == 0:
                today_vol = vol
            elif 1 <= i <= 20:
                sum_vol20 += vol
            else:
                break

        avg_vol20 = sum_vol20 / 20     # 20일의 평균 거래량을 계산한 후 조회 시작일의 거래량과 비교
        if today_vol > avg_vol20 * 10:
            return True     # 만약 조회 시작일의 거래량이 평균 거래량을 1,000% 초과한다면 True를 반환


    def update_buy_list(self, buy_list):
        f = open("buy_list.txt", "wt")
        for code in buy_list:
            f.writelines("매수;"+ code + ";시장가;10;0;매수전\n")   # 개수는 수정해야 함
        f.close()


    # 매도 구현
    # def update_sell_list(self, sell_list):
    #     f = open("sell_list.txt", "wt")
    #     for code in sell_list:
    #         f.writelines("매도;"+ code + ";시장가;10;0;매도전\n")
    #     f.close()


    def run(self):      # 실행
        buy_list = []
        num = len(self.kosdaq_codes)

        for i, code in enumerate(self.kosdaq_codes):
            print(i, '/', num)
            if self.check_skyrocket(code):
                #print("급등주: ", code)
                #print("급등주: %s, %s" % (code, self.kiwoom.get_master_code_name(code)))
                buy_list.append(code)

        self.update_buy_list(buy_list)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    makedata = MakeData()
    makedata.run()


"""
* 급등주 포착 알고리즘
특정 거래일의 거래량이 이전 시점의 평균 거래량보다 1000% 이상 급증하는 종목을 매수
'이전 시점의 평균 거래량'을 특정 거래일 이전의 20일(거래일 기준) 동안의 평균 거래량으로 정의
'거래량 급증'은 특정 거래일의 거래량이 평균 거래량보다 1000% 초과일 때 급등한 것으로 정의
"""
