# /learner.py
# 정책 학습기 클래스를 가지고 일련의 학습 데이터를 준비하고 정책 신경망을 학습
import os
import locale   # 통화(currency) 문자열 포맷
import logging  # 학습 과정 중에 정보 기록
import numpy as np
import settings
from learning.agent import Agent
from learning.environment import Environment
# from learning.network import Network
from learning.visualizer import Visualizer

logger = logging.getLogger(__name__)
locale.setlocale(locale.LC_ALL, 'ko_KR.UTF-8')


class Learner:
    def __init__(self, stock_code, chart_data, training_data=None, min_trading_unit=1,
                max_trading_unit=2, delayed_reward_threshold=.05, lr=0.01):
        self.stock_code = stock_code
        self.chart_data = chart_data
        self.environment = Environment(chart_data)
        self.agent = Agent(self.environment,
                           min_trading_unit=min_trading_unit,
                           max_trading_unit=max_trading_unit,
                           delayed_reward_threshold=delayed_reward_threshold)
        self.training_data = training_data
        self.sample = None
        self.training_data_idx = -1
        # 신경망 입력 크기(17개) = 학습 데이터의 크기(15개) + agent 상태 크기(2개)
        self.num_features = self.training_data.shape[1] + self.agent.STATE_DIM
        self.network = Network(
            input_dim=self.num_features, output_dim=self.agent.NUM_ACTIONS, lr=lr)
        self.visualizer = Visualizer()


    def reset(self):    # Epoch 초기화 함수
        self.sample = None
        self.training_data_idx = -1 # 학습 데이터를 읽어가면서 이 값은 1씩 증가


