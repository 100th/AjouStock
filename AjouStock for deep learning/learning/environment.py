# /learning/environment.py
# 투자할 종목의 차트 데이터를 관리하는 모듈
class Environment:

    PRICE_IDX = 4                       # 종가의 위치. 5번째 열에 있어서.

    def __init__(self, chart_data=None):
        self.chart_data = chart_data    # 주식 종목의 차트 데이터
        self.observation = None         # 현재 관측치
        self.idx = -1                   # 차트 데이터에서 현재 위치

    def reset(self):                    # idx와 observation 초기화
        self.observation = None
        self.idx = -1

    def observe(self):                  # idx를 다음 위치로 이동하고 observation을 업데이트
        if len(self.chart_data) > self.idx + 1:
            self.idx += 1
            self.observation = self.chart_data.iloc[self.idx]
            return self.observation
        return None

    def get_price(self):                # 현재 observation에서 종가를 획득
        if self.observation is not None:
            return self.observation[self.PRICE_IDX]
        return None

    def set_chart_data(self, chart_data):
        self.chart_data = chart_data
