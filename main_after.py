# main_after.py
# 강화학습 후에 실행하는 모듈
# 저장된 정책 신경망 모델을 불러와서 실행
import os
import logging
import settings
import datetime
from data import data_management, save_csv
from learner import Learner


if __name__ == '__main__':
    code_list = save_csv.load_buy_list()

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
        training_data = training_data[(training_data['date'] >= '2018-03-02') &
                                      (training_data['date'] <= '2018-08-03')]
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

        # fit()이 아니라 trade() 함수 호출
        date = datetime.datetime.strftime(datetime.datetime.today(), '%Y%m%d')
        learner.trade(balance=10000000,
                             model_path=os.path.join(settings.BASE_DIR,
                             'result/models/{}/model_{}.h5'.format(stock_code, date)))