# -----------------------------------------------------------------------------------------
    def fit(self,            # 학습 함수 선언 부분. 핵심 함수.
        num_epoches=1000,    # 수행할 반복 학습의 전체 횟수
        max_memory=60,       # 배치 학습 데이터를 만들기 위해 과거 데이터를 저장할 배열
        balance=10000000,    # Agent의 초기 투자 자본금을 정해주기 위한 인자
        discount_factor=0,   # 지연 보상이 발생했을 때, '직전 발생 지점 ~ 현재 발생 지점' 전체에 현재 지연 보상 적용
                             # 먼 과거의 행동일수록 지연 보상을 약하게(할인 적용). 판단 근거가 흐려지기 때문에
        start_epsilon=.5,    # 초기 탐험 (무작위 투자) 비율
        learning=True):      # 학습 유무를 정함. 학습을 마치면 학습된 정책 신경망 모델이 만들어진다.
                             # - True : 학습을 해서 정책 신경망 모델을 만듦
                             # - False : 학습한 모델로 투자 시뮬레이션만
        logger.info("LR: {lr}, DF: {discount_factor}, "
                    "TU: [{min_trading_unit}, {max_trading_unit}], "
                    "DRT: {delayed_reward_threshold}".format(
            lr=self.network.lr,
            discount_factor=discount_factor,
            min_trading_unit=self.agent.min_trading_unit,
            max_trading_unit=self.agent.max_trading_unit,
            delayed_reward_threshold=self.agent.delayed_reward_threshold))

        self.visualizer.prepare(self.environment.chart_data)

        # Visualizer 결과 저장 폴더 준비
        epoch_summary_dir = os.path.join(
            settings.BASE_DIR, 'result/epoch_summary/%s/epoch_summary_%s' % (
                self.stock_code, settings.timestr))
        if not os.path.isdir(epoch_summary_dir):
            os.makedirs(epoch_summary_dir)

        # 초기 자본금 설정
        self.agent.set_balance(balance)

        # 초기화
        max_portfolio_value = 0
        epoch_win_cnt = 0

        # 학습 반복
        for epoch in range(num_epoches):
            loss = 0.               # 신경망의 결과가 학습 데이터와 얼마나 차이가 있는지 (낮을 수록 좋음)
            itr_cnt = 0             # 수행한 Epoch 수
            win_cnt = 0             # 수행한 Epoch 중에서 수익이 발생한 Epoch 수
            exploration_cnt = 0     # 무작위 투자를 수행한 횟수
            batch_size = 0
            pos_learning_cnt = 0    # 수익이 발생하여 긍정적 지연 보상을 준 수
            neg_learning_cnt = 0    # 손실이 발생하여 부정적 지연 보상을 준 수

            # 초기화
            memory_sample = []          # 샘플
            memory_action = []          # 행동
            memory_reward = []          # 즉시보상
            memory_prob = []            # 정책 신경망의 출력
            memory_pv = []              # 포트폴리오 가치
            memory_num_stocks = []      # 보유 주식 수
            memory_exp_idx = []         # 탐험 위치
            memory_learning_idx = []    # 학습 위치

            self.environment.reset()
            self.agent.reset()
            self.network.reset()
            self.reset()

            self.visualizer.clear([0, len(self.chart_data)])    # 2, 3, 4번째 차트 초기화

            # 학습을 진행할 수록 탐험 비율 감소
            if learning:
                epsilon = start_epsilon * (1. - float(epoch) / (num_epoches - 1))
            else:
                epsilon = 0

            while True:
                # 샘플 생성
                next_sample = self._build_sample()
                if next_sample is None:
                    break

                # 정책 신경망 또는 탐험에 의한 행동 결정
                # 정책 신경망의 출력 = 매매 했을 때 PV를 높일 확률
                # 결정한 행동 : action, 결정에 대한 확신 : confidence, 무작위 투자 유무 : exploration.
                action, confidence, exploration = self.agent.decide_action(
                    self.network, self.sample, epsilon)

                # 결정한 행동을 수행하고, 즉시 보상과 지연 보상 획득.
                immediate_reward, delayed_reward = self.agent.act(action, confidence)

                min_trading_unit_temp = self.agent.decide_trading_unit(confidence)
                validity_temp = self.agent.validate_action(action)

                # 맨 마지막 training_data_idx에서 어떤 행동을 해야할지 찾아내기
                if learning == False and len(self.training_data) == self.training_data_idx + 1:
                    print("-" * 80)
                    print("Length of training_data", len(self.training_data))
                    print("training_data_idx : ", self.training_data_idx)
                    print("validity_temp : ", validity_temp)
                    print("action : ", action)
                    print("confidence : ", confidence)
                    print("min_trading_unit_temp : ", min_trading_unit_temp)
                    print("-" * 80)

                    return validity_temp, action, min_trading_unit_temp

                # 행동과 그 결과를 메모리에 저장
                # 목적 : (1) 학습에서 배치 학습 데이터로 사용   (2) Visualizer에서 차트 그릴 때 사용
                memory_sample.append(next_sample)
                memory_action.append(action)
                memory_reward.append(immediate_reward)
                memory_pv.append(self.agent.portfolio_value)
                memory_num_stocks.append(self.agent.num_stocks)
                memory = [(
                    memory_sample[i],
                    memory_action[i],
                    memory_reward[i])
                    for i in list(range(len(memory_action)))[-max_memory:]]

                if exploration:
                    memory_exp_idx.append(itr_cnt)
                    memory_prob.append([np.nan] * Agent.NUM_ACTIONS) # 무작위 투자시엔 Nan값
                else:
                    memory_prob.append(self.network.prob)

                # 반복에 대한 정보 갱신
                batch_size += 1                              # 배치 크기
                itr_cnt += 1                                 # 반복 카운팅 횟수
                exploration_cnt += 1 if exploration else 0   # 무작위 투자 횟수
                win_cnt += 1 if delayed_reward > 0 else 0    # 수익이 발생한 횟수

                if delayed_reward == 0 and batch_size >= max_memory:    # 메모리가 꽉차면
                    delayed_reward = immediate_reward                   # 즉시 보상으로 지연 보상 대체
                    self.agent.base_portfolio_value = self.agent.portfolio_value

                if learning and delayed_reward != 0:    # 학습 모드 & 지연 보상 존재 -> 정책 신경망 갱신
                    batch_size = min(batch_size, max_memory)
                    x, y = self._get_batch(
                        memory, batch_size, discount_factor, delayed_reward)
                    if len(x) > 0:
                        if delayed_reward > 0:
                            pos_learning_cnt += 1
                        else:
                            neg_learning_cnt += 1
                        # 정책 신경망 갱신
                        loss += self.network.train_on_batch(x, y)        # 준비한 배치 데이터로 학습 진행
                        memory_learning_idx.append([itr_cnt, delayed_reward])   # 학습이 진행된 인덱스 저장
                    batch_size = 0                          # 학습이 진행되었으니 배치 데이터 크기 초기화

            # Epoch Visualizer
            num_epoches_digit = len(str(num_epoches))
            epoch_str = str(epoch + 1).rjust(num_epoches_digit, '0')    # 1 -> 0001

            self.visualizer.plot(
                epoch_str=epoch_str, num_epoches=num_epoches, epsilon=epsilon,
                action_list=Agent.ACTIONS, actions=memory_action,
                num_stocks=memory_num_stocks, outvals=memory_prob,
                exps=memory_exp_idx, learning=memory_learning_idx,
                initial_balance=self.agent.initial_balance, pvs=memory_pv)

            self.visualizer.save(os.path.join(
                epoch_summary_dir, 'epoch_summary_%s_%s.png' % (settings.timestr, epoch_str)))

            # Epoch 관련 정보 로그 기록
            if pos_learning_cnt + neg_learning_cnt > 0:
                loss /= pos_learning_cnt + neg_learning_cnt
            logger.info("[Epoch %s/%s]\tEpsilon:%.4f\t#Expl.:%d/%d\t"
                        "#Buy:%d\t#Sell:%d\t#Hold:%d\t"
                        "#Stocks:%d\tPV:%s\t"
                        "POS:%s\tNEG:%s\tLoss:%10.6f" % (
                            epoch_str, num_epoches, epsilon, exploration_cnt, itr_cnt,
                            self.agent.num_buy, self.agent.num_sell, self.agent.num_hold,
                            self.agent.num_stocks,
                            locale.currency(self.agent.portfolio_value, grouping=True),
                            pos_learning_cnt, neg_learning_cnt, loss))

            # 학습 관련 정보 갱신
            max_portfolio_value = max(
                max_portfolio_value, self.agent.portfolio_value)
            if self.agent.portfolio_value > self.agent.initial_balance:
                epoch_win_cnt += 1
        # ---------------- 여기 까지 for 문 끝 --------------------

        # 학습 관련 정보 로그 기록
        logger.info("Max PV: %s, \t # Win: %d" % (
            locale.currency(max_portfolio_value, grouping=True), epoch_win_cnt))
