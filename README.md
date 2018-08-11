# AjouStock
> Stock trading project using Keras with Python

## About
> Not yet

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

## Plan
- 그래프 수정 필요 (화살표 잘못 그려짐)
- GUI에서 진행 상황, 강화학습 진행 로그 보여지도록 기능 추가
- 파일 위치 한 번에 관리하도록 변경 (절대 위치 수정)

## GUI
![gui](/image/v0.1.png)

## Tree Graph
![tree](/image/tree-graph.png)
### Data
- Datamanagement : chart_data와 training_data를 생성하는 모듈
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
- Kiwoom : 키움증권 API로부터 데이터 얻어오고, 내 계좌 정보 얻어오는 모듈
### Main
- Main Before : 강화학습 전에 실행. 주식 데이터를 읽고, 차트 데이터와 학습 데이터를 준비하고, 주식투자 강화학습을 실행하는 모듈
- Main After : 강화학습 후에 실행. 저장된 정책 신경망 모델을 불러와서 실행하는 모듈
- Trading : 키움증권 API를 이용해 실제 트레이딩 하는 모듈
