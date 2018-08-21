# /data/skyrocket.py
# 급등주 포착 알고리즘으로 구매할 종목 추천
import os
import time
import datetime
import requests
import traceback
import settings
import pandas as pd
from bs4 import BeautifulSoup as bs


# 500개씩 종목코드를 나누는 함수
def extract():
    df_code = pd.read_html('http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13', header=0)[0]
    df_code.종목코드 = df_code.종목코드.map('{:06d}'.format)
    df_code = df_code[['회사명', '종목코드']]
    df_code = df_code.rename(columns={'회사명': 'name', '종목코드': 'code'})
    # len(df_code)      # 2018.8.9. 기준 2215개

    df_extract_1 = df_code.loc[:499,:]
    df_extract_2 = df_code.loc[500:999,:]
    df_extract_3 = df_code.loc[1000:1499,:]
    df_extract_4 = df_code.loc[1500:1999,:]
    df_extract_5 = df_code.loc[2000:,:]

    code_list_1 = []
    code_list_2 = []
    code_list_3 = []
    code_list_4 = []
    code_list_5 = []

    for i in range(0, len(df_extract_1)):
        code = df_extract_1.loc[i].code
        code_list_1.append(code)

    for i in range(500, 500+len(df_extract_2)):
        code = df_extract_2.loc[i].code
        code_list_2.append(code)

    for i in range(1000, 1000+len(df_extract_3)):
        code = df_extract_3.loc[i].code
        code_list_3.append(code)

    for i in range(1500, 1500+len(df_extract_4)):
        code = df_extract_4.loc[i].code
        code_list_4.append(code)

    for i in range(2000, 2000+len(df_extract_5)):
        code = df_extract_5.loc[i].code
        code_list_5.append(code)

    return code_list_1, code_list_2, code_list_3, code_list_4, code_list_5


# Parsing 함수
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


# 거래량(volume) dateframe 만드는 함수
def get_volume_df(code, skyrocket_period):
    url = 'http://finance.naver.com/item/sise_day.nhn?code={code}'.format(code=code)
    res = requests.get(url)
    res.encoding = 'utf-8'
    soup = bs(res.text, 'lxml')

    time.sleep(1.0)

    el_table_navi = soup.find("table", class_="Nnavi")
    el_td_last = el_table_navi.find("td", class_="pgRR")
    if el_td_last != None:
        pg_last = el_td_last.a.get('href').rsplit('&')[1]
        pg_last = pg_last.split('=')[1]
        pg_last = int(pg_last)

        start_date = datetime.date.today() + datetime.timedelta(days = -skyrocket_period)
        start_date = datetime.datetime.strftime(start_date, '%Y.%m.%d')
        end_date = datetime.datetime.strftime(datetime.datetime.today(), '%Y.%m.%d')

        extracted_df = None
        for page in range(1, pg_last+1):
            dataframe = parsing(code, page)
            dataframe_filtered = dataframe[dataframe['날짜'] > start_date]
            if extracted_df is None:
                extracted_df = dataframe_filtered
            else:
                extracted_df = pd.concat([extracted_df, dataframe_filtered])
            if len(dataframe) > len(dataframe_filtered):
                break

        extracted_df.columns = ["date", "close", "compare", "open", "high", "low", "volume"]
        extracted_df.drop(['close', 'compare', 'open', 'high', 'low'], axis=1, inplace=True)
        extracted_df['volume'] = extracted_df['volume'].astype(int)
        extracted_df = extracted_df.round(0)
        extracted_df['date'] = pd.to_datetime(extracted_df.date)
        extracted_df = extracted_df.sort_values(by='date', ascending=False)

        return(extracted_df)

    else:
        extracted_df = pd.DataFrame(columns=["date", "volume"])
        return(extracted_df)


