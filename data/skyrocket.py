# /data/skyrocket.py
# 급등주 포착 알고리즘으로 구매할 종목 추천
import time
import datetime
import requests
import traceback
import pandas as pd
from bs4 import BeautifulSoup as bs


df_code = pd.read_html('http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13', header=0)[0]
df_code.종목코드 = df_code.종목코드.map('{:06d}'.format)
df_code = df_code[['회사명', '종목코드']]
df_code = df_code.rename(columns={'회사명': 'name', '종목코드': 'code'})
# len(df_code)      # 2018.8.2. 기준 2211개
# df_extract = df_code.iloc[100:110,:]
df_extract = df_code.iloc[:10]

code_list=[]
for i in range(len(df_extract)):
    code = df_extract.loc[i].code
    code_list.append(code)


class Skyrocket:
    # Parsing 함수
    def parsing(self, code, page):
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


    # 거래량(volume) dateframe 만드는 함수
    def get_volume_df(self, code):
        url = 'http://finance.naver.com/item/sise_day.nhn?code={code}'.format(code=code)
        res = requests.get(url)
        res.encoding = 'utf-8'
        soup = bs(res.text, 'lxml')

        time.sleep(1.0)

        el_table_navi = soup.find("table", class_="Nnavi")
        el_td_last = el_table_navi.find("td", class_="pgRR")
        pg_last = el_td_last.a.get('href').rsplit('&')[1]
        pg_last = pg_last.split('=')[1]
        pg_last = int(pg_last)

        start_date = datetime.date.today() + datetime.timedelta(days=-26)
        start_date = datetime.datetime.strftime(start_date, '%Y.%m.%d')
        end_date = datetime.datetime.strftime(datetime.datetime.today(), '%Y.%m.%d')

        df_21 = None
        for page in range(1, pg_last+1):
            dataframe = self.parsing(code, page)
            dataframe_filtered = dataframe[dataframe['날짜'] > start_date]
            if df_21 is None:
                df_21 = dataframe_filtered
            else:
                df_21 = pd.concat([df_21, dataframe_filtered])
            if len(dataframe) > len(dataframe_filtered):
                break

        df_21.columns = ["date", "close", "compare", "open", "high", "low", "volume"]
        df_21.drop(['close', 'compare', 'open', 'high', 'low'], axis=1, inplace=True)
        df_21['volume'] = df_21['volume'].astype(int)
        df_21 = df_21.round(0)
        df_21['date'] = pd.to_datetime(df_21.date)
        df_21 = df_21.sort_values(by='date', ascending=False)

        return(df_21)


    # 급등주인지 판단하는 함수
    def check_skyrocket(self, df_21, code):
        # df = self.get_volume_df(code)
        volumes = df_21['volume']

        if len(volumes) < 15:
            return False

        sum_vol14 = 0   # 일별 거래량 누적
        today_vol = 0   # 조회 시작일 거래량

        for i, vol in enumerate(volumes):
            if i == 0:
                today_vol = vol
            elif 1 <= i <= 14:
                sum_vol14 += vol
            else:
                break

        avg_vol14 = sum_vol14 / 14
        if today_vol > avg_vol14 * 10:
            print(today_vol, "<-------------- The volume of TODAY")
            print(int(avg_vol14), "<-------------- The volume of AVERAGE for 14 days")
            skyrocket_ratio = round(today_vol / avg_vol14 * 100, 2)
            print(skyrocket_ratio, "<-------------- %")
            return True, skyrocket_ratio
        else:
            print(today_vol, "<-------------- The volume of TODAY")
            print(int(avg_vol14), "<-------------- The volume of AVERAGE for 14 days")
            skyrocket_ratio = round(today_vol / avg_vol14 * 100, 2)
            print(skyrocket_ratio, "<-------------- %")
            return False, skyrocket_ratio


    # 실행하는 함수
    def run(self, code_list):
        skyrocket_list = []
        skyrocket_ratio_list = []

        num = len(code_list)

        for i in range(num): # enumerate(code_list)
            code = code_list[i]
            df_21 = self.get_volume_df(code)
            print(i, '/', num)
            sky_boolean, skyrocket_ratio = self.check_skyrocket(df_21, code)
            if sky_boolean == True:
                print(code, "<------------- SKYROCKET!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                skyrocket_list.append(code)
                skyrocket_ratio_list.append(skyrocket_ratio)
            else:
                print(code, "<------------- nothing.")

        self.update_skyrocket_list(skyrocket_list, skyrocket_ratio_list)


    # update_skyrocket_list 업데이트 함수
    def update_skyrocket_list(self, skyrocket_list, skyrocket_ratio_list):
        f = open("C:/Users/B-dragon90/Desktop/Github/AjouStock/data/list/skyrocket_list.txt", "wt")
        for i in range(len(skyrocket_list)):
            f.writelines(skyrocket_list[i] + ";" + skyrocket_ratio_list[i] + "%" + "\n")   # 개수는 수정해야 함
        f.close()


if __name__ == "__main__":
    sky = Skyrocket()
    sky.run(code_list)


"""
* 급등주 포착 알고리즘
특정 거래일의 거래량이 이전 시점의 평균 거래량보다 10배 이상 급증하는 종목을 매수
'이전 시점의 평균 거래량'을 특정 거래일 이전의 14일(거래일 기준) 동안의 평균 거래량으로 정의
'거래량 급증'은 특정 거래일의 거래량이 평균 거래량보다 10배 초과일 때 급등한 것으로 정의
"""

# sk = Skyrocket()
# df_21 = sk.get_volume_df(code_list)
# sk.check_skyrocket(df_21, code_list)
# sk.run(df_21, code_list)
