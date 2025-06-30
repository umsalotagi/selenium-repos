# -*- coding: utf-8 -*-
"""
Created on Sun Oct 20 17:41:31 2024

@author: usalotagi

Double heikin ashi 
--> check on hourly to filter, or just store it
--> check on 10 min, with 

keep track of key levels and check on hiekin ashi chart, if 
-- BB band should be high, grren to red etc should happen near that band 

-- check highest green after red and enter that 
-- or highest green after doji green  almost 1% price for 30 min candle 
-- this crossoer should happen below 55 ema or at 55 ema 
-- cyclic and trending where green to red does not apply 

** green to red should happen at ema 55 or above ema 55

>> should follow pattern of weakened red and string green similar 
>> should be large momentum body 
>> MACD cruve should be opening 
>> exit half at weak hiekin ashi, remaining half at MACD closure 
>> cons -- entry is late, possible downtrend 
>> stop loss -- start if trend 
>> go for stocks in new in last 3 days , test for both 15 min and 1 hour data 
# >> dont go for alpha stocks for now 

>> where green to red switch etc happen, should we care -- no , strategy is to catch momentum



ichimoko and heikien ashi 

"""


import pandas_ta as ta
import numpy as np
import pandas as pd
import copy
import time
import datetime as dt
import os
import locale
from kiteconnect import KiteConnect
import statsmodels.api as sm
import csv
import ast
from stocktrends import Renko
from kiteconnect.exceptions import NetworkException


