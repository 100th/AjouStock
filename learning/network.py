# /learning/network.py
# 투자 행동을 결정하기 위해 신경망을 관리
# import tensorflow as tf
import numpy as np
from keras.models import Sequential
from keras.layers import Activation, LSTM, Dense, BatchNormalization
from keras.optimizers import sgd


class Network:    # Keras를 사용하여 LSTM 신경망 구성.
    def __init__(self, input_dim=0, output_dim=0, lr=0.01):
        self.input_dim = input_dim
        self.lr = lr

        self.model = Sequential()   # 전체 신경망 구성

        # 세 개의 LSTM 층을 256 차원으로 구성하고, dropout을 50%로 정하여 과적합을 피함.
        self.model.add(LSTM(256, input_shape=(1, input_dim), return_sequences=True, stateful=False, dropout=0.5))
        self.model.add(BatchNormalization())
        self.model.add(LSTM(256, return_sequences=True, stateful=False, dropout=0.5))
        self.model.add(BatchNormalization())
        self.model.add(LSTM(256, return_sequences=False, stateful=False, dropout=0.5))
        self.model.add(BatchNormalization())        # 노드 추가
        self.model.add(Dense(output_dim))
        self.model.add(Activation('sigmoid'))

        # 학습 알고리즘 : 확률적 경사 하강법(SGD), 학습 속도(Learning rate, LR) : 0.01
        self.model.compile(optimizer=sgd(lr=lr), loss='mse')
        self.prob = None


    def reset(self):      # prob 변수 초기화
        self.prob = None


    def predict(self, sample):  # 신경망을 통해 투자 행동별 확률 계산
        self.prob = self.model.predict(np.array(sample).reshape((1, -1, self.input_dim)))[0] # 2차원 배열로 재구성
        return self.prob


    def train_on_batch(self, x, y): # 입력으로 들어온 학습 데이터 집합 x와 레이블 y로 정책 신경망을 학습
        return self.model.train_on_batch(x, y)


    def save_model(self, model_path):   # 학습한 정책 신경망을 파일로 저장
        if model_path is not None and self.model is not None:
            self.model.save_weights(model_path, overwrite=True) # save_weights()로 HDF5 파일로 저장


    def load_model(self, model_path):   # 저장한 정책 신경망을 불러오기 위한 함수
        if model_path is not None:
            self.model.load_weights(model_path)