# -----------------------------------------------------------------------------------------


    # 배치 데이터 생성
    def _get_batch(self, memory, batch_size, discount_factor, delayed_reward):
        x = np.zeros((batch_size, 1, self.num_features))        # x : 일련의 학습 데이터 및 Agent 상태
        y = np.full((batch_size, self.agent.NUM_ACTIONS), 0.5)  # y : 일련의 지연 보상

        for i, (sample, action, reward) in enumerate(reversed(memory[-batch_size:])):
            x[i] = np.array(sample).reshape((-1, 1, self.num_features))
            y[i, action] = (delayed_reward + 1) / 2     # 지연 보상이 1인 경우 1로, -1인 경우 0으로
            if discount_factor > 0:
                y[i, action] *= discount_factor ** i
        return x, y


    # 학습 데이터를 구성하는 샘플 하나를 생성하는 함수
    def _build_sample(self):
        self.environment.observe()
        if len(self.training_data) > self.training_data_idx + 1:    # 다음 인덱스가 존재하는지 확인
            self.training_data_idx += 1
            self.sample = self.training_data.iloc[self.training_data_idx].tolist()  # 인덱스의 데이터를 받아와서 sample로 저장
            self.sample.extend(self.agent.get_states())     # sample에 Agent 상태를 15개에서 +2개하여 17개로
            return self.sample
        return None


# -----------------------------------------------------------------------------------------
    # 학습된 정책 신경망 모델로 주식투자 시뮬레이션 진행
    def trade(self, model_path=None, balance=2000000):
        if model_path is None:
            return
        self.network.load_model(model_path=model_path)
        validity, action, min_trading_unit = self.fit(balance=balance, num_epoches=1, learning=False)

        return validity, action, min_trading_unit
