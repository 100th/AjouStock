# /learning/agent.py
# 투자 행동을 수행하고 투자금과 보유 주식을 관리
import numpy as np


class Agent:
    STATE_DIM = 2  # 주식 보유 비율, 포트폴리오 가치 비율

    TRADING_CHARGE = 0.00015  # 매매 수수료 0.015%
    TRADING_TAX = 0.003  # 거래세 0.3%

    ACTION_BUY = 0  # 매수
    ACTION_SELL = 1  # 매도
    ACTION_HOLD = 2  # 홀딩
    ACTIONS = [ACTION_BUY, ACTION_SELL]
    NUM_ACTIONS = len(ACTIONS)


    def __init__(self, environment, min_trading_unit=1,
        max_trading_unit=2, delayed_reward_threshold=.05):

        self.environment = environment

        self.min_trading_unit = min_trading_unit  # 최소 매매 단위
        self.max_trading_unit = max_trading_unit  # 최대 매매 단위 (이 값을 크게 잡으면 결정한 행동에 대한 확신이 높을 때 더 많이 매매 하도록 설계)
        self.delayed_reward_threshold = delayed_reward_threshold  # 지연보상 임계치 (손익률이 이 값을 넘으면 지연 보상 발생)

        self.initial_balance = 0            # 초기 자본금
        self.balance = 0                    # 현재 현금 잔고
        self.num_stocks = 0                 # 보유 주식 수
        self.portfolio_value = 0            # balance + num_stocks * (현재 주식 가격)
        self.base_portfolio_value = 0       # 직전 학습 시점의 portfolio_value (현재 포트폴리오 가치가 증가했는지 감소했는지를 비교할 기준)
        self.num_buy = 0                    # 매수 횟수
        self.num_sell = 0                   # 매도 횟수
        self.num_hold = 0                   # 홀딩 횟수
        self.immediate_reward = 0           # 즉시 보상 (행동을 수행한 시점에서 수익이 발생하면 1, 아니면 -1)

        self.ratio_hold = 0                 # 주식 보유 비율 = 현재 보유 주식 수 / 최대 보유 주식 수
        self.ratio_portfolio_value = 0      # 포트폴리오 가치 비율 (직전 지연 보상이 발생했을 때의 포트폴리오 가치 대비 현재 포트폴리오 가치 비율)


    def reset(self):    # Agent 상태 초기화 (한 Epoch마다 Agent 상태 초기화)
        self.balance = self.initial_balance
        self.num_stocks = 0
        self.portfolio_value = self.initial_balance
        self.base_portfolio_value = self.initial_balance
        self.num_buy = 0
        self.num_sell = 0
        self.num_hold = 0
        self.immediate_reward = 0
        self.ratio_hold = 0
        self.ratio_portfolio_value = 0


    def set_balance(self, balance): # 초기 자본금 설정
        self.initial_balance = balance


    def get_states(self):   # Agent 상태 획득 (주식 보유 비율, 포트폴리오 가치 비율)
        self.ratio_hold = self.num_stocks / int(self.portfolio_value / self.environment.get_price())
        self.ratio_portfolio_value = self.portfolio_value / self.base_portfolio_value
        return (self.ratio_hold, self.ratio_portfolio_value)


    def decide_action(self, policy_network, sample, epsilon):   # 탐험 또는 정책 신경망에 의한 행동 결정
        confidence = 0.
        if np.random.rand() < epsilon:
            exploration = True
            action = np.random.randint(self.NUM_ACTIONS)  # 무작위로 행동 결정
        else:
            exploration = False
            probs = policy_network.predict(sample)  # 각 행동에 대한 확률
            action = np.argmax(probs) if np.max(probs) > 0.1 else Agent.ACTION_HOLD # 출력 값이 너무 작으면 홀딩
            confidence = probs[action]
        return action, confidence, exploration


    def validate_action(self, action):      # 행동의 유효성 판단
        validity = True
        if action == Agent.ACTION_BUY:      # 적어도 1주를 살 수 있는지 확인
            if self.balance < self.environment.get_price() * (
                1 + self.TRADING_CHARGE) * self.min_trading_unit:
                validity = False
        elif action == Agent.ACTION_SELL:   # 주식 잔고가 있는지 확인
            if self.num_stocks <= 0:
                validity = False
        return validity


    def decide_trading_unit(self, confidence):  # 매수 또는 매도할 주식 수 결정
        if np.isnan(confidence):
            return self.min_trading_unit
        added_trading = max(min(                # confidence가 높을수록 더 크게
            int(confidence * (self.max_trading_unit - self.min_trading_unit)),
            self.max_trading_unit-self.min_trading_unit), 0)
        return self.min_trading_unit + added_trading


    def act(self, action, confidence):      # 행동 수행 (매수, 매도, 홀딩)
        if not self.validate_action(action):
            action = Agent.ACTION_HOLD

        curr_price = self.environment.get_price()

        self.immediate_reward = 0   # 즉시 보상 초기화. 에이전트가 행동을 할 때마다 결정되기 때문에.

        # 매수
        if action == Agent.ACTION_BUY:
            trading_unit = self.decide_trading_unit(confidence)
            balance = self.balance - curr_price * (1 + self.TRADING_CHARGE) * trading_unit
            if balance < 0:
                trading_unit = max(min(int(self.balance / (
                        curr_price * (1 + self.TRADING_CHARGE))),
                        self.max_trading_unit), self.min_trading_unit)
            invest_amount = curr_price * (1 + self.TRADING_CHARGE) * trading_unit
            self.balance -= invest_amount
            self.num_stocks += trading_unit
            self.num_buy += 1

        # 매도
        elif action == Agent.ACTION_SELL:
            trading_unit = self.decide_trading_unit(confidence)
            trading_unit = min(trading_unit, self.num_stocks)
            invest_amount = curr_price * (
                1 - (self.TRADING_TAX + self.TRADING_CHARGE)) * trading_unit
            self.num_stocks -= trading_unit
            self.balance += invest_amount
            self.num_sell += 1

        # 홀딩
        elif action == Agent.ACTION_HOLD:
            self.num_hold += 1
            self.immediate_reward = -1

        # 포트폴리오 가치 갱신
        self.portfolio_value = self.balance + curr_price * self.num_stocks
        profitloss = (self.portfolio_value - self.base_portfolio_value) / self.base_portfolio_value

        # 즉시 보상 판단 : 수익 발생 = 1, 손실 = -1.
        self.immediate_reward = 1 if profitloss >= 0 else -1

        # 지연 보상 판단
        if profitloss > self.delayed_reward_threshold:          # 긍정적 학습
            delayed_reward = 1
            self.base_portfolio_value = self.portfolio_value
        elif profitloss < -self.delayed_reward_threshold:       # 부정적 학습
            delayed_reward = -1
            self.base_portfolio_value = self.portfolio_value
        else:
            delayed_reward = 0
            
        return self.immediate_reward, delayed_reward
