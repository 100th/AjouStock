# /data/save_csv.py
# 원하는 종목의 ohlcv 데이터를 파싱하고 CSV 파일로 저장하는 모듈
import os
import datetime
import traceback
import requests
import pandas as pd
from bs4 import BeautifulSoup as bs


code = '035420'  # NAVER


def parsing(code, page):
    try:
        url = 'http://finance.naver.com/item/sise_day.nhn?code={code}&page={page}'.format(code=code, page=page)
        res = requests.get(url)
        soup = bs(res.text, 'lxml')
        dataframe = pd.read_html(str(soup.find("table")), header=0)[0]
        dataframe = dataframe.dropna()
        return dataframe
    except Exception as e:
        traceback.print_exc()
    return None


# 시작일과 종료일
start_date = datetime.datetime.strftime(datetime.datetime(year=2018, month=1, day=1), '%Y.%m.%d')
end_date = datetime.datetime.strftime(datetime.datetime.today(), '%Y.%m.%d')

ohlcv = None
for page in range(1, pg_last+1):
    dataframe = parsing(code, page)
    dataframe_filtered = dataframe[dataframe['날짜'] > start_date]
    if ohlcv is None:
        ohlcv = dataframe_filtered
    else:
        ohlcv = pd.concat([ohlcv, dataframe_filtered])
    if len(dataframe) > len(dataframe_filtered):
        break

# 데이터 전처리
ohlcv.columns = ["date", "close", "compare", "open", "high", "low", "volume"]
ohlcv.drop('compare', axis=1, inplace=True)
ohlcv_edit = ohlcv.reindex(['date', 'open', 'high', 'low', 'close', 'volume'], axis=1)
ohlcv_edit[['open', 'high', 'low', 'close', 'volume']] = ohlcv[['open', 'high', 'low', 'close', 'volume']].astype(int)
ohlcv_edit = ohlcv_edit.round(0)
ohlcv_edit['date'] = pd.to_datetime(ohlcv_edit.date)
ohlcv_edit = ohlcv_edit.sort_values('date')
# ohlcv_edit.head()

# CSV 파일로 저장
folder = 'C:/Users/B-dragon90/Desktop/Github/AjouStock/data/csv_data'
if not os.path.exists(folder):
    os.makedirs(folder)
path = os.path.join(folder, '{code}.csv'.format(code=code))
ohlcv_edit.to_csv(path, header=False, index=False)
