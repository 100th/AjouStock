# make_list.py
# Main 모듈을 통해 매매 리스트 생성. skyrocket과 save_csv 모듈 데이터 수정 가능.
# 64비트의 파이썬, 아나콘다 환경에서 실행 가능
import sys
import os
import main_before, main_after, settings
from data import skyrocket, save_csv


# 급등주 포착 ----------------------------------------------------------------
# skyrocket.py 실행
def run_skyrocket():
    skyrocket_period = 21
    skyrocket_criteria = 5
    skyrocket_idx = '0000 ~ 0499'
    # skyrocket_idx = '0500 ~ 0999'
    # skyrocket_idx = '1000 ~ 1499'
    # skyrocket_idx = '1500 ~ 1999'
    # skyrocket_idx = '2000 ~'
    skyrocket.skyrocket_run(skyrocket_period, skyrocket_criteria, skyrocket_idx)


# 급등주 OHLCV를 csv로 저장 ----------------------------------------------------------------
# save_csv.py 실행
def run_save_csv():
    csv_start_date = '2018-05-01'
    save_csv.save_csv_run(csv_start_date)


# Main 실행 ----------------------------------------------------------------
# Main Before 실행
def run_main_before():
    before_start_date = '2018-06-01'
    before_end_date = '2018-07-01'
    before_min_unit = 1
    before_max_unit = 2
    before_delayed = 0.2
    before_learning = 0.001
    before_balance = 10000000
    before_epoch = 10
    before_epsilon = 0.5
    main_before.main_before_run(before_start_date, before_end_date, before_min_unit,
                    before_max_unit, before_delayed, before_learning, before_balance,
                    before_epoch, before_epsilon)


# Main After 실행
def run_main_after():
    after_start_date = '2018-04-02'
    after_min_unit = 1
    after_max_unit = 2
    main_after.main_after_run(after_start_date, after_min_unit, after_max_unit)



# run_skyrocket()
# run_save_csv()
# run_main_before()
run_main_after()
