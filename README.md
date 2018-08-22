# AjouStock
> Stock trading project using Keras with Python

## About
> 강화학습과 딥러닝을 이용한 주식 자동매매 프로그램입니다. Data 모듈에서 급등주 포착 알고리즘을 통해 종목을 추천한 후, 선정된 종목의 OHLCV 데이터를 크롤링하여 CSV 파일로 저장합니다. Learning 모듈에서 초기에는 임의로 투자하여 수익이 발생했을 경우에 +1점을 부여하고, 손실이 발생했을 때에는 -1점을 부여하여 딥러닝과 강화학습으로 더 나은 방향으로 학습시킵니다. Supportment 모듈에서는 키움증권 HTS와 API를 통해 원하는 데이터를 요청합니다. Main 모듈에서는 학습한 투자 모델을 바탕으로 실제 트레이딩을 진행하며, 신경망 모델을 만듭니다.

## How to use
- 파이썬 64비트 환경에서 make_list.py를 실행하여 급등주를 포착하고 딥러닝 모델 생성
- 파이썬 32비트 환경에서 trading.py를 실행하여 buy_list.txt와 sell_list.txt를 읽고 실제 거래를 진행

## Development Environment
- Windows 10 64bit
- Python 3.6
- Anaconda 32bit
- 키움증권 Open API+

## Requirements
- keras
- tensorflow
- numPy
- pandas
- matplotlib
- mpl-finance
- pyqt5
- traceback
- requests
- beautifulsoup4
- datetime

## Period
> 2018.7.2. ~ 2018.8.24.

## GUI
![gui](/image/v0.1.png)

## Tree Graph
![tree](/image/tree-graph2.png)

### Data
- Data management : chart_data와 training_data를 생성하는 모듈
- Save CSV : 원하는 종목의 OHLCV 데이터를 파싱하고 CSV 파일로 저장하는 모듈
- Skyrocket : 급등주 포착 알고리즘으로 구매할 종목을 추천하는 모듈

### Learning
- Learner : 정책 학습기 클래스를 가지고 일련의 학습 데이터를 준비하고 정책 신경망을 학습하는 모듈
- Agent : 투자 행동을 수행하고 투자금과 보유 주식을 관리하는 모듈
- Environment : 투자할 종목의 차트 데이터를 관리하는 모듈
- Visualizer : 시각화 모듈
- Network : 투자 행동을 결정하기 위해 신경망을 관리하는 모듈

### Supportment
- Settings : 환경변수와 파일 위치 관리하는 모듈

### Execution for deep learning
- Main Before : 강화학습 전에 실행. 주식 데이터를 읽고, 차트 데이터와 학습 데이터를 준비하고, 주식투자 강화학습을 실행하는 모듈
- Main After : 강화학습 후에 실행. 저장된 정책 신경망 모델을 불러와서 실행하는 모듈
- Make List : Pyqt5 GUI로 연결하여 딥러닝 부분의 세부적인 수치 조정을 하는 모듈

### Execution for kiwoom api
- Trading : Pyqt5 GUI로 연결하고 키움증권 API에 연결해 실제 트레이딩 하는 모듈
- Kiwoom : 키움증권 API로부터 데이터 얻어오고, 내 계좌 정보 얻어오는 모듈