# 급등주인지 판단하는 함수
def check_skyrocket(extracted_df, code, skyrocket_period, skyrocket_criteria):
    volumes = extracted_df['volume']
    # print(extracted_df)
    if len(volumes) == 0:
        return 'False', 0.0

    sum_vol = 0   # 일별 거래량 누적
    today_vol = 0   # 조회 시작일 거래량

    for i, vol in enumerate(volumes):
        if i == 0:
            today_vol = vol
        elif 1 <= i <= skyrocket_period:
            sum_vol += vol
        else:
            break


    avg_vol = sum_vol / skyrocket_period
    # print("today vol: ", today_vol)
    # print("avg_vol: ", avg_vol)
    if avg_vol == 0:
        return "False", 0.0
    if today_vol > avg_vol * skyrocket_criteria:
        print(today_vol, "<-------------- The volume of TODAY")
        print(int(avg_vol), "<-------------- The volume of AVERAGE for selected days")
        skyrocket_ratio = round(today_vol / avg_vol * 100, 2)
        print(skyrocket_ratio, "<-------------- %")
        sky_boolean = 'True'
        return sky_boolean, skyrocket_ratio

    else:
        print(today_vol, "<-------------- The volume of TODAY")
        print(int(avg_vol), "<-------------- The volume of AVERAGE for selected days")
        skyrocket_ratio = round(today_vol / avg_vol * 100, 2)
        print(skyrocket_ratio, "<-------------- %")
        sky_boolean = 'False'
        return sky_boolean, skyrocket_ratio


# 만약 skyrocket_idx가 0000 ~ 0499라면
def update_skyrocket_list_first(skyrocket_list, skyrocket_ratio_list):
    f = open(os.path.join(settings.BASE_DIR, "data/list/skyrocket_list.txt"), "wt") # 지우고 새로 쓴다
    for i in range(len(skyrocket_list)):
        f.writelines(str(skyrocket_list[i]) + ";" + str(skyrocket_ratio_list[i]) + "%" + "\n")
    f.close()


# 만약 skyrocket_idx가 0000 ~ 0499가 아니라 나머지라면
def update_skyrocket_list_rest(skyrocket_list, skyrocket_ratio_list):
    f = open(os.path.join(settings.BASE_DIR, "data/list/skyrocket_list.txt"), "a+t") # 맨 뒤에 이어쓴다 (추가)
    for i in range(len(skyrocket_list)):
        f.writelines(str(skyrocket_list[i])+ ";"+ str(skyrocket_ratio_list[i])+ "%" + "\n")
    f.close()


# skyrocket.txt에 급등주 코드와 비율 추가하는 함수
def write_skyrocket_txt(code_list, is_first, skyrocket_period, skyrocket_criteria):
    skyrocket_list = []
    skyrocket_ratio_list = []

    num = len(code_list)

    for i in range(num): # enumerate(code_list)
        code = code_list[i]
        extracted_df = get_volume_df(code, skyrocket_period)
        print(i, '/', num)
        sky_boolean, skyrocket_ratio = check_skyrocket(extracted_df, code, skyrocket_period, skyrocket_criteria)

        if sky_boolean == 'True':
            print(code, "<------------- SKYROCKET!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            skyrocket_list.append(code)
            skyrocket_ratio_list.append(skyrocket_ratio)
        else:
            print(code, "<------------- nothing.")

    if is_first == 'True':
        update_skyrocket_list_first(skyrocket_list, skyrocket_ratio_list)

    else:
        update_skyrocket_list_rest(skyrocket_list, skyrocket_ratio_list)


# skyrocket 실행하는 함수
def skyrocket_run(skyrocket_period, skyrocket_criteria, skyrocket_idx):
    code_list_1, code_list_2, code_list_3, code_list_4, code_list_5 = extract()

    if skyrocket_idx == "0000 ~ 0499":
        is_first = 'True'
        write_skyrocket_txt(code_list_1, is_first, skyrocket_period, skyrocket_criteria)

    elif skyrocket_idx == "0500 ~ 0999":
        is_first = 'False'
        write_skyrocket_txt(code_list_2, is_first, skyrocket_period, skyrocket_criteria)

    elif skyrocket_idx == "1000 ~ 1499":
        is_first = 'False'
        write_skyrocket_txt(code_list_3, is_first, skyrocket_period, skyrocket_criteria)

    elif skyrocket_idx == "1500 ~ 1999":
        is_first = 'False'
        write_skyrocket_txt(code_list_4, is_first, skyrocket_period, skyrocket_criteria)

    else:
        is_first = 'False'
        write_skyrocket_txt(code_list_5, is_first, skyrocket_period, skyrocket_criteria)
