# /learning/visualizer.py
# 시각화 모듈
import numpy as np
import matplotlib.pyplot as plt
from mpl_finance import candlestick_ohlc


class Visualizer:
    def __init__(self):
        self.fig = None  # 캔버스 같은 역할 객체
        self.axes = None  # 차트 그리기 위한 객체


    def prepare(self, chart_data):  # 4x1의 차트를 만들 준비. 캔버스를 만듦.
        self.fig, self.axes = plt.subplots(nrows=4, ncols=1, facecolor='w', sharex=True)
        for ax in self.axes:
            ax.get_xaxis().get_major_formatter().set_scientific(False)
            ax.get_yaxis().get_major_formatter().set_scientific(False)

# 차트 1. 종목 일봉 차트 (epoch와 상관없음)
        self.axes[0].set_title('1. Daily Chart')
        self.axes[0].set_ylabel('Env.')
        x = np.arange(len(chart_data))
        volume = np.array(chart_data)[:, -1].tolist()
        self.axes[0].bar(x, volume, color='b', alpha=0.3)
        ax = self.axes[0].twinx()
        # ohlc = open, high, low, close
        ohlc = np.hstack((x.reshape(-1, 1), np.array(chart_data)[:, 1:-1]))
        candlestick_ohlc(ax, ohlc, colorup='r', colordown='b') # 양봉 : 빨강, 음봉 : 파랑


    def plot(self, epoch_str=None, num_epoches=None, epsilon=None,
            action_list=None, actions=None, num_stocks=None,
            outvals=None, exps=None, learning=None,
            initial_balance=None, pvs=None):
        x = np.arange(len(actions))  # 모든 차트가 공유할 x축 데이터
        actions = np.array(actions)  # 에이전트의 행동 (차트2)
        outvals = np.array(outvals)  # 정책 신경망의 출력 (차트3)
        pvs_base = np.zeros(len(actions)) + initial_balance  # 초기 자본금 (차트4)

# 차트 2. Agent 상태 (수행한 행동 = 배경 색, 보유 주식 수 = 라인 차트)
        colors = ['r', 'b'] # 매수 : 빨강, 매도 : 파랑
        for actiontype, color in zip(action_list, colors):
            for i in x[actions == actiontype]:
                self.axes[1].axvline(i, color=color, alpha=0.3)
        self.axes[1].set_title('2. Agent Status')
        self.axes[1].plot(x, num_stocks, '-k')

# 차트 3. 정책 신경망의 출력 및 탐험
        self.axes[2].set_title('3. Output and Expedition of Network')
        for exp_idx in exps:                        # 탐험 = 노랑
            self.axes[2].axvline(exp_idx, color='y')
        for idx, outval in zip(x, outvals):         # 탐험 X = 하양
            color = 'white'
            if outval.argmax() == 0:
                color = 'r'                         # 매수 = 빨강
            elif outval.argmax() == 1:
                color = 'b'                         # 매도 = 파랑
            self.axes[2].axvline(idx, color=color, alpha=0.1)
        styles = ['.r', '.b']
        for action, style in zip(action_list, styles):
            if len(outvals) == 0:
                print("----------------ERROR-----------------")
                continue
            self.axes[2].plot(x, outvals[:, action], style)

# 차트 4. 포트폴리오 가치
        self.axes[3].set_title('4. Portfolio Value')
        self.axes[3].axhline(initial_balance, linestyle='-', color='gray')
        self.axes[3].fill_between(x, pvs, pvs_base, where=pvs > pvs_base, facecolor='r', alpha=0.2)
        self.axes[3].fill_between(x, pvs, pvs_base, where=pvs < pvs_base, facecolor='b', alpha=0.2)
        self.axes[3].plot(x, pvs, '-k') # 수익 : 빨강, 손실 : 파랑
        for learning_idx, delayed_reward in learning:
            if delayed_reward > 0:  # 학습 수행 위치 표시
                self.axes[3].axvline(learning_idx, color='r', alpha=0.5)
            else:
                self.axes[3].axvline(learning_idx, color='b', alpha=0.5)

        self.fig.suptitle('Epoch %s/%s (epsilon=%.2f)' % (epoch_str, num_epoches, epsilon), fontsize=20)
        plt.tight_layout()
        plt.subplots_adjust(top=.9)


    def clear(self, xlim):    # Figure를 초기화하고 저장하는 함수
        for ax in self.axes[1:]:
            ax.cla()
            ax.relim()
            ax.autoscale()
        self.axes[1].set_ylabel('Agent')
        self.axes[2].set_ylabel('Output')
        self.axes[3].set_ylabel('Value')
        for ax in self.axes:
            ax.set_xlim(xlim)
            ax.get_xaxis().get_major_formatter().set_scientific(False)
            ax.get_yaxis().get_major_formatter().set_scientific(False)
            ax.ticklabel_format(useOffset=False)


    def save(self, path):  # 그림파일로 저장
        plt.savefig(path)


"""
* plot() 함수 인자
epoch_str : Figure 제목으로 표시한 에포크
num_epoches : 총 수행할 에포크 수
epsilon : 탐험률
action_list : 에이전트가 수행할 수 있는 전체 행동 리스트
actions : 에이전트가 수행한 행동 배열
num_stocks : 주식 보유 수 배열
outvals : 정책 신경망의 출력 배열
exps : 탐험 여부 배열
initial_balance : 초기 자본금
pvs : 포트폴리오 가치 배열
"""