def ATR(DF,n):
    "function to calculate True Range and Average True Range"
    df = DF.copy()
    df['H-L']=abs(df['high']-df['low'])
    df['H-PC']=abs(df['high']-df['close'].shift(1))
    df['L-PC']=abs(df['low']-df['close'].shift(1))
    df['TR']=df[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
    df['ATR'] = df['TR'].rolling(n).mean()
    #df['ATR'] = df['TR'].ewm(span=n,adjust=False,min_periods=n).mean()
    df2 = df.drop(['H-L','H-PC','L-PC'],axis=1)
    return df2['ATR']

def CAGR(DF):
    "function to calculate the Cumulative Annual Growth Rate of a trading strategy"
    df = DF.copy()
    df["cum_return"] = (1 + df["ret"]).cumprod()
    n = len(df)/(252*78)
    CAGR = (df["cum_return"].tolist()[-1])**(1/n) - 1
    return CAGR

def volatility(DF):
    "function to calculate annualized volatility of a trading strategy"
    df = DF.copy()
    vol = df["ret"].std() * np.sqrt(252*78)
    return vol

def sharpe(DF,rf):
    "function to calculate sharpe ratio ; rf is the risk free rate"
    df = DF.copy()
    sr = (CAGR(df) - rf)/volatility(df)
    return sr
    

def max_dd(DF):
    "function to calculate max drawdown"
    df = DF.copy()
    df["cum_return"] = (1 + df["ret"]).cumprod()
    df["cum_roll_max"] = df["cum_return"].cummax()
    df["drawdown"] = df["cum_roll_max"] - df["cum_return"]
    df["drawdown_pct"] = df["drawdown"]/df["cum_roll_max"]
    max_dd = df["drawdown_pct"].max()
    return max_dd


def instrumentLookup(symbol):
    try:
        return nse_instrument_df[nse_instrument_df.tradingsymbol==symbol].instrument_token.values[0]
    except:
        return -1

def fetchOHLCExtended(ticker, interval, period_days, inception_date=None):
    """extracts historical data and outputs in the form of dataframe
       inception date string format - dd-mm-yyyy"""
    instrument = instrumentLookup(ticker)
    if inception_date:
        from_date = dt.datetime.strptime(inception_date, '%d-%m-%Y')
    else:
        from_date = dt.date.today() - dt.timedelta(period_days)
    to_date = dt.date.today()
    data = pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    while True:
        if from_date >= (dt.date.today() - dt.timedelta(100)):
            new_data = pd.DataFrame(kite.historical_data(instrument,from_date,dt.date.today(),interval))
            if data.empty:
                data = new_data
            else:
                data = pd.concat([data, new_data],ignore_index=True)
            break
        else:
            to_date = from_date + dt.timedelta(100)
            new_data = pd.DataFrame(kite.historical_data(instrument,from_date,to_date,interval))
            if data.empty:
                data = new_data
            else:
                data = pd.concat([data, new_data],ignore_index=True)
            from_date = to_date + dt.timedelta(1)
    data.set_index("date",inplace=True)
    return data

invalid_token_tickers = []
def fetchOHLCExtendedAll(tickers, interval, period_days):
    entire_data = {}
    for ticker in tickers:
        try:
            from_date = dt.date.today() - dt.timedelta(period_days)
            entire_data[ticker] = fetchOHLC(ticker, interval, from_date, dt.date.today())
            entire_data[ticker].dropna(inplace=True,how="all")
            
        except NetworkException as e:
            print("Possible too many request error, retyring for ", ticker, e)
            time.sleep(0.2)
            from_date = dt.date.today() - dt.timedelta(period_days)
            entire_data[ticker] = fetchOHLC(ticker, interval, from_date, dt.date.today())
            entire_data[ticker].dropna(inplace=True,how="all")
            
        except Exception as e:
            print("Possible invalid token for", ticker, e)
            invalid_token_tickers.append(ticker)
    return entire_data

def fetchOHLC(ticker, interval, from_date, to_date, instrument_token=None):
    """extracts historical data and outputs in the form of dataframe
       inception date string format - dd-mm-yyyy"""
    if instrument_token:
        instrument = instrument_token
    else:
        instrument = instrumentLookup(ticker)
    #print("fetchOHLC", ticker, instrument, interval, from_date, to_date)
    data = pd.DataFrame(kite.historical_data(instrument,from_date,to_date,interval))
    if data.empty:
        print("No data found for ", ticker)
        return data
    data.set_index("date",inplace=True)
    return data

def trading_view_ema(ohlc, ema_period, column_name):
    # check definition from tradingview and code this line by line
    ohlc[column_name] = ohlc["close"].rolling(window=ema_period).mean()
    multiplier = 2 / (ema_period+1)
    firstRowDone = False
    ema_column = []
    prev = 0
    for index, row in ohlc.iterrows():
        if pd.isna(row[column_name]):
            #print("not good", row[column_name])
            ema_column.append(row[column_name])
        elif not firstRowDone:
            firstRowDone = True
            prev = row[column_name]
            ema_column.append(row[column_name])
            #print ("first ema is sma")
        else:
            new_ema = (row["close"] - prev)*multiplier + prev
            prev = new_ema
            ema_column.append(new_ema)
    ohlc[column_name] = ema_column


def MACD(DF,a,b,c):
    """function to calculate MACD
       typical values a = 12; b =26, c =9"""
    df = DF.copy()
    df["MA_Fast"]=df["close"].ewm(span=a,min_periods=a).mean()
    df["MA_Slow"]=df["close"].ewm(span=b,min_periods=b).mean()
    df["MACD_A"]=df["MA_Fast"]-df["MA_Slow"]
    df["Signal"]=df["MACD_A"].ewm(span=c,min_periods=c).mean()
    return (df["MACD_A"],df["Signal"])

def slope(ser,n):
    "function to calculate the slope of n consecutive points on a plot"
    slopes = [i*0 for i in range(n-1)]
    for i in range(n,len(ser)+1):
        y = ser[i-n:i]
        x = np.array(range(n))
        y_scaled = (y - y.min())/(y.max() - y.min())
        x_scaled = (x - x.min())/(x.max() - x.min())
        x_scaled = sm.add_constant(x_scaled)
        model = sm.OLS(y_scaled,x_scaled)
        results = model.fit()
        slopes.append(results.params.iloc[-1])
    slope_angle = (np.rad2deg(np.arctan(np.array(slopes))))
    return np.array(slope_angle)



def ichimoko(df, fast=9, slow=26, span_b=52, shift_size=26):
    df['Tenkan_sen'] = (df["high"].rolling(window=fast).max() + df["low"].rolling(window=fast).min()) / 2
    df['Kijun_sen'] = (df["high"].rolling(window=slow).max() + df["low"].rolling(window=slow).min()) / 2
    
    df['Senkou_span_A'] = ((df['Tenkan_sen'] + df['Kijun_sen']) / 2).shift(shift_size)
    df['Senkou_span_B'] = (df["high"].rolling(window=span_b).max() + df["low"].rolling(window=span_b).min()) / 2
    df['Senkou_span_B'] = df['Senkou_span_B'].shift(shift_size)
    
    df['Chikou_span'] = df["close"].shift(-shift_size)

def heikinashi(df):
    df['HA_Close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
    df['HA_Open'] = 0.0 
    for i in range(1, len(df)):
        df['HA_Open'].iat[i] = (df['HA_Open'].iat[i - 1] + df['HA_Close'].iat[i - 1]) / 2
    df['HA_Open'].iat[0] = df['open'].iat[0]
    df['HA_High'] = df[['HA_Open', 'HA_Close']].join(df['high']).max(axis=1)
    df['HA_Low'] = df[['HA_Open', 'HA_Close']].join(df['low']).min(axis=1)
    
    df['Bullish'] = (df['HA_Close'] > df['HA_Open']) & (df['HA_Low'] == df['HA_Open'])
    df['Bearish'] = (df['HA_Close'] < df['HA_Open']) & (df['HA_High'] == df['HA_Open'])
    df['Doji_Bearish'] = (df['HA_Close'] < df['HA_Open']) & (df['HA_High'] != df['HA_Open']) & np.abs(df['HA_Close'] - df['HA_Open']) < ((df['HA_High'] - df['HA_Low']) * 0.1)
    df['Doji_Bullish'] = (df['HA_Close'] > df['HA_Open']) & (df['HA_Low'] != df['HA_Open']) & np.abs(df['HA_Close'] - df['HA_Open']) < ((df['HA_High'] - df['HA_Low']) * 0.1)
    # medium to large body - to be calculated with percentage of close price
    df['large_body'] = np.abs(df['HA_Close'] - df['HA_Open']) > df['HA_Close'] * 0.001
    
    # size matter video from trading institute youtube 
    # check in 1 hour if we are in bull with respect to ichimoko cloud then enter with 15 min data 
    # stock whoes earning are nearing announced 
    
    # 3 green candle / or dojo and then 2/3 large body red -- then enter trade , also  confirmt with candles 
   
    
    

#================================= constants ==================================

investment = 10000
cwd = os.chdir("C:\\Users\\usalotagi\\Python\\webdriver")
locale.setlocale(locale.LC_ALL, '')
date_strftime_format = "%Y-%m-%y %H:%M:%S"
access_token = open("access_token.txt",'r').read()
key_secret = open("api_key.txt",'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
kite.set_access_token(access_token)


nse_instrument_dump = kite.instruments("NSE")
nse_instrument_df = pd.DataFrame(nse_instrument_dump)

ohlc_dict = {}
tickers_signal = {}
tickers_ret = {}
only_renko = {}




#================================== strategy ==================================
# 1. test it for nifty 50
# 2. then test is for positive/negative alpha 3 months 1 stock
#============ code to run the strategy 
# 3. then test it for options alpha 3 months 
# 4. if time permits test it for 1 month alpha

def run_strategy(interval, tickers, tickers_strategy_definition, start_day_list, end_day_list, enter_strategy_list, exit_strategy_list):

    global entire_data, entire_data_hr, ohlc_dict_hr, ohlc_dict, higher_interval
    
    print("started downloading data", interval)
    entire_data = fetchOHLCExtendedAll(tickers, interval, 100) #75 # 120 #30
    print("started downloading 60 min data")
    entire_data_hr = fetchOHLCExtendedAll(tickers, higher_interval, period_days=180) #150
    
    
    #tickers.remove(invalid_token_tickers)
    
    ohlc_dict_hr = copy.deepcopy(entire_data_hr)
    ohlc_dict = copy.deepcopy(entire_data)
    
    for ticker in tickers:
        ohlc_dict_hr[ticker]["ema_9_new"]=ohlc_dict_hr[ticker]["close"].ewm(span=9,min_periods=9).mean()
        ohlc_dict_hr[ticker]["ema_13_new"]=ohlc_dict_hr[ticker]["close"].ewm(span=13,min_periods=13).mean()
        ohlc_dict_hr[ticker]["ema_55_new"]=ohlc_dict_hr[ticker]["close"].ewm(span=55,min_periods=55).mean()

        ohlc_dict_hr[ticker].dropna(inplace=True)
        #ohlc_dict_hr[ticker].index = ohlc_dict_hr[ticker].index.tz_localize(None)
        
        ichimoko(ohlc_dict_hr[ticker], fast=9, slow=26, span_b=52, shift_size=26)
        heikinashi(ohlc_dict_hr[ticker])
        
        pass
        
    
    
    for ticker in tickers:
        tickers_signal[ticker] = ""
        tickers_ret[ticker] = []
        
        print("calculating ATR and rolling max price for ",ticker)
        ohlc_dict[ticker]["ATR"] = ATR(ohlc_dict[ticker],20)
        
        trading_view_ema(ohlc_dict[ticker], 9, "ema_9")
        trading_view_ema(ohlc_dict[ticker], 13, "ema_13")
        trading_view_ema(ohlc_dict[ticker], 55, "ema_55")
        
        macd, macd_sig = MACD(ohlc_dict[ticker],12,26,9)
        ohlc_dict[ticker]["macd"]= macd
        ohlc_dict[ticker]["macd_sig"]= macd_sig
        ohlc_dict[ticker]["macd_slope"] = slope(ohlc_dict[ticker]["macd"],5)
        ohlc_dict[ticker]["macd_sig_slope"] = slope(ohlc_dict[ticker]["macd_sig"],5)
        
        ohlc_dict[ticker]["macd_buy"] = (ohlc_dict[ticker]["macd"]>ohlc_dict[ticker]["macd_sig"]) & (ohlc_dict[ticker]["macd"].shift(1)<ohlc_dict[ticker]["macd_sig"].shift(1))
        ohlc_dict[ticker]["macd_buy_signal"] = ohlc_dict[ticker]["macd_buy"] & (ohlc_dict[ticker]["macd_slope"]>ohlc_dict[ticker]["macd_sig_slope"])
        #ohlc_renko[ticker]["macd_buy_2"] = (ohlc_renko[ticker]["macd"]>ohlc_renko[ticker]["macd_sig"]) & (ohlc_renko[ticker]["macd_slope"]>ohlc_renko[ticker]["macd_sig_slope"])

        ohlc_dict[ticker]["macd_sell"] = (ohlc_dict[ticker]["macd"]<ohlc_dict[ticker]["macd_sig"]) & (ohlc_dict[ticker]["macd"].shift(1)>ohlc_dict[ticker]["macd_sig"].shift(1))
        ohlc_dict[ticker]["macd_sell_signal"] = ohlc_dict[ticker]["macd_sell"] & (ohlc_dict[ticker]["macd_slope"]<ohlc_dict[ticker]["macd_sig_slope"])
        #ohlc_renko[ticker]["macd_sell_2"] = (ohlc_renko[ticker]["macd"]<ohlc_renko[ticker]["macd_sig"]) & (ohlc_renko[ticker]["macd_slope"]<ohlc_renko[ticker]["macd_sig_slope"])

        ohlc_dict[ticker].dropna(inplace=True)
        #ohlc_dict[ticker].set_index('Date', inplace=True)

        ichimoko(ohlc_dict[ticker], fast=9, slow=26, span_b=52, shift_size=26)
        heikinashi(ohlc_dict[ticker])
        pass
    

    # run in loops
    for i in range(len(enter_strategy_list)):
        global enter_strategy, exit_strategy

        enter_strategy = enter_strategy_list[i]
        exit_strategy = exit_strategy_list[i]
        run_other_parts_of_strategy(ohlc_dict, interval, tickers, tickers_strategy_definition,  enter_strategy, exit_strategy)
    pass
    
    

def run_other_parts_of_strategy(ohlc_dict, interval, tickers, tickers_strategy_definition, enter_strategy, exit_strategy):

    ohlc_renko = copy.deepcopy(ohlc_dict)
    
        
    tickers_signal = {}
    tickers_ret = {}
    for ticker in tickers:
        tickers_signal[ticker] = ""
        tickers_ret[ticker] = [0]
        
    final_output = []
    final_output_2 = {}
    global output_all, sell_output_all
    output_all =  None
    sell_output_all = None
    
    
    for ticker in tickers:
        buy_enter_time = []
        buy_enter_price = []
        buy_exit_time = []
        buy_exit_price = []
        buy_symbol = []
        
        sell_symbol = []
        sell_enter_time = []
        sell_enter_price = []
        sell_exit_time = []
        sell_exit_price = []
        
        stop_loss = None
        
        global check_hourly_bull, check_crossover, check_interval_bull, check_price_above_cloud, check_chiku_above_cloud
        global check_heikin_ashi, check_chiku_above_price, is_day_trade
        global exit_heikin_ashi, exit_crossunder, exit_when_in_cloud
        global check_higher_frame
        
        print("calculating returns for ",ticker)
        for i in range(1,len(ohlc_renko[ticker])):
            index = ohlc_renko[ticker].index[i]
            #print(ticker, i, index)
            if tickers_signal[ticker] == "":
                
                if (index.hour >= 15 and index.minute >= 0):
                    continue
                if (index.hour >= 14 and index.minute >= 55):
                    continue
                
                
                # create overbought and oversold lines by yourself and trade on it 
                enter_buy = True
                enter_sell = True

                is_bull_r = ohlc_renko[ticker]["ema_9"].iloc[i]>ohlc_renko[ticker]["ema_55"].iloc[i] and ohlc_renko[ticker]["ema_9"].iloc[i]>ohlc_renko[ticker]["ema_13"].iloc[i]
                is_bear_r = ohlc_renko[ticker]["ema_9"].iloc[i]<ohlc_renko[ticker]["ema_55"].iloc[i] and ohlc_renko[ticker]["ema_9"].iloc[i]<ohlc_renko[ticker]["ema_13"].iloc[i]
                
                if check_interval_bull:
                    if not is_bull_r:
                        enter_buy = False
                    if not is_bear_r:
                        enter_sell = False
                
                # this is error
                buy_1 = ohlc_dict_hr[ticker][ohlc_dict_hr[ticker].index <= index].iloc[-1]
                is_bull_hourly = buy_1["ema_9_new"]>buy_1["ema_55_new"] and buy_1["ema_9_new"]>buy_1["ema_13_new"]
                sell_1 = ohlc_dict_hr[ticker][ohlc_dict_hr[ticker].index <= index].iloc[-1]
                is_bear_hourly = sell_1["ema_9_new"]<sell_1["ema_55_new"] and sell_1["ema_9_new"]<sell_1["ema_13_new"]
                
                if check_hourly_bull:
                    if not is_bull_hourly:
                        enter_buy = False
                    if not is_bear_hourly:
                        enter_sell = False

                if check_price_above_cloud:
                    if ohlc_renko[ticker]["close"].iloc[i] < ohlc_renko[ticker]["Senkou_span_A"].iloc[i]:
                        enter_buy = False
                    if ohlc_renko[ticker]["close"].iloc[i] > ohlc_renko[ticker]["Senkou_span_B"].iloc[i]:
                        enter_sell = False
                
                if check_crossover:
                    one = ohlc_renko[ticker]["Tenkan_sen"].iloc[i] > ohlc_renko[ticker]["Kijun_sen"].iloc[i]
                    two = ohlc_renko[ticker]["Tenkan_sen"].iloc[i-1] <= ohlc_renko[ticker]["Kijun_sen"].iloc[i-1]
                    if not (one and two):
                        enter_buy = False
                    one = ohlc_renko[ticker]["Tenkan_sen"].iloc[i] < ohlc_renko[ticker]["Kijun_sen"].iloc[i]
                    two = ohlc_renko[ticker]["Tenkan_sen"].iloc[i-1] >= ohlc_renko[ticker]["Kijun_sen"].iloc[i-1]
                    if not (one and two):
                        enter_sell = False
                
                # shift by 26 period : shift_size
                if check_chiku_above_cloud:
                    if ohlc_renko[ticker].shift(26)["Chikou_span"].iloc[i] < ohlc_renko[ticker].shift(26)["Senkou_span_A"].iloc[i]:
                        enter_buy = False
                    if ohlc_renko[ticker].shift(26)["Chikou_span"].iloc[i] > ohlc_renko[ticker].shift(26)["Senkou_span_B"].iloc[i]:
                        enter_sell = False
                        
                if check_chiku_above_price:
                    if ohlc_renko[ticker].shift(26)["Chikou_span"].iloc[i] < ohlc_renko[ticker].shift(26)["close"].iloc[i]:
                        enter_buy = False
                    if ohlc_renko[ticker].shift(26)["Chikou_span"].iloc[i] > ohlc_renko[ticker].shift(26)["close"].iloc[i]:
                        enter_sell = False
                

                if check_higher_frame:
                    if ohlc_dict_hr[ticker]["close"].iloc[i] < ohlc_dict_hr[ticker]["Senkou_span_A"].iloc[i]:
                        enter_buy = False
                    if ohlc_dict_hr[ticker]["close"].iloc[i] > ohlc_dict_hr[ticker]["Senkou_span_B"].iloc[i]:
                        enter_sell = False
                        
                # Bullish, Bearish, Doji_Bearish, Doji_Bullish, large_body
                if check_heikin_ashi:
                    # bull
                    if ohlc_renko[ticker]["Bullish"].iloc[i] and ohlc_renko[ticker]["large_body"].iloc[i]:
                        onee = ohlc_renko[ticker]["HA_Open"].iloc[i] or ohlc_renko[ticker]["HA_Close"].iloc[i]
                
                
                if enter_buy:
                    tickers_signal[ticker] = "Buy"
                    buy_enter_time.append(index)
                    buy_enter_price.append(ohlc_renko[ticker]["close"].iloc[i])
                    buy_symbol.append(ticker)
                    stop_loss = ohlc_renko[ticker]["Senkou_span_B"].iloc[i]
                        
                elif enter_sell:
                    tickers_signal[ticker] = "Sell"
                    sell_enter_time.append(index)
                    sell_enter_price.append(ohlc_renko[ticker]["close"].iloc[i])
                    sell_symbol.append(ticker)
                    stop_loss = ohlc_renko[ticker]["Senkou_span_A"].iloc[i]
                pass
            
            elif tickers_signal[ticker] == "Buy":
                if ohlc_renko[ticker]["low"].iloc[i] < stop_loss:
                    tickers_signal[ticker] = ""
                    buy_exit_price.append(stop_loss)
                    buy_exit_time.append(index)
                else:
                    exitNow = False
                    if exit_heikin_ashi:
                        # todo
                        pass
                    if exit_crossunder:
                        one = ohlc_renko[ticker]["Tenkan_sen"].iloc[i] < ohlc_renko[ticker]["Kijun_sen"].iloc[i]
                        two = ohlc_renko[ticker]["Tenkan_sen"].iloc[i-1] >= ohlc_renko[ticker]["Kijun_sen"].iloc[i-1]
                        if not (one and two):
                            exitNow = True
                        pass
                    if exit_when_in_cloud:
                        if ohlc_renko[ticker]["close"].iloc[i] < ohlc_renko[ticker]["Senkou_span_A"].iloc[i]:
                            exitNow = True
                        pass
                    
                    if exitNow:
                        tickers_signal[ticker] = ""
                        buy_exit_price.append(ohlc_renko[ticker]["close"].iloc[i])
                        buy_exit_time.append(index)
                    elif is_day_trade and (index.hour == 15 and index.minute == 5):
                        # trading end time
                        tickers_signal[ticker] = ""
                        buy_exit_price.append(ohlc_renko[ticker]["close"].iloc[i])
                        buy_exit_time.append(index)
                pass
            
            elif tickers_signal[ticker] == "Sell":

                
                if ohlc_renko[ticker]["high"].iloc[i] > stop_loss :
                    tickers_signal[ticker] = ""
                    sell_exit_price.append(stop_loss)
                    sell_exit_time.append(index)
                else: 
                    exitNow = False
                    if exit_heikin_ashi:
                        # todo
                        pass
                    if exit_crossunder:
                        one = ohlc_renko[ticker]["Tenkan_sen"].iloc[i] > ohlc_renko[ticker]["Kijun_sen"].iloc[i]
                        two = ohlc_renko[ticker]["Tenkan_sen"].iloc[i-1] <= ohlc_renko[ticker]["Kijun_sen"].iloc[i-1]
                        if not (one and two):
                            exitNow = True
                        pass
                    if exit_when_in_cloud:
                        if ohlc_dict_hr[ticker]["close"].iloc[i] > ohlc_dict_hr[ticker]["Senkou_span_B"].iloc[i]:
                            exitNow = True
                        pass
                    
                    
                    if exitNow:
                        tickers_signal[ticker] = ""
                        sell_exit_price.append(ohlc_renko[ticker]["close"].iloc[i])
                        sell_exit_time.append(index)
                    elif is_day_trade and (index.hour == 15 and index.minute == 5):
                        # trading end time
                        tickers_signal[ticker] = ""
                        sell_exit_price.append(ohlc_renko[ticker]["close"].iloc[i])
                        sell_exit_time.append(index)
                pass
            
        if len(buy_enter_time) != len(buy_exit_time):
            print("SOMETHING WRONG", buy_enter_time, "exit", buy_exit_time)
            buy_enter_time.pop()
            buy_enter_price.pop()
            buy_symbol.pop()
        if len(sell_enter_time) != len(sell_exit_time):
            print("SOMETHING WRONG SELL", sell_enter_time, "sell_exit", sell_exit_time)
            sell_enter_time.pop()
            sell_enter_price.pop()
            sell_symbol.pop()
            
        output = pd.DataFrame(data = {"time": buy_enter_time, "buy_symbol": buy_symbol, "buy_enter_price": buy_enter_price, "buy_exit_price" : buy_exit_price, "buy_exit_time": buy_exit_time})
        output["profit"] = output["buy_exit_price"] - output["buy_enter_price"]
        output["ret"] = output["profit"]/output["buy_enter_price"]
        output["holding_time"] = output["buy_exit_time"] - output["time"]
        
        sell_output = pd.DataFrame(data = {"time": sell_enter_time, "sell_symbol": sell_symbol, "sell_enter_price": sell_enter_price, "sell_exit_price" : sell_exit_price, "sell_exit_time": sell_exit_time})
        sell_output["profit"] = sell_output["sell_enter_price"] - sell_output["sell_exit_price"]
        sell_output["ret"] = sell_output["profit"]/sell_output["sell_enter_price"]
        sell_output["holding_time"] = sell_output["sell_exit_time"] - sell_output["time"]
        
        if len(output) == 0:
            #print(len(output), " length of output..")
            output_summary = {"symbol": ticker, "interval": interval, "mean_ret": 0, 
                              "strike": 0, "avg_holding_period" : 0, "no_of_trades": len(output)}
        else:
            #output["ret"].mean()
            #print("now again ")
            #output["holding_time"].mean()
            # assuming its weekly return, calculating all max_dd, cagr and sharpe metrices
            output_summary = {"symbol": ticker, "interval": interval, "mean_ret": output["ret"].mean(), 
                        "strike": (output["profit"] > 0).sum() / len(output),
                        "avg_holding_period" : output["holding_time"].mean(),"no_of_trades": len(output)}
            
        if len(sell_output) == 0:
            #print(len(output), " length of output..")
            output_summary_sell = {"symbol": ticker, "interval": interval, "mean_ret": 0, 
                              "strike": 0, "avg_holding_period" : 0, "no_of_trades": len(sell_output)}
        else:
            # assuming its weekly return, calculating all max_dd, cagr and sharpe metrices
            output_summary_sell = {"symbol": ticker, "interval": interval, "mean_ret": sell_output["ret"].mean(), 
                        "strike": (sell_output["profit"] > 0).sum() / len(sell_output),
                        "avg_holding_period" : sell_output["holding_time"].mean(),"no_of_trades": len(sell_output)}
            
        final_output_2[ticker + "BUY"] = output_summary
        final_output_2[ticker + "SELL"] = output_summary_sell
        final_output.append(output_summary)
        final_output.append(output_summary_sell)
        
        
        
        if len(output) > 0:
            if output_all is not None:
                output_all = pd.concat([output_all, output], ignore_index=True)
            else:
                output_all = output
        if len(sell_output) > 0:
            #print("ouuuuu", sell_output)
            if sell_output_all is not None:
                sell_output_all = pd.concat([sell_output_all, sell_output], ignore_index=True) 
            else:
                sell_output_all = sell_output
    
    if type(output_all) == pd.DataFrame:
        cagr_buy = (output_all["buy_exit_price"].sum() / output_all["buy_enter_price"].sum()) ** (252/5) - 1
        no_of_trades_buy = len(output_all)
        avg_return = round(output_all["ret"].sum()/no_of_trades_buy, 5)
        sum_return = round(output_all["ret"].sum(), 5)
        strike_buy = round( (output_all["profit"] > 0).sum() / no_of_trades_buy , 2)
        str_output_buy_pretext = "BUY interval {} tickers_strategy_definition {}, enter {}, exit {}, tickers {}".format(interval, tickers_strategy_definition, enter_strategy, exit_strategy, "no_storing_here")
        str_output_buy = "BUY cagr {} avg_return {} simple_return_buy {} strike {} trades {} cagr_per_trade {} profit_per_trade {}".format(cagr_buy, avg_return, sum_return, strike_buy, no_of_trades_buy, cagr_buy/no_of_trades_buy, sum_return/no_of_trades_buy)
        serious_output.append(str_output_buy_pretext)
        serious_output.append(str_output_buy)
        print(str_output_buy_pretext)
        print(str_output_buy)
    
    if type(sell_output_all) == pd.DataFrame:
        cagr_sell = (sell_output_all["sell_enter_price"].sum() / sell_output_all["sell_exit_price"].sum()) ** (252/5) - 1
        no_of_trades_sell = len(sell_output_all)
        avg_return = round( sell_output_all["ret"].sum()/no_of_trades_sell , 5)
        sum_return = round( sell_output_all["ret"].sum() , 5)
        strike_sell = round( (sell_output_all["profit"] > 0).sum() / no_of_trades_sell , 2)
        str_output_sell_pretext = "SELL interval {} , tickers_strategy_definition {}, enter {}, exit {}, tickers {}".format(interval, tickers_strategy_definition, enter_strategy, exit_strategy,  "no_storing_here")
        str_output_sell = "SELL cagr {} avg_return {} simple_return_buy {} strike {} trades {} cagr_per_trade {} profit_per_trade {}".format(cagr_sell, avg_return, sum_return, strike_sell, no_of_trades_sell, cagr_sell/no_of_trades_sell, sum_return/no_of_trades_sell)
        serious_output.append(str_output_sell_pretext)
        serious_output.append(str_output_sell)
        print(str_output_sell_pretext)
        print(str_output_sell)
        pass
    pass

    

#==============================================================================


three_month_alpha_options = ['MCX','TRENT','PERSISTENT','MPHASIS','BALRAMCHIN','SHRIRAMFIN','LUPIN','MGL','GLENMARK','NAUKRI','IEX','COFORGE','PEL','DIXON','LTIM','INFY','VOLTAS','PIIND','SYNGENE','SBILIFE','ICICIPRULI','OFSS','HCLTECH','ICICIGI','JUBLFOOD','COLPAL','BAJAJ-AUTO','BHARTIARTL','SUNPHARMA','BAJAJFINSV','TECHM']

nifty_options_stocks = ['M&M', 'ULTRACEMCO', 'HAL', 'TITAN', 'ADANIPORTS', 'COALINDIA', 'ASIANPAINT', 'POWERGRID', 'BAJAJ-AUTO', 'BAJAJFINSV', 'WIPRO', 'TRENT', 'IOC', 'NESTLEIND', 'SIEMENS', 'JSWSTEEL', 'BEL', 'DLF', 'SBILIFE', 'TATASTEEL', 'RELIANCE', 'TCS', 'HDFCBANK', 'BHARTIARTL', 'ICICIBANK', 'INFY', 'SBIN', 'HINDUNILVR', 'ITC', 'LT', 'HCLTECH', 'BAJFINANCE', 'SUNPHARMA', 'TATAMOTORS', 'ONGC', 'NTPC', 'MARUTI', 'AXISBANK', 'KOTAKBANK', 'ADANIENT', 'INDIGO', 'GRASIM', 'PFC', 'LTIM', 'VEDL', 'RECLTD', 'PIDILITIND', 'HDFCLIFE', 'ABB', 'TECHM', 'BPCL', 'AMBUJACEM', 'GAIL', 'GODREJCP', 'HINDALCO', 'BRITANNIA', 'DIVISLAB', 'TATAPOWER', 'CIPLA', 'EICHERMOT', 'TVSMOTOR', 'MOTHERSON', 'BANKBARODA', 'CHOLAFIN', 'PNB', 'SHRIRAMFIN', 'HAVELLS', 'TATACONSUM', 'TORNTPHARM', 'INDUSTOWER', 'DABUR', 'HEROMOTOCO', 'ZYDUSLIFE', 'DRREDDY', 'INDUSINDBK', 'ICICIGI', 'ICICIPRULI', 'UNITDSPR', 'CUMMINSIND', 'LUPIN', 'POLYCAB', 'IDEA', 'COLPAL', 'APOLLOHOSP', 'GMRINFRA', 'CANBK', 'OFSS', 'BHEL', 'JINDALSTEL', 'HDFCAMC', 'NAUKRI', 'BOSCHLTD', 'HINDPETRO', 'INDHOTEL', 'SHREECEM', 'AUROPHARMA', 'MARICO', 'PERSISTENT', 'GODREJPROP', 'MUTHOOTFIN', 'SRF', 'DIXON', 'IRCTC', 'BHARATFORG', 'ALKEM', 'ASHOKLEY', 'SBICARD', 'BERGEPAINT', 'PIIND', 'OBEROIRLTY', 'ABBOTINDIA', 'NMDC', 'LTTS', 'VOLTAS', 'CONCOR', 'MPHASIS', 'ABCAPITAL', 'MRF', 'BALKRISIND', 'IDFCFIRSTB', 'TATACOMM', 'PETRONET', 'SAIL', 'UBL', 'ASTRAL', 'AUBANK', 'COROMANDEL', 'GLENMARK', 'FEDERALBNK', 'PAGEIND', 'UPL', 'BIOCON', 'GUJGASLTD', 'ACC', 'JUBLFOOD', 'COFORGE', 'LTF', 'ESCORTS', 'EXIDEIND', 'DEEPAKNTR', 'M&MFIN', 'MFSL', 'IGL', 'LICHSGFIN', 'DALBHARAT', 'JKCEMENT', 'IPCALAB', 'SYNGENE', 'APOLLOTYRE', 'BANDHANBNK', 'NATIONALUM', 'SUNTV', 'ABFRL', 'HINDCOPPER', 'CROMPTON', 'LALPATHLAB', 'TATACHEM', 'MCX', 'LAURUSLABS', 'PEL', 'ATUL', 'AARTIIND', 'CHAMBLFERT', 'RAMCOCEM', 'BATAINDIA', 'IEX', 'INDIAMART', 'BSOFT', 'MGL', 'MANAPPURAM', 'GRANULES', 'NAVINFLUOR', 'PVRINOX', 'RBLBANK', 'CUB', 'BALRAMCHIN', 'CANFINHOME', 'METROPOLIS', 'GNFC']
nifty_options_stocks =  ['M&M', 'ULTRACEMCO']

# ============ 

start_day_list = [(9,1)]
end_day_list = [(9,30)]
enter_stategy_list = ["macd_buy_2"]
exit_strategy_list = ["macd"]


serious_output = []

#tickers = 
many_tickers = [nifty_options_stocks]
many_tickers_names = ["nifty_options_stocks"]

for i in range(0, len(many_tickers)):
    tickers = many_tickers[i]
    ticker_name = many_tickers_names[i]
    higher_interval = "60minute"
    global check_hourly_bull, check_crossover, check_interval_bull, check_price_above_cloud, check_chiku_above_cloud
    global check_heikin_ashi, check_chiku_above_price, is_day_trade
    global exit_heikin_ashi, exit_crossunder, exit_when_in_cloud, check_higher_frame
    serious_output = []
    t1 = ticker_name + "_10min_2atr"
    check_hourly_bull, check_crossover, check_interval_bull, check_price_above_cloud = True, True, True, True
    check_chiku_above_cloud, check_heikin_ashi, check_chiku_above_price = False, False, False
    check_higher_frame = True
    is_day_trade = True
    exit_heikin_ashi = False
    exit_crossunder = True
    exit_when_in_cloud = False
    
    run_strategy("15minute", tickers, ticker_name + "_15min_10atr_2renko", start_day_list, end_day_list, enter_stategy_list, exit_strategy_list)
    with open("ichimoku_"+ticker_name + "_15min_crossover" + ".txt", "w") as file:
        for line in serious_output:
            file.write(line + "\n")
    
    
#
#CAGR(strategy_df)
#sharpe(strategy_df,0.025)
#max_dd(strategy_df)  


# vizualization of strategy return
#(1+strategy_df["ret"]).cumprod().plot()
