# /data/data_management.py
# chart_data와 training_data를 생성하는 모듈
import pandas as pd
import numpy as np


def load_chart_data(fpath):     # csv파일 불러오는 함수
    chart_data = pd.read_csv(fpath, thousands=',', header=None)
    chart_data.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
    return chart_data


def preprocess(chart_data):     # 종가와 거래량의 이동 평균값 구하는 함수
    prep_data = chart_data
    windows = [5, 10, 20, 60, 120]
    for window in windows:
        prep_data['close_ma{}'.format(window)] = prep_data['close'].rolling(window).mean()
        prep_data['volume_ma{}'.format(window)] = (
            prep_data['volume'].rolling(window).mean()) # 롤링 평균 = 이동 평균
    return prep_data


def build_training_data(prep_data):     # 여러가지 비율(ratio)을 구한다.
    training_data = prep_data
    # 시가/전일종가 비율(open_lastclose_ratio) = (현재 종가 - 전일 종가) / 전일 종가
    training_data['open_lastclose_ratio'] = np.zeros(len(training_data))
    training_data.loc[1:, 'open_lastclose_ratio'] = \
        (training_data['open'][1:].values - training_data['close'][:-1].values) / \
        training_data['close'][:-1].values
    # 고가/종가 비율(high_close_ratio)
    training_data['high_close_ratio'] = \
        (training_data['high'].values - training_data['close'].values) / \
        training_data['close'].values
    # 저가/종가 비율(low_close_ratio)
    training_data['low_close_ratio'] = \
        (training_data['low'].values - training_data['close'].values) / \
        training_data['close'].values
    # 종가/전일종가 비율(close_lastclose_ratio)
    training_data['close_lastclose_ratio'] = np.zeros(len(training_data))
    training_data.loc[1:, 'close_lastclose_ratio'] = \
        (training_data['close'][1:].values - training_data['close'][:-1].values) / \
        training_data['close'][:-1].values
    # 거래량/전일거래량 비율(volume_lastvolume_ratio)
    training_data['volume_lastvolume_ratio'] = np.zeros(len(training_data))
    training_data.loc[1:, 'volume_lastvolume_ratio'] = \
        (training_data['volume'][1:].values - training_data['volume'][:-1].values) / \
        training_data['volume'][:-1]\
            .replace(to_replace=0, method='ffill') \
            .replace(to_replace=0, method='bfill').values   # 거래량 값이 0이면 이전의 0이 아닌 값으로 바꿈

    windows = [5, 10, 20, 60, 120]  # 이동평균 종가 비율, 이동평균 거래량 비율을 구함.
    for window in windows:
        # 이동평균 종가 비율 = (현재 종가 - 이동 평균) / 이동 평균
        training_data['close_ma%d_ratio' % window] = \
            (training_data['close'] - training_data['close_ma%d' % window]) / \
            training_data['close_ma%d' % window]
        training_data['volume_ma%d_ratio' % window] = \
            (training_data['volume'] - training_data['volume_ma%d' % window]) / \
            training_data['volume_ma%d' % window]
    return training_data

# chart_data = pd.read_csv(fpath, encoding='CP949', thousands=',', engine='python')
