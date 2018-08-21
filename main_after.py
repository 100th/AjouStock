# main_after.py
# 강화학습 후에 실행하는 모듈
# 저장된 정책 신경망 모델을 불러와서 실행
import os
import logging
import settings
import datetime
from data import data_management, save_csv
from learner import Learner


def main_after_run(after_start_date, after_min_unit, after_max_unit):
    code_list = save_csv.load_skyrocket_list()

    min_trading_unit_buy_list = []
    min_trading_unit_sell_list = []
    code_list_buy = []
    code_list_sell = []

    for i in range(len(code_list)):
        stock_code = code_list[i]

        # 로그 기록
        log_dir = os.path.join(settings.BASE_DIR, 'result/logs/%s' % stock_code)
        timestr = settings.get_time_str()
        file_handler = logging.FileHandler(filename=os.path.join(
            log_dir, "%s_%s.log" % (stock_code, timestr)), encoding='utf-8')
        stream_handler = logging.StreamHandler()
        file_handler.setLevel(logging.DEBUG)
        stream_handler.setLevel(logging.INFO)
        logging.basicConfig(format="%(message)s",
                            handlers=[file_handler, stream_handler], level=logging.DEBUG)

        # 데이터 준비
        chart_data = data_management.load_chart_data(
            os.path.join(settings.BASE_DIR, 'data/csv_data/{}.csv'.format(stock_code)))
        prep_data = data_management.preprocess(chart_data)
        training_data = data_management.build_training_data(prep_data)

        # 기간 필터링
        today = datetime.datetime.strftime(datetime.datetime.today(), '%Y%m%d')
        training_data = training_data[(training_data['date'] >= after_start_date) &
                                      (training_data['date'] <= today)]
        training_data = training_data.dropna()

        # 차트 데이터 분리
        features_chart_data = ['date', 'open', 'high', 'low', 'close', 'volume']
        chart_data = training_data[features_chart_data]

        # 학습 데이터 분리
        features_training_data = [
            'open_lastclose_ratio', 'high_close_ratio', 'low_close_ratio',
            'close_lastclose_ratio', 'volume_lastvolume_ratio',
            'close_ma5_ratio', 'volume_ma5_ratio',
            'close_ma10_ratio', 'volume_ma10_ratio',
            'close_ma20_ratio', 'volume_ma20_ratio',
            'close_ma60_ratio', 'volume_ma60_ratio',
            'close_ma120_ratio', 'volume_ma120_ratio']
        training_data = training_data[features_training_data]

        # 비 학습 투자 시뮬레이션 시작
        learner = Learner(
            stock_code=stock_code,          # 종목 코드
            chart_data=chart_data,          # 차트 데이터
            training_data=training_data,    # 학습 데이터
            min_trading_unit=1,             # 최소 투자 단위
            max_trading_unit=3)             # 최대 투자 단위

        # trade() 함수 호출
        validity, action, min_trading_unit = learner.trade(balance=10000000,
                                                model_path=os.path.join(settings.BASE_DIR,
                                                'result/models/{}/model_{}.h5'.format(stock_code, today)))

        if validity == True:
            if action == 0:      # 매수
                min_trading_unit_buy_list.append(min_trading_unit)
                code_list_buy.append(stock_code)

            elif action == 1:    # 매도
                min_trading_unit_sell_list.append(min_trading_unit)
                code_list_sell.append(stock_code)

    # buy_list.txt와 sell_list.txt로 저장
    b_list = open(os.path.join(settings.BASE_DIR, "data/list/buy_list.txt"), "wt")
    for i in range(len(code_list_buy)):
        b_list.writelines("buy;" + str(code_list_buy[i]) + ";market;" + str(min_trading_unit_buy_list[i]) + ";0;before\n")
    b_list.close()

    s_list = open(os.path.join(settings.BASE_DIR, "data/list/sell_list.txt"), "wt")
    for i in range(len(code_list_sell)):
        s_list.writelines("sell;" + str(code_list_sell[i]) + ";market;" + str(min_trading_unit_sell_list[i]) + ";0;before\n")
    s_list.close()


# agent의 act 함수 참고하여 행동에 따른 세부 설정 적용하기
